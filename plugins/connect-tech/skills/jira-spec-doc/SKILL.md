---
name: jira-spec-doc
description: >
  Generates a full product spec doc in Markdown from a Jira ticket ID or URL.
  Use this skill whenever the user shares a Jira ticket ID (like CCC-284) or a
  Jira URL (like https://dimagi.atlassian.net/browse/CCC-284) and asks for a
  spec doc, design doc, tech spec, or product specification to be created or
  drafted from it. Also trigger when the user says things like "write a spec for
  this ticket", "generate a spec from this Jira", "turn this ticket into a spec",
  or "make a spec doc for [ticket ID]". The skill fetches the ticket's title,
  description, and metadata from Jira, then produces a structured Markdown file
  with both a Design Doc section and a Tech Spec section following the Connect
  Spec Doc template format. Always use this skill when a Jira ticket is the
  primary input and a spec doc is the desired output.
---

# Jira Spec Doc Generator

This skill takes a Jira ticket ID or URL and produces a comprehensive product spec doc as a Markdown file, following the Connect Spec Doc template with both a **Design Doc** and a **Tech Spec** section.

## Step 1: Extract the ticket ID

Parse the ticket ID from whatever the user provides:
- A bare ID like `CCC-284`
- A full URL like `https://dimagi.atlassian.net/browse/CCC-284`
- A casual mention like "ticket 284 in CCC"

## Step 2: Fetch ticket data from Jira

Use the Jira MCP tool (`getJiraIssue`) to fetch the ticket. Use cloudId `dbff467f-3c3f-4ced-a2ba-a29e1941edd6` (Dimagi's Atlassian instance).

Pull these fields:
- `summary` — becomes the document title
- `description` — primary source of content
- `issuetype.name` — helps shape the narrative (Bug, Story, Task, Idea, etc.)
- `status.name` — for context
- `assignee` — for the Author field if present
- `project.key` and `project.name` — for the Epic/project field
- Any linked issues or parent epic if available

## Step 3: Generate the spec doc

Write a Markdown file to `./outputs/<TICKET-ID>-spec-doc.md`, creating the `outputs/` directory if it doesn't exist.

Use the ticket data to populate the template as fully as possible. For fields the ticket doesn't supply, make a reasonable inference based on what you know, or leave a clear `_[Add X]_` placeholder. The goal is a document that's genuinely useful as a starting point — not just a skeleton with empty fields.

Follow this exact structure:

---

### Document structure

```
# <ticket summary>

**Jira Ticket:** [<TICKET-ID>](<ticket URL>)

---

## Design Doc

| Field | Details |
|---|---|
| **Related Materials** | [<TICKET-ID>](<ticket URL>) |
| **Mockups / Wireframes** | _Add link_ |
| **Author** | <assignee name, or "_Add name_"> |
| **Requested Reviewers** | _Add reviewers_ |
| **Feature Release Path** | Path 3 - Iterative Product Area |
| **Release Switch** | Required |
| **Implementation Tickets** | _Add tickets_ |

---

### Background

**Problem Description / User Story:**
<2–4 sentence description of the problem from the user's perspective, drawn from the ticket description>

**Background:**
<How did this problem arise? Why does it matter? What's been tried or observed? Infer from the ticket if not explicit.>

**Goals:**
- _Usage goals:_ <What measurable outcome are we aiming for after this ships?>
- _Implementation goals:_ <What must the implementation achieve to be considered done?>
- _(Optional) Effectiveness goals:_ <Are there effectiveness/workflow improvements we're targeting?>

**Non-Goals:**
- <What is explicitly out of scope for this phase?>

**Future Requirements:**
- <What related work might follow in a later phase?>

---

### Assumptions

- <Key assumption 1>
- <Key assumption 2>

---

### User Stories

**As a <role>:**
- <I want to X, so that Y.>

(Include one user story per affected role if multiple are apparent from the ticket.)

---

### Solution Summary

**Area 1 – <short label>**
<Description of the primary solution area>

**Area 2 – <short label, if applicable>**
<Description of a secondary solution area, if needed>

---

### Success Evaluation

<2–4 sentences describing how we'll know this was successful: metrics, behavioral changes, error rates, etc.>

---

### (Optional) Review Tracker

| Reviewer | Status | Notes |
|---|---|---|
| _Add reviewer_ | Not started | |

---
---

## Tech Spec

**Epic:** _Add Epic_
**Ticket Number & Description:** [<TICKET-ID>](<ticket URL>) — <ticket summary>

| Field | Details |
|---|---|
| **Related Materials** | [<TICKET-ID>](<ticket URL>) |
| **Mockups / Wireframes** | _Add link_ |
| **Author** | <assignee name, or "_Add name_"> |
| **Feature Release Path** | Path 3 - Iterative Product Area |
| **Release Switch** | Required |
| **Implementation Tickets** | _Add tickets_ |

---

### Introduction

<2–3 sentences summarizing what this ticket is about from a technical perspective, what the fix/change involves at a high level, and why it matters.>

---

### Solution

**Current Solution:**
<Describe the current behavior or system state that this ticket is addressing.>

**Proposed Solution:**
<Describe the proposed technical approach: what changes, where, and how. Include:
- Any external components or dependencies involved
- Security considerations
- How the solution scales
- Limitations of the approach
- Expected API changes
- Error logging considerations
- Any DB/model changes>

**Monitoring and Alerting Plan:**
<Describe any logging, analytics, or alerting that should accompany this change.>

**Deployment and Release:**
<Describe the release plan: feature flag usage, phased rollout if applicable, rollback strategy.>

**Alternative Solutions:**
<List 1–2 alternatives considered and why this approach was chosen over them.>

---

### Suggested Subheadings

**Model Changes:**
<Describe any data model or database schema changes, or state "No model changes anticipated.">

**Django View Changes:**
<Describe any backend view or API changes needed.>

**Frontend Changes:**
<Describe any frontend/UI changes, including component-level details where possible.>

**API Definitions:**
<Define any new or modified API endpoints: method, path, request/response format, permissions.>

---

### Further Considerations

- <Any open questions, edge cases, or cross-cutting concerns worth flagging for reviewers.>
```

---

## Dimagi role and terminology glossary

Use these terms precisely and consistently throughout the spec doc. Abbreviations are commonly used in tickets — always expand them correctly:

| Abbreviation | Full term |
|---|---|
| PM | Program Manager |
| NM | Network Manager |
| FLW | Front Line Worker |

Never substitute generic terms like "user", "admin", or "project manager" when a specific role is implied. If a ticket says "PM-only action", write "Program Manager" throughout the doc.

## Codebase references

Every Tech Spec must include a **Relevant Codebases** section immediately after the metadata table and before the Introduction. Link the correct repo(s) based on what the ticket involves:

- **Web / backend work** (Connect web app, PM portal, APIs, Django views, data models): [commcare-connect](https://github.com/dimagi/commcare-connect)
- **Mobile work** (FLW-facing Android app, OTP screens, PIN flows, mobile UX): [commcare-android](https://github.com/dimagi/commcare-android)

Many tickets touch both — include both links when the work spans web and mobile. Use the ticket description to infer which codebase(s) apply: mobile keywords include "app", "Android", "OTP screen", "PIN", "FLW experience"; web keywords include "Connect web", "dashboard", "PM portal", "Django", "API endpoint".

Add this section to the Tech Spec right after the metadata table:

```
### Relevant Codebases

- [commcare-connect](https://github.com/dimagi/commcare-connect) — <one-line description of what changes here>
- [commcare-android](https://github.com/dimagi/commcare-android) — <one-line description of what changes here>
```

(Include only the repo(s) that are relevant; omit the other if it's truly not involved.)

## Guidelines for writing good content

**Draw from the ticket description thoroughly.** Even a short description usually implies architecture, user roles, permissions, and failure modes. Reason through the implications rather than just paraphrasing.

**Be specific about roles.** Always use the full role names from the glossary above. Generic language ("users") is less useful than precise language ("Program Managers" or "Front Line Workers").

**Make intelligent inferences.** If the ticket says "hide button X for role Y," you can infer:
- There's currently no role check on button X (current state)
- A role check needs to be added (proposed solution)
- Backend enforcement may also be needed (security consideration)
- QA should test both roles (further considerations)

**Leave clear placeholders.** Anything you can't confidently infer should use `_[Add X]_` or `_Add X_` in italics so the author immediately knows what to fill in.

**Keep structure consistent.** The section headers must match the template exactly — reviewers expect to navigate to specific sections.

## Output

Save the file to `./outputs/<TICKET-ID>-spec-doc.md`, creating the `outputs/` directory if it doesn't exist. Tell the user the file path where the spec doc was saved.
