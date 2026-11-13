# Weekly Rollup

A weekly rollup condenses one ISO week of daily journal entries into a short summary at `<weekly_dir>/YYYY-Www.md` (e.g. `2026-W46.md`). Rollups let `sync` and long-range reflection (quarterly goals, annual reviews) read a few dozen short files instead of hundreds of daily ones. Daily entries stay the source of truth. Never edit or delete them when writing a rollup.

## Writing a rollup

1. Read every file in `<daily_dir>` dated within the ISO week (Monday through Sunday). If there are none, don't write a rollup.
2. Read `<manager_dir>/goals.md` so goal progress is judged against the current goals.
3. Write `<weekly_dir>/YYYY-Www.md` using the template below. If the file already exists, overwrite it. The rollup is regenerated from the dailies, not appended to.
4. Only summarize what the journal says. Don't invent outcomes. If something was planned but there's no record of whether it happened, say so.
5. Keep it short: aim for under ~25 lines. It's an index into the week, not a retelling.
6. End each bullet with a link to the daily entry (or entries) it comes from, as a standard relative markdown link: `([2026-11-10](../daily/2026-11-10.md))`. These let readers, and skills like `sync`, jump to the day behind a claim instead of rereading the whole week. Use standard links rather than `[[wikilinks]]` so they work everywhere, including Obsidian's graph and backlinks.

```markdown
# Week YYYY-Www (Mon DD – Fri DD Month)

**Wins:**
- [things finished, shipped, or unblocked] ([YYYY-MM-DD](../daily/YYYY-MM-DD.md))

**Slipped / carried over:**
- [planned but not done, especially anything that carried over more than once]

**Goal progress:**
- [one line per goal from goals.md: what moved it, or "no progress"]

**Patterns & notes:**
- [recurring themes, unplanned work that took over, decisions made, notable answers to custom questions]
```

Leave out any section with nothing to report.
