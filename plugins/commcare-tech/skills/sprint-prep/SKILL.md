---
name: sprint-prep
description: Prepare for the next sprint. Reviews your board and drafts your sprint plan message.
disable-model-invocation: true
argument-hint: <your name or "help">
---

# Sprint Prep

Review the engineer's current and next sprint boards, flag anything that needs attention, and draft a sprint plan message for the Slack channel defined in Constants.

## Input

`$ARGUMENTS` — The engineer's name (for Jira lookup) or just run with no arguments to self-assign. Examples:
- `/sprint-prep` (uses current authenticated user)
- `/sprint-prep Graham`
- `/sprint-prep help` (shows what this command does)

## Constants

- **Project:** `SAAS`
- **Cloud ID:** `dbff467f-3c3f-4ced-a2ba-a29e1941edd6`
- **Sprint field:** `customfield_10010`
- **Board ID:** `97`
- **Jira base URL:** `https://dimagi.atlassian.net/browse/`
- **Slack channel:** `#commcare-tech-sprint-grooming-and-planning`
- **Slack channel ID:** `C08FEMC126L`

## Team Context

The CommCare Tech team runs two-week sprints named with sequential letters (e.g., Sprint U, Sprint V, Sprint W). Each sprint cycle has two parallel sprints in the SAAS project:
- A **Platform** sprint (infrastructure, devops, migrations, Celery, Kafka, ES, CouchDB, Postgres, AWS, Ansible, Docker, Redis, monitoring, CI/CD, dependencies, security patching)
- A **Product** sprint (features, UI/UX, bug fixes, app builder, reports, exports, case management, forms, mobile, web apps, formplayer, formbuilder, messaging, feature flags, data exports)

Sprint names follow the pattern: `CommCare [Product|Platform] [Letter] [(dates)]`

## Jira Status Definitions

| Status | Category | Meaning |
|---|---|---|
| Prioritized | To Do | Ready to be worked on but not started |
| In Progress | In Progress | Actively being worked on |
| In Review | In Progress | PR is up, awaiting review or QA |
| Accepted | Done | Work is complete and merged |
| Deployed | Done | Live in production |
| Won't Do | Done | Intentionally not doing |

## Steps

### 1. Identify the engineer

- If `$ARGUMENTS` is empty or not provided, use `atlassianUserInfo` to get the current authenticated user's account ID and display name.
- If `$ARGUMENTS` is a name, use `lookupJiraAccountId` with the cloud ID to resolve their account ID.
- If `$ARGUMENTS` is "help", explain what this command does and exit.

Store the resolved `accountId` and `displayName` for use in all subsequent queries.

### 2. Discover active sprints

Search for active sprints using JQL:

```
project = SAAS AND sprint in openSprints() ORDER BY created DESC
```

Fetch at least 5 results. Extract sprint data from `customfield_10010` on each issue. Identify:
- The **current Platform sprint** (name contains "Platform")
- The **current Product sprint** (name contains "Product")

Also search for future sprints by looking for sprints in the next letter. Use JQL:

```
project = SAAS AND sprint in futureSprints() ORDER BY created DESC
```

Fetch at least 5 results. Identify:
- The **next Platform sprint**
- The **next Product sprint**

If future sprints aren't created yet, note this and skip next-sprint analysis.

### 3. Audit current sprint tickets

For each active sprint the engineer has tickets in, query:

```
project = SAAS AND assignee = "<accountId>" AND sprint = <sprint_id> ORDER BY status ASC
```

Run separately for Platform and Product sprints.

For each ticket, capture the ticket key, summary, and current status. Do not display the raw ticket list to the engineer — use this data internally to prepare for steps 4 and 7.

### 4. Review next sprint tickets

For each next sprint (Platform and Product), query:

```
project = SAAS AND assignee = "<accountId>" AND sprint = <next_sprint_id> ORDER BY status ASC
```

Summarize what's already lined up. If the next sprint is empty for this engineer, flag it:

> ⚠️ No tickets in the next [Platform|Product] sprint. You may need to pull from the backlog or create tickets for planned work.

### 7. Ask for highlights and confirm carryovers

Ask the following three questions one at a time, waiting for the engineer's response after each before proceeding to the next.

**Question 1 — Highlights:** Group the completed and in-review tickets into thematic categories (up to 5, but could be just 1 if the work was focused). Include tickets with status Accepted, Deployed, or In Review — if a PR is up, the engineering work is done and it counts as a highlight. Present those categories — not individual tickets — and ask:

> **Here's what you completed this sprint. Which of these do you want to highlight?**
>
> • Category A — brief description
> • Category B — brief description

Wait for response. When the engineer selects a category, note the individual tickets in that category for use in the draft.

**Question 2 — Carryovers:** Show the tickets still in progress (In Progress or Prioritized/not started) and ask. In Review tickets are already covered as highlights above — only include them here if they've been in review for an unusually long time and might genuinely be stuck:

> **Are any of these tickets at risk of rolling over?**
>
> • SAAS-AAAAA (In Progress): summary
> • SAAS-BBBBB (Prioritized): summary

Wait for response.

**Question 3 — Next sprint highlights:** If the engineer has no tickets in the next sprint, warn them but continue:

> ⚠️ No tickets assigned in the next sprint yet. This might be intentional, but wanted to flag it.

If there are tickets, group them into thematic categories (up to 5, could be just 1) and ask:

> **Here's what's lined up for next sprint. Anything you want to call out?**
>
> • Category A — brief description
> • Category B — brief description

Wait for response. When the engineer selects a category, note it for use in the draft summary sentence.

**Question 4 — Blockers:** Ask:

> **Anything you're stuck on or could use help with?**

Wait for response. If they mention a blocker, include it as a note at the top of the draft message.

After all four responses are collected, proceed to draft the message.

### 8. Draft the sprint plan message

Using the engineer's selected highlights and the data collected, draft a three-section message.

**Format:**

```
**Highlights from the last sprint**
Summary sentence here.
• [SAAS-XXXXX](https://dimagi.atlassian.net/browse/SAAS-XXXXX): One-line description of what was accomplished
• [SAAS-YYYYY](https://dimagi.atlassian.net/browse/SAAS-YYYYY): One-line description

**What might carry over**
Summary sentence here.
• [SAAS-ZZZZZ](https://dimagi.atlassian.net/browse/SAAS-ZZZZZ): Brief note on status / why it's carrying over

**What I plan to work on in the next sprint**
Summary sentence here.
• [SAAS-AAAAA](https://dimagi.atlassian.net/browse/SAAS-AAAAA): Short description
• [SAAS-BBBBB](https://dimagi.atlassian.net/browse/SAAS-BBBBB): Short description

**Challenges**
Brief description of what the engineer is working through or could use help with.
```

**Important:** When sending to Slack via the API, use `\n\n` (double newline) between each section. Slack collapses single newlines, so you need two to get visible spacing between sections.

**Rules for the draft:**
- **Highlights:** Use only what the engineer selected — do not decide on their behalf. Write a 1-sentence summary of the highlighted work based on the ticket content and what the engineer said when selecting the category. Place this before the ticket list. For individual ticket lines, use the ticket title as-is.
- **Carryovers:** Include tickets the engineer confirmed might roll over. Write a 1-sentence summary before the ticket list explaining why they're carrying over, based on what the engineer said. For individual ticket lines, use the ticket title as-is.
- **Next sprint:** Include ALL tickets from the next sprint. Write a 1-sentence summary before the ticket list based on the categories the engineer highlighted and the ticket content.
- **Challenges:** Include what the engineer answered for this above. If the engineer said nothing is challenging them, write "None" as the content.
- If the engineer mentioned any context about PTO, travel, or reduced availability during the conversation, note it at the top (e.g., "Offline for a couple of days next week").
- Keep descriptions short — one line per ticket. Match the casual style used in the channel (not formal).
- Use Slack `**bold**` syntax (double asterisks) for section headers. Single `*` renders as italic in Slack's API.

### 9. Present everything

Output the full report in this order:

**1. Ask for highlights** (step 7 above) — wait for response.

**5. Draft Sprint Plan Message**

The message should be split into two parts for Slack:

**Part 1 — Channel message (TLDR):** A single sentence prefixed with `**Sprint update:** ` (bold, using double asterisks), summarizing what was accomplished and what's coming next. Write it conversationally — avoid stiff phrasing like "Next sprint:" and instead weave the upcoming work naturally into the sentence. This is posted directly in the channel.

**Part 2 — Thread reply (full update):** The detailed sprint plan, posted as a reply in the thread of the TLDR message.

```
## TLDR (posted in channel)

One-sentence summary of highlights and what's next.

## Full Update (posted as thread reply)

**Highlights from the last sprint**
Summary sentence here.
• [SAAS-XXXXX](...): What was accomplished

**What might carry over**
Summary sentence here.
• [SAAS-YYYYY](...): Still in progress — brief status

**What I plan to work on in the next sprint**
Summary sentence here.
• [SAAS-ZZZZZ](...): Planned work

**Challenges**
Brief description of what the engineer is working through or could use help with.
```

**6. Ask for confirmation**

> Anything you want to add, remove, or change before you post this?

## Important Safety Rules

- **NEVER move tickets between sprints.** Only suggest moves.
- **NEVER change ticket statuses.** Only flag discrepancies.
- **Post to Slack after confirmation.** After the engineer approves the draft, post the TLDR and thread reply to the Slack channel defined in Constants unless the engineer specifies a different channel.
- **NEVER create or delete tickets.** This command is read-only against Jira.
- If the engineer wants to make changes to tickets based on the audit, suggest they use `/jira-ticket` or do it manually.

## Edge Cases

- **Engineer is on only one team (Platform or Product):** Only query and report on the relevant sprint. Don't show empty sections for the other.
- **No active sprints found:** Tell the engineer sprints may not be created yet. Suggest they check the [backlog](https://dimagi.atlassian.net/jira/software/c/projects/SAAS/boards/97/backlog).
- **No tickets in current OR next sprint:** The engineer may be new, between projects, or planning hasn't happened. Don't assume something is wrong — just report what you see.
- **Engineer has tickets in sprints beyond the next one:** Ignore them. Only report on current and immediately next sprints.
- **Multiple people with the same first name in Jira lookup:** Show matches and ask the engineer to confirm.
