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
4. Write the PR description following the "PR description content" guidance below.
5. Create the PR as a draft with `gh pr create --draft`, passing the description via a heredoc. If editing the PR later and `gh pr edit` fails with a GraphQL error, fall back to `gh api -X PATCH repos/:owner/:repo/pulls/<n>` rather than retrying GraphQL.
6. Output the PR URL.

## PR description content

The diff is the primary source of truth. Your job in the description is to give the reviewer what the diff *can't* show, and nothing else. Reviewers are busy — a tight description is read, a long one is skimmed. Aim for a few sentences to a short paragraph for most PRs; reach for more length only when the change genuinely needs it.

### Include only what's load-bearing

- **Why the change exists** — the bug, motivation, goal, ticket link, or surrounding context. This is almost always worth a sentence.
- **Where to focus review attention** — risky areas, subtle decisions, places the diff doesn't make obvious on its own.
- **Choices that aren't visible in the diff** — tradeoffs made, alternatives considered and rejected, constraints from other systems.
- **Out-of-band info** — deploy ordering, dependencies on other PRs, follow-up work explicitly left out of scope, feature-flag state.
- **How to verify** — only when it isn't obvious from the change itself.

### Cut everything else

- Don't recap what the diff already shows or restate commit messages in prose — the reviewer can read both.
- Don't walk through the change file-by-file.
- Don't open with framing like "This PR introduces..." / "This PR refactors..." — say the thing directly, or skip the meta-sentence.
- Don't write generic test plans ("tests pass", "added unit tests"). Either describe what was actually tested in a way that helps a reviewer trust the change, or omit.
- Don't pad with hype words ("comprehensive", "robust", "elegant") or invent bullet points to round out a list.
- Don't leave the template's HTML comment placeholders in the final body, and don't write boilerplate just to occupy a section.

### Handling PR templates

When a template exists, treat each section as a *prompt* — "is there something load-bearing for this category?" — not a blank that must be filled.

- If yes → write the shortest version that conveys it.
- If no → omit the section entirely, or replace it with one short line (e.g. "N/A — pure refactor, no behavior change"). Don't invent content to fill it.

The point of the template is to remind you of categories the reviewer might care about, not to enforce a fixed shape.

### Example

For a PR that adds a retry around a flaky external API call:

> Bad (padded, recaps the diff):
> ```
> ## Summary
> This PR introduces a comprehensive retry mechanism for our external API calls. It robustly handles transient failures by wrapping the call in a retry loop.
>
> ## Changes
> - Added `retry_with_backoff` helper in `utils/retry.py`
> - Updated `client.py` to use the new helper
> - Added unit tests
>
> ## Test plan
> - [x] Tests pass
> ```
>
> Good (load-bearing only):
> ```
> Vendor's `/sync` endpoint started returning 502s a few times a day (see incident #482). Wrapping the call in 3 retries with exponential backoff; surfacing the final failure unchanged so existing alerting still fires.
>
> Worth a closer look: the backoff sleeps inside the request handler, so worst-case latency on a fully failed call is now ~7s. Acceptable for this path but flagging it.
> ```
