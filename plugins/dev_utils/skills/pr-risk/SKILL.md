---
name: pr-risk
description: Use when grading how risky a Dimagi mobile/CommCare pull request is and setting its risk label (Low Risk, Medium Risk, High Risk) — "grade the risk on this PR", "what risk label should this get", "regrade #4012 after my changes", "set the risk label". Called by `create-mobile-pr` before a PR opens; run it directly on an existing PR to grade it later or regrade it after changes.
---

# Grade PR Risk

Propose one risk level for a mobile PR, let the author confirm or override it, then record it as **exactly one** risk label plus one reason line in the Safety story. The label is optional: if the author declines, set nothing.

Labels: `Low Risk`, `Medium Risk`, `High Risk`. Never any other spelling.

## Two modes

- **Before the PR exists** (called from `create-mobile-pr`): grade the local branch, get the author's answer, and hand back the label and the reason line. `create-mobile-pr` puts them in `gh pr create`. Run steps 1, 2 and 4, then only the label check in step 5.1, since `gh pr create --label` fails on a label the repo lacks.
- **On an existing PR** (a number, URL, or the current branch's PR): run every step.

## 1. Gather

Before the PR exists:

```bash
git diff master...HEAD --stat
git diff master...HEAD
git log master..HEAD --oneline
```

On an existing PR:

```bash
gh pr view <PR> --json number,url,labels,body,files,commits
gh pr diff <PR>
```

Reuse what the caller already gathered instead of fetching it again, including the author's answer about their own testing. If there is no answer yet, ask: "What did you personally do to test this?" Never invent testing.

## 2. Grade

Pick the **highest** level any part of the change reaches. Weigh what the change can break and how likely that is, not how big the diff is.

**Core flows first.** `core-flows.md` lists the paths users take every day (CommCare login through sync, PersonalID signup, the Connect Opportunity flow). If the changed code runs on one of them, directly or through a caller, and a defect could block the user, lose their work or send wrong data, the grade is **High**, however small or isolated the change. Check reach by searching for callers of what changed, starting from the classes that file names. Copy, styling, logging or analytics on a core-flow screen does not count when it cannot block the flow; grade it as usual.

**High** — a defect could lose or corrupt data, lock users out, or break the app for everyone:
- A change on a core flow, as above.
- Database migrations, or anything that rewrites persisted data, form instances, or the user's saved state.
- Login, PersonalID, sessions, tokens, encryption, or keys.
- Sync, form submission, case restore, or other server round trips most users depend on.
- App startup and the launch path.
- Dependency, SDK, `targetSdk`, Gradle, or build-config upgrades.
- Removing or bypassing a feature flag or kill switch that guarded shipped behavior.

**Medium** — a defect would break one feature or change behavior existing users rely on:
- A behavior change for existing users in a single feature.
- Shared code with several callers, or a change to a public helper.
- Network error handling or a third-party integration.
- Perf-sensitive code (list rendering, startup work, large queries).
- New screens or flows that are not behind a flag.

**Low** — a defect would be cosmetic or easy to notice and harmless:
- Copy, strings, translations, layout, or styling.
- Logging or analytics events.
- Tests, docs, or comments only.
- New code behind a flag that is off by default.
- One call site in one module, off the core flows, with the author having run it.

Then adjust for testing: if the author only read the diff, or did not exercise the paths the change touches, raise Low to Medium. Testing never lowers a High.

`../create-mobile-pr/risk-categories.md` lists what usually matters in a Safety story; it informs the grade but is not a second rubric.

## 3. Read what is already there (existing PR only)

- **Current label:** any of the three risk labels on the PR. If there are several (from before this skill), note them all; step 5 removes the extras.
- **Earlier reason line:** the line starting `**Risk:` in the Safety story. If it reads `(author's call; graded <Level>)`, the author overrode an earlier grade.

## 4. Ask the author

Show the proposal in this shape and wait:

> Proposed risk: **Medium**. Behavior change in the delivery list for every existing Connect user.
> Currently labeled: Low Risk. *(existing PR only)*
>
> Keep Medium, pick Low or High, or skip the label?

**An earlier author override stands** unless the dev changes it: propose the author's level again, and show the new grade beside it ("graded Low now; you set Medium last time"). Don't argue the grade back up or down.

Then build the **reason line**:

- Author kept the grade: `**Risk: Medium.** <reason>`
- Author overrode it: `**Risk: High** (author's call; graded Medium). <reason>` — the reason is the author's, in their words if they gave one, otherwise the grader's reason for the level they picked.

**Budget:** the reason is ≤15 words, says why this level and nothing the label already says. Lead with the risky thing, not the file name. When a core flow made it High, name the flow: `**Risk: High.** Changes case list filtering on the case selection core flow.`

If the author skips the label, there is no reason line either. On an existing PR, ask whether to also remove the current risk label and reason line; do only what they say.

## 5. Apply

One `gh pr edit` swaps the label and rewrites the body, so the PR never carries two risk labels.

1. **Label exists?** (both modes) `gh label list --search Risk --json name`. Create the chosen label if the repo lacks it, and nothing else:

   ```bash
   gh label create "Low Risk"    --color 0E8A16 --description "Small blast radius; unlikely to break existing behavior"
   gh label create "Medium Risk" --color FBCA04 --description "Changes existing behavior or shared code; worth a careful review"
   gh label create "High Risk"   --color FF0000 --description "If the PR introduce high risk changes that has high probability of introducing breaking changes"
   ```

   Never `--force`: it would rewrite a label the repo already has.

2. **Body.** Write the PR body to a temp file with the reason line in place:
   - Replace the existing `**Risk:` line if there is one.
   - Otherwise insert it as the first line under the Safety story heading (`## Safety story` or `### Safety story`), followed by a blank line.
   - No Safety story section: add `## Safety story` with just the reason line, after the ticket link.
   - Touch nothing else in the body.

3. **One edit:**

   ```bash
   gh pr edit <PR> --add-label "Medium Risk" --remove-label "Low Risk" --body-file <tmp>
   ```

   Pass `--remove-label` for every other risk label on the PR, and omit it when there is none. If the level is unchanged, skip the label flags and only rewrite the body if the reason line changed. If nothing changed, skip the edit.

Then report the level, the label change (`Low Risk → Medium Risk`), and the PR URL.

## Hard rules

- At most one of `Low Risk`, `Medium Risk`, `High Risk` on a PR after this skill runs.
- The author confirms or overrides before anything is labeled; never label on the grade alone.
- An earlier author override is kept unless the dev changes it.
- Label swap and body rewrite happen in one `gh pr edit`.
- Never touch labels other than the three risk labels, and never recolor or rename an existing label.
- Don't backfill old PRs. Grade a PR only when asked.
