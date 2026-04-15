---
name: create-pr
description: >
  End-to-end PR creator. Generates a crisp and clear title, fills the repo PR template
  for the body, pushes the branch if needed, and opens the PR via gh.
  Supports --draft and --confirm flags. Auto-invoke when the user says
  "build my PR", "create PR", "ship PR", "open PR", "pr builder".
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git push:*), Bash(git ls-remote:*), Bash(git rev-parse:*), Bash(git status:*), Bash(gh pr create:*), Bash(gh pr list:*), Bash(gh auth status:*), Bash(ls:*), Bash(cat:*), Read
---

# create-pr — title + body + create

You are building a full pull request: generating a short crisp title, a clear body that fills the repo's PR template, pushing the branch if needed, and creating the PR via `gh`.

Never invent commits, file changes, or test files. Everything in the title and body must come from the actual diff.

## Step 1 — parse `$ARGUMENTS`

`$ARGUMENTS` may contain any combination of:

- A base branch name (first non-flag token). Default to `main` if not provided.
- `--draft` — create the PR as a draft.
- `--confirm` — show preview AND ask the user to approve before running `gh pr create`. Without this flag, preview is shown and the PR is created immediately after.

Record these as `BASE`, `DRAFT`, `CONFIRM` for the remaining steps.

## Step 2 — preflight checks

Run these and fail fast with a clear single-line message if any check fails. Do **not** continue past a failed check.

```
!gh auth status
!git branch --show-current
!gh pr list --head "$(git branch --show-current)" --state open --json number,url
```

Failure conditions:

- `gh auth status` non-zero → stop with: `gh is not authenticated. Run 'gh auth login' first.`
- Current branch equals `BASE` → stop with: `You are on the base branch (<BASE>). Checkout a feature branch first.`
- `gh pr list` returns any rows → stop with: `PR #<N> already exists: <url>. Aborting.`

## Step 3 — gather diff context (tiered, to survive large diffs)

Run these in order, cheapest first:

```
!git log {BASE}..HEAD --no-merges --oneline
!git diff {BASE}...HEAD --stat
!git diff {BASE}...HEAD --name-only
```

If `--stat` shows no changes vs `BASE`, stop with: `No changes vs <BASE>. Nothing to create a PR for.`

Then decide whether to pull the full diff:

- **Small change** (under ~500 lines changed per `--stat` totals) → run `git diff {BASE}...HEAD` and use the full diff.
- **Large change** (500+ lines, or many files) → do **not** dump the full diff. Instead:
  1. Identify the 3–6 most important files from `--name-only` (migrations, new files, files with the most churn from `--stat`, files whose names suggest the core intent).
  2. Run `git diff {BASE}...HEAD -- <file1> <file2> ...` for just those files.
  3. Rely on commit messages + `--stat` + file names for everything else.

This keeps the skill usable on big refactors without drowning in noise.

## Step 4 — analyse

Extract from the diff and commit messages:

- **What changed**: which files/modules; what was added, modified, removed.
- **Why** (in this order): (1) commit messages, (2) code comments and docstrings, (3) the shape of the change. If commit messages are unhelpful (e.g. `wip`, `fixes`) and the code doesn't make intent obvious, write the "why" conservatively — describe what the change *does*, not an invented motivation. Do not hedge with "the purpose is unclear" on every PR; only flag uncertainty when it is genuinely ambiguous.
- **User-facing effect**: any template, view, URL, API, UI text, or behavior a user would notice? If purely internal, note that.
- **Risk surface**: does it touch auth, payments, migrations, public APIs, permissions, infra, shared utilities?
- **Tests**: new or changed test files? Gaps?

### Change-type heuristics (apply if triggered)

- **Migration files touched** (`*/migrations/*.py`, `alembic/`, `*.sql`): flag in Safety story — name the tables/columns affected, whether it's reversible, whether it runs on large tables, and whether there's a backfill. Call out `RunPython` / `RunSQL` blocks specifically.
- **API changes** (`serializers.py`, `views.py` in API dirs, URL patterns under `/api/`): flag as potential breaking change. Note API version and whether it's a new endpoint, modified response shape, or removed field.
- **Async / Celery task changes** (`tasks.py`, `@shared_task`, `@app.task`): mention queue impact, retry behavior, and whether existing in-flight tasks will deserialize correctly after the change.
- **Test-only change** (every changed file is under `tests/` or matches `test_*.py` / `*_test.py`): mark as test-only in Product Description (`No user-facing changes.`) and in Safety story (inherently low-risk — no production code path changes).
- **Backend-only change** (no template / static / frontend file touched): state plainly in Product Description: `No user-facing changes.` Do not invent user impact.
- **Permissions / auth changes** (`permissions.py`, `decorators.py` in auth dirs, `@permission_required`): flag as high-risk surface. Safety story must address who gains/loses access.
- **Feature flag / waffle changes** (`flags/`, `switch_names.py`, `Waffle`): note the flag name and default state. Low-risk if behind a flag; call that out.

## Step 5 — writing rules (apply to both title and body)

- **Short sentences.** One idea per sentence. No nested clauses.
- **Plain language.** A PM or designer must understand Product Description and Safety story without a glossary. If a technical term is unavoidable, add a plain-English parenthetical.
- **Precise, not vague.** Name the actual thing. Not "updated some logic" → "changed how login tokens expire".
- **Concise.** Each section: 2–4 sentences or a short bullet list. No padding.
- **No Jira/ticket links.** Skip ticket references entirely.
- **No placeholders.** Every `<!-- ... -->` from the template must be replaced with real content or the section omitted if it genuinely does not apply.

## Step 6 — generate the title

Rules:

- Imperative mood: `Fix X`, `Add Y`, `Remove Z`, `Rename A to B`. Not `Fixes`, `Added`, `Adding`.
- Under 70 characters.
- One idea. Describes the actual change, not a category.
- No prefixes: no ticket IDs, no `feat:` / `fix:`, no branch-name echoes.
- No trailing period.

Good: `Fix task-type rename breaking visit list view`
Bad: `Updates for task type` (vague) · `fix: stuff` (prefix + vague) · `CCCT-2336 Update visit views` (prefix + vague)

### Vague-word self-check

After drafting the title, scan it for these weak words: `update`, `updates`, `improve`, `improvement`, `improvements`, `tweak`, `adjust`, `refactor` (alone), `misc`, `various`, `stuff`, `things`, `cleanup` (alone), `changes`, `minor`.

If the title contains any of these as its main verb/noun, **regenerate it** and name the actual thing. "Update visit views" → `Fix visit views breaking on renamed task types`. "Refactor auth" → `Split auth middleware into session and API paths`. The regenerated title must pass this check before you move on.

## Step 7 — locate and read the repo PR template

The repo's PR template is the source of truth for body structure. Locate it by trying these paths in order (GitHub's own lookup order) and use the **first one that exists**:

1. `.github/PULL_REQUEST_TEMPLATE.md`
2. `.github/pull_request_template.md`
3. `docs/PULL_REQUEST_TEMPLATE.md`
4. `docs/pull_request_template.md`
5. `PULL_REQUEST_TEMPLATE.md` (repo root)
6. `pull_request_template.md` (repo root)

Use `ls` to check for each path, then `Read` the first one found. Record the full template verbatim as `TEMPLATE`.

If none of the paths exist → use this fallback template as `TEMPLATE`:

```markdown
## Summary

<!-- What changed and why -->

## Test plan

<!-- How this was verified -->
```

If the repo has multiple templates under `.github/PULL_REQUEST_TEMPLATE/` (a directory), list the directory, pick the one whose name best matches the change (e.g. `bug_fix.md` for a fix, `feature.md` for new functionality), and use that. If unclear, ask the user which template to use.

## Step 8 — generate the body from `TEMPLATE`

Fill every section of `TEMPLATE` with real content from the diff:

- Preserve every heading, checkbox, and section ordering from `TEMPLATE` exactly.
- Replace every HTML comment (`<!-- ... -->`) with real prose.
- **Never leave a section empty and never silently drop one.** If a section genuinely does not apply to this change, write exactly one line stating that explicitly with the reason — e.g. `Not applicable — this PR only touches internal helper functions and has no automated tests by design.` or `No user-facing changes.` Reviewers must be able to tell you *considered* the section, not that you forgot it.
- If a section has a checkbox (like `- [ ] Reviewers are appropriate`), leave the checkbox state as-is — do not auto-check anything on the user's behalf.
- Apply the writing rules from Step 5 to every section you fill.

Section-specific guidance when the template has these common sections:

- **Product Description / User impact** → 2–4 sentences in plain English a PM would understand. Name the actual screen / button / flow / error. If no user-facing effect: write exactly `No user-facing changes.`
- **Technical Summary / Description** → 2–4 plain sentences: what was built or changed and why. Include design decisions only if non-obvious. Skip anything already in the product section.
- **Safety story / Risk** → 2–4 sentences. What was tested locally, why the change is low-risk, rollback / blast radius. Flag data impact if models or migrations are touched.
- **Automated test coverage / Tests** → name the test files added or changed with one line each on what they would catch. If no tests changed, say so explicitly and explain why that is acceptable or call it out as a gap.
- **QA Plan / Manual testing** → numbered steps a human can follow. Name the page, the action, and the expected result.

If the template contains sections you do not have guidance for, fill them using the same writing rules: concise, plain, precise, no placeholders left behind.

## Step 9 — show the preview

Print the generated title and body back to the user as a single fenced markdown block so they can see exactly what is about to be created. Use this exact shape:

```
Branch: <current-branch>  →  Base: <BASE>
Draft: <yes|no>

Title: <generated title>

Body:
---
<generated body>
---
```

## Step 10 — confirm (only if `--confirm` was passed)

If `CONFIRM` is true, stop here and ask the user in plain text: `Create this PR now?` Wait for their reply. Any answer that is not clearly affirmative (`yes`, `y`, `ok`, `go`, `ship it`) → stop with: `Aborted. No PR created.`

If `CONFIRM` was not passed, continue directly to Step 11.

## Step 11 — push the branch if it is not on the remote

```
!git ls-remote --exit-code --heads origin "$(git branch --show-current)"
```

If exit code is non-zero, run:

```
!git push -u origin HEAD
```

If the push fails, stop and surface the error. Do not continue to `gh pr create`.

## Step 12 — create the PR

Write the body to a temp file, then pass it via `--body-file` to avoid any shell-escaping issues with markdown content.

```
!cat > /tmp/create-pr-body.md <<'BODYEOF'
<generated body>
BODYEOF
```

Then:

```
!gh pr create --base {BASE} --title "<generated title>" --body-file /tmp/create-pr-body.md [--draft]
```

Include `--draft` only if `DRAFT` is true.

Clean up: `rm -f /tmp/create-pr-body.md`.

## Step 13 — output the PR URL

`gh pr create` prints the new PR URL on stdout. Echo it back to the user on its own line, prefixed with `PR created: `.

Example final output:

```
PR created: https://github.com/dimagi/commcare-connect/pull/1234
```

## Hard rules

- Never amend commits, never rebase, never force-push, never `git reset`. The only write-side git command you may run is `git push -u origin HEAD` for a branch the remote does not yet have.
- Never modify code or tests as part of this skill. Title and body come from what already exists in the diff.
- Never invent test files, ticket IDs, or flags that the diff does not show.
- If anything fails, stop and surface the exact error. Do not retry blindly.

