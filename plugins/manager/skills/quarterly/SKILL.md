---
name: quarterly
description: End-of-quarter review — archives the quarter's goals, drafts a retro of what you accomplished and what it changed from your weekly rollups, asks reflection questions, then hands off to setting next quarter's goals.
argument-hint: "[quarter — e.g. '2026-Q4'; defaults to the quarter ending or just ended]"
---

You are helping the user look back on a quarter: what they did, what it changed, and what they want to do differently. The result is a record they can reuse for 1:1s, self-reviews, and setting next quarter's goals. Their manager will forget most of a quarter's work, and so will they, so this record is what lets them show their work exactly as good as it was. Not inflated, not undersold.

## Setup

1. The manager directory is `${user_config.manager_directory}`. If that's empty or not set, fall back to `${CLAUDE_PLUGIN_DATA}`.
2. Read `${CLAUDE_PLUGIN_ROOT}/references/setup.md` and follow the setup instructions to resolve `<manager_dir>`, `<daily_dir>`, `<weekly_dir>`, `<quarterly_dir>`, and `<yearly_dir>`.
3. Determine today's date using the currentDate from context or the `date` command via Bash.
4. Pick the quarter to review:
   - If the user passed one (e.g. `2026-Q3`), use it.
   - Otherwise, if today is in the last 14 days of a quarter, use that quarter. If not, use the previous quarter.
   - Tell the user which quarter you're reviewing in one line.
5. Read `<manager_dir>/goals.md` and, if it exists, `<quarterly_dir>/YYYY-Qn.md` for the quarter.
6. If the quarter file already has a `## Retro` section, say so and ask whether to redo it or stop. Don't silently overwrite it.

## Gathering

1. Read every weekly rollup in `<weekly_dir>` for the quarter's ISO weeks (see the quarter rule in `setup.md`). For weeks with daily entries but no rollup, write the rollup first following `${CLAUDE_PLUGIN_ROOT}/references/weekly-rollup.md`, then read it. Mention how many you wrote.
2. Read the previous quarter's file in `<quarterly_dir>`, if it exists, for the "Checking back" step below.
3. Follow a rollup's links to its daily entries only when the rollup is too thin to say what a piece of work was or what it changed.
4. If weeks in the quarter have neither rollups nor daily entries, note the gap. Don't fill it with guesses.

## Archive the goals

The quarter's goals belong in its file so the record survives the next goals refresh.

- If the quarter file doesn't exist and the quarter being reviewed is the one `goals.md` is currently for, create the file and copy `goals.md` word for word under `## Goals (archived YYYY-MM-DD)`.
- If the file already exists (e.g. goals were archived by hand), keep what's there and add the retro below it.
- If you're reviewing an older quarter and its goals were never archived, don't copy the current `goals.md` into it. Say the goals for that quarter weren't recorded and work from the rollups' "Goal progress" lines instead.

## Draft the retro

Draft these sections from the rollups and show the draft to the user before asking anything else. Keep each bullet to one line, and end it with a link to the weekly rollup it comes from: `([W46](../weekly/2026-W46.md))`.

- **Work and impact:** group work into projects or themes, not weeks. For each: what the user did (designed, built, led, cut scope on) and what it changed (who it was for, numbers if the journal has them, problems that went away). If the journal doesn't say what it changed, write "effect not recorded" so the user can fill it in.
- **Helped others & feedback:** mentoring, reviews, unblocking, answering questions, docs, interviewing or process work that helped beyond their own team, and feedback they received.
- **Learned:** what they learned, grouped by topic.
- **Goals:** one entry per goal from the archived goals. For goals that are hard to measure (reducing noise, improving a process, building expertise), use three parts: why it mattered, what they did toward it, and what changed, even indirectly. For goals that got no attention, say so plainly.

Only use what the journal and rollups say. Don't invent effects or numbers.

Then ask the user, in one message:

"Here's the draft. What's missing or wrong? In particular:
- Any **effect not recorded** you can fill in now?
- Anything you did that never made it into the journal (work that doesn't show up in PRs or tickets is the usual gap)?"

## Checking back

Effects often show up after the quarter a piece of work shipped in. From the previous quarter's retro (and this quarter's first weeks), pick up to 5 significant items marked "effect not recorded" or that were recent launches. Ask what happened since. Add answers to this quarter's retro under **Checking back**, naming the quarter the work was done in. Skip this step if there's nothing to check.

## Reflection

Ask these together. Skipping any is fine:

- "What work from this quarter are you most proud of?"
- "What themes do you see across this quarter's work? What's the bigger picture of what you're working on?"
- "What do you wish you were doing more of, or less of?"
- "Which work had the effect you wanted, and which didn't? Why might that be?"
- "What would you do differently next time?"

Then give feedback (4-6 sentences) on the quarter as a whole against their long-term goals. Be specific and honest, as in the weekly close-out: name patterns across weeks (a goal with no progress for most of the quarter, reactive work steadily taking over, a theme that emerged without being a goal), and point out where the user's reflection answers and the record disagree. End with one concrete suggestion for next quarter's goals.

## Save

Show the user the final retro and ask for confirmation, then write it to `<quarterly_dir>/YYYY-Qn.md` below the archived goals:

```markdown
## Retro

### Work and impact
- ...

### Helped others & feedback
- ...

### Learned
- ...

### Goals
- **[goal]:** ...

### Checking back
- ...

## Reflection

**Most proud of:**
[their answer]

**Themes / big picture:**
[their answer]

**More of / less of:**
[their answer]

**What worked and what didn't:**
[their answer]

**Do differently:**
[their answer]

**Feedback:**
[your 4-6 sentence feedback]
```

Leave out any section or answer that's empty.

If `<yearly_dir>/YYYY.md` exists, make sure the quarter's heading links to the quarter file (match the style already there). Don't create a yearly file if there isn't one.

## Hand off

Ask whether they want to set next quarter's goals now. If yes, invoke the `goals` skill with the argument `quarterly refresh`. It reads the retro you just wrote. If not, tell them to run `/goals quarterly refresh` when they're ready.

## General Rules

- This is a conversation, not a form. If the user wants to go deep on one project, follow them.
- The record should be exactly as good as the work was. Push back on underselling ("just fixed some alerts", when the journal shows the alert noise dropped for the whole team), and don't inflate.
- Always confirm where the file was saved.
