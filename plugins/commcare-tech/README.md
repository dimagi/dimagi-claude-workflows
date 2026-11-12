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

- `vulnerability-management` — Carry a CommCare security vulnerability from
  report to published advisory: COMMVULN tickets, draft GHSAs, readiness
  checks on private PRs, public PRs, publishing, and mirror cleanup. Policy
  stays on the team's Confluence pages, which the skill reads at each phase.
  Example: `/vulnerability-management check COMMVULN tickets in Pre-disclosure are ready to release`

- `dependency-upgrade` — Upgrade a Python or JS dependency safely: find the
  latest safe version, review the changelog, assess impact from how the library
  is actually used in the repo, perform the upgrade, and open a PR with the
  changelog and assessment. Example: `/dependency-upgrade django`

- `dependency-upgrade-review` — Review a Dependabot (or other dependency-bump)
  PR: identify changed packages, research changelogs, assess breaking-change
  and codebase impact, then post the analysis as a PR comment (after
  confirming with you). Example: `/dependency-upgrade-review 12345`

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
