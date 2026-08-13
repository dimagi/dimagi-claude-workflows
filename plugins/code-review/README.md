# code-review

Two ways to review code: hand it off to parallel specialist agents, or work
through it yourself with Claude alongside.

## Skills

- `code-review` — Review code, a PR diff, a file, or a directory. Spawns six
  parallel specialist reviewers — design, quality, code smells, security,
  maintainability, and commit structure — then deduplicates, calibrates
  severity, and synthesises one prioritised report. Hands-off. (The commit
  structure reviewer is skipped when there's no commit range to review, leaving
  five.)

- `pair-review` — Review a GitHub PR interactively, commit by commit, in a
  dedicated `review` worktree. You read the code and write your own comments;
  Claude explains what each commit and line does on demand and tracks progress
  by reading your pending GitHub review. Read-only — it never writes to
  GitHub.

  ```
  /pair-review https://github.com/dimagi/commcare-hq/pull/37998
  ```

## Agents

The specialist reviewers live in `agents/` and are spawned by the `code-review`
skill rather than invoked directly: `design-reviewer`, `quality-reviewer`,
`smells-reviewer`, `security-reviewer`, `maintainability-reviewer`, and
`branch-reviewer`. Each writes its findings as JSON for the orchestrator to
merge. Other plugins can reuse them — `uss-tech`'s `/uss-review` runs these
five alongside a USS-specific sixth reviewer.
