---
name: sync
description: Prep for 1:1s with your manager — auto-summarizes journal entries since your last sync into a briefing with wins, progress, and blockers.
argument-hint: "[manager name or topic focus]"
---

You are helping the user prepare for a 1:1 meeting with their manager by summarizing recent work from their journal.

## Setup

1. The manager directory is `${user_config.manager_directory}`. If that's empty or not set, fall back to `${CLAUDE_PLUGIN_DATA}`.
2. Read `${CLAUDE_PLUGIN_ROOT}/references/setup.md` and follow the setup instructions to resolve `<manager_dir>` and `<daily_dir>`.
3. Read the goals file (`<manager_dir>/goals.md`) to have the user's goals in context.
4. Determine the date range to summarize:
   - Read the sync log file at `<manager_dir>/.last_sync`. It contains a single date (`YYYY-MM-DD`) — the last time a sync was run.
   - If the sync log doesn't exist, default to the last 14 days.
   - The range is: **day after last sync** through **today**.

## Gathering Context

5. For each ISO week that falls entirely within the date range and has a rollup in `<weekly_dir>`, read the rollup instead of that week's daily entries. For everything else in the range (partial weeks, weeks without a rollup), list the journal files in `<daily_dir>` and read them. If a rollup is too thin to support a point you want to make, read that week's dailies too.
5. If the user passed an argument (e.g. a manager name or topic), note it — you'll tailor the summary to that context.

## Generating the Sync Summary

6. Present a structured summary to the user in this format:

```
## 1:1 Sync Prep — [date range]

### Wins & Accomplishments
- [Concrete things completed, shipped, or unblocked — pull from "Accomplished" and "Finished today" sections]

### In Progress
- [Work that's actively ongoing — pull from recent "Plans for today" and "Notes for tomorrow" sections]

### Blockers & Concerns
- [Anything flagged as a blocker, things that didn't get done repeatedly, or frustrations mentioned]

### Goal Alignment
[2-3 sentence assessment of how the period went relative to long-term goals. Reference specific days and entries — not vague summaries. Name which goals got attention and which didn't. If deep work was lacking, say so plainly.]

### Suggested Talking Points
- [2-4 bullet points the user might want to raise with their manager, based on the above]
```

7. After presenting the summary, ask the user:
   - "Anything you want to add, change, or emphasize before I save this?"

8. Incorporate any feedback, then save the sync summary by appending to today's journal entry at `<daily_dir>/YYYY-MM-DD.md`:

```markdown
## 1:1 Sync Prep [HH:MM]

**Period:** [start date] to [end date]

**Wins:**
[bulleted list]

**In Progress:**
[bulleted list]

**Blockers:**
[bulleted list]

**Goal alignment:**
[your assessment]

**Talking points:**
[bulleted list]
```

9. Update the sync log file at `<manager_dir>/.last_sync` with today's date (overwrite the file with just `YYYY-MM-DD`).

## General Rules

- If the journal file for today doesn't exist, create it with a `# Journal - YYYY-MM-DD` heading before appending.
- Always confirm that the sync prep has been saved and the sync log has been updated.
- Keep the summary concise and actionable — this is a meeting prep tool, not an essay.
