# manager

A daily rhythm for professional goals: check in each morning, wrap up each
evening, and keep a journal that turns into 1:1 material without extra effort.

The four skills share one directory — `goals.md` at the top level and a
`daily/` folder of `YYYY-MM-DD.md` journal entries. It's created on first use.

## Skills

- `standup` — Morning check-in. Surfaces your goals, summarises where you left
  off, captures today's plan, and gives goal-alignment feedback. Switches to
  weekly review mode on your review day.

- `shutdown` — End-of-day wrap-up. Captures what got done, what didn't, and the
  plan for tomorrow. Closes out the week on your review day.

- `sync` — Prep for a 1:1. Summarises journal entries since your last sync into
  a briefing of wins, progress, and blockers.
  Example: `/sync focus on the migration`

- `goals` — Review, update, and refine your goals conversationally.
  Example: `/goals quarterly refresh`

## Configuration

Both settings are optional:

- `manager_directory` — where goals and journal entries live. Defaults to the
  plugin's own data directory.
- `review_day` — the day `standup` and `shutdown` switch to weekly review mode.
  Defaults to Friday.

## Weekly rollups

The weekly close-out in `shutdown` also writes a short summary of the week
to `weekly/YYYY-Www.md`: wins, what slipped, progress on each goal, and
patterns. Each point links back to the daily entry it came from. If you
skip a close-out, the next `standup` catches up the
missed week. `sync` reads rollups for full weeks instead of every daily
entry, and they make quarterly or annual reflection much quicker. To
backfill older weeks, ask for it.

## Custom questions

To add your own questions to `standup` or `shutdown`, create
`questions.md` in your manager directory. Each `## <skill>` section holds
the questions for that skill. A `## <skill> (weekly)` section adds
questions on your review day. An indented `→` line says what to do with the
answer:

```markdown
## shutdown
- What was painful today that others might not see?
  → If answered, add it to the "Pain Points" section of ideas.md.

## shutdown (weekly)
- Did I make progress on this quarter's idea write-up?

## standup
- Anything from yesterday I'm avoiding?
```

Custom questions are asked alongside the built-in ones, and their answers
are saved to the journal entry.
