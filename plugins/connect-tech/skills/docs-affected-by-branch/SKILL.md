---
name: docs-affected-by-branch
description: >
  Use when working on a CommCare Connect branch, before or after its PR is opened, and the user
  asks which Confluence docs the change affects or makes out of date, or what belongs in the PR's
  Documentation section.
argument-hint: "[Jira ticket key or URL, or \"none\"]"
---

# Docs Affected by Branch

Find the Confluence pages the current branch makes out of date and list the edits each one
needs. The code is the local checkout — don't clone anything. The mobile repo is out of scope
unless the branch changes it.

Read `${CLAUDE_PLUGIN_ROOT}/references/connect-docs.md` first. Steps 3 and 4 use it.

## Step 1: Get the ticket

Run `gh pr view --json body,baseRefName` to see whether the branch has a PR. Then take the
ticket from the first of these that applies:

1. **A ticket was passed as an argument** — use it. "none" means there is no ticket.
2. **The branch has a PR whose description links a Jira ticket** — use that ticket.
3. **Otherwise** — ask the user for the Jira ticket key or URL. There may not be one, so accept
   "none".

If there is a ticket, fetch it and collect the Confluence pages it links: its **Documentation to
Update** list, or any Confluence links in its description. These are the pages the ticket
expects to change.

If the PR exists and its description has a **Documentation** section, collect the pages listed
there too.

## Step 2: Read the change

Diff the branch against its base, where `<base>` is the PR's `baseRefName`, or `main` when there
is no PR. Fetch first so the base is current:

```bash
git fetch origin <base>
git diff origin/<base>...HEAD
```

From the diff, collect the things a user can see or rely on: page and button labels, column
headers, status names, error and notification strings, CSV column names, permissions, limits,
and the names of new or changed features. Ignore refactors, tests and internal code that
changes no behaviour.

If nothing user-facing changed, say so in one line, use `None` as the Documentation list, and go
to Step 5.

## Step 3: Find candidate pages

Follow **Finding affected pages** in the reference, using the terms from Step 2. Add every page
the ticket or the PR's Documentation section links, even if search didn't return it.

## Step 4: Report

Check each candidate page against the diff only, not against the whole codebase. List the edits
in the **Edit format** from the reference.

End with a list for the PR's **Documentation** section:

- Pages that need an edit, with links
- Pages linked on the ticket or the PR that the diff turned out not to affect
- Pages the diff affects that neither the ticket nor the PR linked
- "New page needed: …" where applicable

## Step 5: Update the PR

- **If the branch has no PR:** stop. The user pastes the list into the description when they
  open the PR.
- **If it has one:** show how its **Documentation** section differs from the list, then offer
  to replace the section with `gh pr edit`. Change only that section, and only after the user
  agrees. If the description has no Documentation section, offer to add one.
