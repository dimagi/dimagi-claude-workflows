# Version Message Format

Confluence stores a free-text version message with every page update. It shows up in Page History next to the version number. This is your single best tool for making wiki edits traceable.

## The format

```
Add [thing] per Slack discussion YYYY-MM-DD with [Names]. ADF surgical insert.
```

The "ADF surgical insert" suffix is optional but useful — it signals to anyone reviewing the version diff that the write went through the safe path, not a markdown round-trip.

## Examples by edit type

**Clarifying note in existing section:**

> `Add clarifying info panel under 'Configure data forwarding' (per Slack 2026-05-13 with Pawan/Cal/Ajeet). ADF surgical insert.`

**Section rewrite based on a thread:**

> `Rewrite 'Verification workflow' section to reflect 2026-05-08 design change discussed with Cal and the verification team in Slack. ADF surgical insert.`

**New page from a longer discussion:**

> `Create 'Data residency setup for international projects' page based on multi-day Slack thread (2026-04-22 → 2026-04-25, leads: Pawan, Cal, Mary). ADF write.`

**Stale-content correction:**

> `Correct 'Generate API keys' step — old URL was wrong. Confirmed in Slack 2026-05-11 with Sarvesh. ADF surgical insert.`

## Why this format

- **Type of edit** comes first so the reviewer immediately sees whether to expect a small or large change.
- **Date** anchors the rationale to a specific moment so the Slack thread can be found.
- **Names** make it possible to follow up if context is missing.
- **"ADF surgical insert"** distinguishes safe targeted edits from full-page rewrites.

## What to avoid

- Generic messages like `"Update page"` or `"Add note"` — these are useless for future readers.
- Names without dates, or dates without names — both are needed for traceability.
- Skipping the version message entirely (the API allows it, but you should never do this).
