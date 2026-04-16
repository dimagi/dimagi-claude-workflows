---
name: connect-web-release-notes
description: >
  Generates Markdown release notes for the most recent release of the dimagi/commcare-connect
  GitHub repository. No input needed — the skill automatically finds the latest release,
  collects all PRs merged since the previous release, and produces a clean Markdown file
  grouped into three sections: New, Improvements, and Bug Fixes.

  Use this skill whenever the user asks to generate, write, or create release notes for
  Connect, asks what changed in the last release, wants a changelog, or says something like
  "summarize the changes since the last release". Also trigger when the user mentions
  a new Connect release was created on GitHub.
---

# Connect Release Notes

Generate release notes for the most recent release of `dimagi/commcare-connect`. Run
end-to-end automatically — no input is required from the user.

## Terminology

Use user-facing product terms, not internal code names:

| Use this | Not this |
|---|---|
| PersonalID | ConnectID |

If a PR title or body uses an internal model name, database field, or code identifier
as if it were a product concept, rephrase it into plain language.

## Step 1: Find the releases

```bash
gh release list --repo dimagi/commcare-connect --limit 5
```

Identify the **latest release** and the **previous release**. Note both tag names and
published dates (you need both to bound the PR search).

## Step 2: Find merged PRs between the releases

```bash
gh pr list \
  --repo dimagi/commcare-connect \
  --state merged \
  --search "merged:PREV_DATE..LATEST_DATE" \
  --json number,title,author,mergedAt,labels \
  --limit 100
```

Use `YYYY-MM-DD` format for both dates.

## Step 3: Fetch PR details

For each PR, fetch the title and body:

```bash
gh pr view <number> --repo dimagi/commcare-connect --json title,body,labels
```

Batch these in parallel — fetch several per message to avoid unnecessary round-trips.
Focus on the **Product Description** section of each body — that's where the user-facing
impact is described.

**Handling reverts:** If a PR title starts with "Revert" and references another PR,
exclude *both* that revert PR and the original PR it reverts. Their net effect on the
codebase is zero, so they don't belong in release notes.

## Step 4: Categorize each PR

Assign each PR to exactly one of:

- **New** — a brand-new feature or capability that didn't exist before
- **Improvements** — an enhancement, refinement, or extension of something existing;
  also includes new API capabilities that extend existing endpoints
- **Bug Fixes** — a correction to broken or incorrect behavior

**Skip entirely** (don't include in any section):
- Purely internal refactors: model/field renames with no user-facing effect
- Unreleased feature removals (waffle switches never rolled out)
- Feature flag / waffle switch cleanup for already-released features
- Dependency bumps, CI config changes, version pin updates

**Don't skip just because a PR has no Product Description section.** Some PRs (e.g.
new third-party integrations, infrastructure additions) only have a Technical Summary.
If the PR introduces something that affects users or operators — a new integration,
a new configuration option, a new service — include it. Use the PR title and
Technical Summary to write the description.

## Step 5: Write the release notes

Group everything into exactly three top-level sections — no feature-area subsections.
Within each section, order items from most impactful / most user-visible to least.

```markdown
# Release Notes — Connect v{version}
*Released {date}*

---

## New

**Feature Title** — One to two sentences written for a non-technical stakeholder.
What does the user now see or can now do? [Screenshots](PR_URL)

...

---

## Improvements

**Feature Title** — Description. [Demo](PR_URL)

...

---

## Bug Fixes

**Feature Title** — Description of what was broken and what the fix does.

...
```

**Title:** Short noun phrase — rephrase the raw PR title if it reads like a commit
message or ticket reference. The title should describe the *thing*, not the *action*
(e.g. "Work Area CSV Export", not "Add CSV export for work areas").

**Description:** One to two sentences. What does the user now see or experience?
Avoid implementation details. Omit a section entirely if it has no items.

**Links:** Add `[Screenshots](PR_URL)` if the PR body contains screenshots,
`[Demo](PR_URL)` if it contains a video or GIF. Don't add links otherwise.

## Step 6: Save the output

```bash
mkdir -p ./outputs
```

Save to `./outputs/release_notes_{version}.md`.

## Step 7: Post to Confluence

Post the release notes to the top of the Web Release Notes page:
**Page ID:** `3870556169`
**Cloud ID:** `dimagi.atlassian.net`

First fetch the current page content so you know what's already there. Then update
the page with the new release notes prepended above any existing content, separated
by a horizontal rule (`---`).

Include the GitHub PR links (`[Screenshots](PR_URL)` / `[Demo](PR_URL)`) in the
Confluence version — don't strip them.

Use `"Add v{version} release notes"` as the version message.

Tell the user the file path where the notes were saved and confirm the Confluence
page was updated with a link to it.

## Step 8: Post to Slack

Post the release notes to the Connect release notes Slack channel:
**Channel:** `#connect-product-feed` (channel ID: `C08MRUZ8T9A`)

Use the Slack MCP `slack_send_message` tool. Format the message using Slack's mrkdwn
syntax — *not* standard Markdown:

- Opening line: `**Connect v{version}** — Released {date}` (no emojis)
- Section headers: `**NEW**`, `**IMPROVEMENTS**`, `**BUG FIXES**` (bold all-caps, no `##`)
- Bullet items: `• Feature Title — Description. <PR_URL|Screenshots>` or `<PR_URL|Demo>`
  - Feature title is plain text; only section headers are bold
- Use `**double asterisks**` for bold — the tool uses standard Markdown where `*single*` renders as italic
- Links: `<url|label>` syntax (not `[label](url)`)
- Do **not** use `---` horizontal rules — they are invalid in Slack messages
- Do **not** use emojis anywhere in the message
- Keep bullet descriptions concise (one sentence); the full notes are on Confluence
- End with a plain link to the Confluence page:
  `Full release notes: <https://dimagi.atlassian.net/wiki/spaces/connectpublic/pages/3870556169/Web+Release+Notes|Web Release Notes on Confluence>`

Confirm to the user that the Slack message was posted and include the message link.
