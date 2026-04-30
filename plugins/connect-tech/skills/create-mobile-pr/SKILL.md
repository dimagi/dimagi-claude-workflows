---
name: create-mobile-pr
description: Use when the user asks to create, open, or submit a GitHub pull request, or when implementation is complete and the user wants to push and open a PR
---

# Create GitHub Pull Request

## Overview

Open a draft GitHub pull request with a JIRA-prefixed title, a description generated from the repo's PR template, and the current user as assignee. The PR is opened as a draft so the user can review on GitHub and mark it ready for review (and request reviewers) themselves. QA notes go into `RELEASES.md`, not the PR description.

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
- `cat RELEASES.md` -- the current release file (used to find the active release section for QA Notes)

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

### 4. Update RELEASES.md with QA Notes

QA notes belong in `RELEASES.md`, not in the PR description.

1. Open `RELEASES.md` and find the **most recent release section** (the topmost `## CommCare X.YZ` heading).
2. Locate its `### QA Notes` subsection.
3. Append one or more bullet points describing what QA should manually verify for this change.

**Write QA notes for testers with phone access only.**

The QA team does **not** have access to developer tools. Assume their only tooling is:

- A build of the app installed on their phone
- The app's normal UI and any user-facing surfaces (settings, forms, Connect, PersonalID, etc.)
- Their own test accounts / test projects
- Server-side admin views they would normally use (e.g. HQ), if relevant to the feature

Do **not** write steps that require:

- Android Studio, Logcat, adb, or any IDE
- Reading source code, stack traces, or build artifacts
- Running unit tests, instrumentation tests, or scripts
- Inspecting databases, internal storage, or shared preferences directly
- Any tooling a developer would use but a manual tester would not

QA notes should read as user-level actions and observable outcomes: "do X in the app, expect Y to happen." If a regression cannot be observed without developer tools, say so and rely on automated coverage instead of writing an unrunnable QA step.

After updating `RELEASES.md`, stage and commit the change on the current branch with a short message such as `Add QA notes for TICKET-NUMBER`. Use a separate commit so it is easy to review.

### 5. Generate PR Description from the Template

Read `.github/PULL_REQUEST_TEMPLATE.md` and fill it out according to the instructions in the HTML comments of each section. Replace the HTML comments with actual content -- do not leave them in the final description.

**Prepend a ticket link heading at the very top of the description (before the first template section):**

- Format: `### [TICKET-NUMBER](https://dimagi.atlassian.net/browse/TICKET-NUMBER)`
- Example: `### [CCCT-2264](https://dimagi.atlassian.net/browse/CCCT-2264)`
- Display text is just the ticket number

For each template section, follow the guidance in its HTML comment, with these specific rules:

#### Safety story -- be neutral, not advocacy

The Safety story is **not** a defense of the PR. Do not stack arguments in favor of merging. Write it as a balanced risk assessment that lets a reviewer judge the change on its merits.

Structure the Safety story with two short lists:

- **What gives confidence:** concrete, factual reasons the change is likely safe -- e.g. the user's personal testing (from step 3, described in their own words), narrow scope of the diff, existing automated coverage that exercises the changed code paths, the change being behind a flag, etc. Only include items that are actually true; do not pad.
- **Risks to review:** honest risks the reviewer should consider -- e.g. data migrations, behavior changes for existing users, code paths not covered by automated tests, areas the author did not manually exercise, third-party integrations affected, performance-sensitive paths, error-handling changes, etc. If the author did limited testing, that itself is a risk and should be listed.

If a risk is genuinely mitigated, say *how* it is mitigated rather than dismissing it. If a risk is not mitigated, leave it in the list so the reviewer can decide whether to ask for more work.

#### QA Plan -- point to RELEASES.md

The QA Plan section in the PR description should not duplicate the QA notes. Replace it with a short pointer, for example:

> QA notes for this change have been added to the QA Notes section of [RELEASES.md](../RELEASES.md) under the current release.

If a QA ticket exists, link it here as well.

#### Other sections

Fill out Product Description, Technical Summary, and Automated test coverage from the diff, commits, and any user-provided context. Incorporate the user's testing description (from step 3) into the Safety story's "What gives confidence" list rather than fabricating details.

**Omit the Labels and Review section from the PR description.** Do not include its heading or body in the generated description.

### 6. Ensure Branch is Pushed

Check if the current branch has an upstream remote:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

If no upstream exists, push the branch:

```bash
git push -u origin HEAD
```

If the branch is behind the remote, push the latest commits (this will include the RELEASES.md commit from step 4):

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

After creation, output the PR URL so the user can see it.

## Common Mistakes

- Forgetting to extract the ticket number and using the raw branch slug as the title
- Using sentence case in the title -- every word in the description portion must start with a capital letter
- Making the title too long -- keep it under 72 characters total
- Opening the PR without `--draft`
- Passing `--reviewer` -- reviewer requests are the user's job after they take the PR out of draft
- Not pushing the branch before attempting to create the PR
- Leaving the template's HTML comment placeholders in the description instead of replacing them with content
- Forgetting the ticket link heading at the very top of the description
- Including the Labels and Review section from the PR template -- it must be omitted
- Forgetting `--assignee "@me"`
- Writing QA notes that require developer tooling (Android Studio, Logcat, adb, unit tests, internal storage inspection, etc.) -- QA only has a phone build
- Duplicating QA notes in the PR description's QA Plan section instead of pointing to RELEASES.md
- Writing the Safety story as advocacy for the PR -- it must list both confidence factors and unresolved risks neutrally
- Inventing testing the author did not actually do -- ask the user explicitly if it is unclear
