---
name: jira-bug-ticket
description: Create Jira bug tickets with all required and optional fields. Use this skill whenever a user wants to file, log, report, or create a bug, defect, or issue in Jira. Triggers on phrases like "create a bug ticket", "log a bug", "file a Jira issue", "report a bug", "open a ticket for this bug", or any time someone describes a software problem and wants it tracked. Always use this skill when bug reporting or Jira ticket creation is involved, even if the user doesn't say "skill" or "Jira" explicitly.
---

# Jira Bug Ticket Skill

## Goal
Guide the user through filing a complete, well-structured Jira bug ticket. Collect all required and optional fields upfront in one shot, show a formatted preview, and only create the ticket after explicit user confirmation.

---

## Step 1: Collect All Information Upfront

Ask the user for everything in a single message. Use this template:

---
**Let's file a bug ticket! Please provide the following:**

**Required:**
- **Summary** – A short, clear title for the bug (e.g., "Login button unresponsive on mobile Safari")
- **Description** – A full description of the bug: what happened, what was expected, and steps to reproduce if known
- **Priority** – P1 (Critical/outage), P2 (High/major impact), P3 (Medium/moderate impact), P4 (Low/minor issue), or P5 (Trivial/cosmetic)

**Optional (leave blank to skip):**
- **Users/programs impacted** – How many users or systems are affected?
- **Product area / feature** – Which area of the product is this in? (e.g., "Checkout flow", "Authentication")
- **Which program is impacted** – Specific program or service name (e.g., "iOS app", "Payment service")
- **Components** – Relevant technical components (e.g., "Frontend", "API", "Database")
- **Troubleshooting steps taken** – What has already been tried or ruled out?
- **Attachments** – Any screenshots, logs, or files? (Share links or describe what you'd attach)
---

## Step 2: Show a Formatted Preview

Once the user provides info, display a clean preview of the ticket before creating it:

```
📋 JIRA BUG TICKET PREVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type:        Bug
Summary:     [summary]
Priority:    [P0/P1/P2/P3]

Description:
[description]

── Optional Fields ──────────────────────
Users/Programs Impacted:  [value or —]
Product Area / Feature:   [value or —]
Program Impacted:         [value or —]
Components:               [value or —]
Troubleshooting Taken:    [value or —]
Attachments:              [value or —]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then ask: **"Does this look correct? Reply 'yes' to create the ticket, or let me know what to change."**

---

## Step 3: Look Up the Jira Project

Before creating, you need the Jira cloudId and the right project. Use the Atlassian tools:

1. Call `getAccessibleAtlassianResources` to get the cloudId.
2. Default to project key **`CI`** — use it without asking unless the user has explicitly specified a different project or says they want to choose.

---

## Step 4: Create the Ticket

Use `createJiraIssue` with:
- `issueTypeName`: `"Bug"`
- `summary`: the summary
- `contentFormat`: `"markdown"` — always set this so the description renders correctly
- `description`: Build a well-structured description in Markdown that includes:
  - The user's description
  - A **Troubleshooting Steps Taken** section (if provided)
  - A **Users/Programs Impacted** section (if provided)
  - An **Attachments** section (if provided)

### Handling `additional_fields` — Known Pitfalls

The `additional_fields` parameter passes fields directly to the Jira API. Several fields commonly fail:

- **`priority`**: The priority names must match the project's configured priorities EXACTLY. The names vary by project — "Medium", "Highest", etc. may not exist. **Do NOT include priority in the first attempt.** If the user specified a priority, try adding it in a follow-up `editJiraIssue` call, or first call `getJiraIssueTypeMetaWithFields` to discover the valid priority names for the project.
- **`components`**: Components must already exist in the project. Jira returns a permissions error ("You do not have permission to create new components") if you reference a component name that doesn't exist — it tries to create it rather than failing gracefully. **Do NOT include components unless you have verified they exist** via `getJiraIssueTypeMetaWithFields`.
- **`customfield_*`**: Custom field IDs vary by Jira instance. Discover them via `getJiraIssueTypeMetaWithFields` before using.

**Recommended approach:** Create the ticket with only `summary`, `description`, `issueTypeName`, and `contentFormat` first. If that succeeds, use `editJiraIssue` to add priority, components, and other optional fields in a second call. This avoids a single bad field blocking ticket creation entirely.

### Description Template (Markdown)

```markdown
## Bug Description
[user's description]

## Steps to Reproduce
[extract from description if present, otherwise omit]

## Expected vs Actual Behavior
[extract from description if present, otherwise omit]

---
**Product Area / Feature:** [value or N/A]
**Program Impacted:** [value or N/A]
**Users / Programs Impacted:** [value or N/A]

## Troubleshooting Steps Taken
[value or N/A]

## Attachments
[value or N/A]
```

---

## Step 5: Confirm and Share the Link

After creating, respond with:
- A success message
- The ticket key (e.g., `PROJ-123`)
- A direct link to the ticket if available in the API response

---

## Tips & Edge Cases

- If the user provides very little description, gently nudge them: "Could you add steps to reproduce or what you expected to happen? This helps the engineering team triage faster."
- If priority is unclear, suggest one based on the described impact and ask the user to confirm.
- If no Jira connection is available, explain that the Atlassian integration needs to be connected and offer to show the ticket as formatted text they can copy.
- Never create the ticket without explicit user confirmation ("yes", "create it", "looks good", etc.).
