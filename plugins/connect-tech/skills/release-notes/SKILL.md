---
name: release-notes
description: >
  Generates Markdown release notes for the most recent release of a GitHub repository.
  Given a GitHub repo URL (or owner/repo), this skill finds the latest two releases, collects
  all PRs merged between them, categorizes each change as New / Improvement / Fix / Infra / Docs,
  and produces a clean, grouped Markdown file saved to the outputs folder.

  Use this skill whenever the user asks to "generate release notes", "write a changelog",
  "summarize what changed in the last release", "what was in the last release", or similar.
  Also trigger when the user provides a GitHub repo URL or owner/repo string alongside any
  mention of releases, PRs, or changelogs. The skill works for any public or private GitHub
  repo accessible via the user's `gh` CLI session.
---

# Release Notes Skill

You are generating release notes for the most recent release of a GitHub repository. The goal is a clean, human-readable Markdown summary of what changed — the kind of thing you'd send to stakeholders or post in a changelog.

## Inputs

The user will provide a GitHub repo — either as a full URL (`https://github.com/owner/repo`) or an `owner/repo` string. Extract the `owner/repo` identifier from whatever they provide.

If the user specifies a product name to use in the title, use that. For the `dimagi/commcare-connect` repo, the product name is **"Connect"** (not "CommCare Connect").

## Terminology

When writing user-facing release notes, use the correct user-facing terms — not internal code names:

| Use this | Not this |
|---|---|
| PersonalID | ConnectID |

If you encounter other code-level identifiers in PR titles or bodies, use your judgment: if it reads like an internal variable name or database field rather than a product concept, rephrase it into plain language.

## Step 1: Find the releases

```bash
gh release list --repo <owner/repo> --limit 5
```

Identify the **latest release** (most recent) and the **previous release** (the one before it). Note the tag names and published dates of both.

## Step 2: Find merged PRs between the releases

Use the published dates of the two releases to filter merged PRs:

```bash
gh pr list \
  --repo <owner/repo> \
  --state merged \
  --search "merged:YYYY-MM-DD..YYYY-MM-DD" \
  --json number,title,author,mergedAt,labels \
  --limit 100
```

Use the previous release date as the start and the latest release date as the end.

## Step 3: Fetch PR details

For each PR, fetch the title and body to understand what it does:

```bash
gh pr view <number> --repo <owner/repo> --json title,body,labels
```

Read the body — not just the title — to get the actual description of what changed. The first few sentences of the body (often under a "Product Description" or similar heading) are usually the most useful.

Batch these requests efficiently — there's no need to fetch one at a time if you can parallelize.

## Step 4: Categorize and group

Assign each PR one of these categories based on what it does:

- **`New`** — A brand-new feature or capability that didn't exist before
- **`Improvement`** — An enhancement, refinement, or extension of something existing
- **`Fix`** — A bug fix or correction
- **`Infra`** — Infrastructure, performance, configuration, or DevOps changes
- **`Docs`** — Documentation-only changes

Then group related PRs into logical **sections** by feature area (e.g., "Work Areas", "Notifications & Email", "Reporting"). If several PRs all touch the same feature, they belong in the same section. A section with only one item is fine. Don't force unrelated things together.

Skip PRs that are purely internal (e.g., dependency bumps, version bumps, CI config) unless they're meaningful to users.

## Step 5: Write the release notes

Use this format:

```markdown
# Release Notes — {Product Name} v{version}
*Released {date}*

---

## {Section Name}

**`New`** **Feature Title** — One or two sentence description of what changed and why it matters. [Screenshots](PR_URL)

**`Improvement`** **Feature Title** — Description.

---

## {Section Name}

**`Fix`** **Feature Title** — Description.
```

Guidelines:
- **Feature Title**: A short noun phrase describing the change (not the PR title verbatim — rephrase if needed to be user-facing).
- **Description**: Write for a non-technical stakeholder. What does the user now see or experience? Avoid implementation details unless they matter to the user. Keep it to one or two sentences.
- **Links**: If a PR has screenshots in its body, add `[Screenshots](PR_URL)`. If there are relevant Confluence/docs links you know about, add them too. Don't make up links.
- **Order**: Lead with the most impactful / user-visible sections. Bug fixes and infra go at the end.

## Step 6: Save the output

Save the file to `./outputs/release_notes_{version}.md`, creating the `outputs/` directory if it doesn't exist.

Then tell the user the file path where the notes were saved.
