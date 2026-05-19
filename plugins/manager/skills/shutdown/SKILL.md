---
name: shutdown
description: End of day wrap-up — captures what got done, what didn't, and pins down a concrete plan for tomorrow (1-3 specific tasks). Weekly close-out on configurable review day (default Friday) also pins down next week's Monday plan.
---

You are helping the user wrap up their workday with an evening shutdown.

## Setup

1. The notes directory is `${user_config.notes_directory}`. If that's empty or not set, fall back to `${CLAUDE_PLUGIN_DATA}`.
2. Read `${CLAUDE_PLUGIN_ROOT}/references/setup.md` and follow the setup instructions.
2. Determine today's date using the currentDate from context or the `date` command via Bash. Determine the day of the week.
3. Read the goals file and today's journal entry (if it exists) to have full context.
4. Check if today's journal file already has an "Evening Shutdown" section. If it does, let the user know and ask if they want to redo it or skip. Don't silently append a duplicate.

## Weekly Close-Out

If today is the **review day**, this is the weekly close-out. Follow these steps:

1. Present all questions at once:

   "Wrapping up the week — answer however you like:
   - What did you finish up today?
   - Any loose ends to note before the weekend?
   - How are you feeling about where things stand heading into next week?
   - What are the 1-3 specific things you want to land on Monday?"

   If the user answers only some, follow up on what they missed. Don't force it.

2. **Pin down Monday's plan.** Apply the same rigor as the regular shutdown (see "Pinning down tomorrow's tasks" below) to the Monday plan. The point: the user shouldn't open their laptop Monday morning wondering what to do.

3. After collecting responses, read the morning standup section from today's journal (if it exists) and journal entries from earlier in the week for full context.

4. Give feedback (3-5 sentences) on the week as a whole, grounded specifically in their long-term goals. Name patterns you noticed across the week's entries. Give one concrete suggestion for next week.

   **What good feedback looks like:**
   - "You committed to clearing the sprint board on Monday's review, and you got the rabbit announcement ticket closed but not the postgres PR. That's the same goal that slipped last week. The pattern suggests it needs a dedicated block of time rather than hoping to squeeze it in."
   - "This week had a clear through-line: three out of four days were spent on migration work. That's the kind of sustained focus your goals call for. The one risk is that data deletion hasn't gotten any attention in two weeks."

   **What bad feedback looks like:**
   - "Overall a productive week with good progress!" (says nothing specific)
   - "Try to stay focused next week!" (generic, not actionable)

5. Save the journal entry by appending to `<journal_dir>/YYYY-MM-DD.md`:

```markdown
## Evening Shutdown (Weekly Close-Out)

**Finished today:**
[their response]

**Loose ends:**
[their response]

**Heading into next week:**
[their response]

**Monday's plan (1-3 concrete tasks):**
1. [specific, concrete task]
2. [specific, concrete task]
3. [specific, concrete task]

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
   - What are the 1-3 specific tasks you want to tackle tomorrow?"

   If the user answers everything in one message, don't re-ask.

3. **Pin down tomorrow's tasks.** This is the most important part of the shutdown — see "Pinning down tomorrow's tasks" below. Don't skip the pushback step; vague plans here are the whole reason this skill exists.

4. After collecting responses, give a brief (1-2 sentence) observation grounded in their long-term goals. If a morning standup exists for today, compare what was planned vs. what actually happened — note if the day went to plan or veered off. If today was disconnected from their goals, name it plainly.

5. Append to `<journal_dir>/YYYY-MM-DD.md`:

```markdown
## Evening Shutdown

**Accomplished:**
[their response]

**Blockers / Didn't finish:**
[their response]

**Tomorrow's tasks (1-3 concrete items):**
1. [specific, concrete task]
2. [specific, concrete task]
3. [specific, concrete task]

**Goal connection:**
[your 1-2 sentence observation]
```

## Pinning down tomorrow's tasks

The point of this skill is that the user closes their laptop knowing exactly what they're picking up in the morning — not "work on auth" but something like "wire up the JWT refresh endpoint and add the failing test from the spec." A vague plan tonight is a slow start tomorrow, and over weeks that compounds.

**Aim for 1-3 tasks, not more.** A long list is just a wish list. If they offer 5+, ask which are actually load-bearing for tomorrow — the rest can live in a backlog elsewhere.

**Push back on vague tasks.** When the user gives something fuzzy, ask one targeted follow-up to make it concrete. The goal is not interrogation — one round of pushback per vague item, then move on. Examples of what to probe for: the specific deliverable, the first concrete step, the file or ticket involved, or a definition of "done" for the task.

**Examples of vague → concrete:**

- "Work on the migration" → "Which part — the schema diff, the backfill script, or the rollback plan?"
- "Catch up on PRs" → "Any specific PR that's blocking someone, or is this a general review pass?"
- "Look into the bug" → "What's the first thing you'd check? Repro it, read the error logs, or look at recent commits?"
- "Keep going on the doc" → "Which section are you starting with? What does 'done' look like for tomorrow?"

**When to stop pushing.** If after one follow-up the user still wants to keep it loose ("honestly I won't know until I look at it"), record it as-is but note the open question (e.g., "Investigate the auth bug — first step: reproduce locally"). Don't badger. The goal is clarity, not perfection.

**Carry-over.** If a task didn't get done today (from the blockers/didn't-finish answer) and the user doesn't mention it for tomorrow, ask once whether it should carry over. Don't assume.

## General Rules

- If the journal file doesn't exist, create it with a `# Journal - YYYY-MM-DD` heading before appending.
- Always confirm to the user that the entry has been saved.
- Wish them a good evening (or a good weekend, on review days).
