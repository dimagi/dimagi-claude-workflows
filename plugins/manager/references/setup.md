# Plugin Setup

1. Resolve paths from the manager directory determined by the SKILL.md that referred you here:
   - **Manager directory** (`<manager_dir>`): top-level. Holds `goals.md`, `.last_sync`, and any other standalone files the user adds over time.
   - **Daily directory** (`<daily_dir>`): `<manager_dir>/daily`. Holds daily journal entries (`YYYY-MM-DD.md`) from standup and shutdown.
   - **Weekly directory** (`<weekly_dir>`): `<manager_dir>/weekly`. Holds weekly rollups (`YYYY-Www.md`, ISO week). See `${CLAUDE_PLUGIN_ROOT}/references/weekly-rollup.md`.
2. Create directories if they don't exist:
   - If `<manager_dir>` doesn't exist, create it.
   - If `<daily_dir>` doesn't exist, create it.
   - If `<weekly_dir>` doesn't exist, create it.
   - If this is the first time the user is using the plugin (no journal files exist in `<daily_dir>` yet), mention where things are being saved so they know.
   - If the goals file (`<manager_dir>/goals.md`) doesn't exist yet, create it using the template at `${CLAUDE_PLUGIN_ROOT}/references/goals-template.md`.
3. The weekly review day is `${user_config.review_day}` (default: Friday).
4. If `<manager_dir>/questions.md` exists, read it. It holds the user's custom questions. See "Custom Questions" below.

## Custom Questions

`<manager_dir>/questions.md` is optional. It has one `## <skill>` section per skill (e.g. `## standup`, `## shutdown`). A section can also be named `## <skill> (weekly)`, meaning it only applies on the review day. Each bullet is a question. A bullet may have an indented line starting with `→`, which is an action to take with the answer.

When a skill reaches its "present questions" step:
- On the review day, use the `## <skill> (weekly)` section. On any other day, use the plain `## <skill>` section. Ignore sections for other skills.
- Ask the custom questions in the same message as the skill's built-in questions, after them. Don't ask them separately.
- If the user doesn't answer a custom question, don't push. These are prompts, not requirements.
- For each answer, follow its `→` action if it has one (e.g. update another file in `<manager_dir>`), and tell the user what you did.
- In the journal entry, add each answered question after the skill's built-in fields and before any feedback field. Format: `**<short label for the question>:**` followed by the answer. Leave out questions that weren't answered.

If the file doesn't exist or has no section for the current skill, skip all of this silently.
