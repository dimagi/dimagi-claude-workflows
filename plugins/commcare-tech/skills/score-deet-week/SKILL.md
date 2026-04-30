---
name: score-deet-week
description: Use when the user wants to divide up, assign, or distribute unscored Jira tickets from the SAAS deet week board (board 252) for scoring/grooming. Triggers on phrases like "score deet week", "split up the unscored tickets", "divide unscored tickets", "assign tickets for scoring", or "who should score these". Mobile tickets always go to Ahmad; the rest get split evenly among the other Platform devs. Posts the result to Slack #commcare-tech.
---

# Score Deet Week Tickets

Workflow for fetching unscored tickets from the SAAS deet week board and dividing them among Platform team developers for scoring, then posting the assignments to Slack.

## Inputs

- **Jira board**: SAAS board 252 (https://dimagi.atlassian.net/jira/software/c/projects/SAAS/boards/252) — the deet week board
- **Slack channel**: `#commcare-tech` (channel ID `CNQ636095`)
- **Cloud ID for Atlassian MCP**: `dimagi.atlassian.net`

## Workflow

### 1. Fetch unscored deet week tickets

**Important context — don't filter by sprint.** Board 252 is the deet week board, but deet week is **not** a Jira sprint. It's a quarterly event identified by a label, and board 252 is just a saved filter on that label. The SAAS project simultaneously has multiple unrelated open sprints (CommCare Product, CommCare Platform, etc.). A `sprint in openSprints()` query will silently mix the wrong work in.

Board 252's filter is:

```
labels = DEET_WEEK_Q<Q>_<YYYY> ORDER BY priority DESC
```

The label changes each quarter. Compute it from today's date:
- Quarter: Q1 = Jan–Mar, Q2 = Apr–Jun, Q3 = Jul–Sep, Q4 = Oct–Dec
- Year: the current calendar year

For example, on 2026-04-30 the label is `DEET_WEEK_Q2_2026`. If no tickets come back, the label may not be created yet or may straddle a quarter boundary — confirm with the user.

**Unscored** in this context means `Effort Range = "Awaiting Score" OR "Effort Range" is EMPTY`. Do **not** use `"Story Points" is EMPTY` — this team scores via the Effort Range custom field, not Story Points, and the two are not equivalent.

Call `mcp__atlassian__searchJiraIssuesUsingJql` with:

- `cloudId`: `dimagi.atlassian.net`
- `jql`: `labels = DEET_WEEK_Q<Q>_<YYYY> AND ("Effort Range" = "Awaiting Score" OR "Effort Range" is EMPTY)`
- `fields`: `["summary", "status", "issuetype", "assignee"]`
- `maxResults`: `100`

If the result fits, parse it inline. If it errors with a saved-output file path, read the **first** `text` element (`.[0].text` — the second is sometimes `null`) and extract per-issue with `jq`:

```bash
jq -r '.[0].text' <saved-output-file> | jq -r '.issues[] | "\(.key)\t\(.fields.issuetype.name)\t\(.fields.status.name)\t\(.fields.assignee.displayName // "Unassigned")\t\(.fields.summary)"'
```

### 2. Confirm the developer list with the user

The Platform team membership changes over time, so don't hardcode it. Ask the user to confirm the current list of devs to divide among **before** assigning. A reasonable starting point to propose (based on recent history): Graham, Amit, Daniel, Jing, Evan, Norman — with Ahmad as the mobile dev.

Phrasing example: "Confirm the devs to divide among — last time it was Graham, Amit, Daniel, Jing, Evan, Norman, and Ahmad gets all mobile tickets. Still right?"

### 3. Identify mobile tickets

A ticket is mobile-related if its summary or description clearly references the mobile app: keywords like "mobile", "CommCare app", "sync", "form open on device", "android", "j2me". Be conservative — if it's ambiguous (e.g., "Missing Image Attachment" without mobile context), treat it as non-mobile.

All mobile tickets go to **Ahmad** (he is the only mobile dev). They do **not** count toward the even split.

### 4. Divide non-mobile tickets evenly

**Shuffle the dev list before assigning** — round-robin gives the first few devs in the list extra tickets when the count doesn't divide evenly, so a fixed order means the same people repeatedly do more scoring. Randomize the dev order each run so the "extras" rotate fairly over time.

Use a real source of randomness (e.g. `python3 -c "import random, sys; devs=sys.argv[1:]; random.shuffle(devs); print(' '.join(devs))" Graham Amit Daniel Jing Evan Norman`) rather than picking an order yourself — your "random" choices tend to be biased.

Then round-robin the non-mobile tickets across the shuffled list. If the count doesn't divide evenly, the first few devs in the shuffled list get one extra ticket each. Order tickets within each dev's section by the order they were assigned (no need to sort by key).

### 5. Format the message for Slack

The `mcp__plugin_slack_slack__slack_send_message` tool accepts standard Markdown (it converts to Slack mrkdwn server-side), so use Markdown syntax — `**bold**`, `[label](url)`, and `-` bullets all render correctly. Use the ticket key (e.g. `SAAS-19572`) as the hyperlink label, followed by an em dash and the summary, so Slack stays scannable while keeping enough context to know what each ticket is about.

Format:

```
Here are the unscored tickets for this upcoming deet week. Please score the tickets you've been given.


**Ahmad (mobile):**
- [SAAS-XXXXX](https://dimagi.atlassian.net/browse/SAAS-XXXXX) — Ticket summary here


**Graham:**
- [SAAS-XXXXX](https://dimagi.atlassian.net/browse/SAAS-XXXXX) — Ticket summary here
- [SAAS-XXXXX](https://dimagi.atlassian.net/browse/SAAS-XXXXX) — Ticket summary here

...
```

Note the blank line **between each dev section** (after the last bullet of one dev and before the next dev's name), and the blank line after the intro sentence. Do **not** put a blank line between a dev's name and their first bullet — that line should run directly into the list.

Notes on formatting:
- Do **not** put a ticket count next to each dev's name — the user finds it noisy. The bullet list itself shows the count.
- Keep the "(mobile)" note next to Ahmad so it's clear why he gets a separate section.
- If Ahmad has no mobile tickets in this batch, omit his section entirely.
- After the per-dev sections, include a **Judgment calls** section flagging any close-call assignments (e.g. ambiguous mobile-vs-non-mobile tickets) so the user can quickly override them. Skip this section if there were no judgment calls.

### 6. Show the user the draft and confirm before posting

Print the formatted message to the conversation and ask for confirmation before sending. The user may want to rebalance (e.g., move a ticket from one dev to another, swap who gets the extra one). After any edits, reprint the final version and confirm again.

### 7. Post to Slack

Use `mcp__plugin_slack_slack__slack_send_message` with:
- `channel_id`: `CNQ636095`
- `text`: the formatted message from step 5

Confirm to the user that it was posted and include the resulting Slack permalink if returned.

## Why this design

- **Confirming devs each run**: team membership shifts (people join, leave, go on PTO). Hardcoding causes silent miss-assignments. A one-line confirmation is cheap insurance.
- **Mobile to Ahmad always**: Ahmad is the sole mobile dev, so mobile tickets need his expertise to score accurately.
- **Key-as-link with summary trailing**: bare URLs are noisy. Hyperlinking just the SAAS key gives a stable, predictable link target while the trailing summary still makes the message scannable.
- **Draft-then-send**: posting to a shared channel is hard to undo. A confirmation step costs nothing and prevents embarrassing reposts.
