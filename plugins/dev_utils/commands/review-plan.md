---
description: Interactively review a plan across architecture, code quality, tests, and performance before any code changes.
---

Review this plan thoroughly before making any code changes. For every issue or recommendation, explain the concrete tradeoffs, give me an opinionated recommendation, and ask for my input before assuming a direction.

My engineering preferences (use these to guide your recommendations):

* DRY is good, but don't over-abstract — duplication is preferable to the wrong abstraction. Flag obvious repetition, but don't force shared code where the use cases might diverge.
* Well-tested code is non-negotiable. I'd rather have too many tests than too few — but tests must be fast. We use pytest. Prefer strategies that avoid hitting the database unnecessarily: separate business logic from DB access so it can be tested with plain unit tests, use factory patterns (factory_boy) for tests that do need the DB, and use mocking where separation isn't practical. Be thoughtful about when a test actually needs `@pytest.mark.django_db`.
* I want code that's "engineered enough" — not under-engineered (fragile, hacky) and not over-engineered (premature abstraction, unnecessary complexity).
* I err on the side of handling more edge cases, not fewer; thoughtfulness > speed.
* Bias toward explicit over clever.

## BEFORE YOU START

Ask if I want one of two modes:

1. **Deep review**: Full, thorough review of all sections. Surface every issue worth discussing — including minor code quality concerns, test gaps, and performance opportunities — not just the big ones.
2. **Major issues only**: Same thorough read-through, but only surface issues that are significant: security vulnerabilities, fundamental design or architecture flaws, critical missing tests, and patterns that will cause serious problems down the line. Skip minor DRY violations, style nits, nice-to-have test improvements, and micro-optimizations.

Use `AskUserQuestion` for this choice before proceeding to any review section.

## 0. Decision Audit (always do this first)

Before evaluating any specific section, read the entire plan and identify the key architectural decisions that are **presented as foregone conclusions** — choices the plan makes without comparing alternatives or explaining the rationale.

These are the decisions most likely to be wrong or suboptimal, because they weren't surfaced for scrutiny at planning time. The goal is to catch them now, before they get built in.

Look specifically for:

* **Transport and protocol choices** — how data is passed between components (HTTP headers, query params, request body, session/cookie, URL path). Plans often pick one without justifying why.
* **Data model choices** — FK vs M2M vs denormalization, nullable vs required fields, UUID vs integer PKs, choice of related_name.
* **Security enforcement pattern** — how auth/permission is checked (middleware vs per-view decorator vs utility function, header-based vs session-based, centralized vs distributed).
* **Integration pattern** — how new components hook into existing ones (monkey-patch, mixin, decorator, utility function, signal, middleware).
* **Naming and structural choices** — app renames, module reorganization, naming conventions that shape everything downstream.

For each decision found:

* State the decision concretely (e.g. "The plan passes workspace context via a custom `X-Custom-Workspace` HTTP header on every request").
* Present 2–3 alternatives that would also be reasonable.
* For each option, give full tradeoff analysis: implementation effort, risk, caching/debuggability implications, and maintenance burden.
* Give your opinionated recommendation and why, mapped to my engineering preferences above.
* Then use `AskUserQuestion` to ask whether I want to proceed with the plan's choice or revisit it.

In **Major issues only** mode: surface only decisions with significant security, design, or architectural implications.
In **Deep review** mode: surface up to 4 decisions.

After addressing all Decision Audit items, use `AskUserQuestion` to confirm I'm ready to move on to the Architecture review.

## 1. Architecture review

Evaluate:

* Overall system design and component boundaries.
* Dependency graph and coupling concerns.
* Data flow patterns and potential bottlenecks.
* Scaling characteristics and single points of failure.
* Security architecture (auth, data access, API boundaries).

Also surface any decisions that weren't caught in the Decision Audit but emerge from deeper analysis of how the components interact.

## 2. Code quality review

Evaluate:

* Code organization and module structure.
* DRY violations — flag clear repetition, but note where duplication might be intentional or where abstracting would couple things that shouldn't be coupled.
* Error handling patterns and missing edge cases (call these out explicitly).
* Technical debt hotspots.
* Areas that are over-engineered or under-engineered relative to my preferences.

## 3. Test review

Evaluate:

* Test coverage gaps (unit, integration, e2e).
* Test quality and assertion strength.
* Missing edge case coverage — be thorough.
* Untested failure modes and error paths.
* Test performance: flag tests that hit the DB unnecessarily or use slow fixtures. Call out opportunities to separate logic from DB access so it can be tested as plain unit tests without `@pytest.mark.django_db`. Where separation isn't feasible, suggest mocks or factories to keep the suite fast.

## 4. Performance review

Evaluate:

* N+1 queries and database access patterns.
* Memory-usage concerns.
* Caching opportunities.
* Slow or high-complexity code paths.

## For each issue you find

For every specific issue (bug, smell, design concern, or risk):

* Describe the problem concretely, with file and line references.
* Present 2–3 options, including "do nothing" where that's reasonable.
* For each option, specify: implementation effort, risk, impact on other code, and maintenance burden.
* Give me your recommended option and why, mapped to my preferences above.
* Then use `AskUserQuestion` to ask whether I agree or want to choose a different direction before proceeding.

## Workflow and interaction

* Do not assume my priorities on timeline or scale.
* After each section, use `AskUserQuestion` to ask for my feedback before moving on.

## Formatting rules

* NUMBER issues (Issue 1, Issue 2, …).
* Give LETTERS for options (A, B, C, …).
* When using `AskUserQuestion`, label each option clearly with the issue NUMBER and option LETTER so I don't get confused.
* Make the recommended option always the 1st option.
* Output the explanation and pros/cons of each section's questions AND your opinionated recommendation and why, then use `AskUserQuestion`.
