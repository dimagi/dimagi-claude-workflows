---
name: create-mobile-pr
description: Use when creating, opening, or submitting a pull request in a Dimagi mobile/CommCare repo — identified by JIRA-prefixed branches (e.g. CCCT-1929-...), a `RELEASES.md` with `### Release Notes` and `### QA Notes` sections, and the dimagi PR template (Safety story / Product Description / Technical Summary / QA Plan). Also triggers on "ship this" or when implementation is complete and ready to push. For repos without these conventions, use the generic `create-pr` skill instead.
---

# Create GitHub Pull Request

Open a **draft** PR with a JIRA-prefixed title, a description built from the repo's PR template, and `--assignee "@me"`. The user reviews and marks it ready on GitHub. Release/QA notes go in `RELEASES.md`, not the PR body.

Every artifact below has a **recipe** (what it contains) and a **budget** (how long it may be). Fill the recipe with true statements up to the budget, then stop. Write to that shape — do not treat the budget as a target to reach. An artifact that would be empty is omitted entirely, heading and all.

**The diff test — apply to every sentence of the PR body.** Before writing a sentence, ask: *could the reviewer learn this by reading the diff?* If yes, delete it. Names of new helpers, params, or values; which file the code lives in; "follows the existing convention"; what a function does mechanically — all visible in the diff, all cut. The PR body exists only for what the code cannot tell the reviewer: why, and what to watch for.

See `example.md` in this directory for a full worked example of good, terse output.

## Process

### 1. Gather context (parallel)

```
git branch --show-current
git log master..HEAD --oneline
git log master..HEAD          # full messages, fallback for ticket
git diff master...HEAD --stat
git diff master...HEAD
cat .github/PULL_REQUEST_TEMPLATE.md
cat RELEASES.md
```

Fold any notes/context/verification steps the user already gave into the right sections.

### 2. Title

**Recipe:** `TICKET Short Description Of The Change`, derived from the commits and diff (not the branch slug).
**Budget:** ≤72 chars. Title Case every word including short ones (On, To, For, The). Preserve acronym/identifier casing (`SSO`, `URL`, `iOS`, `CCCT-1929`).

Extract `TICKET` (`[A-Z]+-[0-9]+`) from the branch prefix; fall back to commit messages; if still none, ask.
Example: `CCCT-1929 Re-Fetch SSO Token On Invalid Token Error`

### 3. Ask about the author's testing

The Safety story needs what the *author* actually did. If they haven't already said, ask:

> What did you personally do to test this? (ran it on a device, exercised a flow, ran a test suite, reviewed the diff only, etc.)

Wait for the answer. Record it honestly, including "did not test locally." Never invent testing.

### 4. Update RELEASES.md

Find the topmost `## CommCare X.YZ` section. Release Notes and QA Notes are **separate decisions, separate drafts-for-approval, separate commits**. **No JIRA ticket numbers anywhere in RELEASES.md.**

**Release Notes** — include only if the change is observable by end users or a specific project. Place under `#### What's New`, `#### Important Bug Fixes`, or `#### Internal Release Notes`.
**Recipe:** one bullet stating what changed *from the user's perspective*.
**Budget:** one line per change. No implementation detail.

**QA Notes** — what a tester with only a phone build must manually verify (app UI, settings, forms, Connect, PersonalID, their own test accounts, HQ admin views). A tester has no Android Studio, Logcat, adb, or tests; if a regression is invisible without those, say so and rely on automated coverage instead of writing an unrunnable step.
**Recipe:** one bullet per distinct check, phrased "verify X still works" / "confirm Y behaves as expected." Only non-obvious risks and behavior changes — the tester already knows the happy path.
**Budget:** 1–3 bullets; hard cap 5.

For each: show the exact bullet(s) and their heading, wait for approval, then commit alone (`Add release notes for TICKET` / `Add QA notes for TICKET`).

### 5. PR description

Build from `.github/PULL_REQUEST_TEMPLATE.md`, replacing every HTML comment with content. **Do not show the description for approval** — it's a draft the user edits on GitHub. Only RELEASES.md needed approval.

**Top of body:** `### [TICKET](https://dimagi.atlassian.net/browse/TICKET)` (display text is just the ticket).

Fill a section only when its recipe has something true to say; otherwise delete that heading and body. Always keep the ticket link and Safety story. **Omit the Labels and Review section.**

- **Safety story** — a neutral risk read in two lists, items only if true. Author actions in **first person** ("I exercised the happy path"); statements about the change in third person.
  - *What gives confidence:* the author's testing (step 3, their words), narrow scope, existing coverage of the touched paths, flag-gating.
  - *Risks to review:* migrations, behavior changes for existing users, untested paths, third-party integrations, perf-sensitive or error-handling changes, limited author testing. Note the mitigation if there is one; otherwise leave it for the reviewer.
- **Technical Summary** — *only* what survives the diff test: why this approach over the obvious alternative, and any non-obvious decision, exclusion, or ordering dependency a reviewer should know before reading. If the diff already speaks for itself, omit the whole section.
  **Budget:** 1–3 sentences.
- **Product Description** — the user-facing behavior change.
  **Budget:** 1–2 sentences.
- **Automated test coverage** — what tests were added or changed and what they lock down.
  **Budget:** 1–2 sentences.

### 6. Push

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}   # upstream?
git push -u origin HEAD    # if none
git push                   # if behind (carries the RELEASES.md commits)
```

### 7. Create the draft PR

```bash
gh pr create --draft \
  --title "TICKET Short Description" \
  --body "$(cat <<'EOF'
<generated description>
EOF
)" \
  --assignee "@me"
```

No `--reviewer` — the user requests reviewers after leaving draft. Capture the printed PR URL for step 8.

### 8. Suggested Review Order comment

Skip if fewer than 2 non-generated files changed.

**Recipe:** the changed files in reading order, each with a short clause of rationale (≤15 words). Order: deleted/replaced code → schema/model/migration → new types/constants → core logic → integration/API → UI → tests (near their code, or first if they document intent) → config/build/cosmetic last. Skip generated files (lock files, compiled output, vendored deps). If the commits already tell a clean story, recommend reading commit-by-commit instead.

```bash
gh pr comment <PR-URL> --body "$(cat <<'EOF'
## Suggested Review Order

- `path/to/file-1.kt` — reason it comes first
- `path/to/file-2.kt` — reason it comes next
EOF
)"
```

Then output the PR URL.

## Hard rules (mechanical, always)

- Draft PR: `--draft`, `--assignee "@me"`, never `--reviewer`.
- No JIRA ticket numbers in RELEASES.md (release notes or QA notes).
- Each RELEASES.md update is its own commit, and only after the user approves the drafted bullets.
- Omit the template's Labels and Review section.
- Never leave the template's HTML-comment placeholders in the body.
- Push the branch before `gh pr create`.
