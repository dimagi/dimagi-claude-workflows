---
name: pair-review
description: Interactively review a GitHub PR commit by commit, together with the user, in a dedicated `review` worktree. Use this whenever the user drops a PR link and wants to go through it *with* you rather than have it reviewed *for* them — "pair review this PR", "let's review this one together", "walk me through PR 123 commit by commit", or a PR URL plus "review this with me". The user reads the code and writes their own comments in GitHub; you explain what each commit and each line does, answer follow-ups against a real checkout, and read their pending review back to them. Never writes to GitHub. For a hands-off automated review with no user in the loop, use the code-review skill instead.
argument-hint: <pr-link-or-number>
---

# Pair Review

Review a PR **with** the user, one commit at a time. They drive. You explain.

This is not an audit and not a report. The user reads the code themselves and leaves
their own comments in GitHub. Your job is to orient them at each commit, then answer
whatever they ask — what a line does, who calls this function, what it looked like
before, why a test is or isn't there.

**Always review commit by commit.** Never reorganise the PR into a file-based reading
order, because commits are what the user's comments anchor to — a reading order that
cuts across them makes the review harder to record, not easier to follow. (If they do
want a narrative reading guide, point them at `/pr-walkthrough`; the two compose well in
that order.)

You make no writes to GitHub in this skill — no comments, no reviews, no replies. The
review is the user's, published under their name, so every word of it should be theirs.
You read their in-progress review to stay in sync with it.

---

## Step 1: Resolve the PR

From the argument, get `owner`, `repo`, `number`. A bare number means the current repo.

```bash
gh api repos/<owner>/<repo>/pulls/<number> \
  --jq '{title, state, headRefName, baseRefName, head_sha: .head.sha, author: .user.login, additions, deletions, changed_files}'
gh api repos/<owner>/<repo>/pulls/<number>/commits --paginate \
  --jq '.[] | {sha, message: (.commit.message | split("\n")[0]), parents: (.parents|length)}'
```

The commits endpoint returns them in order — that's the review order. Any commit with
more than one parent is a merge commit; mark it in the map and skip it, since its diff is
a combined diff that reads confusingly out of context.

If either call fails, stop and report why (auth, wrong repo, PR not found) rather than
guessing.

## Step 2: Locate and prepare the worktree

Find a checkout of `<owner>/<repo>`, preferring a worktree named `review`:

1. If the cwd is inside a git repo whose `origin` matches `<owner>/<repo>`, start there.
2. Otherwise look under `~/projects`, `~/code`, `~/tools`, including `*-worktrees/`
   layouts, which are common here (e.g.
   `~/projects/commcare/code/commcare-hq-worktrees/`). Confirm a candidate by checking
   its remote actually matches — a directory name is not proof.
3. From any worktree or the bare repo, run `git worktree list --porcelain` and pick the
   one whose directory basename is `review`.
4. If nothing turns up, ask the user where to check out. Ask once; don't guess a path.

**Safety gate, before touching anything:** if the review worktree has uncommitted changes
(`git -C <wt> status --porcelain` is non-empty), stop and ask. Work in progress there is
probably someone's half-finished thought, and no review is worth destroying it — never
stash, reset, clean, or checkout over it to make room.

Then check out the PR head, detached:

```bash
git -C <wt> fetch origin "refs/pull/<N>/head"
git -C <wt> checkout --detach FETCH_HEAD
```

`refs/pull/<N>/head` works for PRs from forks, not just same-repo branches. Detaching
avoids three separate failure modes: the PR's branch already being checked out in another
worktree, a stale local branch of the same name getting clobbered, and force-pushes
needing special handling on re-run. Nothing here needs a branch name, since GitHub is
always addressed by explicit repo and PR number.

Confirm `git -C <wt> rev-parse HEAD` matches the PR's `head_sha` before going further. If
it doesn't, say so rather than reviewing the wrong code.

Every later `git` call runs with `-C <wt>`.

## Step 3: Load the pending review

Read the user's in-progress review — see `references/github-pending-reviews.md` for the
endpoints and their traps, which are not guessable and worth reading before you touch
comments.

Group the comments by `original_commit_id`. That grouping is the progress state: it lives
in GitHub, needs no local file, and survives across sessions and machines.

Note the comment IDs you've seen. You'll diff against them later when the user adds more,
and an exact ID set beats trying to remember bodies. If the session runs long, jot them in
your scratchpad.

## Step 4: Kickoff

First, review the full PR diff with all commits applied to see what the final state looks
like. Use `git merge-base <head_sha> origin/<baseRefName-or-default-branch>`, and cross-
check the resulting diffstat against the PR API's additions/deletions/changed_files. When
the diff is very large, read the substantive files first rather than streaming the whole
diff; the goal is to understand it, not to have seen every line of it. Keep the learnings
in mind when reviewing individual commits, especially to note issues with earlier commits
that are fixed in subsequent commits. When such issues are noticed, flag them once; don't
re-raise the same resolved-later note on each subsequent commit unless asked.

Then two things, briefly:

1. **Three sentences** on what the PR does overall. Not a report, not headings.
2. **The commit map**, with comment counts, marking where you're starting:

```
1  1cde3eb2  Add LLM integration scaffolding      2 files   [2 comments]
2  86a3ca3a  Introduce translation format         5 files   [1 comment]
3  944f1b4b  Wire config through settings         3 files   [1 comment]
4  40a2e1b9  Add URL preservation check           1 file    [1 comment]
5  935f764c  Prompt tuning                        1 file    [1 comment]
6  d69477ad  Structure-preservation checks        2 files   [3 comments]
7  881bfe02  Wire up translate_app command        4 files   —
→ starting at commit 7
```

File counts come from git once the worktree is ready (`git show --stat --format= <sha>`),
not from the API. For a PR with many commits, keep the map to one line each and don't
elaborate — it's a table of contents, and the user will tell you where to go.

Start at the earliest commit with no comments. Mention the limitation only if it seems
to matter: a commit the user read and had nothing to say about looks identical to one
they never opened, so invite them to redirect you if the resume point is wrong.

## Step 5: The per-commit loop

Read the commit properly before saying anything about it — `git show <sha> --stat`, then
the diff, and open the surrounding file when the diff alone doesn't explain itself. For a
large commit, read the substantive files first rather than streaming the whole diff; the
goal is to understand it, not to have seen every line of it. Then:

```
── Commit 4/7 ── 40a2e1b9
  "Add URL preservation check"

What it does
  Adds is_valid_app_translation() and wires it into the translate
  loop; failures fall back to the source string.

Worth a look
  • URL_PATTERN is compiled per call, not module level — hot path?
  • No test for the fallback branch.

What do you want to dig into?
```

- **What it does** — 2–4 sentences: what changed, and why it needed to. Name the
  non-obvious behaviour change if there is one.
- **Worth a look** — only when you actually spot something: a bug, an unhandled case, a
  silent behaviour change, a missing test. One line each, three at most. Omit the section
  entirely when the commit is clean; padding it trains the user to skim past it. This is
  your opinion, and it stays visually separate from the explanation so they can tell it
  from fact.
- **Then stop.** Don't roll on to the next commit unprompted — the user needs time to read
  and write, and that pause is the whole point of pairing.

If the commit already has pending comments, show them before your questions so the user
can see what they said last time.

You have the full worktree, so answer follow-ups with evidence rather than inference:
`git log -L` for a function's history, `git blame`, grep for callers, read the
pre-change version at `<sha>^`. Speculating about code you could simply go read wastes the
user's attention.

Let the user navigate: "next", "back to 3", "skip to the one touching views.py", "just
show me the diff". Follow their lead.

Don't run tests or linters on your own initiative — it's slow and usually not what the
question needed. Offer when a question genuinely turns on it, then wait to be told yes.

## Step 6: Staying in sync with their comments

When the user says they've commented — "ok I left a note", "added a few thoughts" —
re-read the pending review, diff it against the IDs you already had, and show what's new.

Then use it. Don't re-explain a point they've already made, and do speak up when a later
commit answers a question they raised earlier — that connection is easy for them to miss
while reading one commit at a time, and it's one of the more useful things you can offer.

If they ask you to help word something, write the comment text and name the file and line
it belongs on, so they can paste it. They post it themselves.
