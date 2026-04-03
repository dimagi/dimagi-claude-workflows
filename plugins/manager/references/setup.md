# Plugin Setup

1. The notes directory should already be determined from the SKILL.md that referred you here. Journal entries are saved there, the goals file is at `<notes_dir>/goals.md`, and the sync log is at `<notes_dir>/.last_sync`.
   - If the notes directory doesn't exist yet, create it.
   - If this is the first time the user is using the plugin (no journal files exist yet), mention where notes are being saved so they know.
   - If the goals file doesn't exist yet, create it using the template at `${CLAUDE_PLUGIN_ROOT}/references/goals-template.md`.
2. The weekly review day is `${user_config.review_day}` (default: Friday).
