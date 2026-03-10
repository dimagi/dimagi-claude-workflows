---
name: docs-vs-code-review
description: >
  Reviews Confluence documentation against actual source code AND internal documentation standards
  to find inaccuracies and gaps, then suggests specific fixes.
  Use this skill whenever a user shares a Confluence page URL and asks to "review the docs",
  "audit documentation", "compare docs to code", "check if the docs are accurate",
  "update docs to match the code", or "what's wrong with this documentation".
  Also trigger when a user says things like "the docs might be out of date", "sync the docs with
  the code", or "check our docs against the guidelines". The skill fetches the Confluence page and
  ALL child pages, clones and reads relevant code, and produces a concise prioritized list of
  specific doc changes needed — only things that need fixing, no confirmation of what's already
  correct. Always use this skill when the user provides a Confluence URL — a GitHub repo URL is
  NOT required, the skill infers the correct repos automatically.
---

# Docs vs. Code Review

Your job is to find where the documentation is wrong or incomplete, then produce a concise list
of specific edits to make. **Only report things that need to change** — skip anything that's
already accurate. The output should read like a focused edit list, not a code audit.

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
