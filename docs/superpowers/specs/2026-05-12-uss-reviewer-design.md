# USS Code-Review Specialist — Design

**Date:** 2026-05-12
**Plugin:** `uss-tech`
**Depends on:** `code-review` plugin

## Goal

Add a USS-specific code-review specialist that complements the existing
`code-review` plugin's 5-agent review with a 6th dimension focused on the
USS Tech team's concerns:

1. Clarifying which audiences are affected by each change (behind a flag, a
   subscription tier, a project setting, or ungated).
2. Checking correctness of any gating that *is* applied.
3. Surfacing blast-radius risks for ungated changes that touch shared
   platform infrastructure.

The deliverable is a new command `/uss-review` and a new specialist agent,
both housed inside the `uss-tech` plugin.

## Non-goals

- This is **not** a gating-compliance auditor. Ungated changes are often
  fine or preferred. The reviewer surfaces audience and impact for clarity;
  it does not flag the absence of a gate as a defect.
- Not modifying the `code-review` plugin. `code-review` remains a
  general-purpose review tool usable by any team in the marketplace.

## Constraints & context

- The marketplace at `.claude-plugin/marketplace.json` lists each plugin as
  an independent opt-in install. Users of `code-review` do not automatically
  get `uss-tech` (or vice versa). The USS specialist must therefore live in
  `uss-tech`, not in `code-review`.
- `/uss-review` is intended for the USS team — it requires the
  `code-review` plugin to be installed (it reuses code-review's 5 agent
  files). This dependency must be documented in the uss-tech README.

## Architecture

### File layout

```
plugins/uss-tech/
├── commands/
│   └── uss-review.md       ← /uss-review command (orchestrator)
└── agents/
    └── uss-reviewer.md     ← the new USS specialist agent
```

The agent uses the same shape as `code-review`'s existing agents (reads
code, writes a JSON file with findings, stays in its lane). The command
file is the orchestrator and the user-facing trigger.

### Execution model: parallel spawn, two-pass output

`/uss-review` spawns **all 6 agents in parallel**: the 5 from
`code-review/agents/` plus `uss-tech/agents/uss-reviewer.md`. They share a
temp working directory and follow the same JSON-per-agent contract that
`code-review` uses today.

After all agents complete, output is rendered in two blocks:

1. **Block 1** — the standard code-review synthesis (Summary, Findings
   table numbered 1–N, Design Observations, What's Working Well), exactly
   as the existing skill produces it.
2. **Block 2** — the USS section, appended after a `---` separator
   (Summary, USS Findings table with `U`-prefixed numbering, User-Facing
   Changes by Audience).

The expand/fix loop after both blocks accepts numbers from either space:
`expand 3`, `fix U2`, `1-4`, `fix U1,U3`, `all`.

### Cross-plugin reference

The `/uss-review` command needs to locate the 5 reviewer agent files
inside the separately-installed `code-review` plugin. `${CLAUDE_PLUGIN_ROOT}`
resolves to the `uss-tech` plugin's root, not `code-review`'s — so the
command needs another mechanism to find `code-review`'s files. Options to
evaluate during implementation:

- Search known marketplace install paths relative to `${CLAUDE_PLUGIN_ROOT}`
  (e.g., `../code-review/agents/`)
- Use a `find` or `glob` over the plugins root to locate `code-review`
- Inline the relevant agent instructions into `/uss-review` itself,
  trading reuse for independence

If `code-review` is not installed, the command should fail with a clear
message instructing the user to install it via `/plugins`. (If the chosen
mechanism is "inline" rather than "reference", this preflight check
becomes unnecessary.)

## The USS reviewer agent

### Focus areas

1. **Audience inventory (primary deliverable)** — for every behavior change
   in the diff, identify the audience: behind a specific flag, limited to a
   subscription tier, gated on a project setting, or ungated (affects all
   CommCare users). The `ungated` bucket is not a problem signal; it is
   transparency about wide-impact changes.

2. **Gate correctness (when gating is used)** — when a gate exists, verify
   it does what's intended: right flag name, right scope (per-project vs.
   per-user), right boolean direction, no bypass paths through ungated
   entry points. About whether the chosen tool works, not whether a tool
   was chosen.

3. **Blast radius for ungated changes** — when something is ungated,
   surface places where the impact may be wider than the author expects, so
   they can confirm the impact is intentional. Checks include:
   - Database migrations (schema changes apply to all projects)
   - Signal handlers, background tasks, scheduled jobs (run independent of
     flags unless explicitly gated)
   - Shared caches, queues, counters (USS load on these affects everyone)
   - Module-level side effects, new imports (startup impact)
   - Changes to shared utilities/helpers (all callers affected)
   - Default-value changes that propagate to ungated callers
   - Performance: slow queries, lock contention on shared tables

### Findings severity rubric

- 🔴 **Critical** — an actual bug, e.g., gate inverted and will run for
  everyone when intended only for USS.
- 🟠 **Major** — significant impact worth confirming, e.g., touches a
  shared signal handler that runs for all projects — intentional?
- 🟡 **Minor** — subtler audience ambiguity or blast-radius risk.
- 💡 **Suggestion** — clarity opportunities (e.g., consolidating where a
  gate is checked, naming the audience explicitly in a comment).

Findings exist to **surface for confirmation or correction**, not to flag
non-compliance with a gating standard.

### JSON output schema

```json
{
  "dimension": "uss-impact",
  "summary": "2-3 sentences on overall audience clarity and any notable blast-radius risks. Neutral on whether changes are gated.",
  "findings": [
    {
      "severity": "critical|major|minor|suggestion",
      "title": "Short descriptive title (max 8 words)",
      "location": "path/to/file.py:L10-L25",
      "description": "What the gating-correctness bug or blast-radius risk is, and what could go wrong concretely.",
      "suggestion": "How to fix or tighten the gate, or how to bound the impact."
    }
  ],
  "user_facing_changes": [
    {
      "audience": "flag:RELEASE_NOTES_V2",
      "changes": [
        "Users with the flag see a new sidebar widget",
        "Edit-flow now bypasses the legacy validator"
      ]
    },
    {
      "audience": "ungated",
      "changes": [
        "Background job switched from DEBUG to INFO logging (affects all)"
      ]
    }
  ]
}
```

The `audience` field is a tagged string for simple grouping by the
synthesizer:

| Tag form | Meaning |
|----------|---------|
| `flag:<NAME>` | Behind a feature flag |
| `subscription:<NAME>+` | Limited to a subscription tier or higher |
| `setting:<NAME>` | Gated on a project setting |
| `ungated` | Affects all CommCare users |

### References

No reference files in v1. Gating idioms and the blast-radius checklist are
inlined in the agent's prompt. If commcare-hq-specific patterns grow past
inline-able, add `plugins/uss-tech/agents/references/gating-patterns.md`
in a follow-up.

## Synthesized output format

### Block 1 — Standard code-review output

Produced verbatim by the standard code-review synthesis logic. No
modifications.

### Block 2 — USS section

```
---

## USS Impact

### Summary
2–3 sentences on overall audience clarity and any notable blast-radius risks.

### USS Findings
| #  | Sev | Finding | Location |
|----|-----|---------|----------|
| U1 | 🔴  | [title] | [file:line] |
| U2 | 🟠  | [title] | [file:line] |

### User-Facing Changes by Audience

**Ungated (affects all CommCare users)**
- Background job switched from DEBUG to INFO logging
- New default for `timeout_seconds` propagates to all callers

**Behind flag `RELEASE_NOTES_V2`**
- Users with the flag see a new sidebar widget
- Edit-flow now bypasses the legacy validator

**Subscription `Pro+`**
- Export now supports CSV in addition to XLSX

**Project setting `enable_advanced_search`**
- Search results include archived records
```

**Audience ordering** in the User-Facing Changes section: `ungated` first
(highest-leverage information), then flags, subscriptions, settings.
Within each audience group, list changes in the order the reviewer
generated them (no enforced ordering).

If the reviewer found no user-facing changes in a given audience bucket,
omit that bucket entirely (no empty headings).

### Expand/fix loop

Mirrors code-review's existing loop semantics, with the parser extended
to recognize the `U` prefix:

| Input pattern | Action |
|---------------|--------|
| `1,3,5` or `U1,U3` | Expand listed findings |
| `1-4` | Expand range from main table |
| `U1-U3` | Expand range from USS table |
| `all` | Expand everything in both tables |
| `fix 2,U1` | Expand and implement listed findings |
| `done` | Exit |
| Natural language | Map to the closest matching finding by title |

## /uss-review command behavior

1. **Preflight**: verify `code-review` plugin is installed by checking that
   the 5 agent files exist at their resolved paths. If missing, print an
   actionable error.
2. **Scope establishment**: same as code-review Step 1 (what to review,
   language, purpose). Read the code with `Read`/`Glob` first.
3. **Spawn 6 agents in parallel** — 5 from code-review plus
   `uss-tech/agents/uss-reviewer.md`. All write JSON to the same temp
   working directory.
4. **Collect** — read all 6 JSON files.
5. **Synthesize** — produce Block 1 (standard code-review synthesis) then
   Block 2 (USS section).
6. **Expand/fix loop** — accept user input across both number spaces until
   `done`.
7. **Cleanup** — remove the temp working directory.

## Out of scope for v1

- A fallback for environments without sub-agent support. (`code-review`
  has one; we will add an analogous fallback to `/uss-review` if needed.)
- Auto-detection of USS context to trigger via the standard `/review`
  flow. `/uss-review` is an explicit opt-in.
- Skill-based intent triggering ("review for USS impact") — command-only
  for now.
- Reference files for commcare-hq-specific gating idioms.

## Open questions

- **Cross-plugin reference mechanism** — how `/uss-review` should locate
  `code-review`'s agent files. See the Cross-plugin reference section for
  candidate approaches. This will be settled when implementation begins,
  not before.

The agent's prompt content (the specific gating idioms and blast-radius
checklist it inlines) will be authored during implementation; some
iteration after first real-use is expected.
