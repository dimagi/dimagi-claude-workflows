#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""
Plan and record a babysit-prs sweep.

Subcommands:

    plan    Enumerate open PRs, classify each quiet/active, and resolve a local
            checkout for the ones needing fix work. Emits JSON to stdout.
    record  Refresh the state file from a plan produced by ``plan``, pruning
            entries for PRs that are no longer open.

Examples:

    # full sweep plan
    uv run sweep_prs.py plan --limit 10 > plan.json

    # single PR (number in the current repo, owner/repo#N, or a PR URL)
    uv run sweep_prs.py plan --pr 3999

    # write state back once the sweep is done
    uv run sweep_prs.py record --plan plan.json --note '<pr-url>=rebased on main'

State lives in ~/.local/state/babysit-prs/state.json keyed by PR URL. Keys the
script does not own (e.g. ``note``) are preserved across records.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

DEFAULT_STATE_FILE = Path.home() / ".local/state/babysit-prs/state.json"
SRC_ROOT = Path(os.environ.get("BABYSIT_SRC_ROOT", Path.home() / "src"))
WORKTREE_SUFFIX = "babysit"

# A stored conclusion in this set means the PR's checks are done and green, so an
# unchanged updatedAt is enough to call the PR quiet without any per-PR API call.
TERMINAL_GOOD = {"SUCCESS", "SKIPPED"}
# CheckRun conclusions / StatusContext states that mean "not finished yet".
NOT_FINISHED = {"PENDING", "QUEUED", "IN_PROGRESS", "WAITING", "REQUESTED", "EXPECTED"}
FAILED = {"FAILURE", "TIMED_OUT", "CANCELLED", "ERROR", "ACTION_REQUIRED"}
# Enumerate enough open PRs that pruning is measured against all of them.
SEARCH_FLOOR = 100
PR_VIEW_FIELDS = (
    "headRefOid,headRefName,baseRefName,isDraft,mergeStateStatus,"
    "headRepositoryOwner,statusCheckRollup"
)


class GhError(RuntimeError):
    pass


def run_gh(args: list[str]) -> Any:
    """Run a gh command that emits JSON and return the parsed result."""
    proc = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise GhError(f"gh {' '.join(args)} failed: {proc.stderr.strip()}")
    out = proc.stdout.strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise GhError(f"gh {' '.join(args)} returned unparseable output: {exc}") from exc


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", "-C", str(repo)] + args, capture_output=True, text=True
    )
    if check and proc.returncode != 0:
        raise GhError(f"git {' '.join(args)} in {repo} failed: {proc.stderr.strip()}")
    return proc


def load_state(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text() or "{}")
    except json.JSONDecodeError:
        return {}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def whoami() -> str:
    return run_gh(["api", "user"])["login"]


# ---------------------------------------------------------------------------
# PR enumeration
# ---------------------------------------------------------------------------

PR_URL_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")
PR_REF_RE = re.compile(r"^(?:([^/\s]+)/([^#\s]+)#)?(\d+)$")


def parse_pr_ref(ref: str) -> tuple[str, int]:
    """Resolve a PR reference to ``(owner/repo, number)``."""
    match = PR_URL_RE.search(ref)
    if match:
        return f"{match.group(1)}/{match.group(2)}", int(match.group(3))
    match = PR_REF_RE.match(ref.strip())
    if not match:
        raise GhError(f"cannot parse PR reference: {ref!r}")
    owner, repo, number = match.groups()
    if owner and repo:
        return f"{owner}/{repo}", int(number)
    return run_gh(["repo", "view", "--json", "nameWithOwner"])["nameWithOwner"], int(number)


def search_prs(
    owners: list[str], limit: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    """Return (all open PRs found, the ``limit`` most recently active, truncated?).

    The full list is what state pruning must be measured against — pruning
    against the truncated list would drop state for still-open PRs. When the
    search itself hits its cap the full list is *also* incomplete, so the third
    element tells the caller that pruning is unsafe this sweep.
    """
    search_limit = max(limit, SEARCH_FLOOR)
    args = [
        "search", "prs", "--author=@me", "--state=open",
        "--limit", str(search_limit),
        "--json", "number,title,url,repository,isDraft,updatedAt",
    ]
    for owner in owners:
        args += ["--owner", owner]
    prs = run_gh(args) or []
    prs.sort(key=lambda p: p.get("updatedAt") or "", reverse=True)
    return prs, prs[:limit], len(prs) >= search_limit


def lookup_pr(ref: str) -> dict[str, Any]:
    nwo, number = parse_pr_ref(ref)
    data = run_gh(
        ["pr", "view", str(number), "--repo", nwo,
         "--json", "number,title,url,isDraft,updatedAt,state"]
    )
    if (data.get("state") or "").upper() != "OPEN":
        raise GhError(
            f"{nwo}#{number} is {(data.get('state') or 'unknown').lower()}, not open — "
            "refusing to work it"
        )
    return {
        "number": data["number"],
        "title": data["title"],
        "url": data["url"],
        "isDraft": data["isDraft"],
        "updatedAt": data["updatedAt"],
        "repository": {"nameWithOwner": nwo, "name": nwo.split("/", 1)[1]},
    }


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def rollup_summary(rollup: Optional[list[dict[str, Any]]]) -> dict[str, Any]:
    """Collapse a statusCheckRollup into conclusions plus failing check details."""
    entries = rollup or []
    conclusions, failing, pending = [], [], []
    for entry in entries:
        name = entry.get("name") or entry.get("context") or "?"
        url = entry.get("detailsUrl") or entry.get("targetUrl") or ""
        # CheckRun uses status/conclusion; StatusContext only has state, so an
        # unfinished status context shows up as a PENDING "conclusion".
        conclusion = (entry.get("conclusion") or entry.get("state") or "").upper()
        status = (entry.get("status") or "").upper()
        if (status and status != "COMPLETED") or conclusion in NOT_FINISHED:
            pending.append(name)
            continue
        conclusions.append(conclusion or "NONE")
        if conclusion in FAILED:
            run_match = re.search(r"/actions/runs/(\d+)", url)
            failing.append({
                "name": name,
                "conclusion": conclusion,
                "detailsUrl": url,
                "run_id": int(run_match.group(1)) if run_match else None,
            })
    unique = sorted(set(conclusions))
    if failing:
        overall = "FAILURE"
    elif pending:
        overall = "PENDING"
    elif not entries:
        overall = "NONE"
    elif unique == ["SKIPPED"]:
        overall = "SKIPPED"
    elif set(unique) <= {"SUCCESS", "SKIPPED", "NEUTRAL"}:
        overall = "SUCCESS"
    else:
        overall = unique[0] if unique else "NONE"
    return {
        "conclusion": overall,
        "conclusions": unique,
        "pending": pending,
        "failing": failing,
    }


def fetch_comments(nwo: str, number: int, me: str, since: Optional[str]) -> tuple[list[dict], Optional[str]]:
    """Return (comments newer than ``since`` and not mine, newest comment timestamp).

    Covers inline review comments, the PR conversation, and review submission
    bodies — a "changes requested" review whose feedback is only in the review
    body exists in none of the comment endpoints.

    Fetch errors deliberately propagate: treating a failed call as "no comments"
    would both hide feedback and overwrite the stored comment cursor with a
    timestamp derived from an incomplete fetch.
    """
    comments: list[dict[str, Any]] = []
    endpoints = [
        (f"repos/{nwo}/pulls/{number}/comments?per_page=100", "review"),
        (f"repos/{nwo}/issues/{number}/comments?per_page=100", "issue"),
        (f"repos/{nwo}/pulls/{number}/reviews?per_page=100", "review_submission"),
    ]
    for endpoint, kind in endpoints:
        raw = run_gh(["api", "--paginate", endpoint]) or []
        for item in raw:
            body = (item.get("body") or "").strip()
            state = (item.get("state") or "").upper()
            if kind == "review_submission" and (not body or state == "PENDING"):
                # Bodiless reviews add nothing; their inline comments arrive
                # via the review-comments endpoint. PENDING = unsubmitted draft.
                continue
            comments.append({
                "kind": kind,
                "id": item.get("id"),
                "user": (item.get("user") or {}).get("login"),
                # Reviews are stamped submitted_at, not created_at.
                "created_at": item.get("created_at") or item.get("submitted_at"),
                "review_state": state if kind == "review_submission" else None,
                "path": item.get("path"),
                "line": item.get("line") or item.get("original_line"),
                "url": item.get("html_url"),
                "body": body[:200],
            })
    timestamps = [c["created_at"] for c in comments if c["created_at"]]
    newest = max(timestamps) if timestamps else None
    fresh = [
        c for c in comments
        if c["user"] != me and (since is None or (c["created_at"] or "") > since)
    ]
    fresh.sort(key=lambda c: c["created_at"] or "")
    return fresh, newest


def classify(pr: dict[str, Any], state: dict[str, Any], me: str, force: bool) -> dict[str, Any]:
    """Build the per-PR plan entry, doing per-PR fetches only when needed."""
    url = pr["url"]
    nwo = pr["repository"]["nameWithOwner"]
    prior = state.get(url, {})
    entry: dict[str, Any] = {
        "url": url,
        "number": pr["number"],
        "title": pr["title"],
        "repo": nwo,
        "repo_name": pr["repository"]["name"],
        "is_draft": pr["isDraft"],
        "updated_at": pr["updatedAt"],
        "prior_state": prior or None,
        "reasons": [],
        "flags": [],
    }

    quiet_by_prefilter = (
        not force
        and prior.get("updated_at") == pr["updatedAt"]
        and (prior.get("ci_conclusion") or "").upper() in TERMINAL_GOOD
    )
    if quiet_by_prefilter:
        entry.update({
            "status": "quiet",
            "skipped_fetch": True,
            "head_sha": prior.get("head_sha"),
            "last_comment_at": prior.get("last_comment_at"),
            "needs_dispatch": False,
        })
        return entry

    view = run_gh(["pr", "view", url, "--json", PR_VIEW_FIELDS])
    merge_state = view.get("mergeStateStatus")
    if merge_state == "UNKNOWN":
        # GitHub computes mergeability lazily and the first query after a push
        # routinely returns UNKNOWN; taking that at face value would hide every
        # BEHIND and DIRTY PR. Asking again gives it a chance to settle.
        time.sleep(3)
        view = run_gh(["pr", "view", url, "--json", PR_VIEW_FIELDS])
        merge_state = view.get("mergeStateStatus")
    ci = rollup_summary(view.get("statusCheckRollup"))
    head_sha = view["headRefOid"]
    head_owner = (view.get("headRepositoryOwner") or {}).get("login")
    new_comments, newest_comment_at = fetch_comments(
        nwo, pr["number"], me, prior.get("last_comment_at")
    )

    entry.update({
        "skipped_fetch": False,
        "head_sha": head_sha,
        "head_branch": view["headRefName"],
        "base_ref": view["baseRefName"],
        "merge_state": merge_state,
        "ci": ci,
        "new_comment_count": len(new_comments),
        # Previews only — the dispatched agent re-fetches full bodies via iterate-pr.
        "new_comments": new_comments[:20],
        "last_comment_at": newest_comment_at,
    })

    reasons = entry["reasons"]
    if new_comments:
        reasons.append("new_comments")
    if ci["failing"]:
        reasons.append("ci_failing")
    elif ci["conclusion"] == "PENDING" or head_sha != prior.get("head_sha"):
        reasons.append("ci_pending")
    if merge_state == "BEHIND":
        reasons.append("behind_base")
    if merge_state == "DIRTY":
        reasons.append("conflicts")
        entry["flags"].append("merge conflicts — needs manual resolution")
    if merge_state in (None, "UNKNOWN"):
        entry["flags"].append("mergeability not computed yet — base freshness unknown")
    if force:
        # An explicitly named PR is always worked, whatever its state.
        reasons.insert(0, "requested")

    is_fork = head_owner and head_owner != nwo.split("/", 1)[0]
    if is_fork:
        entry["flags"].append(f"head branch lives in fork {head_owner} — no local fix actions")

    entry["status"] = "active" if reasons else "quiet"
    # A pending run needs no fix work of its own; wait for it to finish instead.
    # Conflicts are hands-off in a sweep, but fair game when I ask for one PR.
    fixable = {"new_comments", "ci_failing", "behind_base", "requested"}
    entry["needs_dispatch"] = bool(
        fixable & set(reasons) and not is_fork and (force or merge_state != "DIRTY")
    )
    return entry


# ---------------------------------------------------------------------------
# Checkout resolution
# ---------------------------------------------------------------------------


def worktree_paths(main: Path) -> dict[str, str]:
    """Map branch name -> worktree path for every worktree of this clone."""
    proc = run_git(main, ["worktree", "list", "--porcelain"], check=False)
    if proc.returncode != 0:
        return {}
    branches: dict[str, str] = {}
    path = None
    for line in proc.stdout.splitlines():
        if line.startswith("worktree "):
            path = line.split(" ", 1)[1]
        elif line.startswith("branch ") and path:
            branches[line.split(" ", 1)[1].removeprefix("refs/heads/")] = path
    return branches


def resolve_checkout(entry: dict[str, Any], create: bool) -> dict[str, Any]:
    """Find (or create) a local checkout of the PR branch."""
    main = SRC_ROOT / entry["repo_name"]
    branch = entry["head_branch"]
    if not (main / ".git").exists():
        return {"path": None, "problem": f"no clone at {main} — clone it to enable fix actions"}

    existing = worktree_paths(main)
    if branch in existing:
        return {"path": existing[branch], "created": False, "main_clone": str(main)}
    target = SRC_ROOT / f"{entry['repo_name']}.{WORKTREE_SUFFIX}" / branch
    if not create:
        # A dry run still reports what a real sweep would dispatch, so this is a
        # deferred action rather than a problem that cancels the dispatch.
        return {
            "path": None,
            "deferred": True,
            "would_create": str(target),
            "main_clone": str(main),
        }

    try:
        run_git(main, ["fetch", "origin", branch])
        has_local = run_git(main, ["rev-parse", "--verify", f"refs/heads/{branch}"], check=False).returncode == 0
        if has_local:
            # A pre-existing local branch can lag or diverge from origin. Fixing
            # from a stale tip earns a rejected push at best and a force-push
            # that drops the remote commits at worst. Check before creating the
            # worktree — creating one and then bailing would leave it behind for
            # the next sweep to adopt as a valid checkout, skipping this guard.
            ahead = run_git(
                main, ["rev-list", "--count", f"origin/{branch}..{branch}"], check=False
            )
            if ahead.returncode != 0 or ahead.stdout.strip() != "0":
                return {
                    "path": None,
                    "problem": (
                        f"local branch {branch} in {main} has commits not on "
                        f"origin/{branch} — reconcile it by hand"
                    ),
                }
        add = ["worktree", "add", str(target), branch] if has_local else [
            "worktree", "add", "--track", "-b", branch, str(target), f"origin/{branch}"
        ]
        run_git(main, add)
        if has_local:
            # Behind-only by the check above, so this fast-forward cannot conflict.
            run_git(target, ["merge", "--ff-only", f"origin/{branch}"])
    except GhError as exc:
        return {"path": None, "problem": str(exc)}
    return {"path": str(target), "created": True, "main_clone": str(main)}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def state_update_for(entry: dict[str, Any]) -> dict[str, Any]:
    if entry.get("skipped_fetch"):
        # Nothing was re-read, so there is nothing to update. Writing derived
        # values here would clobber the stored conclusion the pre-filter needs.
        return {}
    return {
        "updated_at": entry["updated_at"],
        "head_sha": entry.get("head_sha"),
        "ci_conclusion": (entry.get("ci") or {}).get("conclusion", "none").lower(),
        "base_behind": entry.get("merge_state") == "BEHIND",
        "last_comment_at": entry.get("last_comment_at"),
    }


def refreshed_state(entry: dict[str, Any]) -> dict[str, Any]:
    """Re-read a PR so post-push SHAs and check states land in the state file."""
    if entry.get("skipped_fetch", True):
        return entry["state_update"]
    try:
        view = run_gh(["pr", "view", entry["url"], "--json", PR_VIEW_FIELDS])
    except GhError:
        return entry["state_update"]
    ci = rollup_summary(view.get("statusCheckRollup"))
    return {
        # updated_at stays at its plan-time value on purpose. last_comment_at is
        # not re-read here, and a post-sweep updated_at paired with a pre-sweep
        # comment cursor would let the next sweep's pre-filter call the PR quiet
        # and silently swallow comments that landed during this sweep. A stale
        # updated_at only costs one extra per-PR fetch next time.
        "updated_at": entry["updated_at"],
        "head_sha": view["headRefOid"],
        "ci_conclusion": ci["conclusion"].lower(),
        "base_behind": view.get("mergeStateStatus") == "BEHIND",
        "last_comment_at": entry.get("last_comment_at"),
    }


def cmd_plan(args: argparse.Namespace) -> int:
    state = load_state(args.state_file)
    me = whoami()
    truncated = False
    if args.pr:
        prs = [lookup_pr(ref) for ref in args.pr]
        all_open_urls = []
    else:
        all_open, prs, truncated = search_prs(args.owner, args.limit)
        all_open_urls = [pr["url"] for pr in all_open]

    entries = []
    for pr in prs:
        entry = classify(pr, state, me, force=bool(args.pr))
        if entry["needs_dispatch"]:
            checkout = resolve_checkout(entry, create=not args.no_worktree)
            entry["checkout"] = checkout
            if not checkout["path"] and not checkout.get("deferred"):
                entry["needs_dispatch"] = False
                entry["flags"].append(checkout["problem"])
        entry["state_update"] = state_update_for(entry)
        entries.append(entry)

    plan = {
        "me": me,
        "mode": "single" if args.pr else "sweep",
        "state_file": str(args.state_file),
        "all_open_urls": all_open_urls,
        # The open-PR list itself was capped, so it cannot be used for pruning.
        "search_truncated": truncated,
        "counts": {
            "total": len(entries),
            "quiet": sum(1 for e in entries if e["status"] == "quiet"),
            "active": sum(1 for e in entries if e["status"] == "active"),
            "dispatch": sum(1 for e in entries if e["needs_dispatch"]),
        },
        "prs": entries,
    }
    json.dump(plan, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    plan = json.loads(Path(args.plan).read_text())
    state_file = Path(plan.get("state_file") or args.state_file)
    state = load_state(state_file)
    notes = {}
    for note in args.note:
        if "=" not in note:
            raise GhError(f"--note must be URL=TEXT, got {note!r}")
        note_url, text = note.split("=", 1)
        notes[note_url] = text

    urls = [entry["url"] for entry in plan["prs"]]
    for entry in plan["prs"]:
        url = entry["url"]
        # Keep keys the script doesn't own (e.g. note) and layer fresh values on top.
        merged = dict(state.get(url, {}))
        merged.update(refreshed_state(entry) if args.refresh else entry["state_update"])
        if url in notes:
            merged["note"] = notes[url]
        state[url] = merged

    pruned = []
    still_open = set(plan.get("all_open_urls") or []) | set(urls)
    prunable = (
        plan.get("mode") == "sweep"
        and not args.no_prune
        and not plan.get("search_truncated")
    )
    if prunable:
        pruned = [url for url in state if url not in still_open]
        for url in pruned:
            del state[url]

    save_state(state_file, state)
    json.dump(
        {"state_file": str(state_file), "recorded": len(urls), "pruned": pruned},
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-file", type=Path,
        default=Path(os.environ.get("BABYSIT_STATE_FILE", DEFAULT_STATE_FILE)),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="enumerate, classify, and resolve checkouts")
    plan.add_argument("--owner", action="append", default=[], help="restrict to org (repeatable)")
    plan.add_argument("--limit", type=int, default=10, help="max PRs to plan (default 10)")
    plan.add_argument(
        "--pr", action="append", default=[],
        help="single-PR mode: number, owner/repo#number, or PR URL (repeatable)",
    )
    plan.add_argument(
        "--no-worktree", action="store_true",
        help="never create a worktree (use for --dry-run sweeps)",
    )
    plan.set_defaults(func=cmd_plan)

    record = sub.add_parser("record", help="write state back from a plan")
    record.add_argument("--plan", required=True, help="path to the plan JSON")
    record.add_argument(
        "--note", action="append", default=[], metavar="URL=TEXT",
        help="attach a free-text note to a PR's state entry (repeatable)",
    )
    record.add_argument(
        "--no-refresh", dest="refresh", action="store_false",
        help="record the planned values instead of re-fetching each active PR",
    )
    record.add_argument("--no-prune", action="store_true", help="keep state for PRs not in the plan")
    record.set_defaults(func=cmd_record)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except GhError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
