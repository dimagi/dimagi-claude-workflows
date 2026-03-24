---
description: Fetch all review comments on the current branch's PR, evaluate each one, apply fixes where warranted, reply, and optionally resolve threads.
argument-hint: [--resolve] [--dry-run]
allowed-tools: Bash(gh auth status:*), Bash(gh repo view:*), Bash(gh pr view:*), Bash(gh api:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(bash:*), Read, Edit
---

> **Deprecated:** This command is superseded by the `iterate-pr` skill, which handles both review feedback and CI failures in a single workflow. Prefer using that skill instead.

Detect the upstream repository and current PR automatically, then work through every unresolved review comment end-to-end.

If `--dry-run` is in $ARGUMENTS, print the plan but make no changes (no commits, no replies, no resolves).
If `--resolve` is in $ARGUMENTS, resolve each thread after replying.

---

## 0. Prerequisites

1. Verify `gh auth status`. If not authenticated, tell the user to run `gh auth login` and stop.
2. Detect the repo:
   ```bash
   gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"'
   ```
   Store as `REPO` (e.g. `owner/repo`) and extract `OWNER` and `REPO_NAME` separately.
   Use `--repo $REPO` on every subsequent `gh api` call, but NOT on `gh pr view` (see below).
3. Find the open PR for the current branch:
   ```bash
   # Do NOT pass --repo here — gh pr view infers the PR from the current branch
   # and --repo requires an explicit branch/number argument.
   gh pr view --json number,title,baseRefName -q '"#\(.number): \(.title) (base: \(.baseRefName))"'
   ```
   Store `PR_NUMBER`. If no open PR is found, tell the user and stop.

---

## 1. Fetch All Review Comments

Run the fetch script:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/fetch-comments.sh "$OWNER" "$REPO_NAME" "$PR_NUMBER"
```

The script outputs a single JSON object:

```json
{
  "inline_comments": [...],   // REST pull-request review comments
  "issue_comments":  [...],   // REST PR-level issue comments
  "threads":         [...]    // GraphQL review threads with id, isResolved, comment_id
}
```

Build a map of `comment_id → thread_id` from `threads` and filter out entries where `isResolved: true`.

Group `inline_comments` into threads: comments with an `in_reply_to_id` belong to the same thread as the root comment. For each thread, show the full conversation.

---

## 2. Evaluate Every Thread

Print a numbered list of all unresolved threads/comments with:
- Thread number
- File path + line (for inline comments)
- Author
- Full comment body (and any replies in the thread)
- URL

For each thread, read the relevant source file(s) and diff context to understand what the reviewer is pointing at. Think carefully:

- Is the suggestion valid? Would it improve correctness, clarity, or maintainability?
- Is it a style preference that conflicts with project conventions (check CLAUDE.md if present)?
- Is it already addressed by prior commits on this branch?
- Does it require more information before acting?

Classify each thread as one of:
- **FIX** — apply the suggested change (or an equivalent improvement)
- **RESPOND_ONLY** — the concern is noted but no code change is needed; reply with explanation
- **SKIP** — already addressed or clearly out of scope (note why)

If `--dry-run` is active, print the classification table and stop here.

---

## 3. Apply Fixes

For each thread classified **FIX**:

1. Make the code change.
2. Verify the change doesn't break surrounding logic.
3. Stage the file (do not commit yet — batch all fixes into one commit).

---

## 4. Run Quality Checks

Before committing, run the project's quality pipeline to confirm fixes don't break anything.

Detect language from manifest files (`pyproject.toml`/`setup.py` → Python, `package.json` → Node/TypeScript). Check `.github/workflows/` for CI commands first; fall back to:

| Language | Commands |
|----------|----------|
| Python | `pytest -q`, `ruff check`, `ruff format --check` |
| Node/TS | project test/lint/format scripts, `tsc --noEmit` |

If a tool isn't installed, skip with a note. Fix any failures before proceeding.

---

## 5. Commit and Push

If any files were changed:

```bash
git add <changed files>
git commit -m "fix: address PR #$PR_NUMBER review comments

- <bullet per thread: what was changed and why>"
git push
```

Store the resulting commit SHA.

---

## 6. Reply to Every Thread

For each thread (FIX, RESPOND_ONLY, or SKIP with a note):

**Inline review comment reply:**
```bash
gh api -X POST repos/$REPO/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies \
  -f body="$REPLY_BODY"
```

Reply templates:
- **FIX**: `"Fixed in $COMMIT_SHA. $DESCRIPTION_OF_CHANGE"`
- **RESPOND_ONLY**: `"$EXPLANATION (no code change needed)"`
- **SKIP**: `"Already addressed in a prior commit / out of scope: $REASONING"`

For general issue comments, reply via:
```bash
gh api -X POST repos/$REPO/issues/$PR_NUMBER/comments \
  -f body="$REPLY_BODY"
```

---

## 7. Resolve Threads (only if `--resolve` in $ARGUMENTS)

For each thread that was replied to, resolve it via GraphQL using the thread ID collected in Step 1:

```bash
# IMPORTANT: multiline mutations fail with "UNKNOWN_CHAR" — use single-line form.
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"'$THREAD_ID'"}){thread{isResolved}}}'
```

---

## 8. Summary

Print a final table:

| # | File | Comment (truncated) | Action | Commit / Note |
|---|------|---------------------|--------|---------------|
| 1 | src/foo.rs:42 | "Use `Option` instead..." | Fixed | abc1234 |
| 2 | README.md | "Typo in heading" | Fixed | abc1234 |
| 3 | src/bar.rs:10 | "Consider splitting..." | Responded | Design decision explained |

---

## Notes

- Thread IDs (GraphQL `id`) differ from comment IDs (REST `databaseId`). Collect both in Step 1.
- Only users with write access can resolve review threads.
- If `gh` hits auth/rate issues mid-run, tell the user to run `gh auth login`, then retry from the failed step.
- If the GraphQL resolve mutation fails with a permissions error, skip resolution and note it in the summary.
