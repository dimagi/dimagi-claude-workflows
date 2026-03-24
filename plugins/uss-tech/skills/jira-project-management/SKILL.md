---
name: jira-project-management
description: >
  Use when the user interacts with Jira tickets, epics, or Confluence
  design docs for the USS team. Triggers when the user mentions a USH
  ticket key or URL, asks about sprint status, requests ticket
  summaries or comments, wants to create or find a design doc, or
  asks to transition a ticket's status.
---

# Jira Project Management (USS)

Manage USS Jira tickets, epics, and associated Confluence design docs.

## Constants

| Constant | Value |
|----------|-------|
| Cloud ID | `dbff467f-3c3f-4ced-a2ba-a29e1941edd6` |
| Project Key | `USH` (team refers to it as "USS") |
| Jira Base URL | `https://dimagi.atlassian.net` |
| Confluence Space Key | `uss` |
| Design Docs Parent Page ID | `3802038305` |
| Sprint Custom Field | `customfield_10010` |

## Status Workflow

Prioritized → In Progress → In Review → QA → Fix on Deploy → Done

## Routing

Read the appropriate reference file based on user intent:

| Intent | Reference |
|--------|-----------|
| Fetch, summarize, or list tickets/epics | tickets-and-epics.md |
| Add or read comments on a ticket | tickets-and-epics.md |
| List children of an epic | tickets-and-epics.md |
| View sprint tickets (current or upcoming) | tickets-and-epics.md |
| Transition a ticket's status | tickets-and-epics.md |
| Create, fetch, or edit a design doc | design-docs.md |

## Parsing Ticket References

Accept any of these forms and normalize to a ticket key:
- Bare key: `USH-6495`
- Full URL: `https://dimagi.atlassian.net/browse/USH-6495` → `USH-6495`
- Casual: "ticket 6495" → assume `USH-6495`

Always use the Cloud ID from Constants as the `cloudId` parameter for
all MCP tool calls.
