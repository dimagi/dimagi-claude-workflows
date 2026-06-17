---
name: audit-dependencies
description: Run a full dependency audit for a project — covers Python (pip-tools) and front-end (npm/yarn) if present. Produces report, applies safe bumps, emits Jira-ready ticket list for risky/EoL items. Use when running quarterly maintenance or on demand.
---

# Audit Dependencies

## Overview

End-to-end audit of a project's direct dependencies against PyPI, npm, and `endoflife.date`. Produces `docs/dependency-audit-YYYY-MM-DD.md`, applies category A+B bumps to the lockfiles, and emits a ticket list for category C+D items.

Covers Python — either pip-tools (`*.in` → `*.txt` workflow) or uv (`pyproject.toml` → `uv.lock`) — and JavaScript (npm/yarn `package.json`) if present. Detect which Python toolchain the project uses and run that one; do not mix the two. If a project only has one ecosystem, skip the steps for the other.

## Step 0: Discover project structure

Before starting, orient yourself:

1. **Python:** First determine the toolchain.
   - **uv:** Look for `uv.lock` alongside a `pyproject.toml`: `find . -name "uv.lock" -not -path "*/node_modules/*"`. If found, the direct-dependency surface is `[project.dependencies]` and any `[dependency-groups]` / `[project.optional-dependencies]` in `pyproject.toml`.
   - **pip-tools:** Otherwise find `.in` files: `find . -name "*.in" -path "*/requirements*" | grep -v node_modules`, and their corresponding lockfiles (`*.txt`).
2. **JavaScript:** Check for `package.json` (and `package-lock.json` or `yarn.lock`): `find . -name "package.json" -not -path "*/node_modules/*" | head -5`.
3. **Test command:** Check `pyproject.toml`, `setup.cfg`, or `pytest.ini` for Python tests. Check `package.json` `scripts` for JS tests. Look for required env vars in `.env_template` or `conftest.py`.
4. **Major framework:** Read the Python lockfile to determine the current Django (or other framework) version — this sets the "framework floor" for Step 6.

## Steps

### Python

1. **Snapshot current pins** from the lockfile(s) discovered in Step 0 (`*.txt` for pip-tools, `uv.lock` for uv).

2. **Compute available upgrades:**
   - **pip-tools:** `pip-compile --upgrade --dry-run` on each `.in` file.
   - **uv:** `uv lock --upgrade --dry-run` to preview the resolved upgrades against the current `uv.lock`.

3. **For each direct dep** (from the `.in` files, or from `pyproject.toml` for uv), fetch latest version from PyPI:
   ```bash
   python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('https://pypi.org/pypi/<pkg>/json'))['info']['version'])"
   ```

4. **EoL check** for framework-grade components via `https://endoflife.date/api/<product>.json`. At minimum check: `python`, `django` (if used), `postgres` (if used). Flag anything currently in use that is past EoL or within 6 months of EoL.

5. **Classify each Python dep** using the A/B/C/D scheme (see Classification below).

6. **Check framework floor.** For each B/A candidate, verify whether the target version requires a newer version of the major framework (Django, etc.) than currently running. If yes and the framework upgrade is itself deferred to a ticket, demote the package to C and link it to that ticket.

### JavaScript (if `package.json` found)

7. **Run `npm audit`** (or `yarn audit` if using yarn) to surface known CVEs in the current lockfile:
   ```bash
   npm audit --json 2>/dev/null | python -c "import json,sys; d=json.load(sys.stdin); print(f\"{d['metadata']['vulnerabilities']}\")"
   ```

8. **Check for outdated packages**:
   ```bash
   npm outdated
   ```

9. **Classify JS deps** using the same A/B/C/D scheme. Note: for JS major bumps, check the package's CHANGELOG or migration guide — breaking changes are common across major versions.

10. **Apply safe JS bumps** (`npm update` for patch/minor, or `npm install <pkg>@<version>` for specific targets). Run the JS test suite after each bump. If anything breaks, revert and demote to C.

### Report and tickets

11. **Write report** to `docs/dependency-audit-<today>.md` with:
    - **Process section:** classification criteria (A/B/C/D definitions), tools used (pip-compile or uv lock — whichever the project uses, PyPI API, npm audit, npm outdated, endoflife.date, git grep, pip-audit), and source files audited.
    - Summary (dep counts per category, split by ecosystem if both present)
    - EoL findings table
    - Per-package table (Python and JS sections if both present): current version, latest version, category, action, changelog link
    - "Bumps to apply" list (A + B)
    - "Tickets to file" list (C + D)

12. **Apply Python A+B bumps**, one package at a time using the project's toolchain:
    - **pip-tools:** `pip-compile --upgrade-package <pkg>`.
    - **uv:** `uv lock --upgrade-package <pkg>` (bump the constraint in `pyproject.toml` first if the target exceeds the current spec).

    After each bump, run the test suite and `pre-commit run -a`. If anything breaks, demote to C and revert.

    Commit structure:
    - One bulk commit for all A-class bumps
    - One bulk commit for all B-class bumps that required no code changes
    - One commit per B-class bump that required minor code changes (so it can be reverted in isolation)
    - JS bumps in their own commit(s), separate from Python bumps

13. **Emit ticket list** for C+D items to `docs/dependency-audit-<today>-tickets.md` using Jira-ready format (title, current→target, EoL date, risk, references). Roll framework-floor-blocked packages into the framework upgrade ticket.

14. **Commit the applied bumps** following the structure in step 12. Do not commit the audit report or ticket list — leave that to the operator. Do not push or open a PR.

### Classification

Used for both Python and JS deps:

- **A — Patch/minor:** non-breaking version bump.
- **B — Low-risk major:** major bump where the changelog has no breaking changes affecting this project's import/usage surface (verify with `git grep` for Python; check import/usage patterns for JS).
- **C — Risky major:** breaking changes affect the code.
- **D — EoL / security:** upstream support ended, within 6 months of EoL, or active CVE.

## When to invoke

- Quarterly maintenance (see `docs/dependency-maintenance.md` if it exists in this project).
- After a Dependabot security alert if a broader review is wanted.
- Before planning a major framework upgrade.

## References

- pip-tools docs: https://pip-tools.readthedocs.io
- uv docs (lockfile & upgrades): https://docs.astral.sh/uv/concepts/projects/sync/
- endoflife.date API: https://endoflife.date/api/<product>.json
- OSV vulnerability DB (used by pip-audit): https://osv.dev
- npm audit docs: https://docs.npmjs.com/cli/commands/npm-audit
