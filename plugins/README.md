# Plugins

This directory contains Claude Code plugins for this repository.

## Installation

**Add this marketplace:**
```
/plugin marketplace add dimagi/dimagi-claude-workflows
```

**Browse available plugins:**
```
/plugins
```

---

## code-review

Thorough code review via 5 parallel specialist agents — design, quality, code smells, security, and maintainability — synthesised into a single prioritised review.

**Skills**

- `code-review`: Review code, a PR diff, a file, or a directory. Spawns parallel reviewer agents and produces a structured, severity-ranked report.

---

## dev-utils

Utility commands for general development tasks.

**Commands**

- `/create-pr`: Commit staged/unstaged changes, push to a new branch if on main, and open a pull request.

- `/review-plan`: Interactively review a plan across architecture, code quality, tests, and performance before writing any code. Works through issues one section at a time with opinionated recommendations and asks for your input before assuming a direction.

- `/resolve-pr-comments`: Fetch all unresolved review threads on the current branch's PR, evaluate each one, apply fixes where warranted, reply, and optionally resolve threads.
  - `--resolve`: resolve each thread after replying
  - `--dry-run`: print the evaluation plan but make no changes

- `/resolve-ci-failures [<pr_number> [<repo>]]`: Show CI failures for a PR, diagnose the root cause, apply fixes, re-run the failing tests to verify, then commit and push. Defaults to the current branch's PR and repo if arguments are omitted.

---

## commcare-tech

CommCare Tech Division skills for interacting with JIRA.

**Skills**

- `sprint-prep`: Prepare for the next sprint. Reviews your Jira board, walks through highlights and carryovers interactively, and drafts a sprint plan message for Slack.

- `jira-ticket`: Create a SAAS Jira ticket from a plain-English description. Handles assignee, issue type, effort, priority, sprint assignment, and epic linking automatically. Example: `/jira-ticket fix the login redirect bug`

- `jira-cve`: Create a security ticket from a GitHub Dependabot alert URL. Fetches the alert details, maps severity to priority, and delegates to `jira-ticket` with the right fields pre-filled. Example: `/jira-cve https://github.com/dimagi/commcare-hq/security/dependabot/740`
