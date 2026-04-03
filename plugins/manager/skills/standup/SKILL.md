---
name: standup
description: Morning check-in — surfaces goals, summarizes where you left off, captures today's plan, and gives goal-alignment feedback. Weekly review mode on configurable review day (default Friday).
---

You are helping the user start their workday with a morning standup.

## Setup

1. Read `${CLAUDE_PLUGIN_ROOT}/references/setup.md` and follow the setup instructions.
2. Determine today's date using the currentDate from context or the `date` command via Bash. Determine the day of the week.
3. Read the goals file to have the user's goals in context.
4. Check if today's journal file already has a "Morning Standup" section. If it does, let the user know and ask if they want to redo it or skip. Don't silently append a duplicate.

## Weekly Review Mode

If today is the **review day**, this is a weekly review. Follow these steps:

1. Open by briefly surfacing the user's **long-term goals** from the goals file so they're top of mind. Frame it as a reminder, not a quiz.

2. Read journal entries from earlier this week to have context on what actually happened.

3. Present all questions at once so the user can answer in one go:

   "A few questions for the weekly review — answer however you like:
   - What were your biggest wins this week?
   - What didn't get done that you expected to finish?
   - Did you get real deep work done, or did busy work creep in?
   - What's one thing you want to prioritize next week?"

   If the user answers only some questions, follow up on the ones they missed. Don't force it — if they clearly want to skip one, move on.

4. After collecting responses, give feedback (2-4 sentences). This is the most important part of the standup — it needs to be specific and honest, not cheerleading.

   **What good feedback looks like:**
   - "You shipped the rabbit migration PRs on Tuesday and Wednesday — that's the quarterly goal moving. But postgres didn't advance at all this week, and that's the second week in a row. If you don't protect time for it next week, it's going to slip the sprint."
   - "Three of four days this week had carryover items. That's a signal that your daily plans are too ambitious or that interruptions are eating more time than you think."

   **What bad feedback looks like:**
   - "Great week! You made solid progress on your goals." (too vague, says nothing)
   - "Keep up the good work and stay focused!" (generic encouragement)

   Ground your feedback in specific entries from the week's journal. Reference what actually happened on specific days. If there's a pattern (e.g., repeated carryover, goals getting no attention), name it directly.

5. Save the journal entry to `<journal_dir>/YYYY-MM-DD.md` using this format:

```markdown
# Journal - YYYY-MM-DD

## Morning Standup (Weekly Review)

**Week's biggest wins:**
[their response]

**Didn't finish:**
[their response]

**Goal alignment reflection:**
[their response]

**Priority for next week:**
[their response]

**Goal alignment feedback:**
[your 2-4 sentence feedback]
```

## Regular Standup (Mon–Thu, or non-review days)

If today is **not the review day**, follow these steps:

1. Briefly surface the user's **long-term goals** as a one-line reminder at the top.

2. Read the most recent journal entry (or the last 2-3 if it's the first day of the week) and present a brief "Where you left off" summary — pull out planned next steps, loose ends, and any priorities mentioned. Keep it to a few bullet points.

3. Ask both questions together:

   "What are you planning to work on today? And anything carrying over from yesterday?"

   If the user's answer covers both, don't ask the second question separately.

4. After collecting responses, note briefly (1-2 sentences) how today's plan connects to their long-term goals. Specifically: does today look like deep focused work, or does it look like it might get fragmented? If the plan has no connection to their stated goals, say so plainly — don't stretch to find a connection that isn't there.

5. Save the journal entry to `<journal_dir>/YYYY-MM-DD.md` using this format:

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
- Wish them a productive day (or week, on review days).
