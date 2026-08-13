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

Two ways to review code: hand it off to parallel specialist agents, or work through it yourself with Claude alongside.

**Skills**

- `code-review`: Review code, a PR diff, a file, or a directory. Spawns 6 parallel reviewer agents — design, quality, code smells, security, maintainability, and commit structure — and produces a structured, severity-ranked report. Hands-off.

- `pair-review`: Review a GitHub PR interactively, commit by commit, in a dedicated `review` worktree. You read the code and write your own comments; Claude explains what each commit and line does on demand and tracks progress by reading your pending GitHub review. Read-only — it never writes to GitHub. Example: `/pair-review https://github.com/dimagi/commcare-hq/pull/37998`

---

## dev-utils

Utility commands and skills for general development tasks. See [dev_utils/README.md](dev_utils/README.md) for the full list.

**Commands**

- `/review-plan`: Interactively review a plan across architecture, code quality, tests, and performance before writing any code. Works through issues one section at a time with opinionated recommendations and asks for your input before assuming a direction.

- `/pr-walkthrough <pr-link-or-number>`: Generate a comprehensive reading guide for a pull request — includes a narrative reading order, architecture impact analysis, review comment summary, prior state context, and potential concerns ranked by risk.

**Skills**

- `create-pr`: Commit staged/unstaged changes, push to a new branch if on main, and open a pull request using the repo's PR template.

- `create-mobile-pr`: For mobile PRs in the dimagi/commcare-android repository, open a draft GitHub pull request with a JIRA-prefixed title and a template-generated description, appending QA notes to the active release section of RELEASES.md in a separate commit, and assign the current user without requesting reviewers.

- `iterate-pr`: Fix CI failures and address review feedback on the current branch's PR in a single pass. Gathers feedback (LOGAF-categorized), fixes high/medium issues, prompts on low-priority items, checks CI, verifies locally, commits, pushes, and replies to all threads. Supports `--dry-run`.

- `babysit-prs`: One sweep over all your open PRs — new review comments, CI, branch freshness, lint and generated-artifact drift, description sync — with a sub-agent per PR and state tracking so reruns skip handled work. Designed to be driven by `/loop`. Pass a PR number to work a single PR instead.

- `pr-status-report`: Generate a structured, prioritized report of all open PRs in the current GitHub repository, grouping them by what needs the current user's attention — reviews requested of them, their own PRs with failing CI or change requests, PRs awaiting review, and PRs they have already reviewed — and ending with a numbered action-items list.

- `explain-diff-html`: Generate a rich, self-contained HTML explanation of a diff, branch, or PR — background, intuition, code walkthrough, and an interactive quiz.

- `grill-me`: Interrogate a plan or design one question at a time until every open decision is resolved, recording the outcomes in a design doc.

- `git-rebase`: Fixup squashing, interactive rebase cleanup, moving changes between commits, splitting an edit across history, and recovering from a failed autosquash.

- `audit-dependencies`: Full dependency audit for Python (pip-tools or uv) and JavaScript (npm/yarn). Writes a dated report, applies the safe bumps, and emits a Jira-ready ticket list for risky and end-of-life items.

- `add-mobile-string`: Add a new Android string resource (with translations across all supported locales) to the CommCare Android project, given a resource name and English text.

- `vertical-ordering`: Place callers above callees. Auto-applies (not user-invocable) when writing or reorganizing functions.

---

## commcare-tech

CommCare Tech Division skills for interacting with JIRA.

**Skills**

- `sprint-prep`: Prepare for the next sprint. Reviews your Jira board, walks through highlights and carryovers interactively, and drafts a sprint plan message for Slack.

- `jira-ticket`: Create a SAAS Jira ticket from a plain-English description. Handles assignee, issue type, effort, priority, sprint assignment, and epic linking automatically. Example: `/jira-ticket fix the login redirect bug`

- `jira-cve`: Create a security ticket from a GitHub Dependabot alert URL. Fetches the alert details, maps severity to priority, and delegates to `jira-ticket` with the right fields pre-filled. Example: `/jira-cve https://github.com/dimagi/commcare-hq/security/dependabot/740`

- `writing-commits-and-prs`: Team conventions for branches, commits, PR titles, descriptions, and reviewable diffs across Dimagi repos. Auto-applies (not user-invocable) when drafting a commit, naming a branch, writing a PR title, or composing/editing a PR description.

---

## connect-tech

CommCare Connect Team skills for documentation, specs, and release notes.

**Skills**

- `release-notes`: Generate Markdown release notes for the most recent release of a GitHub repository. Finds all PRs merged between the last two releases, categorizes and groups them, and writes a clean stakeholder-ready file to `outputs/`. Example: `/release-notes dimagi/commcare-connect`

- `jira-spec-doc`: Generate a full product spec doc (Design Doc + Tech Spec) from a Jira ticket ID or URL. Fetches ticket data and produces a structured Markdown file following the Connect Spec Doc template. Example: `/jira-spec-doc CCC-284`

- `docs-vs-code-review`: Audit Confluence documentation against actual source code to find inaccuracies and gaps. Fetches all pages under a root Confluence URL, clones the relevant repos, and produces a prioritized edit list. Example: `/docs-vs-code-review https://dimagi.atlassian.net/wiki/spaces/connectpublic/pages/3215458305`

- `jira-tickets-from-plan`: Reviews an AI plan, breaks it into logically independent tickets, and creates them in Jira. Example: `/jira-tickets-from-plan https://github.com/dimagi/commcare-android/blob/1fc89da7c1bdec74406b9689522f50595bd7fc76/docs/superpowers/plans/2026-05-11-ccct-2164-decouple-login-from-connect-launch.md`

---

## uss-tech

USS Tech Team skills for Jira project management and Confluence design docs.

**Commands**

- `/uss-review`: Thorough code review with a USS impact specialist. Runs code-review's 5 reviewers in parallel with a USS-specific 6th reviewer; renders the standard synthesis followed by a USS section with audience-bucketed user-facing changes. Requires the `code-review` plugin.

**Skills**

- `jira-project-management`: Manage USH Jira tickets, epics, sprints, and Confluence design docs. Implicit skill — triggers when you mention a USH ticket, ask about sprint status, request a design doc, etc.
