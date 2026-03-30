# Tickets and Epics Reference

Use the constants from SKILL.md for all tool calls (Cloud ID, Project
Key, Sprint Custom Field).

## Fetching & Summarizing a Ticket

Use `mcp__atlassian__getJiraIssue`:
- `cloudId`: Cloud ID from constants
- `issueIdOrKey`: the parsed ticket key
- `responseContentFormat`: `"markdown"`

Present: summary, status, assignee, description, linked issues, parent
epic.

## Fetching Comments

Comments are not returned by default. To get them:
- `fields`: `["comment", "summary"]`
- `responseContentFormat`: `"markdown"`

Present each comment with author, timestamp, and body.

## Adding Comments

Use `mcp__atlassian__addCommentToJiraIssue`:
- `contentFormat`: `"markdown"`

**Always confirm the comment content with the user before posting.**

## Fetching & Summarizing an Epic

Fetch the epic itself the same way as a ticket, then query for children:

```
project = USH AND parent = <epic-key> ORDER BY status ASC, created ASC
```

Use `mcp__atlassian__searchJiraIssuesUsingJql`. Present children grouped
by status, showing key, summary, status, and assignee for each.

## Sprint Queries

USS runs two parallel sprints per cycle — **Product** and **Platform**
— named like `CommCare [Product|Platform] [Letter] [(dates)]`. Sprint
data is in `customfield_10010`.

**Discover active sprints:**

```
project = USH AND sprint in openSprints()
```

Fetch several results and extract sprint names/IDs from
`customfield_10010`. Identify Product vs Platform by name.

**Discover future sprints:**

```
project = USH AND sprint in futureSprints()
```

**List tickets in a sprint:**

Default to the current sprint when the user asks about "my tickets",
"the sprint", etc.

```
project = USH AND sprint = <sprint_id> ORDER BY status ASC
```

Add `AND assignee = currentUser()` if the user asks about their own
tickets.

Group results by status: Prioritized, In Progress, In Review, QA,
Fix on Deploy, Done.

## Transitioning Status

Use `mcp__atlassian__getTransitionsForJiraIssue` to discover available
transitions, then `mcp__atlassian__transitionJiraIssue` to apply.

**Always confirm with the user before transitioning.**
