---
description: Generate a comprehensive reading guide for a pull request — includes a narrative reading order, architecture impact analysis, review comment summary, prior state context, and potential concerns ranked by risk.
argument-hint: <pr-link-or-number>
allowed-tools: Bash(gh pr view:*), Bash(gh pr diff:*), Bash(gh api:*), AskUserQuestion
disable-model-invocation: true
---

# PR Review Guide

You are a senior engineer helping me understand a pull request. Your goal is to figure out the **best reading order** so I can understand the new code as clearly as possible — not just a file list, but a narrative path through the changes.

## Step 1: Gather full PR context

If the argument (`$0`) is a full URL, extract the PR number and repo from it (use `--repo owner/repo` with `gh`). If it's just a number, assume the current repo. If any command fails (auth issues, PR not found), stop and tell the user what went wrong before continuing.

Collect ALL of the following:

1. **PR description and metadata:**
   !`gh pr view $0 --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles,labels,milestone`

2. **Full diff:**
   !`gh pr diff $0`

3. **PR-level comments (conversation):**
   !`gh pr view $0 --json comments`

4. **Review summaries and inline review comments:**
   !`gh pr view $0 --json reviews,reviewDecision`
   For inline (line-level) review comments, use the REST API. First, determine the owner, repo, and PR number from the argument (e.g., `https://github.com/acme/widgets/pull/42` → owner=acme, repo=widgets, number=42). Then fetch the raw JSON:
   `gh api repos/<owner>/<repo>/pulls/<number>/comments --paginate`
   This command does NOT have the `!` prefix because the placeholders must be substituted first. Extract the owner, repo, and PR number from the argument, substitute them, then run the command. Use `--paginate` to ensure all comments are fetched (the API returns at most 30 per page by default).

5. **Commit history:**
   !`gh pr view $0 --json commits`

Once all data is collected, tell the user: "I have all the PR context. Analyzing now."

## Step 2: Analyze and build a reading guide

Analyze the gathered context and produce a **Reading Guide** with the following structure:

### Overview
- One-paragraph summary of what this PR does and why
- Size assessment (trivial / small / medium / large / massive)
- Key areas of the codebase affected

### Review Comments Summary
If there are existing review comments or inline discussions, briefly summarize the key threads and whether they've been resolved. This context is important to have before diving into the code, so the reader knows what's contentious. If there are no comments, skip this section.

### Prior State
Briefly describe how the system worked **before** this PR. Mental models are built on contrast — the reader needs to understand "it used to work like X, now it works like Y." Focus on the parts of the system that this PR changes. Keep it to 2-4 sentences.

### Architecture Impact
Before listing the reading order, assess architectural changes:
- **What architectural patterns or boundaries does this PR touch?** (e.g., new service layer, changed data flow, modified API contract, new dependency between modules)
- **Does this PR introduce, modify, or remove any architectural components?** (e.g., new middleware, changed state management approach, altered pub/sub topology)
- **Are there any shifts in responsibility between layers or modules?**

If the PR has meaningful architectural impact, call it out clearly. If it's a localized change with no architectural significance, say so briefly and move on.

### Reading Strategy

Before producing the reading order, determine which strategy fits this PR best:

**Strategy A — Single linear path (default).** Use when the PR has one coherent flow: a refactor, a single feature addition, a bug fix. Most PRs fall here.

**Strategy B — Multiple perspectives.** Use when the PR touches code that participates in distinct flows. Common signals:
- Both user-facing code (forms, templates, UI) and API/external-service code (serializers, API views, webhooks) are changed
- Both read paths and write paths are modified
- The PR integrates a new service that has both an inbound flow (receiving data) and an outbound flow (sending data)
- Changes span both a CLI interface and a web interface to the same logic

When you detect multiple perspectives, present them to the user with `AskUserQuestion`:

> This PR has changes that participate in multiple distinct flows:
> 1. **[Flow name]** — [1-sentence description, e.g., "the path a user follows when configuring the service through the admin UI"]
> 2. **[Flow name]** — [1-sentence description, e.g., "the path an external webhook follows when it hits the ingest API"]
> 3. **All perspectives** — walk through each flow one after another
>
> Which perspective would you like to start with?

Then produce a reading order for the chosen perspective. Shared files (e.g., models) appear in every perspective but are framed differently — note what to pay attention to for *this specific flow*. After completing one perspective, ask if the user wants to continue with another.

**Strategy C — Tests-first.** Use when the PR is primarily a behavior change, bug fix, or the tests are unusually clear about intent. In this strategy, start with the test files to establish *what* the code should do, then follow with the implementation to see *how* it does it.

### Recommended Reading Order

**For large PRs (>20 files):** Group files into logical changesets by feature or concern first, then provide a reading order within each group.

**Skip generated files** (lock files, compiled output, vendored dependencies) unless the PR description specifically calls them out.

For each step in the reading order, provide:
1. **File(s)** to read and which hunks/lines matter
2. **Why this comes at this point** in the reading order (e.g., "this defines the data model everything else depends on")
3. **The code** — include the relevant diff hunks inline (from the diff gathered in Step 1). The user should be reading actual code at every step, not just descriptions of it. Show the key changes, not the entire file diff — trim to the hunks that matter for this step.
4. **What to pay attention to** — the key decisions, patterns, or tricky bits
5. **Architecture notes** — if this step introduces or changes architectural patterns, boundaries, or cross-cutting concerns, highlight them here (e.g., "this adds a caching layer between the service and repository", "this changes the auth middleware chain"). Skip this for steps with no architectural relevance.
6. **Relationship** to previous steps — categorize it: **depends on** (this builds on something introduced earlier), **parallel to** (independent concern at the same layer), **refines** (extends or specializes something already seen), or **enables** (later steps won't make sense without this)

Use these heuristics for ordering:
- Read deleted/replaced code before its replacement to understand what changed
- Read new types/interfaces before their consumers
- Read renamed/moved files before files that were modified in-place
- Schema / data model changes first
- Core logic / domain layer next
- Integration / API / controller layer
- Tests and validation (unless using Strategy C, where tests come first)
- Config, infra, and cosmetic changes last

If commits tell a clean story (i.e., the author structured them intentionally), consider recommending a commit-by-commit reading order instead and say why.

### Core Transformation
In one sentence, state the core transformation this PR makes: "Before this PR, [X]. After this PR, [Y]." This forces synthesis and gives the reader a single anchor to hold the whole PR against.

### Potential Concerns
List the **top 3–5 concerns**, ordered by risk. For each, state:
- What the concern is
- What could go wrong
- How to verify it (e.g., "check if X is tested", "confirm Y handles the nil case")

Include things like: risky patterns, missing tests, unclear naming, large files that could be split, **architectural red flags** (tight coupling, abstraction leaks, circular dependencies, layer violations).