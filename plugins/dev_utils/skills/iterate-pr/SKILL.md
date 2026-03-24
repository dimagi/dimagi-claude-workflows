---
name: iterate-pr
description: Fix CI failures and address review feedback on the current branch's PR. Use when CI is failing, review comments need addressing, or you need to push fixes for an open PR. Supports --dry-run to preview without changes.
---

# Iterate on PR

One-shot workflow: gather review feedback, fix CI failures, verify locally, commit, push, and reply to all threads.

**Requires**: GitHub CLI (`gh`) authenticated.

**Important**: All scripts must be run from the repository root directory (where `.git` is located), not from the skill directory. Use the full path to the script via `${CLAUDE_SKILL_ROOT}`.

If `--dry-run` is in $ARGUMENTS, print the plan but make no changes (no commits, no pushes, no replies).

## Bundled Scripts

### `scripts/fetch_pr_checks.py`

Fetches CI check status and extracts failure snippets from logs.

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_checks.py [--pr NUMBER]
```

Returns JSON:
```json
{
  "pr": {"number": 123, "branch": "feat/foo"},
  "summary": {"total": 5, "passed": 3, "failed": 2, "pending": 0},
  "checks": [
    {"name": "tests", "status": "fail", "log_snippet": "...", "run_id": 123},
    {"name": "lint", "status": "pass"}
  ]
}
```

### `scripts/fetch_pr_feedback.py`

Fetches and categorizes PR review feedback using the LOGAF scale.

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_feedback.py [--pr NUMBER]
```

Returns JSON with feedback categorized as:
- `high` - Must address before merge (h:, blocker, changes requested)
- `medium` - Should address (m:, standard feedback)
- `low` - Optional (l:, nit, style, suggestion)
- `bot` - Informational automated comments (Codecov, Dependabot, etc.)
- `resolved` - Already resolved threads

Review bot feedback (from Copilot, Claude, CodeQL, etc.) appears in `high`/`medium`/`low` with `review_bot: true` — it is NOT placed in the `bot` bucket.

Each feedback item may include:
- `thread_id` - GraphQL node ID for inline review comments (used for replies)

### `scripts/reply_to_thread.py`

Replies to PR review threads. Batches multiple replies into a single GraphQL call.

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/reply_to_thread.py THREAD_ID "body" [THREAD_ID "body" ...]
```

## Workflow

### 1. Identify PR

```bash
gh pr view --json number,url,headRefName
```

Stop if no PR exists for the current branch.

### 2. Gather and Address Review Feedback

Run `uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_feedback.py` to get categorized feedback.

**Auto-fix (no prompt):**
- `high` - must address (blockers, security, changes requested)
- `medium` - should address (standard feedback)

When fixing feedback:
- Understand the root cause, not just the surface symptom
- Check for similar issues in nearby code or related files
- Fix all instances, not just the one mentioned

This includes review bot feedback (items with `review_bot: true`). Treat it the same as human feedback:
- Real issue found → fix it
- False positive → skip, but note why (will be included in reply)
- Never silently ignore review bot feedback — always verify the finding

**Prompt user for selection:**
- `low` - present numbered list and ask which to address:

```
Found 3 low-priority suggestions:
1. [l] "Consider renaming this variable" - @reviewer in api.py:42
2. [nit] "Could use a list comprehension" - @reviewer in utils.py:18
3. [style] "Add a docstring" - @reviewer in models.py:55

Which would you like to address? (e.g., "1,3" or "all" or "none")
```

**Skip silently:**
- `resolved` threads
- `bot` comments (informational only)

Track every thread's disposition (fixed, declined, false-positive, skipped) for the reply step.

If `--dry-run`: print the classification table and skip to the Summary step.

### 3. Check CI and Fix Failures

Run `uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_pr_checks.py` to get structured failure data.

For each failure:
1. Read the `log_snippet` and trace backwards from the error to understand WHY it failed
2. **Run the failing test(s) locally first.** Derive test names from the failure output. If they pass locally, do NOT attempt to fix the code — the failure is likely environmental. Investigate: cache not cleared between tests, `transaction.on_commit()` callbacks in rolled-back test transactions, test ordering dependencies, or shared mutable state. Report findings to the user.
3. If tests fail locally too, read the relevant code and check for related issues
4. Fix the root cause with minimal, targeted changes

Do NOT assume what failed based on check name alone — always read the logs.

### 4. Verify Locally

Before committing, verify fixes locally:
- If you fixed a test failure: re-run that specific test
- If you fixed a lint/type error: re-run the linter or type checker on affected files
- For any code fix: run existing tests covering the changed code

Detect the test runner from manifest files (`pyproject.toml`/`setup.py` → Python, `package.json` → Node/TS). Check `.github/workflows/` for CI commands first.

If local verification fails, fix before proceeding — do not push known-broken code.

### 5. Commit and Push

```bash
git add <changed files>
git commit -m "fix: address PR feedback and CI failures

- <bullet per change: what was changed and why>"
git push
```

Store the resulting commit SHA for replies.

### 6. Reply to All Threads

**Inline review threads** (items with `thread_id`): reply using the batch script.

**Issue-level comments** (items without `thread_id`): reply via REST API:
```bash
gh api -X POST repos/{owner}/{repo}/issues/{pr_number}/comments -f body="$REPLY_BODY"
```

Use `${CLAUDE_SKILL_ROOT}/scripts/reply_to_thread.py` for inline threads. Batch all replies into a single call:

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/reply_to_thread.py \
  PRRT_abc $'Fixed — description of change.\n\n*— Claude Code*' \
  PRRT_def $'Not applicable — reason.\n\n*— Claude Code*'
```

**Reply format by disposition:**
- **Fixed**: `"Fixed in <SHA>. <description of change>.\n\n*— Claude Code*"`
- **Declined (low)**: `"Noted — declined by author. <brief reason if given>.\n\n*— Claude Code*"`
- **False positive**: `"Not applicable — <reason>.\n\n*— Claude Code*"`

**Guards:**
- Before replying, check if the thread already has a reply ending with `*— Claude Code*` to avoid duplicates
- End every reply with `\n\n*— Claude Code*`
- If the script fails, log and continue — do not block the workflow

### 7. Summary

Print a final table:

| # | File | Comment (truncated) | Action | Commit / Note |
|---|------|---------------------|--------|---------------|
| 1 | src/foo.py:42 | "Use `Optional` instead..." | Fixed | abc1234 |
| 2 | README.md | "Typo in heading" | Fixed | abc1234 |
| 3 | src/bar.py:10 | "Consider splitting..." | Declined | Low priority, user chose "none" |
| 4 | CI: tests | pytest failure in test_api | Fixed | abc1234 |

## Fallback

If scripts fail, use `gh` CLI directly:
- `gh pr checks --json name,state,bucket,link`
- `gh run view <run-id> --log-failed`
- `gh api repos/{owner}/{repo}/pulls/{number}/comments`
