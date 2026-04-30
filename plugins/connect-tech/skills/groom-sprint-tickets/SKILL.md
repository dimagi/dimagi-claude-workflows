---
name: groom-sprint-tickets
description: "Slash command: /groom-sprint-tickets <sprint name>. Do NOT auto-invoke. Only runs when explicitly called via slash command."
user_invocable: true
---

# Groom Sprint Tickets

## Overview

Identifies tickets in a Jira sprint that are missing story points, assesses whether their requirements are clear enough for estimation by examining the ticket details and the codebase, then either posts clarifying questions as a comment or suggests an updated ticket description.

## Usage

```
/groom-sprint-tickets Web Team - Sprint 89
```

The sprint name is passed as the argument. If no argument is provided, ask the user for the sprint name before proceeding.

## Workflow

```dot
digraph groom {
    rankdir=TB;
    node [shape=box];

    input [label="/groom-sprint-tickets <sprint name>" shape=doublecircle];
    fetch [label="Fetch sprint tickets with\ncustomfield_10017 (story points)"];
    filter [label="Identify tickets where\nstory points = null"];
    none [label="Report: all tickets have\nstory points" shape=doublecircle];
    pick [label="For each unpointed ticket"];
    details [label="Fetch full ticket details\n+ comments"];
    has_response [label="Has unanswered\nclarifying questions?" shape=diamond];
    skip [label="Skip - awaiting response"];
    explore [label="Explore codebase for\nrelated code"];
    assess [label="Requirements clear\nenough to estimate?" shape=diamond];
    questions [label="Post clarifying questions\nas Jira comment"];
    update [label="Suggest updated description\nto user for approval"];
    test_docs [label="Identify testing &\ndocumentation needs"];
    links [label="Add issue links\n(blocked by, relates to)"];
    next [label="Next ticket" shape=doublecircle];

    input -> fetch;
    fetch -> filter;
    filter -> none [label="none found"];
    filter -> pick [label="found"];
    pick -> details;
    details -> has_response;
    has_response -> skip [label="yes, still waiting"];
    has_response -> explore [label="no"];
    explore -> assess;
    assess -> questions [label="no - unclear"];
    assess -> update [label="yes - clear"];
    update -> test_docs;
    test_docs -> links [label="if dependencies found"];
    questions -> next;
    links -> next;
    skip -> next;
}
```

## Process

### Step 1: Retrieve Sprint Tickets

Query Jira for all tickets in the sprint, including story points:

```
JQL: sprint = "<sprint name>"
Fields: summary, status, issuetype, assignee, customfield_10017
```

**Important:** Story points are stored in `customfield_10017` in the Dimagi Jira instance. This field is NOT listed in field metadata — it only appears when requesting `*all` fields or by explicit name.

Present a summary table of all tickets showing which have/lack story points.

### Step 2: For Each Unpointed Ticket

Fetch the full ticket including comments:

```
Fields: summary, description, parent, issuelinks, comment, components, customfield_10008 (epic link)
```

**Check comments first.** If you previously posted clarifying questions and there is no response yet, skip the ticket and note it as "awaiting response."

If there IS a response to prior questions, proceed to assessment incorporating the answers.

### Step 3: Explore the Codebase

Use the codebase to understand the scope of work described in the ticket:

- Search for views, templates, models, URLs, and tasks mentioned or implied by the ticket
- Identify what exists today vs. what needs to change
- Note any dependencies on other tickets or shared code
- Check for existing test coverage of the affected code (unit tests, integration tests)
- Check for existing documentation (README sections, docstrings, user-facing docs) that would need updating

This context is critical for assessing whether requirements are specific enough and for identifying testing and documentation needs in Step 5.

### Step 4: Assess Requirement Clarity

Requirements are **clear enough** if:
- Each acceptance criterion maps to identifiable code changes
- The scope boundaries are unambiguous (what's in vs. out)
- Dependencies on other tickets are explicit
- No key decisions are left undefined (e.g., "remove or change" without specifying which)

Requirements **need clarification** if:
- The ticket title contradicts the acceptance criteria (e.g., "reassess" vs "remove")
- Scope is ambiguous (UI-only vs full backend cleanup)
- Dependencies exist but aren't called out
- Key implementation decisions are deferred without clear ownership

Regardless of clarity, also evaluate **testing and documentation needs** (used in Step 5):
- **Unit tests needed** if the ticket changes logic, adds endpoints, modifies models, or alters business rules — especially if the affected code already has test coverage that must be updated
- **Unit tests NOT needed** for pure copy changes, configuration tweaks, or UI-only styling adjustments with no logic
- **Documentation updates needed** if the ticket changes user-facing behavior, API contracts, configuration options, or onboarding flows — especially if existing docs cover the affected area
- **Documentation NOT needed** for internal refactors, bug fixes that restore expected behavior, or changes with no user-visible impact

### Step 5: Take Action

**If requirements are unclear → Post clarifying questions:**
- Post a numbered list of specific questions as a Jira comment
- Each question should reference what's ambiguous and offer concrete options where possible
- Keep questions scoped to what's needed for estimation, not implementation details
- If you identified testing or documentation gaps during assessment, include questions about them (e.g., "Should this include unit tests for the new validation logic?" or "The API docs currently describe the old behavior — should updating them be part of this ticket or a separate one?")

**If requirements are clear → Suggest updated description:**
- Draft an updated description with detailed acceptance criteria
- Place updated scope above the original description, separated by a horizontal rule
- Preserve the original description below for reference
- **Include testing and documentation requirements** in the acceptance criteria (see Step 5a below)
- Present the draft to the user for approval before pushing
- After approval, update the description AND add issue links (e.g., "is blocked by") for any dependencies identified

### Step 5a: Add Testing & Documentation Requirements

When suggesting an updated description (requirements are clear), assess and include the following based on what you found in Step 3 and Step 4:

**Unit Testing:**
- If the affected code has existing tests, add an acceptance criterion: "Update existing unit tests in `<test file>` to cover the changed behavior"
- If the change introduces new logic without existing test coverage, add: "Add unit tests for `<specific component/function>`"
- Specify what to test — don't just say "add tests." Reference the specific behavior, edge cases, or validation rules that need coverage
- If no tests are needed, do not add a testing criterion — omitting it is fine

**Documentation:**
- If user-facing behavior changes and docs exist, add an acceptance criterion: "Update `<doc location>` to reflect the new behavior"
- If a new feature or API endpoint is added, add: "Document `<feature/endpoint>` in `<appropriate location>`"
- If the change affects configuration, onboarding, or admin workflows, note which docs need updating
- If no documentation updates are needed, do not add a documentation criterion

**Format in the acceptance criteria:**
```
## Acceptance Criteria
- [ ] <functional criterion 1>
- [ ] <functional criterion 2>
- [ ] Update unit tests in `tests/test_payments.py` to cover new validation rules
- [ ] Update API documentation to reflect the new `status` field on the response
```

Testing and documentation criteria go at the end of the acceptance criteria list, after the functional requirements.

### Step 6: Report

After processing all unpointed tickets, summarize:
- How many tickets were assessed
- How many had questions posted (awaiting clarification)
- How many had descriptions updated (ready for estimation)
- How many were skipped (already awaiting prior responses)

## Jira Field Reference

| Field | Key | Notes |
|-------|-----|-------|
| Story Points | `customfield_10017` | Not in metadata; must request explicitly |
| Sprint | `customfield_10010` | Array of sprint objects |
| Epic Link | `customfield_10008` | Parent epic key |
| All fields | `["*all"]` | Use when discovering custom fields |

## Common Mistakes

- **Using `customfield_10016` for story points** — Wrong field. Use `customfield_10017`.
- **Updating ticket without user approval** — Always present description changes for review first.
- **Posting questions without codebase context** — Questions grounded in code are more specific and actionable.
- **Ignoring existing comments** — Always check if clarifying questions were already posted and whether responses exist.
- **Putting dependency info only in description** — Use Jira issue links ("is blocked by") for dependencies, not just description text.
- **Adding generic "add tests" criteria** — Be specific: name the test file, the function/behavior to test, and what edge cases matter. "Add unit tests" alone is not actionable.
- **Adding test/doc criteria to every ticket** — Only add them when the change genuinely warrants it. Pure config changes, copy edits, and styling tweaks don't need test or doc acceptance criteria.
