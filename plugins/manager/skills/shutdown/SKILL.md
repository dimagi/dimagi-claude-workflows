---
name: shutdown
description: End of day wrap-up — captures what got done, what didn't, and plans for tomorrow. Weekly close-out on configurable review day (default Friday).
---

You are helping the user wrap up their workday with an evening shutdown.

## Setup

1. Read `${CLAUDE_PLUGIN_ROOT}/references/setup.md` and follow the setup instructions.
2. Determine today's date using the currentDate from context or the `date` command via Bash. Determine the day of the week.
3. Read the goals file and today's journal entry (if it exists) to have full context.
4. Check if today's journal file already has an "Evening Shutdown" section. If it does, let the user know and ask if they want to redo it or skip. Don't silently append a duplicate.

## Weekly Close-Out

If today is the **review day**, this is the weekly close-out. Follow these steps:

1. Present all questions at once:

   "Wrapping up the week — answer however you like:
   - What did you finish up today?
   - Any loose ends to note before the weekend?
   - How are you feeling about where things stand heading into next week?"

   If the user answers only some, follow up on what they missed. Don't force it.

2. After collecting responses, read the morning standup section from today's journal (if it exists) and journal entries from earlier in the week for full context.

3. Give feedback (3-5 sentences) on the week as a whole, grounded specifically in their long-term goals. Name patterns you noticed across the week's entries. Give one concrete suggestion for next week.

   **What good feedback looks like:**
   - "You committed to clearing the sprint board on Monday's review, and you got the rabbit announcement ticket closed but not the postgres PR. That's the same goal that slipped last week. The pattern suggests it needs a dedicated block of time rather than hoping to squeeze it in."
   - "This week had a clear through-line: three out of four days were spent on migration work. That's the kind of sustained focus your goals call for. The one risk is that data deletion hasn't gotten any attention in two weeks."

   **What bad feedback looks like:**
   - "Overall a productive week with good progress!" (says nothing specific)
   - "Try to stay focused next week!" (generic, not actionable)

4. Save the journal entry by appending to `<journal_dir>/YYYY-MM-DD.md`:

```markdown
## Evening Shutdown (Weekly Close-Out)

**Finished today:**
[their response]

**Loose ends:**
[their response]

**Heading into next week:**
[their response]

**Weekly goal alignment feedback:**
[your 3-5 sentence feedback]
```

## Regular Shutdown (non-review days)

If today is **not the review day**, follow these steps:

1. If today's journal has a morning standup section, read it to know what was planned.

2. Present all questions together:

   "How'd today go?
   - What did you accomplish?
   - Any blockers or things that didn't get done?
   - Anything to carry into tomorrow?"

   If the user answers everything in one message, don't re-ask.

3. After collecting responses, give a brief (1-2 sentence) observation grounded in their long-term goals. If a morning standup exists for today, compare what was planned vs. what actually happened — note if the day went to plan or veered off. If today was disconnected from their goals, name it plainly.

4. Append to `<journal_dir>/YYYY-MM-DD.md`:

```markdown
## Evening Shutdown

**Accomplished:**
[their response]

**Blockers / Didn't finish:**
[their response]

**Notes for tomorrow:**
[their response]

**Goal connection:**
[your 1-2 sentence observation]
```

## General Rules

- If the journal file doesn't exist, create it with a `# Journal - YYYY-MM-DD` heading before appending.
- Always confirm to the user that the entry has been saved.
- Wish them a good evening (or a good weekend, on review days).
