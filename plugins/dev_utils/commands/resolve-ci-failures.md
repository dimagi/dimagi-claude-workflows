---
description: Show CI failures for a PR and fix them
argument-hint: [<pr_number> [<repo>]]
allowed-tools: Bash(bash:*), Bash(gh pr checks:*), Bash(gh api:*), Bash(gh repo view:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Read, Edit
---

## 1. Fetch failures

Run the script to show which checks failed and the relevant log output:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/resolve-ci-failures.sh $ARGUMENTS
```

If there are no failures, tell the user and stop.

## 1b. Run failing tests locally

Before reading source code, run the failing tests locally using the project's test runner.

Derive the test names from the failure output (e.g., `FAILED tests/foo/test_bar.py::TestClass::test_method`). Check `pyproject.toml`, `package.json`, or `.github/workflows/` to find the correct test runner invocation.

If the tests **pass locally**, do NOT attempt to fix the code directly — the failure is likely environmental. Instead, investigate why the tests behave differently in CI. Common causes:
- Cache not cleared between tests (Redis, waffle flags, rate limiting)
- `transaction.on_commit()` callbacks that never fire inside rolled-back test transactions
- Test ordering dependency or shared mutable state

If the tests **fail locally**, continue to step 2 as normal.

## 2. Diagnose and fix

### Common failure patterns

| Pattern | Likely cause |
|---|---|
| Flaky (sometimes pass, sometimes fail in CI) | Test ordering dependency, shared mutable state, or time-dependent logic |

For each failure:

1. Read the relevant source files to understand the problem.
2. Apply the fix.
3. Stage the changed files (do not commit yet — batch all fixes).

## 3. Verify fixes

Re-run the specific failing tests locally to confirm they pass before committing. Derive the test command from the failure output and the project's test runner (check `pyproject.toml`, `package.json`, or `.github/workflows/` for the correct invocation).

If any tests still fail, return to step 2 and fix them before proceeding.

## 4. Commit and push

Once all fixes are applied:

```bash
git add <changed files>
git commit -m "fix: resolve CI failures

- <bullet per failure: what was fixed and why>"
git push
```

## 5. Summary

Print a brief summary of what was fixed.
