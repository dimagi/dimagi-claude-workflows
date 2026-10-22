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

- `jira-cve-sync` — Bulk-sync Dependabot alerts for the repo you run it from
  with SAAS security tickets: create missing tickets via `jira-cve`, close
  tickets whose alert is fixed, link open/merged PRs, and record a one-time
  impact investigation on every open ticket. Reads the repo's `AGENTS.md` for
  context. Prints the plan, applies it, then reports only what deviated.
  Example: `cd ~/dimagi/commcare-hq && /jira-cve-sync --dry-run`

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
