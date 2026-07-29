---
name: babysit-prs
description: One sweep over my open PRs — address new review comments, check CI, branch freshness, lint/format & generated-artifact drift, and description sync, fixing and pushing — tracking state so reruns skip already-handled work. Designed to be driven by /loop. Pass a PR number to work a single PR instead.
argument-hint: "[<pr>] [--owner <org>] [--limit <n>] [--dry-run]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, Task, Agent
model: opus
---

# Babysit PRs

Perform **one sweep** over my open pull requests. For each PR: address new review comments, check CI, branch freshness, lint/format and generated-artifact drift, and description sync, then fix and push. Record what was handled so the next sweep skips it. (This skill does not run a review pass of its own — it only responds to review comments already on the PR. Comments from bots and automated reviewers count the same as human ones: evaluate every comment on merit.)

This skill does a single iteration on purpose. Run it continuously with the loop runner:

```text
/loop 20m /babysit-prs
/loop /babysit-prs          # self-paced
```

All fix work happens in **sub-agents** — one per PR — so the sweep's own context stays small and PRs are worked concurrently.

## Modes

- **Sweep** (default, no PR argument): plan across my open PRs, dispatch a sub-agent per PR needing work, record state.
- **Single PR** (`/babysit-prs 3999`, `/babysit-prs dimagi/open-chat-studio#3999`, or a PR URL): dispatch one sub-agent to identify and resolve everything wrong with that PR. State is consulted but ignored for the quiet check — an explicitly named PR is always worked, and merge conflicts are in scope (in a sweep they are only flagged).

## Arguments

- `<pr>`: a PR number (in the current repo), `owner/repo#number`, or a PR URL → single-PR mode. Repeatable.
- `--owner <org>`: only sweep PRs in repos owned by `<org>` (repeatable). Default: all my open PRs across orgs (`dimagi`, `dimagi-rad`, `taskbadger`, `czue`, `snopoke`, …).
- `--limit <n>`: max PRs to process this sweep (default: 10, newest activity first).
- `--dry-run`: report what would be done; take no fix actions, post nothing, create no worktrees, and don't update state.

## State

State lives in `~/.local/state/babysit-prs/state.json`, keyed by PR URL:

```json
{
  "https://github.com/dimagi/open-chat-studio/pull/3866": {
    "updated_at": "2026-07-21T17:05:00Z",
    "head_sha": "abc123",
    "ci_conclusion": "success",
    "base_behind": false,
    "last_comment_at": "2026-07-21T17:00:00Z",
    "note": "optional free-text carried across sweeps"
  }
}
```

- A PR is **quiet** (skip it) when its current head SHA matches `head_sha`, its CI conclusion is unchanged and not failing, it is not behind its base, and it has no review comments newer than `last_comment_at`. Anything else makes it **active**.
- `updated_at` is a cheap pre-filter, but only when the stored `ci_conclusion` is terminal-good (`success` or `skipped`): completing check runs do not bump a PR's `updatedAt`, so a PR recorded as pending or failing still needs the per-PR fetch even when `updatedAt` is unchanged. New review comments *do* bump `updatedAt`, so this pre-filter also catches them.
- `note` is mine to use for context worth carrying between sweeps (e.g. "flake resolved upstream, don't chase"). The script never overwrites it unless you pass `--note`.

## Bundled Script

`scripts/sweep_prs.py` does the enumerating, classifying, and checkout resolution — everything that was manual API plumbing.

```bash
# sweep plan
uv run ${CLAUDE_SKILL_DIR}/scripts/sweep_prs.py plan [--owner ORG]... [--limit N] [--no-worktree]

# single-PR plan (number / owner/repo#number / URL)
uv run ${CLAUDE_SKILL_DIR}/scripts/sweep_prs.py plan --pr 3999

# write state back at the end of the sweep
uv run ${CLAUDE_SKILL_DIR}/scripts/sweep_prs.py record --plan <plan.json> [--note 'URL=text']...
```

`plan` emits JSON: overall `counts`, and per PR its `status` (`quiet`/`active`), `reasons` (`new_comments`, `ci_failing`, `ci_pending`, `behind_base`, `conflicts`, `requested`), `ci.failing` (name, conclusion, `run_id`), `new_comments` previews (inline comments, PR conversation, and review submission bodies), `merge_state`, `flags` (things needing my attention, e.g. missing clone, fork head, conflicts), and `needs_dispatch`. A `checkout` object appears only on PRs that need dispatch; under `--no-worktree` its `path` is `null` and `deferred` is true (the PR is still counted as needing dispatch, so the dry run reports real work).

`record` re-reads each active PR so post-push SHAs and check states land in state, preserves `note` and any other keys it doesn't own, and prunes state for PRs that are no longer open (measured against the full open-PR list, not the `--limit` slice — and skipped entirely if that list was itself capped).

## Your Task

### Step 1: Plan

Write the plan to a file — Step 3 needs it to record state — and read it:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/sweep_prs.py plan --limit 10 > /tmp/babysit-plan.json
```

Add `--owner`/`--limit` from my arguments, `--pr <ref>` for single-PR mode, and `--no-worktree` under `--dry-run`.

Under `--dry-run`: report the plan (Step 3's table, "would do" phrasing), then stop — no sub-agents, no state write.

### Step 2: Dispatch a Sub-Agent per PR

For every PR with `needs_dispatch: true`, dispatch **one sub-agent** (`general-purpose`). Never do the fix work in this context. Send all dispatches **in a single message** so they run concurrently — each works in its own checkout.

PRs that are `active` but not dispatched (CI merely pending, conflicts, fork head, missing clone) get no agent; carry their `reasons`/`flags` straight into the summary.

Give each agent everything it needs — it cannot see the plan JSON or my arguments:

```text
Work PR <url> ("<title>") in the repo <owner/repo>.
Checkout: <checkout.path> — cd there first; do all work in that checkout, never in
another. Before touching anything, run `git fetch origin && git status -sb`: if
there are uncommitted changes you did not make, or the branch has diverged from
`origin/<branch>`, stop and report rather than building on top of it.

Why it needs attention: <reasons, in plain words>
Failing checks: <name (run_id) for each, or "none">
New comments since last sweep: <count> from <users>

Do the following, in this order — earlier steps may push commits:

1. Review comments and/or legitimate CI failures → invoke the `iterate-pr` skill
   from this checkout. It gathers feedback, fixes legitimate findings and CI
   failures, verifies locally, commits, pushes, and replies to threads per its own
   rules. One invocation covers both — do not run it twice. You are running
   unattended: do not prompt, and treat low-priority suggestions as declined.
2. Flaky CI failure (infra/timeout/known-flaky, unrelated to the diff) → re-run
   only the failed jobs with `gh run rerun <run-id> --failed`. Never push a
   "fix" for a flake.
3. Behind base (`behind_base` in the reasons) → `git fetch origin && git rebase
   origin/<base>` (or merge, if the repo prefers merge), then push. **Never
   force-push** unless the branch is already rebased and only I have touched it —
   if unsure, stop and report instead.
4. Auto-fixes → run the repo's formatter/linter (prefer `pre-commit run -a` when
   `.pre-commit-config.yaml` exists; else `ruff`/`black`, `npm run lint --fix`,
   `./gradlew spotlessApply`) and regenerate committed generated artifacts
   (Django migrations, requirements/lockfiles, OpenAPI/GraphQL schemas,
   snapshots). Commit and push only genuine drift, not regeneration noise.
   Commit messages minimal (`lint`, `regen migrations`) — do not enumerate changes.
5. Description sync → if the diff has drifted materially from the PR body, update
   it with `gh pr edit`, falling back to `PATCH /repos/<owner>/<repo>/pulls/<number>`
   via `gh api` if `gh pr edit` fails with a GraphQL error. Keep it minimal. For
   mobile/CommCare repos (JIRA-prefixed branch, `RELEASES.md` with
   `### Release Notes` / `### QA Notes`), follow the `create-mobile-pr`
   conventions for those sections.

Never merge, close, or mark ready-for-review. If a step fails twice, stop
retrying it and report it.

Report back: one line per action taken, each pushed SHA, and anything you left
for me to handle.
```

In **single-PR mode**, prepend a discovery step to that prompt: have the agent independently identify what is wrong with the PR — read the diff, the failing logs, every open review thread, the base-branch relationship, and whether the description still matches — then resolve what it found, using the steps above as the playbook rather than the full scope. Merge conflicts are in scope here: resolve them if the resolution is unambiguous, otherwise report and leave the branch clean. Report anything it chose not to fix, and why.

### Step 3: Record State and Summarize

Once all agents have reported:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/sweep_prs.py record --plan /tmp/babysit-plan.json
```

Add `--note '<pr-url>=<text>'` for any PR where a sub-agent surfaced context worth carrying into the next sweep (a known flake, a deliberate decision, work left for me). Skip this step entirely under `--dry-run`.

End with a summary table:

| PR | Title | Status | Action taken |
| --- | --- | --- | --- |
| [ocs#3866](…) | Add retry to webhook delivery | 2 new comments | Addressed via iterate-pr, pushed `a1b2c3` |
| [ocs#3865](…) | Fix session timeout handling | CI failing (legit) | Fixed test via iterate-pr, pushed `def456` |
| [scout#337](…) | Bump scout deps | behind base | Rebased on main, pushed |
| [taskbadger#410](…) | Parallelize task runner | flaky CI | Re-ran failed jobs |
| [formplayer#1575](…) | Upgrade Gradle | quiet | skipped |

If every PR was quiet, the summary is the single line: `All <n> open PRs quiet; nothing to do.`

Finally, print when this sweep finished so I can see when it last ran:

```bash
date '+Last run: %Y-%m-%d %H:%M:%S %Z'
```

Output that line at the very end of the run, after the summary.
