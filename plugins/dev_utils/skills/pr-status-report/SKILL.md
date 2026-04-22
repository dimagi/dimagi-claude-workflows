---
name: pr-status-report
description: Use when the user asks for a PR report, PR status, open PRs overview, or wants to know which pull requests need their attention in the current repository
---

# PR Status Report

## Overview

Generate a structured report of all open PRs in the current repository, categorized by what needs the current GitHub user's attention. The report prioritizes actionability — review requests and failing CI on your own PRs come first.

## When to Use

- User asks "what PRs need my attention?"
- User asks for a PR status report or open PR overview
- User wants to triage their PR workload

## Process

### 0. Resolve the Target Repository

Determine the repo to report on. Prefer an explicit `owner/repo` the user provided; otherwise auto-detect from the current working directory:

```bash
gh repo view --json nameWithOwner,owner --jq '{repo: .nameWithOwner, owner: .owner.login}'
```

If this fails (not inside a gh-recognized repo), ask the user which repo to report on before continuing.

Cache the values for later steps:
- `REPO` — full `owner/name` (e.g., `dimagi/commcare-android`)
- `OWNER` — just the owner/org segment

### 1. Identify the Current User and Their Teams

Run in parallel:

```bash
gh api user --jq '.login'
```

```bash
gh api orgs/OWNER/teams --jq '.[].slug'
```

The teams call 404s if `OWNER` is a personal account rather than an organization. Treat a 404 as "no teams" and skip the team-membership checks entirely.

If teams were returned, check membership for each:

```bash
gh api orgs/OWNER/teams/TEAM_SLUG/members --jq '.[].login' | grep -q USERNAME
```

Cache the team names the user belongs to — needed to resolve team-based review requests in step 5.

**Note:** PR `reviewRequests` uses display names (e.g., `Connect Mobile Devs`) while the API returns slugs (e.g., `connect-mobile-devs`). Match case-insensitively or normalize both to lowercase with hyphens.

### 2. Fetch All Open PRs

Fetch in a single call with only the fields needed. Avoid fetching full review bodies — they can be massive (200KB+) and blow up context. Include `additions` and `deletions` for sizing.

```bash
gh pr list --repo REPO --state open --limit 100 \
  --json number,title,author,reviewRequests,reviewDecision,isDraft,mergeable,labels,createdAt,assignees,url,additions,deletions \
  --jq '.[] | {
    number,
    title,
    author: .author.login,
    draft: .isDraft,
    mergeable: .mergeable,
    reviewDecision: .reviewDecision,
    created: .createdAt,
    url,
    additions,
    deletions,
    labels: [.labels[].name],
    reviewers_requested: [.reviewRequests[] | if .__typename == "Team" then ("team:" + .name) else .login end],
    assignees: [.assignees[].login]
  }'
```

**Bot detection:** The `is_bot` field from `gh pr list` is unreliable (always `false`). Identify bots by login: authors containing `[bot]`, or matching known bots like `github-actions`, `dependabot`, `coderabbitai`.

### 3. Fetch Your Review Activity

Get PRs where you have submitted reviews. Fetch the latest review state AND the review timestamp so you can compare against latest commits:

```bash
gh api graphql -f query='
{
  search(query: "repo:REPO is:pr is:open reviewed-by:USERNAME", type: ISSUE, first: 50) {
    nodes {
      ... on PullRequest {
        number
        commits(last: 1) {
          nodes { commit { committedDate } }
        }
        reviews(author: "USERNAME", last: 1) {
          nodes { state submittedAt }
        }
      }
    }
  }
}'
```

Replace `REPO` with the value from step 0 and `USERNAME` with the GitHub login from step 1.

Use the `submittedAt` vs `commits.last.committedDate` comparison to flag PRs where the author pushed new commits after your last review.

### 4. Fetch CI Status for Relevant PRs

Only fetch CI status for PRs that need the user's attention (authored PRs, review-requested PRs).

```bash
gh pr view NUMBER --repo REPO --json statusCheckRollup \
  --jq '[.statusCheckRollup[] | select(.name != null) | {name: .name, conclusion: .conclusion, status: .status}]'
```

Note the `select(.name != null)` — `statusCheckRollup` often contains null entries from check suites that must be filtered out.

Run these calls in parallel for all relevant PRs.

Summarize CI as one of: `passing`, `failing (NAME)`, `pending`, `no checks`.

### 5. Build the Report

Start with a header line: `**Repo:** REPO | **User:** USERNAME | **Date:** YYYY-MM-DD | **Open PRs:** N total`

Organize PRs into these sections, in priority order:

#### Section 1: Review Requested From You

PRs where your username appears directly in `reviewers_requested`, OR where a team you belong to (from step 1) is listed — but exclude PRs you authored (team auto-requests on your own PRs are not real review requests). Mark team-based requests as `(via team)`.

Table columns: PR (linked), Title, Author, Age, CI, Size (`+N/-M`).

#### Section 2: Your PRs Needing Action

PRs you authored that have:
- Changes requested (`reviewDecision: CHANGES_REQUESTED`)
- Failing CI
- Merge conflicts (`mergeable: CONFLICTING`)

Skip draft PRs unless they have specific issues.

#### Section 3: Your PRs Awaiting Review

PRs you authored that are waiting on reviewers. No action needed from you — this is for awareness.

#### Section 4: PRs You Reviewed

PRs where you submitted a review. Show your latest review state (approved, changes requested, commented). If the author pushed commits after your last review (from step 3 timestamp comparison), flag with `(new commits since your review)`.

#### Section 5: Other Notable PRs (optional)

Only include if there are PRs with `High Risk` labels or other signals worth flagging. Skip bot-authored draft PRs (e.g., `[Test Improver]` PRs from `github-actions`, dependabot PRs) unless the user has reviewed them.

### 6. Action Items Summary

End with a numbered list of concrete next steps, ordered by priority:
1. Reviews to submit
2. Fixes needed on your PRs
3. Follow-ups on PRs you reviewed (especially those with new commits)
4. Stale items to close or re-engage

### Formatting Rules

- Use markdown tables for each section
- Link PR numbers: `[#123](url)`
- Show age as relative (e.g., `2d`, `3w`, `84d`)
- Flag PRs older than 30 days as `(stale)`
- Flag PRs older than 90 days as `(very stale)`
- Show diff size as `+additions/-deletions`
- Keep the report scannable — no paragraph-length descriptions per PR
- Exclude coderabbitai and other bot reviews from review counts

## Common Mistakes

- Fetching full review bodies (`.reviews[].body`) — these can be enormous and are not needed for the report
- Not filtering nulls from `statusCheckRollup` — many entries have null name/conclusion/status from check suites
- Relying on `is_bot` field — it returns `false` for all authors; detect bots by login name instead
- Not distinguishing between direct review requests and team-based ones
- Counting team auto-requests on your own PRs as review requests — these are not actionable
- Reporting superseded review states (e.g., showing CHANGES_REQUESTED when the latest review is APPROVED)
- Including bot-authored draft PRs in the main sections — they clutter the report
- Not checking CI status, which is critical for knowing if your own PRs are blocked
- Not comparing review timestamps to latest commit timestamps — miss new activity on reviewed PRs
- Treating the `gh api orgs/OWNER/teams` 404 for personal-account repos as an error instead of "no teams"
