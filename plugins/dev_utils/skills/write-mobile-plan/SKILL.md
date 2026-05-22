---
name: write-mobile-plan
description: Use when the user runs /write-mobile-plan or asks to write/draft an implementation plan, design plan, or scoping doc for a piece of mobile work — typically with a JIRA ticket, design doc, problem description, or conversation context already provided. Saves a human-readable plan to docs/plans/ with GitHub links pointing to master.
---

# Write Mobile Plan

## Overview

Produce an implementation plan that a junior engineer can read end-to-end and start coding from. Save it to `docs/plans/` in the current repo, with GitHub permalink-style links that point to `master`.

**Audience is a human junior engineer.** Do not optimize for AI consumption: no step IDs, no machine-readable scaffolding, no token-saving abbreviations. Write like a tech lead handing off work.

**Structure the work in large sequential phases.** Each phase builds on the previous one, but each phase is a self-contained chunk the engineer can implement, test, and merge before starting the next. See the template for what a phase looks like.

## When to Use

- User runs `/write-mobile-plan`
- User asks to "write a plan", "draft a plan", "scope out X", or similar, for mobile work
- Context for the work already exists in the conversation (JIRA ticket, design doc, problem statement, prior discussion)

If no context exists in the conversation, stop and ask: *"What's the scope of the plan? Share a JIRA ticket, problem description, or design doc."* Do not invent scope.

## Process

1. **Confirm context exists.** If the conversation has no concrete scope, ask for it and wait. Do not proceed without it.

2. **Ask 2-4 clarifying questions** with `AskUserQuestion`. Only ask things you can't confidently infer from context. Common gaps:
   - Scope boundaries (what's explicitly in vs. out)
   - Acceptance criteria / definition of done
   - Constraints (deadlines, backwards compatibility, existing patterns to follow)
   - Approach when multiple viable paths exist

3. **Use the fixed repo for links:** `dimagi/commcare-android`. Link format: `https://github.com/dimagi/commcare-android/blob/master/<path>` with optional line range `#L<start>-L<end>`.

4. **Explore the code** enough to make the plan concrete. Identify the specific files, classes, and functions the engineer will touch. Read enough to name them accurately — do not guess.

5. **Draft the plan** using the template below.

6. **Verify every GitHub link resolves at master** before writing the file:
   - `git cat-file -e master:<path>` confirms the path exists at master
   - For line-range links, confirm the range is within bounds (`git show master:<path> | wc -l`)
   - Fix or drop any link that doesn't resolve. If the code isn't on master yet, describe it in prose instead of linking.

7. **Save the file** to `docs/plans/<slug>.md` in the current working directory. Create `docs/plans/` if it doesn't exist. Slug rules:
   - JIRA ticket present: `<TICKET-ID>-<short-kebab-title>.md` (e.g., `CCCT-2354-back-online-indicator.md`)
   - Otherwise: a descriptive kebab-case slug

8. **Hand off:** announce the file path and tell the user *"Plan saved to `docs/plans/<slug>.md`. Read it over and let me know what to edit."* Do not summarize the plan in chat — the user is about to read it.

## Plan Template

````markdown
# <Title>

**Ticket:** <JIRA URL or ID, if applicable>

## Background

2-4 sentences. What is this, why are we doing it, what problem does it solve? Add context the ticket doesn't already have — do not restate it.

## Goal

1-3 sentences. What does success look like, concretely? What will an observer see that is different after this ships?

## Approach

3-8 sentences. High-level strategy. Briefly note one or two alternatives considered and why this one wins. No code.

## Phases

Structure the work as a small number of large phases. Each phase builds on the previous one, but each phase is a self-contained chunk the engineer can implement, test, and review on its own before moving to the next. A phase is not a single commit — it may take several — but every phase ends with the codebase in a working, mergeable state.

Two or three phases is typical. Do not force more. If a phase has only one step, fold it into an adjacent phase.

### Phase 1: <Phase name>

**Goal:** one sentence on what this phase delivers.

1. **<Step name>** — what changes and why.
   - File: [path/to/File.kt](https://github.com/dimagi/commcare-android/blob/master/path/to/File.kt#L42-L58)
   - Specific change, e.g., "Add `isOnline` field to `ConnectivityViewModel` and emit on connectivity changes."

2. **<Next step>** — ...

### Phase 2: <Phase name>

**Goal:** one sentence.

1. ...

## Testing

- Unit tests: which class, what to verify.
- Instrumentation tests: which flow, what to verify.
- Manual QA: concrete steps a tester can follow.

Omit any bullet that doesn't apply.

## Out of Scope

- Explicit non-goals, to prevent scope creep.

## Open Questions

- Things the engineer should resolve before starting. Omit this section entirely if there are none.
````

## Style Rules

- **No fluff.** Cut anything that doesn't help the engineer act.
- **Concrete over abstract.** "Add `isOnline` field to `ConnectivityViewModel`" beats "Update the connectivity layer."
- **Imperative voice in steps.** "Add X." not "We should add X." not "X will be added."
- **Links point to master only.** Never to a branch, PR ref, or commit SHA. If the code isn't on master yet, describe it in prose.
- **Code blocks only when they clarify a tricky API shape or data structure.** Plans describe intent, not implementation.
- **Skip empty sections.** If there are no open questions, drop the section.
- **Match plan size to work size.** A single-phase, two-step plan is fine.
- **Phases must be sequential and independently shippable.** Each phase ends in a working, mergeable state. A later phase may depend on an earlier phase landing, but the engineer should never need to hold two phases open at once.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Linking to a branch, PR, or commit SHA | Always link to master. If the code isn't on master yet, describe it in prose. |
| Restating the ticket as Background | Background should add context the ticket doesn't have. |
| Vague steps like "update the UI" | Name the file, the class, and the change. |
| Saving without verifying links | Run `git cat-file -e master:<path>` for every link before writing the file. |
| Asking 10 clarifying questions | Cap at 4. Ask only what you can't confidently infer. |
| Drafting AI-friendly scaffolding (step IDs, machine-readable headers) | Audience is a human junior engineer. Write accordingly. |
| Summarizing the plan in chat after saving | Just announce the path. The user is about to read the plan. |
| One-step phases, or six phases for a small change | A phase is a chunk of work, not a single change. Fold single-step phases together; collapse over-decomposed ones. |
| Phases that can't merge independently (e.g., phase 1 leaves the build broken) | Re-cut the phase boundary so phase 1 ends in a working, mergeable state. |
