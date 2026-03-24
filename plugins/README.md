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

**Skills**

- `iterate-pr`: Fix CI failures and address review feedback on the current branch's PR in a single pass. Gathers feedback (LOGAF-categorized), fixes high/medium issues, prompts on low-priority items, checks CI, verifies locally, commits, pushes, and replies to all threads. Supports `--dry-run`.
