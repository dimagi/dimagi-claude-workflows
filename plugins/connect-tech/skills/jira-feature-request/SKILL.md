---
name: jira-feature-request
description: Create Jira feature request tickets (Stories) in the CI project using Dimagi's form 134 format. Use this skill whenever a user wants to submit, log, or create a feature request, new feature idea, product enhancement, or user story in Jira. Triggers on phrases like "create a feature request", "submit a feature idea", "log a feature", "I want to request a feature", "add this to the backlog", "create a story", or any time someone describes something they want the product to do that it doesn't do yet. Always use this skill when feature requests or product enhancements need to be tracked, even if the user doesn't say "Jira" or "ticket" explicitly.
---

# Jira Feature Request Skill (Form 134)

## Goal
Guide the user through filing a well-structured Jira Story in the CI project, matching Dimagi's form 134 format. Collect all relevant fields upfront, show a formatted preview, and only create the ticket after explicit confirmation.

---

## Step 1: Collect Information Upfront

Ask the user for everything in a single message:

---
**Let's file a feature request! Please provide the following:**

**Required:**
- **Summary** – A short, clear title (e.g., "Enable image rendering in CommCare Connect chatbot")
- **User Story** – Describe who needs this and why:
  *"As a [type of user], I want [goal] so that [benefit]."*
- **Priority** – P1 (urgent/blocker), P2 (high), P3 (medium), P4 (low, default), P5 (trivial)

**Optional (leave blank to skip):**
- **Current Behavior** – What happens today?
- **Expected Behavior** – What should happen instead?
- **Impact** – Who is affected and how? (e.g., number of users, programs impacted)
- **CCC Program** – Which program is this for? Options: Child Health Campaign, Early Childhood Development, Group Program Management Plus, Kangaroo Mother Care, Mother Baby Wellness, Readers Distribution, Rooftop Sampling, WellMe, Multiple Programs, Other
- **CCC Product Area** – Which area? Options: Data & Analytics, LLO Administration, Messaging, Notifications, Payments, PersonalID, Verification, Work History, Other
- **CCC User Impact** – Free text description of user impact
- **Components** – Relevant components: Web, Mobile, OCS, App Configuration, Blue Pod Web UI, New Feature Release, other
- **Additional context** – Links, screenshots, related tickets, POC work, etc.
---

## Step 2: Show a Formatted Preview

Display a clean preview before creating:
```
📋 FEATURE REQUEST PREVIEW (Form 134)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type:        Story
Project:     CI
Priority:    [P1–P5]
Summary:     [summary]

User Story:
As a [user type], I want [goal] so that [benefit].

Current Behavior:   [value or —]
Expected Behavior:  [value or —]
Impact:             [value or —]

── CCC Fields ───────────────────────────
CCC Program:        [value or —]
CCC Product Area:   [value or —]
CCC User Impact:    [value or —]

── Other ────────────────────────────────
Components:         [value or —]
Additional Context: [value or —]
Labels:             form, form-134 (auto-applied)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then ask: **"Does this look good? Reply 'yes' to submit, or let me know what to change."**

---

## Step 3: Look Up the Jira Project

1. Call `getAccessibleAtlassianResources` to get the cloudId.
2. Use project key **`CI`** and cloudId `dbff467f-3c3f-4ced-a2ba-a29e1941edd6` — no need to ask.

---

## Step 4: Create the Ticket

Use `createJiraIssue` with:
- `issueTypeName`: `"Story"`
- `projectKey`: `"CI"`
- `cloudId`: `"dbff467f-3c3f-4ced-a2ba-a29e1941edd6"`
- `summary`: the summary
- `contentFormat`: `"markdown"`
- `description`: structured markdown (see template below)
- `additional_fields`:
  - `"priority"`: `{ "name": "P4" }` (or P1–P5 as provided — pass the name directly, e.g. `{ "name": "P3" }`)
  - `"labels"`: `["form", "form-134"]` — always include both
  - `"components"`: `[{ "name": "<component>" }]` — if provided
  - `"customfield_10764"`: `{ "value": "<CCC Program value>" }` — if provided
  - `"customfield_10766"`: `{ "value": "<CCC Product Area value>" }` — if provided
  - `"customfield_10765"`: `"<CCC user impact text>"` — if provided

### Description Template (Markdown)
```markdown
## User Story
As a [user type], I want [goal] so that [benefit].

## Current Behavior
[value, or omit section if not provided]

## Expected Behavior
[value, or omit section if not provided]

## Impact
[value, or omit section if not provided]

---
**Product Area / Feature:** [CCC Product Area or N/A]
**Program Impacted:** [CCC Program or N/A]
**CCC User Impact:** [value or N/A]

## Additional Context
[value, or omit section if not provided]
```

---

## Step 5: Confirm and Share the Link

After creating, respond with:
- A success message
- The ticket key (e.g., `CI-123`)
- A direct link: `https://dimagi.atlassian.net/browse/CI-123`

---

## Tips & Edge Cases

- If the user gives a vague request, ask a clarifying question to understand the specific need before writing the story.
- If no Jira connection is available, show the ticket as formatted text the user can copy.
- Never create the ticket without explicit user confirmation ("yes", "create it", "looks good", etc.).
- The `form` and `form-134` labels must always be included — they're required to match form 134 submissions.
- Priority defaults to P4 if not specified.
- If the user mentions which CCC program or area is affected, always populate the CCC custom fields.
