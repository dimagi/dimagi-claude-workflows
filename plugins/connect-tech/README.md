# connect-tech

Skills for the CommCare Connect team — Jira tickets and specs, release notes,
and keeping Confluence docs honest.

Most of these talk to Jira, Confluence, or Slack, so the corresponding MCP
servers need to be connected.

## Jira

- `jira-bug-ticket` — File a well-structured bug ticket. Collects every field
  in one pass, shows a preview, and only creates the ticket once you confirm.

- `jira-feature-request` — Create a feature request Story in the CI project
  using Dimagi's form 134 format.

- `jira-spec-doc` — Generate a full spec doc (Design Doc + Tech Spec) from a
  Jira ticket ID or URL, following the Connect spec template.
  Example: `/jira-spec-doc CCC-284`

- `jira-tickets-from-plan` — Take an AI-written plan, break it into logically
  independent tickets, and create them in Jira.

- `groom-sprint-tickets` — Groom the tickets in a named sprint. Slash-command
  only; never auto-invoked. Example: `/groom-sprint-tickets Sprint 42`

## Release notes

- `connect-web-release-notes` — Release notes for the latest
  `dimagi/commcare-connect` release, posted to Confluence and Slack. Runs
  end-to-end with no input.

- `release-notes` — The generic version: Markdown release notes for the most
  recent release of any GitHub repo, categorised and grouped for stakeholders.
  Example: `/release-notes dimagi/commcare-connect`

## Documentation

- `docs-vs-code-review` — Audit Confluence documentation against the actual
  source to find inaccuracies and gaps. Give it a root Confluence URL; the
  repos are inferred from the space. Produces a focused edit list, not a full
  audit. Example:
  `/docs-vs-code-review https://dimagi.atlassian.net/wiki/spaces/connectpublic/pages/3215458305`
