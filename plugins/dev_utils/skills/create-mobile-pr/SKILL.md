---
name: create-mobile-pr
description: Use when creating, opening, or submitting a pull request in a Dimagi mobile/CommCare repo — identified by JIRA-prefixed branches (e.g. CCCT-1929-...), a `RELEASES.md` with `### Release Notes` and `### QA Notes` sections, and the dimagi PR template (Safety story / Product Description / Technical Summary / QA Plan). Also triggers on "ship this" or when implementation is complete and ready to push. For repos without these conventions, use the generic `create-pr` skill instead.
---

# Create GitHub Pull Request

## Overview

Open a draft GitHub pull request with a JIRA-prefixed title, a description generated from the repo's PR template, and the current user as assignee. The PR is opened as a draft so the user can review on GitHub and mark it ready for review (and request reviewers) themselves. Release notes and QA notes go into `RELEASES.md`, not the PR description.

**Every generated artifact (title, description, release/QA notes) defaults to concise and high-level: capture the *why* and never restate what the diff already shows.**

## When to Use

- User asks to create, open, or submit a pull request
- User says "make a PR" or "open a PR"
- Implementation is done and user wants to push and open a PR

## Process

### 1. Gather Context

Run these in parallel:

- `git branch --show-current` -- current branch name
- `git log master..HEAD --oneline` -- commits on the branch
- `git log master..HEAD` -- full commit messages (used as fallback for ticket extraction)
- `git diff master...HEAD --stat` -- changed files summary
- `git diff master...HEAD` -- full diff
- `cat .github/PULL_REQUEST_TEMPLATE.md` -- the PR template
- `cat RELEASES.md` -- the current release file (used to find the active release section for Release Notes and QA Notes)

Also check: did the user provide additional notes, context, or verification steps? Incorporate them into the appropriate sections.

### 2. Extract Ticket Number and Build Title

Extract the JIRA ticket number (pattern `[A-Z]+-[0-9]+`) from:

1. **Branch name first** -- the leading prefix before the first description segment
2. **Commit messages as fallback** -- if the branch name has no ticket, scan commit messages for the pattern

Examples:
- `CCCT-1929-refetch-sso-token` -> `CCCT-1929`
- `CI-609-personalid-phone-fragment-crash` -> `CI-609`
- `ENG-42-add-new-feature` -> `ENG-42`

If no ticket number is found anywhere, ask the user for it.

**Build the PR title:** `TICKET-NUMBER Short Concise Description`

- The description after the ticket number should summarize the PR's purpose in a few words
- Derive it from the commits and diff -- do not just reuse the branch name slug
- Keep the total title under 72 characters
- **Capitalize the first letter of every word** in the description portion (including short words like `on`, `to`, `for`, `the`, `a`, `an`, etc.)
- Preserve the existing casing of acronyms, identifiers, and ticket numbers (e.g. `SSO`, `URL`, `iOS`, `CCCT-1929`)
- Example: `CCCT-1929 Re-Fetch SSO Token On Invalid Token Error`

### 3. Ask the User About Their Personal Testing

The Safety Story section depends on what the *author* actually did to verify the change. Before generating the PR description, check whether the user has already described their personal testing (e.g. in earlier turns of this conversation, or in additional notes they provided).

If they have not, ask explicitly -- for example:

> What did you personally do to test these changes? (e.g. ran the app on a device, exercised a specific flow, ran a particular test suite, reviewed the diff only, etc.)

Wait for their answer before proceeding. Do not invent or assume testing the user did not describe. If they say they did not test it locally, record that honestly in the Safety Story.

### 4. Update RELEASES.md (Release Notes and QA Notes)

Release notes and QA notes belong in `RELEASES.md`, not in the PR description. Each is its own decision, its own draft-for-approval, and its own commit so the changes are easy to review.

Open `RELEASES.md` and find the **most recent release section** (the topmost `## CommCare X.YZ` heading).

**Never include JIRA ticket numbers in `RELEASES.md` entries** — not in Release Notes, not in QA Notes. No `CCCT-1234`-style identifiers, no ticket links, no parenthetical ticket references in the bullet text. The ticket lives in the PR title and description.

#### 4a. Release Notes (skip if not required)

The `### Release Notes` subsection is published publicly (Play Store, GitHub Releases, CommCare Forums), plus an `#### Internal Release Notes` block for project-specific notes. Add an entry **only if** the change is observable by end users or relevant projects:

- `#### What's New` — new user-visible features or capabilities
- `#### Important Bug Fixes` — user-visible bug fixes worth surfacing
- `#### Internal Release Notes` — changes relevant only to specific projects

**Skip this step entirely** when the change has no user-visible impact — refactors, dev-tooling, internal-only logic, code cleanup, test-only changes. If unsure, ask the user whether a release note is needed.

Write entries as short, user-facing descriptions of *what changed* from the user's perspective. No ticket numbers. No implementation detail.

Show the user a draft of the release note bullet(s) — which subsection they'll go under and the exact bullet text, verbatim — and wait for their response. Do **not** run `git add` or `git commit` until the user has approved the draft. Once approved, stage and commit the change on the current branch with a short message such as `Add release notes for TICKET-NUMBER`. Use a separate commit so it is easy to review.

#### 4b. QA Notes (skip if not required)

Append bullets to `### QA Notes` describing what QA should manually verify.

**Write QA notes for testers with phone access only.** Assume QA's only tooling is:

- A build of the app installed on their phone
- The app's normal UI and any user-facing surfaces (settings, forms, Connect, PersonalID, etc.)
- Their own test accounts / test projects
- Server-side admin views they would normally use (e.g. HQ), if relevant to the feature

Do **not** write steps that require Android Studio, Logcat, adb, unit/instrumentation tests, internal storage inspection, or any developer-only tooling. QA notes read as user-level actions and observable outcomes: "do X in the app, expect Y." If a regression cannot be observed without developer tools, say so and rely on automated coverage instead of writing an unrunnable QA step.

**Be ruthlessly concise.** QA notes are a checklist of the most important things to verify, not a tutorial.

- Aim for the **fewest bullets possible** — often 1-3. If you are writing more than 5, you are almost certainly being too verbose.
- **Do not write step-by-step instructions.** QA knows how to use the app. "Verify the login screen still loads" is enough; do not enumerate "open the app, tap login, enter credentials, tap submit."
- **Omit anything obvious or implied.** If a flow has an obvious happy path, do not spell it out. Call out only the non-obvious risks, edge cases, or behavior changes a tester would not think to check.
- **One bullet per distinct thing to verify.** Do not split a single check across multiple bullets.
- Prefer "verify X still works after Y" or "confirm Z behaves as expected" framing over numbered procedures.

**Skip this step** when there is nothing for QA to manually verify (e.g. pure refactor with automated coverage, dev-tooling change). If unsure, ask the user.

No ticket numbers in QA bullets.

Show the user a draft of the QA bullet(s) — the release section heading they'll go under (e.g. `## CommCare 2.56`) and the exact bullet text, verbatim — and wait for their response. Do **not** run `git add` or `git commit` until the user has approved the draft. Once approved, stage and commit the change on the current branch with a short message such as `Add QA notes for TICKET-NUMBER`. Use a separate commit so it is easy to review.

### 5. Generate PR Description from the Template

**Do not show the PR description to the user for approval before opening the PR.** The PR is opened as a draft, so the user will review and edit the description on GitHub. Asking them to review a long markdown block in the terminal duplicates that review and wastes their time. The only thing that requires explicit approval before the PR is created is `RELEASES.md` changes (step 4), because those get committed to the repo. The PR title and description do not.

Read `.github/PULL_REQUEST_TEMPLATE.md` and fill out each section per the instructions in its HTML comments. Replace the HTML comments with content — do not leave them in the final description.

**Prepend a ticket link heading at the very top** (before the first template section):

- Format: `### [TICKET-NUMBER](https://dimagi.atlassian.net/browse/TICKET-NUMBER)`
- Example: `### [CCCT-2264](https://dimagi.atlassian.net/browse/CCCT-2264)`
- Display text is just the ticket number

**Be concise.** Every section should be the shortest version that still gives a reviewer what they need. No padding, no restating the diff in prose, no advocacy.

**Omit sections that have nothing valuable to add.** If a section would only contain filler, boilerplate, or a restatement of the obvious, drop the section entirely — heading and body. Examples:

- No new or modified tests → omit the **Automated test coverage** section entirely.
- No user-facing product change (pure refactor, internal cleanup) → omit the **Product Description** section entirely.
- Nothing non-obvious to call out beyond the diff itself → omit the **Technical Summary** section entirely.

Keep the **Safety story** and the ticket link heading in every PR. Other template sections are optional when they would add no signal.

#### Safety story — neutral, first-person, two short lists

The Safety story is a balanced risk assessment, not a defense of the PR. Two short lists, items only if actually true:

- **What gives confidence:** the user's personal testing (from step 3, in their words), narrow diff scope, existing automated coverage of the changed paths, flag-gating, etc.
- **Risks to review:** data migrations, behavior changes for existing users, paths not covered by automated tests, areas the user did not exercise, third-party integrations, performance-sensitive paths, error-handling changes, limited author testing. If a risk is mitigated, say *how*; otherwise leave it for the reviewer to decide.

**Voice:** write the Safety story in the **first person** when describing what the PR author did ("I manually exercised the happy path", not "the author" / "the user" / "the developer"). Statements about the change itself stay in third person.

#### Technical Summary — short, high level only

The Technical Summary is a **high-level orientation** for the reviewer, not a description of the diff. The reviewer can already see the diff.

- **Keep it short.** Aim for 1-3 sentences. A short bulleted list (roughly 2-4 tight bullets) is fine when it concisely groups distinct changes that would be harder to follow in prose — but bullets are not an excuse for length. No code blocks. No file-by-file walkthrough.
- **Do not restate facts that are obvious from reading the code change.** If the only thing you can say is "renames `foo` to `bar` in three files," omit the section entirely (see "Omit sections" guidance above).
- Focus on the **why** and the **shape** of the change: which subsystem is touched, what approach was chosen, and any non-obvious design decision a reviewer should know before reading the diff.
- If the change is a small, self-explanatory fix or rename, prefer omitting the section over writing filler.

#### Product Description and Automated test coverage

Fill Product Description and Automated test coverage from the diff, commits, and user-provided context. Keep each short and concrete. Incorporate the user's testing into the Safety story's confidence list rather than fabricating details elsewhere.

Per the "Omit sections" guidance above, drop either section entirely when it would have no signal — e.g. omit Automated test coverage when no tests were added or modified, and omit Product Description for pure refactors with no user-facing change.

**Omit the Labels and Review section from the PR description.** Do not include its heading or body.

### 6. Ensure Branch is Pushed

Check if the current branch has an upstream remote:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

If no upstream exists, push the branch:

```bash
git push -u origin HEAD
```

If the branch is behind the remote, push the latest commits (this will include any RELEASES.md commits from step 4):

```bash
git push
```

### 7. Create the Pull Request as a Draft

Use `gh pr create` with the `--draft` flag. Do not request reviewers -- the user will mark the PR ready and request reviewers themselves once they have reviewed it on GitHub.

```bash
gh pr create \
  --draft \
  --title "TICKET-NUMBER Short description" \
  --body "$(cat <<'EOF'
<generated PR description here>
EOF
)" \
  --assignee "@me"
```

Key flags:
- `--draft` -- opens the PR in draft mode
- `--title` -- JIRA ticket number followed by short description
- `--body` -- full PR description generated from the template
- `--assignee "@me"` -- assigns to the current GitHub user

Do **not** pass `--reviewer`. Reviewer selection is the user's responsibility once they take the PR out of draft.

Capture the PR URL printed by `gh pr create` — it is needed in step 8.

### 8. Post a Suggested Review Order Comment

After the PR is created, post a comment on it with a **Suggested Review Order**: a short bulleted list of the changed files in the order a reviewer should read them, each with a one-line rationale. This helps reviewers build a mental model of the change instead of clicking through files in GitHub's default order.

**Skip this step** when the PR has fewer than 2 non-generated files changed — there is no order to suggest.

**Decide the order** using these heuristics, in priority order:

- Read deleted or replaced code before its replacement
- Schema / data model / migration changes first
- New types, interfaces, or constants before their consumers
- Core logic / domain layer next
- Integration / API / controller layer after the logic it wraps
- UI / view layer after the data it renders
- Tests near the code they cover (or first, if the tests document intent more clearly than the implementation)
- Config, infra, manifest, build, and cosmetic changes last
- Skip generated files (lock files, compiled output, vendored deps)

If the commits already tell a clean story, recommend reading commit-by-commit instead of file-by-file, and note that in the comment.

**Comment format:**

```markdown
## Suggested Review Order

- `path/to/file-1.kt` — short reason this comes first
- `path/to/file-2.kt` — short reason this comes next
- `path/to/file-3.kt` — short reason
- ...
```

Keep each rationale to a short clause (roughly under 15 words). Do not restate the PR description. Do not list generated files. Use backticks around file paths.

**Post the comment** with `gh pr comment`, using the PR URL captured in step 7:

```bash
gh pr comment <PR-URL> --body "$(cat <<'EOF'
## Suggested Review Order

- `path/to/file-1.kt` — short reason this comes first
- ...
EOF
)"
```

After the comment is posted, output the PR URL so the user can open it.

## Common Mistakes

- Showing the PR title or description to the user for approval before opening the draft PR — the PR is a draft and the user reviews it on GitHub, so terminal-side approval is duplicate work. Only `RELEASES.md` drafts require explicit approval (because they get committed)
- Forgetting to extract the ticket number and using the raw branch slug as the title
- Using sentence case in the title — every word in the description portion must start with a capital letter
- Title over 72 characters
- Opening the PR without `--draft`
- Passing `--reviewer` — reviewer requests are the user's job after they take the PR out of draft
- Not pushing the branch before attempting to create the PR
- Leaving the template's HTML comment placeholders in the description instead of replacing them with content
- Forgetting the ticket link heading at the very top of the description
- Including the Labels and Review section from the PR template — it must be omitted
- Forgetting `--assignee "@me"`
- Including JIRA ticket numbers in `RELEASES.md` entries (release notes or QA notes) — tickets belong in the PR title and description, not in `RELEASES.md`
- Adding a release note for a change with no user-visible impact (refactor, dev-tooling, test-only)
- Adding QA notes for a change with nothing for a manual tester to verify
- Writing QA notes that require developer tooling (Android Studio, Logcat, adb, unit tests, internal storage inspection, etc.) — QA only has a phone build
- Bundling Release Notes and QA Notes into one commit, or bundling them with code changes — each `RELEASES.md` update is its own commit
- Committing a `RELEASES.md` change without first showing the user a draft of the bullet(s) and waiting for their approval
- Writing the Safety story as advocacy for the PR — it must list both confidence factors and unresolved risks neutrally
- Inventing testing the user did not actually do — ask them explicitly if it is unclear
- Writing the Safety story in the third person ("the author did X", "the user tested Y") — the PR is authored by the user, so descriptions of what they did must use "I"
- Padding PR description sections instead of keeping them concise
- Writing a Technical Summary that runs long (more than a few sentences or a short bulleted list), or that restates facts already obvious from the diff (file-by-file walkthrough, renamed identifiers, etc.)
- Keeping a section (Technical Summary, Product Description, Automated test coverage) when it would have no signal — drop the entire section, heading included, instead of filling it with boilerplate
- Writing QA notes as step-by-step user instructions ("open the app, tap login, enter credentials, ...") instead of a short checklist of what to verify
- Writing more QA bullets than necessary, or splitting one logical check across multiple bullets, or restating obvious happy-path behavior QA would test anyway
- Forgetting to post the Suggested Review Order comment after creating the PR
- Including generated files (lock files, compiled output, vendored deps) in the Suggested Review Order
- Listing files in the Suggested Review Order without any rationale, or with rationale longer than a short clause
