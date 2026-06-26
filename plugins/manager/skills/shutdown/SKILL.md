---
name: shutdown
description: End of day wrap-up — captures what got done, what didn't, and plans for tomorrow. Weekly close-out on configurable review day (default Friday).
---

You are helping the user wrap up their workday with an evening shutdown.

## Setup

1. The manager directory is `${user_config.manager_directory}`. If that's empty or not set, fall back to `${CLAUDE_PLUGIN_DATA}`.
2. Read `${CLAUDE_PLUGIN_ROOT}/references/setup.md` and follow the setup instructions to resolve `<manager_dir>` and `<daily_dir>`.
3. Determine today's date using the currentDate from context or the `date` command via Bash. Determine the day of the week.
4. Read the goals file (`<manager_dir>/goals.md`) and today's journal entry at `<daily_dir>/YYYY-MM-DD.md` (if it exists) to have full context.
5. Check if today's journal file already has an "Evening Shutdown" section. If it does, let the user know and ask if they want to redo it or skip. Don't silently append a duplicate.

## GitHub Activity

Before asking any questions, pull a quick summary of GitHub actions the user personally took since their last shutdown. This gives both of you concrete grounding for the "what did you accomplish" conversation and ensures nothing slips through the cracks.

1. Determine the cutoff time: use 24 hours ago from now (`date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ` on Linux, or `date -u -v-24H +%Y-%m-%dT%H:%M:%SZ` on macOS).

2. Fetch the user's GitHub events:
   ```bash
   gh api "/users/$(gh api user --jq '.login')/events?per_page=100"
   ```

3. Filter to events whose `created_at` is after the cutoff, keeping only:
   - `PullRequestReviewEvent` — the user submitted a code review
   - `PullRequestEvent` with `payload.action == "opened"` — the user created a PR
   - `PullRequestEvent` with `payload.action == "merged"` — the user merged a PR

   Ignore all other event types (pushes, comments, label changes, etc.) and ignore any actions triggered by other users even if the user is a reviewer on those PRs.

4. For each qualifying event, get the PR title and URL:
   ```bash
   gh pr view <number> -R <repo> --json title,url
   ```
   The repo name is in `event.repo.name` (e.g. `dimagi/commcare-hq`). The PR number is in `event.payload.number`.

5. Present a brief grouped summary inline before asking questions. For example:
   
   > **Your GitHub activity (past 24 hours):**
   > - Merged: Unify `@serial_task` and `@concurrent_task` (#37802) — dimagi/commcare-hq
   > - Merged: Let uv manage Python in CI workflows (#37816) — dimagi/commcare-hq
   > - Reviewed (approved): Remove app_execution app (#37822) — dimagi/commcare-hq
   
   If there's nothing to show, skip this block silently — don't mention it.

Keep this as context for the journal entry (see templates below).

## Weekly Close-Out

If today is the **review day**, this is the weekly close-out. Follow these steps:

1. Present all questions at once:

   "Wrapping up the week — answer however you like:
   - What did you finish up today?
   - Any loose ends or specific tasks to pick up first thing Monday?
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

4. Save the journal entry by appending to `<daily_dir>/YYYY-MM-DD.md`:

```markdown
## Evening Shutdown (Weekly Close-Out)

**GitHub activity:**
[bullet list from the GitHub activity section, or omit if none]

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
   - What are the specific tasks you're picking up tomorrow?"

   If the user answers everything in one message, don't re-ask.

3. **Sharpen the tasks for tomorrow.** This is the most important part of shutdown — tomorrow's standup reads this as "where you left off," so vague entries here make the next morning worse. If the user's answer is concrete (e.g. "finish the JWT refresh logic in auth.py and open the PR", "draft the Q3 roadmap section on migrations"), accept it. If it's vague ("keep working on the migration", "follow up on PRs", "more onboarding stuff"), push back once: ask what specifically they'll start with — the first file to open, the first person to ping, the first concrete sub-task. One round of sharpening, not an interrogation. If they push back ("I'll figure it out in the morning"), respect that and save what they have.

4. After sharpening, give a brief (1-2 sentence) observation grounded in their long-term goals. If a morning standup exists for today, compare what was planned vs. what actually happened — note if the day went to plan or veered off. If today was disconnected from their goals, name it plainly.

5. Append to `<daily_dir>/YYYY-MM-DD.md`:

```markdown
## Evening Shutdown

**GitHub activity:**
[bullet list from the GitHub activity section, or omit if none]

**Accomplished:**
[their response]

**Blockers / Didn't finish:**
[their response]

**Tomorrow's tasks:**
[sharpened, concrete list — one bullet per task]

**Goal connection:**
[your 1-2 sentence observation]
```

## General Rules

- If the journal file doesn't exist, create it with a `# Journal - YYYY-MM-DD` heading before appending.
- Always confirm to the user that the entry has been saved.
- Wish them a good evening (or a good weekend, on review days).
