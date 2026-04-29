---
name: create-mobile-pr
description: Use when the user asks to create, open, or submit a GitHub pull request, or when implementation is complete and the user wants to push and open a PR
---

# Create GitHub Pull Request

## Overview

Create a GitHub pull request with a JIRA-prefixed title, a description generated from the repo's PR template, the Connect Mobile Devs team as reviewers, and the current user as assignee.

## When to Use

- User asks to create, open, or submit a pull request
- User says "make a PR" or "open a PR"
- Implementation is done and user wants to push and open a PR

## Process

### 1. Gather Context

Run these in parallel:

- `git branch --show-current` -- current branch name
- `git log master..HEAD --oneline` -- commits on the branch
- `git log master..HEAD` -- full commit messages (used as fallback for ticket extraction)
- `git diff master...HEAD --stat` -- changed files summary
- `git diff master...HEAD` -- full diff
- `cat .github/PULL_REQUEST_TEMPLATE.md` -- the PR template

Also check: did the user provide additional notes, context, or verification steps? Incorporate them into the appropriate sections.

### 2. Extract Ticket Number and Build Title

Extract the JIRA ticket number (pattern `[A-Z]+-[0-9]+`) from:

1. **Branch name first** -- the leading prefix before the first description segment
2. **Commit messages as fallback** -- if the branch name has no ticket, scan commit messages for the pattern

Examples:
- `CCCT-1929-refetch-sso-token` -> `CCCT-1929`
- `CI-609-personalid-phone-fragment-crash` -> `CI-609`
- `ENG-42-add-new-feature` -> `ENG-42`

If no ticket number is found anywhere, ask the user for it.

**Build the PR title:** `TICKET-NUMBER Short Concise Description`

- The description after the ticket number should summarize the PR's purpose in a few words
- Derive it from the commits and diff -- do not just reuse the branch name slug
- Keep the total title under 72 characters
- **Capitalize the first letter of every word** in the description portion (including short words like `on`, `to`, `for`, `the`, `a`, `an`, etc.)
- Preserve the existing casing of acronyms, identifiers, and ticket numbers (e.g. `SSO`, `URL`, `iOS`, `CCCT-1929`)
- Example: `CCCT-1929 Re-Fetch SSO Token On Invalid Token Error`

### 3. Generate PR Description from the Template

Read `.github/PULL_REQUEST_TEMPLATE.md` and fill it out according to the instructions in the HTML comments of each section. Replace the HTML comments with actual content -- do not leave them in the final description.

**Prepend a ticket link heading at the very top of the description (before the first template section):**

- Format: `### [TICKET-NUMBER](https://dimagi.atlassian.net/browse/TICKET-NUMBER)`
- Example: `### [CCCT-2264](https://dimagi.atlassian.net/browse/CCCT-2264)`
- Display text is just the ticket number

For each template section, follow the guidance in its HTML comment. Incorporate any user-provided notes, verification steps, or investigation findings into the appropriate sections (usually Technical Summary and Safety story).

**Omit the Labels and Review section from the PR description.** Do not include its heading or body in the generated description.

### 4. Show the Draft to the User and Wait for Approval

Before pushing or creating the PR, present the full draft to the user and explicitly ask them to review it. The draft must include:

- The proposed PR title
- The full proposed PR description (rendered exactly as it will appear on GitHub, including the ticket link heading)

Then ask the user something like: "Does this look good, or would you like any edits before I open the PR?"

**Do not push the branch and do not run `gh pr create` until the user has approved the draft.** If the user requests edits, apply them and show the updated draft again. Repeat until the user confirms.

### 5. Ensure Branch is Pushed

Check if the current branch has an upstream remote:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

If no upstream exists, push the branch:

```bash
git push -u origin HEAD
```

If the branch is behind the remote, push the latest commits:

```bash
git push
```

### 6. Create the Pull Request

Use `gh pr create` with all required flags:

```bash
gh pr create \
  --title "TICKET-NUMBER Short description" \
  --body "$(cat <<'EOF'
<generated PR description here>
EOF
)" \
  --assignee "@me" \
  --reviewer "dimagi/connect-mobile-devs"
```

Key flags:
- `--title` -- JIRA ticket number followed by short description
- `--body` -- full PR description generated from the template
- `--assignee "@me"` -- assigns to the current GitHub user
- `--reviewer "dimagi/connect-mobile-devs"` -- requests review from the Connect Mobile Devs team

After creation, output the PR URL so the user can see it.

## Common Mistakes

- Forgetting to extract the ticket number and using the raw branch slug as the title
- Using sentence case in the title -- every word in the description portion must start with a capital letter
- Making the title too long -- keep it under 72 characters total
- Pushing the branch or running `gh pr create` before the user has approved the draft
- Not pushing the branch before attempting to create the PR
- Leaving the template's HTML comment placeholders in the description instead of replacing them with content
- Forgetting the ticket link heading at the very top of the description
- Including the Labels and Review section from the PR template -- it must be omitted
- Using `--reviewer` with a team name that isn't prefixed by the org (`dimagi/`)
- Forgetting `--assignee "@me"`
