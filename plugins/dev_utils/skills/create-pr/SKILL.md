---
name: create-pr
description: Use when the user asks to create, open, or submit a GitHub pull request, says "make a PR", "open a PR", or wants to commit, push, and turn the current branch into a PR. For mobile/CommCare repos with JIRA-prefixed tickets and RELEASES.md QA notes, prefer create-mobile-pr instead.
allowed-tools: Bash(git checkout:*), Bash(git switch:*), Bash(git add:*), Bash(git status:*), Bash(git diff:*), Bash(git push:*), Bash(git commit:*), Bash(gh pr create:*), Bash(gh pr edit:*), Bash(gh api:*)
---

# Create Pull Request

## Context

- Current branch: !`git branch --show-current`
- `git status`:
  ```!
  git status
  ```
- `git diff HEAD`:
  ```!
  git diff HEAD
  ```
- PR template (GitHub recognizes both casings in `.github/`, repo root, or `docs/`):
  ```!
  for f in \
    .github/PULL_REQUEST_TEMPLATE.md .github/pull_request_template.md \
    PULL_REQUEST_TEMPLATE.md pull_request_template.md \
    docs/PULL_REQUEST_TEMPLATE.md docs/pull_request_template.md; do
    if [ -f "$f" ]; then echo "=== $f ==="; cat "$f"; exit 0; fi
  done
  echo "(no PR template found)"
  ```

## Task

Based on the changes above:

1. If on `main`/`master`, create a new branch first (short, kebab-case, derived from the change).
2. Create a single commit with an appropriate message.
3. Push the branch (`git push -u origin HEAD` if it has no upstream).
4. Create the PR as a draft with `gh pr create --draft`. If a template was found above, fill out its sections according to the HTML comment guidance — replace the comments with real content, don't leave placeholders. If editing the PR later and `gh pr edit` fails with a GraphQL error, fall back to `gh api -X PATCH repos/:owner/:repo/pulls/<n>` rather than retrying GraphQL.
5. Output the PR URL.
