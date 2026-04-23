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

- `/resolve-pr-comments` *(deprecated — use `iterate-pr` skill instead)*: Fetch all unresolved review threads on the current branch's PR, evaluate each one, apply fixes where warranted, reply, and optionally resolve threads.

- `/resolve-ci-failures` *(deprecated — use `iterate-pr` skill instead)*: Show CI failures for a PR, diagnose the root cause, apply fixes, re-run the failing tests to verify, then commit and push.

- `/pr-walkthrough [<pr_link>]`: Generate a comprehensive reading guide for a pull request — includes a narrative reading order, architecture impact analysis, review comment summary, prior state context, and potential concerns ranked by risk.

**Skills**

- `iterate-pr`: Fix CI failures and address review feedback on the current branch's PR in a single pass. Gathers feedback (LOGAF-categorized), fixes high/medium issues, prompts on low-priority items, checks CI, verifies locally, commits, pushes, and replies to all threads. Supports `--dry-run`.

---

## commcare-tech

CommCare Tech Division skills for interacting with JIRA.

**Skills**

- `sprint-prep`: Prepare for the next sprint. Reviews your Jira board, walks through highlights and carryovers interactively, and drafts a sprint plan message for Slack.

- `jira-ticket`: Create a SAAS Jira ticket from a plain-English description. Handles assignee, issue type, effort, priority, sprint assignment, and epic linking automatically. Example: `/jira-ticket fix the login redirect bug`

- `jira-cve`: Create a security ticket from a GitHub Dependabot alert URL. Fetches the alert details, maps severity to priority, and delegates to `jira-ticket` with the right fields pre-filled. Example: `/jira-cve https://github.com/dimagi/commcare-hq/security/dependabot/740`

---

## connect-tech

CommCare Connect Team skills for documentation, specs, and release notes.

**Skills**

- `release-notes`: Generate Markdown release notes for the most recent release of a GitHub repository. Finds all PRs merged between the last two releases, categorizes and groups them, and writes a clean stakeholder-ready file to `outputs/`. Example: `/release-notes dimagi/commcare-connect`

- `jira-spec-doc`: Generate a full product spec doc (Design Doc + Tech Spec) from a Jira ticket ID or URL. Fetches ticket data and produces a structured Markdown file following the Connect Spec Doc template. Example: `/jira-spec-doc CCC-284`

- `docs-vs-code-review`: Audit Confluence documentation against actual source code to find inaccuracies and gaps. Fetches all pages under a root Confluence URL, clones the relevant repos, and produces a prioritized edit list. Example: `/docs-vs-code-review https://dimagi.atlassian.net/wiki/spaces/connectpublic/pages/3215458305`

---

## uss-tech

USS Tech Team skills for Jira project management and Confluence design docs.

**Skills**

- `jira-project-management`: Manage USH Jira tickets, epics, sprints, and Confluence design docs. Implicit skill — triggers when you mention a USH ticket, ask about sprint status, request a design doc, etc.
