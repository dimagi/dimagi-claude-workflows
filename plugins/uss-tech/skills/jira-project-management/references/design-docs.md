# Design Docs Reference

Use the constants from SKILL.md for all tool calls (Cloud ID,
Confluence Space Key, Design Docs Parent Page ID).

## Creating a Design Doc

1. Look up the Confluence space ID from space key `uss` using
   `mcp__atlassian__getConfluenceSpaces`.
2. Create the page with `mcp__atlassian__createConfluencePage`:
   - `spaceId`: the space ID from step 1
   - `parentId`: `3802038305` (Tech Design Docs)
   - `contentFormat`: `"markdown"`
   - `title`: include the ticket key, e.g.
     "USH-6495: Case API Field Filtering Design"
   - `body`: freeform — adapt structure to the ticket context
3. Update the Jira ticket description to append a link to the new doc.
   Use `mcp__atlassian__editJiraIssue`:
   - Fetch the current description first with
     `mcp__atlassian__getJiraIssue`
   - Append the Confluence link at the end of the existing description

## Fetching a Design Doc

The link between a ticket and its design doc is the source of truth.
Follow this sequence:

1. Fetch the ticket with `mcp__atlassian__getJiraIssue` (include
   description and comments via `fields: ["comment", "description"]`).
2. Search the description and comment bodies for Confluence URLs
   matching `dimagi.atlassian.net/wiki/`.
3. If found, extract the page ID from the URL and fetch with
   `mcp__atlassian__getConfluencePage` using
   `contentFormat: "markdown"`.
4. If not found in the ticket, fall back to CQL search:
   ```
   ancestor = 3802038305 AND title ~ "USH-XXXX"
   ```
   Use `mcp__atlassian__searchConfluenceUsingCql`.
5. If still not found, tell the user no linked doc exists and offer to
   create one.

## Editing a Design Doc

1. Fetch current content with `mcp__atlassian__getConfluencePage`.
2. Confirm the intended changes with the user.
3. Use `mcp__atlassian__updateConfluencePage` with:
   - `body`: the modified content
   - `versionMessage`: a brief description of the change
