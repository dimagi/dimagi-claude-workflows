---
name: create-mobile-pr
description: Use when the user asks to create, open, or submit a GitHub pull request, or when implementation is complete and the user wants to push and open a PR
---

# Create GitHub Pull Request

## Overview

Create a GitHub pull request with a JIRA-prefixed title, a description generated from the pr-description skill, the Connect Mobile Devs team as reviewers, and the current user as assignee.

## When to Use

- User asks to create, open, or submit a pull request
- User says "make a PR" or "open a PR"
- Implementation is done and user wants to push and open a PR

## Process

### 1. Gather Context

Run these in parallel:

- `git branch --show-current` -- current branch name
- `git log master..HEAD --oneline` -- commits on the branch
- `git diff master...HEAD --stat` -- changed files summary
- `git diff master...HEAD` -- full diff
- `cat .github/PULL_REQUEST_TEMPLATE.md` -- the PR template
- `gh api user --jq '.login'` -- current GitHub username

Also check: did the user provide additional notes, context, or verification steps? Incorporate them into the appropriate sections.

### 2. Extract Ticket Number and Build Title

Extract the JIRA ticket number from the branch name. The ticket number is the leading prefix before the first description segment, matching the pattern `[A-Z]+-[0-9]+`.

Examples:
- `CCCT-1929-refetch-sso-token` -> `CCCT-1929`
- `CI-609-personalid-phone-fragment-crash` -> `CI-609`
- `ENG-42-add-new-feature` -> `ENG-42`

If no ticket number is found in the branch name, ask the user for it.

**Build the PR title:** `TICKET-NUMBER Short concise description`

- The description after the ticket number should summarize the PR's purpose in a few words
- Derive it from the commits and diff -- do not just reuse the branch name slug
- Keep the total title under 72 characters
- Example: `CCCT-1929 Re-fetch SSO token on invalid token error`

### 3. Generate PR Description

**REQUIRED:** Use the `pr-description` skill to generate the PR body. Invoke it with the Skill tool. Follow its full process (analyze changes, fill out the PR template, etc.). The output of that skill is the PR body.

Do NOT output the description as a code block for copy-pasting -- capture it directly for use in the `gh pr create` command.

### 4. Ensure Branch is Pushed

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

### 5. Create the Pull Request

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
- `--body` -- full PR description generated from the pr-description skill
- `--assignee "@me"` -- assigns to the current GitHub user
- `--reviewer "dimagi/connect-mobile-devs"` -- requests review from the Connect Mobile Devs team

After creation, output the PR URL so the user can see it.

## Common Mistakes

- Forgetting to extract the ticket number from the branch name and using the raw branch slug as the title
- Making the title too long -- keep it under 72 characters total
- Not pushing the branch before attempting to create the PR
- Skipping the pr-description skill and writing a bare-bones body
- Using `--reviewer` with a team name that isn't prefixed by the org (`dimagi/`)
- Forgetting `--assignee "@me"`
