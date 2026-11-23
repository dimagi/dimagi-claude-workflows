---
name: standup
description: Morning check-in — surfaces goals, summarizes where you left off, captures today's plan, and gives goal-alignment feedback.
---

You are helping the user start their workday with a morning standup.

## Setup

1. The manager directory is `${user_config.manager_directory}`. If that's empty or not set, fall back to `${CLAUDE_PLUGIN_DATA}`.
2. Read `${CLAUDE_PLUGIN_ROOT}/references/setup.md` and follow the setup instructions to resolve `<manager_dir>` and `<daily_dir>`.
3. Determine today's date using the currentDate from context or the `date` command via Bash. Determine the day of the week.
4. Read the goals file (`<manager_dir>/goals.md`) to have the user's goals in context.
5. Check if today's journal file (`<daily_dir>/YYYY-MM-DD.md`) already has a "Morning Standup" section. If it does, let the user know and ask if they want to redo it or skip. Don't silently append a duplicate.
6. Find the most recent ISO week before the current one that has daily entries. If `<weekly_dir>` has no rollup for it (e.g. the user skipped their weekly close-out), write one following `${CLAUDE_PLUGIN_ROOT}/references/weekly-rollup.md` and mention it in one line. Only catch up that one week. Don't backfill older weeks unless the user asks.

## Standup

The standup is the same every day, including the review day. The weekly review happens in the `shutdown` weekly close-out, once the week is actually over.

1. Briefly surface the user's **long-term goals** as a one-line reminder at the top.

2. Read the most recent journal entry (or the last 2-3 if it's the first day of the week) and present a brief "Where you left off" summary — pull out planned next steps, loose ends, and any priorities mentioned. Keep it to a few bullet points.

3. Ask both questions together, along with any custom questions for this skill (see "Custom Questions" in `setup.md`):

   "What are you planning to work on today? And anything carrying over from yesterday?"

   If the user's answer covers both, don't ask the second question separately.

4. After collecting responses, note briefly (1-2 sentences) how today's plan connects to their long-term goals. Specifically: does today look like deep focused work, or does it look like it might get fragmented? If the plan has no connection to their stated goals, say so plainly — don't stretch to find a connection that isn't there.

5. Save the journal entry to `<daily_dir>/YYYY-MM-DD.md` using this format:

```markdown
# Journal - YYYY-MM-DD

## Morning Standup

**Plans for today:**
[their response]

**Carrying over:**
[their response]

**Goal connection:**
[your 1-2 sentence note on how today's plan relates to their goals]
```

## General Rules

- If the file already exists, append the standup section rather than overwriting.
- Always confirm to the user that the entry has been saved.
- Wish them a productive day.
