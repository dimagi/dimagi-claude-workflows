---
name: qa-ticket-prep
description: Use when preparing a test plan for a software release. Triggered by phrases like "create test plan for X release", "generate test cases for these changes", "what should we test for version X", or when given a milestone, version number, or Jira release ticket.
---

# QA Ticket Prep

## Overview

Given a release version or Jira release ticket, fetch all related PRs and tickets, read their content and comments, and produce a structured Excel test plan covering happy path, regression, and edge cases.

## Workflow

### Step 0 — Identify the Starting Point

**If given a Jira ticket (e.g. QA-8493):**
1. Read the ticket description and comments
2. Extract the release version from the ticket title or description
3. Extract any linked Jira tickets or PR references
4. Proceed to Step 1 using the version found

**If given a version number or milestone directly (e.g. "2.63"):**
- Proceed straight to Step 1

### Step 1 — Find All PRs for the Release

- Identify the GitHub milestone matching the release version
- Fetch all PRs under that milestone (open and closed)
- Note which PRs are **not yet merged** — write test cases for these normally but flag them (see Step 5)

### Step 2 — Read PRs and Linked Tickets

For each PR:
- Read the **title and description** (not review comments)
- Extract any linked Jira ticket keys from the PR body (e.g. CCCT-1234, SAAS-5678, QA-9012)

For each linked Jira ticket:
- Read the **description and comments** — comments often contain scope changes, QA findings, and edge cases that are not in the description

### Step 3 — Cross-Reference Release Notes

- Check the repo's release notes file (e.g. `RELEASES.md`) for the release version
- Identify anything mentioned in the release notes that has **no matching PR in the milestone** — flag these as gaps and note them in the Prerequisites tab

### Step 4 — Categorise Changes

Sort all changes into:
- **New feature** — needs happy path + regression + edge cases
- **Bug fix** — needs reproduction verification + regression check
- **Internal/analytics only** — no user-facing test cases needed; note it was reviewed and skipped

### Step 5 — Write Test Cases

Organise into one Excel tab per workflow/feature area. Each tab has these columns:

| Column | Notes |
|--------|-------|
| Test Case No | Format: TC-[AREA]-[NNN], e.g. TC-FAL-001 |
| Description | One-line summary of what is being tested |
| Steps to Test | Numbered, specific, reproducible steps |
| Expected Outcome | Clear pass condition |
| Status | Pass / Fail / Blocked / N/A — leave **blank** for unmerged PRs |
| Comments / Notes | For unmerged PRs add: "PR #XXXX not yet merged — confirm in build before testing" |

For each feature area cover:
1. **Happy path** — core successful flow end-to-end
2. **Regression** — areas adjacent to the change that could break
3. **Edge cases** — boundary values, offline behaviour, device rotation, upgrade from previous version, multiple simultaneous conditions

### Step 6 — Add a Prerequisites Tab

First tab in the workbook. List any setup required before testing can begin:
- Server-side configuration (e.g. accounts, assigned tasks, job setup)
- Device requirements (e.g. two devices for multi-device tests)
- Network conditions needed (e.g. airplane mode scenarios)
- App version to upgrade FROM for upgrade path tests

## Output Format

- **File type:** Excel (.xlsx)
- **Tab order:** Prerequisites first, then one tab per workflow, then a Regression & Exploratory tab last
- **Naming:** One tab name per feature area (e.g. "Form Attachment Limit", "Push Notifications")
- **Styling:** Frozen header row, alternating row colours, wrapped text in steps/outcome cells

## Common Mistakes

- **Only reading PR descriptions** — ticket comments frequently contain scope changes, discovered edge cases, and "this also covers X" notes that affect what needs testing
- **Skipping unmerged PRs** — write the test cases; leave Status blank and note the PR is unmerged so the tester knows to verify before running
- **Missing release note gaps** — always cross-reference RELEASES.md; features mentioned there without a matching PR may have been merged without a milestone tag or live in a different repo
- **No prerequisites tab** — testers get blocked on setup; document server-side requirements upfront
- **Internal-only changes with test cases** — analytics or dependency upgrades with no user-facing change don't need test cases; note them as reviewed and skipped to avoid noise