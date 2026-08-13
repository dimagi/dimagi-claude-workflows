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
