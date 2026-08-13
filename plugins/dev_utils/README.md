# dev-utils

Utility commands and skills for general development — mostly the work that
surrounds writing code: opening PRs, keeping them healthy, reviewing plans, and
tidying git history.

Nothing here is Dimagi-specific except `create-mobile-pr` and
`add-mobile-string`, which target the CommCare Android repo.

Most skills shell out to `gh`, so have the GitHub CLI installed and
authenticated.

## Commands

- `/review-plan` — Interactively review a plan across architecture, code
  quality, tests, and performance before any code is written. Asks first
  whether you want a deep review or major issues only, then works section by
  section with opinionated recommendations.

- `/pr-walkthrough <pr-link-or-number>` — Reading guide for a pull request: a
  narrative reading order, architecture impact, a summary of existing review
  comments, and concerns ranked by risk.

## Skills

### Pull requests

- `create-pr` — Commit, push, and open a PR, filling in the repo's PR template
  if it has one.

- `create-mobile-pr` — The Dimagi mobile variant: draft PR, JIRA-prefixed
  title, release and QA notes appended to `RELEASES.md` rather than the PR
  body. Triggers on repos with JIRA branch prefixes and a `RELEASES.md`.

- `iterate-pr` — One pass over the current branch's PR: gather review feedback,
  fix CI failures, verify locally, commit, push, and reply to every thread.
  `--dry-run` prints the plan without changing anything.

- `babysit-prs` — One sweep over *all* your open PRs — new review comments, CI,
  branch freshness, lint and generated-artifact drift, description sync — with
  a sub-agent per PR and state tracking so reruns skip handled work. Built to
  be driven by the loop runner:

  ```
  /loop 20m /babysit-prs
  /loop /babysit-prs          # self-paced
  ```

  Pass a PR number or URL to work a single PR instead.

- `pr-status-report` — Prioritised report of open PRs in the current repo,
  grouped by what needs your attention, ending with a numbered action list.

- `explain-diff-html` — Rich, self-contained HTML explanation of a diff,
  branch, or PR: background, intuition, code walkthrough, and an interactive
  quiz. Written to a dated file outside the repo.

### Working on code

- `grill-me` — Interrogates your plan or design one question at a time until
  every open decision is resolved, recording the outcomes in a design doc.

- `git-rebase` — Fixup squashing, interactive rebase cleanup, moving changes
  between commits, splitting an edit across history, and recovering from a
  failed autosquash.

- `audit-dependencies` — Full dependency audit for Python (pip-tools or uv) and
  JavaScript (npm/yarn). Writes a dated report, applies the safe bumps, and
  emits a Jira-ready ticket list for the risky and end-of-life items.

- `vertical-ordering` — Callers above callees. Auto-applies while writing or
  reorganising functions; not user-invocable.

### CommCare Android

- `add-mobile-string` — Add a string resource and its translations to every
  locale `strings.xml`, discovering the locale set at runtime.
