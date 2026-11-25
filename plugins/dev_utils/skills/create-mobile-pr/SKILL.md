---
name: create-mobile-pr
description: Use when creating, opening, or submitting a pull request in a Dimagi mobile/CommCare repo — identified by JIRA-prefixed branches (e.g. CCCT-1929-...), a `RELEASES.md` with `### Release Notes` and `### QA Notes` sections, and the dimagi PR template (Safety story / Product Description / Technical Summary / QA Plan). Also triggers on "ship this" or when implementation is complete and ready to push. For repos without these conventions, use the generic `create-pr` skill instead.
---

# Create GitHub Pull Request

Open a **draft** PR with a JIRA-prefixed title, a description built from the repo's PR template, an author-confirmed risk label, and `--assignee "@me"`. The user reviews and marks it ready on GitHub. Release/QA notes go in `RELEASES.md`, not the PR body.

Every artifact below has a **recipe** (what it contains) and a **budget** (how long it may be). Fill the recipe with true statements up to the budget, then stop. Write to that shape — do not treat the budget as a target to reach. An artifact that would be empty is omitted entirely, heading and all. **The whole PR body is capped at 120 words** — section bodies, excluding headings and the ticket link. Every section under budget but the body over 120 still fails; drop the least load-bearing section.

**The diff test — apply to every sentence of the PR body.** Before writing a sentence, ask: *could the reviewer learn this by reading the diff?* If yes, delete it. Names of new helpers, params, or values; which file the code lives in; "follows the existing convention"; what a function does mechanically — all visible in the diff, all cut. The PR body exists only for what the code cannot tell the reviewer: why, and what to watch for. `example.md` in this directory is a full worked example of good, terse output.

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

### 2. Pre-PR code review

Run the `code-review:code-review` skill (the code-review plugin's skill, not the built-in `/code-review`) on the branch, commit range `master..HEAD`. dev-utils declares the code-review plugin as a dependency, so it is normally installed already. If the skill isn't available, ask the author to run `/reload-plugins` (which installs missing dependencies) and retry; if it still isn't available, stop the skill: no PR is created without a review.

Before starting, `git status --porcelain` must be empty; if it isn't, ask the author to commit or stash those changes first, so review fixes stay separate from other work.

Let its triage and expand/fix loop run as written: the author fixes, disputes or ignores each finding there, with one change:

- **One commit per finding.** After implementing each finding, before starting the next one, commit only that finding's changes. The subject line says what the fix does (e.g. `Close cursor when sync fails`), not "Address review finding". When a request covers several findings (`fix 2,5`), implement and commit them one at a time. If one change genuinely fixes two findings, commit it once and note both in the body.

When the loop ends:

- **Refresh the diff.** If any fixes were committed, re-run step 1's `git diff` and `--stat` so later steps describe the fixed branch.
- **List unresolved findings.** Unresolved means 🔴 Critical or 🟠 Major, not fixed in the loop, and not withdrawn by the review after the author's pushback. Keep the author's reason when they pushed back and the finding stood. Ignore 🟡 Minor and 💡 Suggestion.
- **Gate.** If any are unresolved, list them and ask with `AskUserQuestion`: "N Critical/Major review findings are unresolved. Continue creating the PR?" with options *Continue* and *Stop*. On *Stop*, end the skill: no RELEASES.md commits, no push, no PR. Never continue on the author's behalf.

Hold the unresolved list for step 11.

### 3. Title

**Recipe:** `TICKET Short Description Of The Change`, derived from the commits and diff (not the branch slug).
**Budget:** ≤72 chars. Title Case every word including short ones (On, To, For, The). Preserve acronym/identifier casing (`SSO`, `URL`, `iOS`, `CCCT-1929`).

Extract `TICKET` (`[A-Z]+-[0-9]+`) from the branch prefix; fall back to commit messages; if still none, ask.
Example: `CCCT-1929 Re-Fetch SSO Token On Invalid Token Error`

### 4. Ask about the author's testing

The Safety story needs what the *author* actually did. If they haven't already said, ask:

> What did you personally do to test this? (ran it on a device, exercised a flow, ran a test suite, reviewed the diff only, etc.)

Wait for the answer. Record it honestly, including "did not test locally." Never invent testing.

### 5. Update RELEASES.md

Find the topmost `## CommCare X.YZ` section. Release Notes and QA Notes are **separate decisions, separate drafts-for-approval, separate commits**. **No JIRA ticket numbers anywhere in RELEASES.md.**

**Release Notes** — go under the `### Release Notes` subsection, in one of `#### What's New`, `#### Important Bug Fixes`, or `#### Internal Release Notes`. Include only if the change is observable by end users or a specific project.
**Recipe:** one bullet stating what changed *from the user's perspective*.
**Budget:** one line per change. No implementation detail.

**QA Notes** — go under the `### QA Notes` subsection. What a tester with only a phone build must manually verify (app UI, settings, forms, Connect, PersonalID, their own test accounts, HQ admin views). A tester has no Android Studio, Logcat, adb, or tests; if a regression is invisible without those, say so and rely on automated coverage instead of writing an unrunnable step.
**Recipe:** one bullet per distinct check, phrased "verify X still works" / "confirm Y behaves as expected." Only non-obvious risks and behavior changes — the tester already knows the happy path.
**Budget:** 1–3 bullets; hard cap 5.

For each: show the user the exact bullet text verbatim and the **release version heading it will go under** (e.g. `## CommCare 2.56`) so they can confirm it is landing in the right release — plus the subsection (`### QA Notes`, or `### Release Notes` → `#### Important Bug Fixes`). Wait for their approval, then commit alone (`Add release notes for TICKET` / `Add QA notes for TICKET`). Do not decide on the user's behalf to skip a note they might want — when in doubt whether a note is warranted, ask.

### 6. Risk level

Follow the `pr-risk` skill in its before-the-PR mode, reusing the diff from step 1 (as refreshed in step 2) and the testing answer from step 4. It proposes Low, Medium or High, the author confirms, overrides or skips, and it hands back a label and a reason line. If the author skips, the PR gets neither.

### 7. PR description

Build from `.github/PULL_REQUEST_TEMPLATE.md`, replacing every HTML comment with content. **Do not show the description for approval** — it's a draft the user edits on GitHub. Only RELEASES.md and the risk level needed approval.

**Top of body:** `### [TICKET](https://dimagi.atlassian.net/browse/TICKET)` (display text is just the ticket).

Fill a section only when its recipe has something true to say; otherwise delete that heading and body. Always keep the ticket link and Safety story. **Omit the Labels and Review section.**

- **Safety story** — starts with the reason line from step 6, if there is one, then a blank line, then a neutral risk read in two lists, `**What gives confidence**` and `**Risks to review**`. Rank candidates by how much each one changes the reviewer's read and keep only the top ones, most important first — true is the floor, not the bar. Author actions in **first person** ("I exercised the happy path"); statements about the change in third person. Note a mitigation if there is one; otherwise leave it for the reviewer. `risk-categories.md` lists what to weigh.
  **Budget:** ≤2 items per list, ≤15 words each; ≤55 words total, not counting the reason line (which still counts toward the 120-word body).
- **Technical Summary** — *only* what survives the diff test: why this approach over the obvious alternative, and any non-obvious decision, exclusion, or ordering dependency a reviewer should know before reading. If the diff already speaks for itself, omit the whole section.
  **Budget:** ≤40 words.
- **Product Description** — the user-facing behavior change.
  **Budget:** ≤25 words.
- **Automated test coverage** — what tests were added or changed and what they lock down.
  **Budget:** ≤25 words.

**Verify before building the body:** count the words in each drafted section and recut any that exceeds its budget — drop the lowest-ranked item, or tighten. Then sum them; if the total exceeds 120, cut the least load-bearing section whole.

### 8. Push

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}   # upstream?
git push -u origin HEAD    # if none
git push                   # if behind (carries the RELEASES.md commits)
```

### 9. Create the draft PR

```bash
gh pr create --draft \
  --title "TICKET Short Description" \
  --body "$(cat <<'EOF'
<generated description>
EOF
)" \
  --assignee "@me" \
  --label "Medium Risk"    # the label from step 6; omit if the author skipped it
```

No `--reviewer` — the user requests reviewers after leaving draft. Capture the printed PR URL for steps 10 and 11.

### 10. Suggested Review Order comment

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

### 11. Unresolved review findings comment

Skip if step 2 left nothing unresolved.

**Recipe:** one bullet per unresolved finding from step 2, Critical first: severity, title, `file:line`, and a clause on the consequence. Append `— Author: <reason>` where the author disputed it.
**Budget:** ≤30 words per bullet.

```bash
gh pr comment <PR-URL> --body "$(cat <<'EOF'
## Unresolved Pre-PR Review Findings

The author opened this PR with these Critical/Major findings from the pre-PR code review unresolved:

- 🔴 **Title** (`path/to/file.kt:42`) — consequence
- 🟠 **Title** (`path/to/file.kt:88`) — consequence — Author: reason
EOF
)"
```

Then output the PR URL.

## Hard rules (mechanical, always)

- Draft PR: `--draft`, `--assignee "@me"`, never `--reviewer`.
- At most one risk label, and only the one the author confirmed in step 6.
- No JIRA ticket numbers in RELEASES.md (release notes or QA notes).
- Each RELEASES.md update is its own commit, and only after the user approves the drafted bullets.
- Omit the template's Labels and Review section.
- Never leave the template's HTML-comment placeholders in the body.
- Every PR body section is at or under its word budget, and the body is ≤120 words.
- Push the branch before `gh pr create`.
- Never skip the step 2 review or open a PR without it.
- Each review fix from step 2 is its own commit, made before the next finding is worked on.
- Never open the PR with unresolved Critical/Major review findings unless the author chose *Continue* in step 2, and then always post them as a comment (step 11).
