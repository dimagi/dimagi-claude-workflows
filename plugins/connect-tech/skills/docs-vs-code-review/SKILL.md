---
name: docs-vs-code-review
description: >
  Reviews Confluence docs against source code to find inaccuracies and suggest fixes. Use when
  the user provides a Confluence URL and asks to review, audit, or check if docs are accurate
  or up to date (GitHub repo not required — inferred from the Confluence space). Can also run
  on a branch, without a URL, to find the Confluence pages the branch's changes make out of date.
---

# Docs vs. Code Review

Your job is to find where the documentation is wrong or incomplete, then produce a concise list
of specific edits to make. **Only report things that need to change** — skip anything that's
already accurate. The output should read like a focused edit list, not a code audit.

There are two ways to start:

- **From a Confluence page** — the user gives a URL. Follow Steps 1–3 below.
- **From a code change** — the user is on a branch (usually about to open a PR) and wants to
  know which docs it affects. Follow [Starting from a code change](#starting-from-a-code-change).

## What you need from the user

You only need:
1. **Confluence page URL** — the root documentation page to review

**GitHub repos are inferred automatically from the Confluence space — do not ask the user for them.**

| Confluence space | Repos to clone and check |
|---|---|
| `connectpublic` or `connect` | `https://github.com/dimagi/commcare-connect` (web/backend) AND `https://github.com/dimagi/commcare-android` (mobile) |
| `commcare` or `CC` | `https://github.com/dimagi/commcare-hq` |

If the space doesn't match any of the above, then ask the user for the repo URL before proceeding.

---

## Step 1: Fetch the root page AND every child page

Get the Atlassian cloud ID using `getAccessibleAtlassianResources`.

Extract the **page ID** from the URL (the number in the path, e.g. `3215458305`).

Then fetch everything under the root:
- `getConfluencePage(pageId, contentFormat="markdown")` — root page
- `getConfluencePageDescendants(pageId, limit=50)` — find all child pages
- `getConfluencePage` for **each child page** — read them all

This is important: the user wants every page under the root reviewed, not just the root page itself. Make a list of all pages you've fetched before moving to the code, so you can systematically check each one.

As you read, note the specific claims each page makes — exact error messages, column names, icon descriptions, navigation steps, character limits, permission rules, and what happens when an action is taken.

---

## Step 2: Clone and read the relevant code

If you are already working in a local checkout of a repo, use it — don't clone it again. Clone
only the repos you don't have locally.

Using the repos inferred from the Confluence space (see table above), clone shallowly:

```bash
git clone --depth=1 https://github.com/ORG/REPO.git /tmp/REPO
```

Find files that implement the documented features. The most useful files to check:

| File | What to look for |
|------|-----------------|
| `models.py` | Field names, `max_length`, status choices, defaults |
| `views.py` | Navigation after actions, permission decorators, side effects |
| `forms.py` | Validation logic, exact error message strings |
| `tasks.py` | SMS/push notification content |
| `tables.py` | Column labels, icon CSS classes (especially color), tooltip text |
| Import files (`visit_import.py` etc.) | Exact required CSV column names — often wrong in docs |
| `utils/flags.py` | Flag string identifiers |

Use grep to find specific behavior across all cloned repos:
```bash
grep -rn "term" /tmp/REPO --include="*.py" | grep -v migration | grep -v test
# For mobile (commcare-android), also check .kt and .java files:
grep -rn "term" /tmp/commcare-android --include="*.kt" --include="*.java"
```

Common gotchas worth checking on every review:
- **CSV import column names**: check the actual constant values, not display labels (e.g., `AMOUNT_COL = "payment amount"`, not `"Amount"`)
- **Icon colors**: search for CSS class (e.g., is it `text-orange-600` or `text-red-600`?)
- **SMS/notification content**: find the actual template string
- **Status values**: check the `TextChoices` class for real string values
- **Rate limits**: search `timedelta` near the relevant view
- **Revoke/undo actions**: what fields are actually cleared vs. retained?
- **"Not found" re-check logic**: does the code retry before giving up, vs. what the docs imply?

---

## Step 3: Produce the edit list

For each page you reviewed, report only the things that need to change. Skip anything correct.

Structure the output as two sections:

### Section A — Inaccurate or Misleading Content

Things where the docs say something wrong or incomplete compared to the code. Order by severity — break things first, then confusing things, then minor wording issues.

Use this format for each item:

---
**[High/Medium/Low] Page: [Page name] — [Short title of issue]**

> [Quote the exact text that's wrong]

Change to: [Exact replacement text, or clear description of what to add/remove]

*(Code: `file.py` — one-line explanation of what the code actually does)*

---

Keep it tight. The code reference is just enough to justify the change — a filename and one sentence, not a walkthrough. Don't explain what you checked and found to be correct.

### Section B — Documentation Quality Gaps

For pages missing required sections per the [Connect Documentation Process](https://dimagi.atlassian.net/wiki/spaces/connect/pages/3092250699/Connect+Documentation+Process). Be brief — one line per gap.

Required sections each page should have: Feature Summary, Usage Overview, Screenshots with accompanying text (the support bot can't read images), Behavior Details/Edge Cases, Version & Last Updated Date.

Best practices to flag if missing:
- No info panel at top explaining purpose and user personas
- Screenshots without text descriptions (support bot can't interpret images)
- No step-by-step instructions
- No FAQs for complex features

Format: `**Page: [Name]** — Missing: [list what's absent]. Recommendation: [one sentence]`

---

## Scope

Cover every page under the root. If you find more than ~10 items in Section A, prioritize the ones that would cause a user to do something wrong (wrong column names, wrong navigation, wrong constraints) over minor wording issues.

---

## Starting from a code change

Use this when the question is "which docs does this branch make out of date?" rather than "is
this page accurate?". The code is the local checkout you are working in — don't clone anything.
The mobile repo is out of scope unless the branch changes it.

### C1: Read the change and the ticket

- Diff the branch against its base: `git diff origin/main...HEAD` (use the PR's base branch if
  it isn't `main`).
- Find the Jira ticket from the branch name, the commit messages or the PR description. If
  there is one, look for relevant documentation links on it — in the description or comments.
  Those are the pages expected to change.

From the diff, collect the things a user could see or rely on: page and button labels, column
headers, status names, error and notification strings, CSV column names, permissions, limits,
and the names of new or changed features. Ignore refactors, tests and internal code that
changes no behaviour.

### C2: Find candidate pages

- **If Atlassian MCP tools are available:** search Confluence in the `connectpublic` and
  `connect` spaces for the terms from C1. Add every page linked on the ticket. Read each
  candidate and keep only pages that describe behaviour the diff changes.
- **If they are not available:** show the user the terms from C1 and ask which pages cover
  them. Accept free text and "None".

If the change introduces a new term, check the
[Connect Glossary](https://dimagi.atlassian.net/wiki/spaces/connectpublic/pages/3146907685/Connect+Glossary).
If no page covers a new user-facing feature, note that a new page is needed.

### C3: Report

Check each kept page against the diff only — not against the whole codebase — and list the
edits in the Section A format from Step 3. Skip Section B; quality gaps belong in a full review.

End with a list the user can paste into the PR's **Documentation** section:

- Pages that need an edit, with links
- Pages linked on the ticket that the diff turned out not to affect
- Pages the diff affects that the ticket did not link
- "New page needed: …" where applicable

If nothing user-facing changed, say so in one line and give `None` as the PR section.
