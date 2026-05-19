---
name: slack-to-confluence
description: Update a Confluence wiki page based on the resolution of a Slack thread, using an ADF surgical edit that preserves page structure. Use when the user wants to "update wiki from Slack", "sync this Slack thread to Confluence", "add this to the wiki", "make a Confluence note from this thread", "incorporate this Slack discussion into the docs", "use this Slack convo to update Confluence", or shares both a Slack thread link and a Confluence page link in the same request. Triggers on any combination of a slack.com archive URL plus a dimagi.atlassian.net wiki URL, even if the verb isn't named explicitly.
---

# Slack-to-Confluence

Take a Slack thread that resolves an ambiguity or surfaces new knowledge, and update a Confluence page to reflect it. The user triggers this manually by sharing a Slack thread link (and usually a Confluence page link or page name).

Follow the seven steps below in order. **Always show a diff and get explicit approval before writing to Confluence.**

## Prerequisites

The Slack MCP and Atlassian MCP must already be connected. If either is missing when triggered, tell the user which connector is missing and stop.

## Step 1 — Collect the Slack source

If the user provided a Slack thread link, parse it:

- URL format: `https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<TIMESTAMP>`
- The timestamp needs a decimal inserted before the last 6 digits: `p1778674209472849` → `1778674209.472849`

If no Slack link was provided, ask for one. Do not proceed without an actual thread to read.

## Step 2 — Read the Slack thread

Use `slack_read_thread` with the parsed `channel_id` and `message_ts`. Read both the parent message and all replies.

Extract:

- **Source page** — the Confluence page being discussed (usually linked in the parent message)
- **The question** — what ambiguity or gap the parent message surfaced
- **The resolution** — the authoritative answer, usually from the most senior or product-knowledgeable replier, often confirmed by others
- **Nuance** — any caveats, edge cases, or "when to use the other option" guidance that should be captured

If the parent links to a wiki page but no resolution is reached in the thread, stop and tell the user the thread is inconclusive.

## Step 3 — Read the target Confluence page

Fetch the page in ADF format, not markdown:

```
getConfluencePage(cloudId="dimagi.atlassian.net", pageId=<ID>, contentFormat="adf")
```

If the page ID isn't obvious, extract it from the URL: `.../pages/<ID>/<slug>`.

If the ADF response is too large to return inline (common — most non-trivial pages are 100KB+), it's saved to a file. **Do not try to load it into context.** Use the script-based pattern in `references/adf-surgical-insert.md`.

## Step 4 — Propose specific edits

Before writing anything, present a structured proposal to the user that includes:

- **Edit type** — one of:
  - *Clarifying note in existing section* (most common — when the wiki is right but ambiguous)
  - *Section rewrite* (when the wiki is wrong or stale)
  - *New child page* (when the topic is substantial and doesn't fit elsewhere)
  - *New top-level page* (rare — for whole new areas)
- **Exact text** — the proposed copy, in its final form, not paraphrased
- **Exact location** — which heading/section, before/after which existing content, with one node of context on each side
- **Space** — default is internal `connect`. Do not write to `connectpublic` without asking.
- **Version message** — what will appear in the page history

For an ADF panel insert specifically, show:
- The panel node JSON
- The node immediately before and the node immediately after the insertion point
- The fact that all other nodes stay byte-identical

## Step 5 — Confirm via AskUserQuestion

Use `AskUserQuestion` with at least three options:

1. "Yes, write as shown"
2. "Tweak the wording first"
3. "Use a different approach" (different panel style, different location, different scope)

Add a separate question about public-space mirroring if the source page is in `connect`. Default option: "Internal only" — the spaces are NOT mirrors.

If the user picks "tweak" — incorporate their feedback and confirm again. Never skip the approval loop, even when the user seems impatient.

## Step 6 — Write the update — ADF only

**Critical:** Never use `contentFormat: "markdown"` for the update on a Confluence page that contains images, tables, panels, macros, or layouts. The markdown round-trip silently mangles them. The example in `references/example-walkthrough.md` shows what goes wrong.

Use the ADF surgical insert pattern in `references/adf-surgical-insert.md`:
1. Fetch ADF → save to file
2. Parse, locate the target heading by index
3. Build the new node
4. `content.insert(index, new_node)`
5. Minify to single-line JSON
6. Pass as the `body` parameter to `updateConfluencePage` with `contentFormat="adf"`

Always include a traceable `versionMessage`. Format:

> `Add [thing] per Slack discussion YYYY-MM-DD with [Names]. ADF surgical insert.`

Example: `"Add clarifying info panel under 'Configure data forwarding' (per Slack 2026-05-13 with Pawan/Cal/Ajeet). ADF surgical insert."`

## Step 7 — Verify and link

After the write succeeds:

- Confirm the response shows the version was bumped
- Share the page URL with the user
- Suggest a quick visual check against the previous version (Confluence Page history → diff)
- Include a "Sources" section with links to both Slack messages and the Confluence page

## Guardrails

- **ADF only** for non-trivial pages. Markdown round-trip is destructive on anything with images, tables, panels, or macros.
- **Always** show the proposed diff before writing. No silent updates.
- **Always** include a version message citing the Slack date and named participants — this is how future readers trace the edit back to its rationale.
- **Default scope is internal only.** When the source page is in `connect`, only update `connect`. Ask before mirroring to `connectpublic`. The two spaces are NOT mirrors of each other — public docs are a distinct curated subset.
- **Search before assuming public has an equivalent.** Use `searchConfluenceUsingCql` against `space = "connectpublic"` before proposing any parallel edit. Usually there isn't a direct match.
- **Don't paraphrase the Slack resolution into something it didn't say.** Quote the authoritative reply faithfully. If multiple repliers contradicted each other, surface that to the user instead of picking a winner.

## See also

- `references/adf-surgical-insert.md` — full Python pattern for splicing ADF without markdown round-trips
- `references/example-walkthrough.md` — worked example showing what good output looks like at each step
- `references/version-message-format.md` — patterns and examples for traceable version messages
