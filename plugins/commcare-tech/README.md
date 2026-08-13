# commcare-tech

Skills for the CommCare Tech Division — Jira workflows on the SAAS project,
sprint rituals, and the team's writing conventions.

Most of these talk to Jira and Slack, so the corresponding MCP servers need to
be connected.

## Skills

- `jira-ticket` — Create a SAAS Jira ticket from a plain-English description.
  Handles assignee, issue type, effort, priority, sprint assignment, and epic
  linking. Example: `/jira-ticket fix the login redirect bug`

- `jira-cve` — Create a security ticket from a GitHub Dependabot alert URL.
  Fetches the alert, maps severity to priority, and delegates to `jira-ticket`
  with the fields pre-filled. Example:
  `/jira-cve https://github.com/dimagi/commcare-hq/security/dependabot/740`

- `dependency-upgrade` — Upgrade a Python or JS dependency safely: find the
  latest safe version, review the changelog, assess impact from how the library
  is actually used in the repo, perform the upgrade, and open a PR with the
  changelog and assessment. Example: `/dependency-upgrade django`

- `sprint-prep` — Prepare for the next sprint. Reviews your Jira board, walks
  through highlights and carryovers interactively, and drafts a sprint plan
  message for Slack.

- `score-deet-week` — Divide unscored tickets on the deet week board among the
  Platform devs for scoring and post the split to `#commcare-tech`. Mobile
  tickets go to Ahmad; the rest are split evenly.

- `writing-commits-and-prs` — Team conventions for branches, commits, PR
  titles, descriptions, and reviewable diffs across Dimagi repos.
  Auto-applies (not user-invocable) when drafting a commit, naming a branch, or
  composing a PR description.
