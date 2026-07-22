---
name: babysit-prs
description: One sweep over my open PRs — address new review comments, check CI, branch freshness, lint/format & generated-artifact drift, and description sync, fixing and pushing — tracking state so reruns skip already-handled work. Designed to be driven by /loop.
argument-hint: "[--owner <org>] [--limit <n>] [--dry-run]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill
model: opus
---

# Babysit PRs

Perform **one sweep** over my open pull requests. For each PR: address new review comments, check CI, branch freshness, lint/format and generated-artifact drift, and description sync, then fix and push. Record what was handled so the next sweep skips it. (This skill does not run a review pass of its own — it only responds to review comments already on the PR. Comments from bots and automated reviewers count the same as human ones: evaluate every comment on merit.)

This skill does a single iteration on purpose. Run it continuously with the loop runner:

```text
/loop 20m /babysit-prs
/loop /babysit-prs          # self-paced
```

## Arguments

- `--owner <org>`: only sweep PRs in repos owned by `<org>` (repeatable). Default: all my open PRs across orgs (`dimagi`, `dimagi-rad`, `taskbadger`, `czue`, `snopoke`, …).
- `--limit <n>`: max PRs to process this sweep (default: 10, newest activity first).
- `--dry-run`: report what would be done; take no fix actions, post nothing, and don't update state.

## State

State lives in `~/.local/state/babysit-prs/state.json`, keyed by PR URL:

```json
{
  "https://github.com/dimagi/open-chat-studio/pull/3866": {
    "updated_at": "2026-07-21T17:05:00Z",
    "head_sha": "abc123",
    "ci_conclusion": "success",
    "base_behind": false,
    "last_comment_at": "2026-07-21T17:00:00Z"
  }
}
```

- A PR is **quiet** (skip it) when its current head SHA matches `head_sha`, its CI conclusion is unchanged and not failing, it is not behind its base, and it has no review comments newer than `last_comment_at`. Anything else makes it **active**.
- `updated_at` is a cheap pre-filter, but only when the stored `ci_conclusion` is terminal-good (`success` or `skipped`): completing check runs do not bump a PR's `updatedAt`, so a PR recorded as pending or failing still needs the per-PR fetch even when `updatedAt` is unchanged. New review comments *do* bump `updatedAt`, so this pre-filter also catches them.

## Your Task

### Step 1: Enumerate Open PRs

```bash
gh search prs --author=@me --state=open --limit 50 \
  --json number,title,url,repository,isDraft,updatedAt
```

If `--owner` was given, add `--owner <org>` to the search. Sort by `updatedAt` descending and keep the first `--limit` PRs. Read the state file (treat a missing file as `{}`).

### Step 2: Classify Each PR

If a PR's `updatedAt` matches the state file's `updated_at` AND its stored `ci_conclusion` is terminal-good (`success` or `skipped`), mark it quiet without any further calls; on an all-quiet sweep the search query is the only API call made. All other PRs get the per-PR fetch:

```bash
gh pr view <url> --json headRefOid,baseRefName,statusCheckRollup,isDraft,mergeStateStatus \
  --jq '{headRefOid, baseRefName, mergeStateStatus, isDraft, conclusions: ([.statusCheckRollup[].conclusion] | unique), failing: [.statusCheckRollup[] | select(.conclusion == "FAILURE") | {name, detailsUrl}]}'
gh api 'repos/<owner>/<repo>/pulls/<number>/comments?sort=created&direction=desc&per_page=20' --jq '[.[] | {id, user: .user.login, created_at}]'
```

Classify each active PR into one or more of:

- **New review comments**: review comments newer than `last_comment_at` from anyone other than me — including bots and automated reviewers. Evaluate each on merit.
- **CI failing or pending-after-push**: `conclusions` contains `"FAILURE"`, or does not yet contain a terminal value, or `headRefOid` differs from stored `head_sha`.
- **Behind base**: `mergeStateStatus` is `BEHIND` or `DIRTY` (needs update/rebase; `DIRTY` = conflicts → flag only).

Quiet PRs get no per-PR output beyond the summary table.

### Step 3: Locate a Checkout (only for PRs needing fix actions)

Fix work needs a local checkout of the PR branch. My clones are flat under `~/src/`, with sibling worktrees named `~/src/<repo>.<suffix>`.

1. Main clone: `~/src/<repo>`. If absent, skip the PR's fix actions and flag it in the summary so I can clone it.
2. Check whether the PR branch is already checked out in a worktree and use that path (never create a second worktree for the same branch):

   ```bash
   git -C ~/src/<repo> worktree list --porcelain
   ```

3. Otherwise create one (fetch first): `git -C ~/src/<repo> fetch origin <branch> && git -C ~/src/<repo> worktree add ~/src/<repo>.babysit/<branch> <branch>`.

### Step 4: Dispatch

Handle each active PR from its checkout. **Order matters**: comments/CI/freshness first (may push commits), then auto-fix and description.

#### 4a. Review comments & CI health

- **New review comments and/or legit CI failure** → invoke the `iterate-pr` skill from the PR's checkout. It gathers review feedback, fixes legitimate findings and CI failures, verifies locally, commits, pushes, and replies to threads per its own rules. One invocation covers both — don't run it twice. This sweep runs unattended under `/loop`, so proceed without prompting.
- **Flaky CI failure** (infra/timeout/known-flaky, unrelated to the diff) → re-run just the failed jobs rather than treating them as legit:

  ```bash
  gh run rerun <run-id> --failed
  ```

  Note the rerun in the summary; do not push a "fix" for flakes.

#### 4b. Branch freshness

- `BEHIND` → update from base: `git -C <checkout> fetch origin && git -C <checkout> rebase origin/<baseRefName>` (or merge base if the repo prefers merge). Push the updated branch. **Never force-push** unless the branch is already rebased and only I have touched it — when unsure, flag instead.
- `DIRTY` (conflicts) → do not attempt; flag in the summary.

#### 4c. Auto-fixes

Run the repo's linter/formatter and regenerate committed generated artifacts, then commit and push only if something changed:

- Detect and run the configured formatter/linter (e.g. `ruff`/`black`/`pre-commit run -a`, `npm run lint --fix`, `./gradlew spotlessApply`) — prefer `pre-commit` if `.pre-commit-config.yaml` exists.
- Regenerate drifted artifacts: Django migrations, `requirements`/lockfiles, OpenAPI/GraphQL schemas, snapshots. Commit only genuine drift, not unrelated regeneration noise.
- Commit message: minimal (e.g. `lint`, `regen migrations`) per my commit style — do not enumerate changes.

#### 4d. Description sync

If the diff has drifted materially from the PR body, update the description to match (`gh pr edit`, falling back to the REST API `PATCH /repos/<owner>/<repo>/pulls/<number>` if `gh pr edit` errors with GraphQL). Keep it minimal — do not enumerate every change. For mobile/CommCare repos (JIRA-prefixed branch, `RELEASES.md` with `### Release Notes` / `### QA Notes`), follow the `create-mobile-pr` conventions for those sections.

Push resulting commits to the PR branch. Never merge, close, or mark ready-for-review. If a dispatch fails twice for the same PR, record the failure in the summary and move on; don't retry within the sweep.

### Step 5: Update State and Summarize

After handling (or skipping) each PR, write its current `updated_at`, `head_sha`, `ci_conclusion`, `base_behind`, and newest `last_comment_at` back to the state file. Drop any state keys not present in the Step 1 search results so closed and merged PRs don't accumulate (skip this entirely under `--dry-run`).

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
