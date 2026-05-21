# slack-to-confluence — a plugin for the Connect team

## What it does

When you and the team work something out in Slack — a clarification, a correction, a "here's how this actually works" — there's almost always a wiki page that should reflect it but doesn't. This plugin closes that loop. Paste a Slack thread link into Cowork/Claude Code, point it at a Confluence page, and it will read the thread, propose a specific edit, show you exactly what will change, get your approval, and write the update.

It uses Confluence's native document format (ADF) so the edit is surgical: only the new content is added, every existing image, table, panel, and macro stays byte-identical. No more "I added a sentence and somehow half the formatting changed."

Every write includes a traceable version message in Confluence's page history that cites the Slack date and participants, so anyone reading the wiki later can find the discussion that justified the edit.

## When to use it

- A Slack thread resolved an ambiguity in the docs → add a clarifying note
- The wiki has stale or wrong content that came up in a discussion → propose a section rewrite
- A longer thread covered a new topic worth documenting → propose a new page

The plugin always asks before writing, so you stay in control of the wording, location, and scope.

## Installation (5 minutes)

### Prerequisites

You need Cowork installed, with the following connectors set up:

1. **Slack** (Dimagi workspace) — to read thread messages
2. **Atlassian** (dimagi.atlassian.net) — to read and update Confluence pages

If you don't have these, set them up in Cowork's Settings → Connectors first.

### Steps in Cowork

1. Download `slack-to-confluence.plugin` 
2. Open Cowork
3. Drag the `.plugin` file into the Cowork chat window
4. Cowork shows a preview of what's inside the plugin — review and click **Install**
5. That's it. The skill is now active.

## How to use it in Cowork

In Cowork, paste a Slack thread URL and tell Claude what you want done. The skill triggers automatically on phrasing like:

- "Update wiki from this Slack thread: <link>"
- "Take this Slack discussion and add it to our docs: <link>"
- "Sync this Slack convo to Confluence: <link>"

You can also paste both a Slack URL and a Confluence page URL in the same message — the skill picks up on the combination.

### What happens next

1. Claude reads the Slack thread (parent + all replies)
2. Claude reads the target Confluence page
3. Claude proposes a specific edit: what to add, where exactly, what panel style, which space, and what the version message will say
4. You see a preview and approve / tweak / reject
5. Claude writes the update via Confluence's native format (no formatting damage)
6. You get a link to the updated page and can verify in Page History

If the thread is inconclusive, Claude will tell you instead of guessing.

## Example walkthrough

> **Matt:** Update wiki from this Slack thread: <https://dimagi.slack.com/archives/C05UNUNH43X/p1778674209472849>
>
> **Claude:** *(reads the thread, finds Pawan and Cal's resolution)* The thread is about whether the "Configure data forwarding" section on the "Run Your First Connect Opportunity" page should say "Forward Forms" or "Forward Form Metadata". Resolution: the wiki is correct as written — but it's confusing. Here's the clarifying note I propose adding right under the existing instruction, in an info panel:
>
> *(shows the exact proposed text + the surrounding context)*
>
> Approve?
>
> **Matt:** Yes
>
> **Claude:** Done. Version 23 is live. Only the new info panel was added — every other node on the page is byte-identical to v22. Version history reads: *"Add clarifying info panel under 'Configure data forwarding' (per Slack 2026-05-13 with Pawan/Cal/Ajeet)."*
> → [View page](https://dimagi.atlassian.net/wiki/spaces/connect/pages/2683405079/Run+Your+First+Connect+Opportunity)

## Defaults worth knowing

- **Internal first.** When the source page is in the internal `connect` space, the plugin only updates `connect` by default. It will explicitly ask before touching `connectpublic` (those two spaces are not mirrors).
- **ADF only.** It never uses markdown for writes. This is deliberate — markdown round-trips silently mangle Confluence pages with rich content.
- **Always asks.** No edit is written without your explicit approval. You can tell it to tweak the wording or change the approach at the confirmation step.

## Questions or issues

If you run into anything weird, ping Matt in Slack. The plugin is in version 0.1.0, so feedback shapes the next iteration.
