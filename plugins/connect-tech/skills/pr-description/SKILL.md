---
name: pr-description
description: Use when the user asks to create, write, or draft a pull request description, or when preparing a PR for review
---

# PR Description Generator

## Overview

Generate a PR description following the team's GitHub PR template by analyzing the branch's commits, code diff, and any user-provided context or notes.

## When to Use

- User asks to create/write/draft a PR description
- User is preparing changes for a pull request
- User asks for help filling out the PR template

## Process

### 1. Gather Context

Run these in parallel:

- `git log master..HEAD --oneline` — commits on the branch
- `git diff master...HEAD --stat` — changed files summary
- `git diff master...HEAD` — full diff
- `cat .github/PULL_REQUEST_TEMPLATE.md` — the PR template

Also check: did the user provide additional notes, context, or verification steps? Incorporate them into the appropriate sections.

### 2. Analyze Changes

- Extract the ticket number from the branch name (e.g., `CCCT-1929` from `CCCT-1929-refetch-sso-token-on-invalid-token-error`) or from commit messages if not present in the branch name
- Understand what the code changes do and why
- Note the scope and blast radius of changes
- Identify any test changes

### 3. Fill Out the PR Template

Follow the team's template structure exactly. Start with the ticket number as a linked heading at the very top:

**Ticket Link (required, at the very top):**
- Format: `### [TICKET-NUMBER](https://dimagi.atlassian.net/browse/TICKET-NUMBER)`
- Example: `### [CCCT-2264](https://dimagi.atlassian.net/browse/CCCT-2264)`
- The display text should be just the ticket number

**Product Description:**
- Describe user-facing effects
- If no visible changes, state that explicitly

**Technical Summary:**
- Describe rationale and design decisions
- If the user provided notes explaining their reasoning, investigation findings, or team discussions, incorporate that context here

**Safety Assurance — Safety story:**
- How confidence was gained (local testing, verification steps)
- Why the change is inherently safe or how blast radius is limited
- If the user described their verification steps, include them as a numbered list

**Safety Assurance — Automated test coverage:**
- Identify related test coverage
- If no new tests, explain why

**Safety Assurance — QA Plan:**
- Describe how to verify the change is regression-free

**Labels and Review:**
- Include the standard checklist items from the template

### 4. Output Format

- Output the description as a fenced markdown code block so the user can copy-paste it directly
- Do not include the HTML comments from the template — replace them with actual content

## Common Mistakes

- Omitting user-provided context or investigation notes from the Technical Summary
- Being too vague in the Safety story — include specific verification steps
- Forgetting the ticket link heading at the very top of the description
- Putting the ticket link in the Technical Summary instead of at the top
- Including the template's HTML comment placeholders instead of replacing them with content