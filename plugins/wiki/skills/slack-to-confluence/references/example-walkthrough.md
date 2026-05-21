# Worked Example — Forward Forms note

This is the example the skill was built from. Read it to see what good output looks like at each step.

## The trigger

The user shared two Slack thread links from the `#connect-eng` channel and said:

> "Update wiki with a clarifying note from this Slack discussion."

Both links were threads in the same channel — first the original question, then the follow-up with the dev replies.

## Step 1 — Parsed Slack URLs

- `https://dimagi.slack.com/archives/C05UNUNH43X/p1778674209472849`
  - channel_id: `C05UNUNH43X`, message_ts: `1778674209.472849`
- `https://dimagi.slack.com/archives/C05UNUNH43X/p1778674255330519`
  - channel_id: `C05UNUNH43X`, message_ts: `1778674255.330519`

## Step 2 — Read thread

Parent message (Jonathan): linked a wiki page section "Configure data forwarding," asked whether the instruction "use Forward Forms" was correct, since there's also a separate "Forward Form Metadata to CommCare Connect" option.

Replies:
- Ajeet initially thought "Forward Form Metadata" should be used
- Pawan confirmed: **current docs are correct** — use "Forward Forms" because Connect's verification workflows need full form data
- Cal explained the "Forward Form Metadata" option is a niche alternative for data-residency cases (e.g., Ansh keeping health data in India)

Resolution: wiki is correct, just ambiguous. Add a clarifying note.

## Step 3 — Read target page

`getConfluencePage(cloudId="dimagi.atlassian.net", pageId="2683405079", contentFormat="adf")`

Response too large to return inline. Saved to `.claude/projects/.../tool-results/...txt`. Extracted via Python; 72 top-level content nodes.

Found "Configure data forwarding" heading at `content[28]`.

## Step 4 — Proposed edit

Presented to user:

- **Edit type**: clarifying note in existing section
- **Text**:
  > **Note:** Use **"Forward Forms"** (not "Forward Form Metadata to CommCare Connect"). Connect's verification workflows require the full form data, which is what "Forward Forms" sends. The "Forward Form Metadata to CommCare Connect" option only transmits metadata and is intended for projects that need to keep form data out of Connect for data-residency reasons (e.g., health data that must remain in-country). For standard setups, use "Forward Forms."
- **Location**: between node 29 (the "Go to Settings → Forward Forms" instruction) and node 30 (the "settings need to be configured" list intro)
- **Visual**: ADF info panel (blue)
- **Space**: internal `connect` only — confirmed that `connectpublic` has no equivalent page (searched it first)
- **Version message**: "Add clarifying info panel under 'Configure data forwarding' (per Slack 2026-05-13 with Pawan/Cal/Ajeet). ADF surgical insert."

## Step 5 — Confirmation

Used AskUserQuestion with three options. User picked "Yes, write it."

## Step 6 — Wrote via ADF

```
content.insert(30, panel_node)   # 72 → 73 nodes
```

The new node:

```json
{
  "type": "panel",
  "attrs": {"panelType": "info"},
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Note: ", "marks": [{"type": "strong"}]},
        {"type": "text", "text": "Use "},
        {"type": "text", "text": "\"Forward Forms\"", "marks": [{"type": "strong"}]},
        {"type": "text", "text": " (not \"Forward Form Metadata to CommCare Connect\")..."}
      ]
    }
  ]
}
```

Body was ~52KB minified. Passed it as the `body` parameter to `updateConfluencePage` with `contentFormat="adf"`. Returned version 23.

## Step 7 — Verified

- Confirmed `version.number = 23`
- Confirmed `version.message` matched what we sent
- Shared page URL with user
- Noted that all 72 original nodes were unchanged (only the inserted panel was new)

## What we tried first that broke

The first attempt used `contentFormat="markdown"` for both the GET and the PUT. The markdown looked clean. The write succeeded. But comparing v20 → v21 in Confluence's page history showed substantial changes to image placement, table widths, and panel renderings throughout the page — not just the section being edited.

Lesson: **never markdown round-trip a rich Confluence page.** Always ADF.

The user reverted v21 manually via Confluence's page history (UI restore is one click), and we redid it via ADF, producing v23 with zero collateral changes.

## Key takeaways

1. The Slack thread URL needs a decimal inserted: `p1778674209472849` → `1778674209.472849`.
2. The Atlassian MCP returns the ADF in a wrapper format `[{type, text}]` — unwrap before parsing.
3. Insert clarifying notes AFTER the heading's introductory paragraph, not immediately after the heading.
4. Always show the diff (new node + neighboring nodes) before writing.
5. Version messages should name the date and the people involved so future readers can trace the edit back to its source.
