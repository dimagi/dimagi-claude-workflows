# Reading pending review comments via the GitHub API

How to read the comments in an unsubmitted ("pending") PR review. Verified live against
`dimagi/commcare-hq#37998`.

This is read-only. The pair-review skill never writes to GitHub — no comments, no reviews,
no replies — so nothing here posts anything. Adding a comment to a pending review is
possible via GraphQL, but deliberately out of scope: the review is published under the
user's name and should be written by them.

A pending review is visible **only to its author**, which is what makes this work — you
can read the user's in-progress thinking, and nobody else can. There is no `gh`
subcommand for any of it, so it's raw `gh api` throughout.

## Finding the pending review

```bash
gh api repos/<owner>/<repo>/pulls/<N>/reviews --paginate \
  --jq '.[] | select(.state=="PENDING") | {id, node_id}'
```

A user has at most one pending review per PR, so this returns zero or one result. Zero
just means they haven't started commenting — not an error.

## Listing its comments

```bash
gh api repos/<owner>/<repo>/pulls/<N>/reviews/<review_id>/comments --paginate \
  --jq '.[] | {id, path, original_commit_id, original_position, body, diff_hunk}'
```

Group by `original_commit_id` for per-commit progress. Track `id` values so you can tell
later which comments are new.

## Showing the user which code a comment refers to

`diff_hunk` carries the surrounding code with the comment, so quote that — it's the whole
context, already fetched, with no arithmetic involved. This is almost always what you
want.

Be aware `diff_hunk` can include a line of trailing context past the anchored line, so
don't present its last line as "the line you commented on" with any confidence. If you
need the anchor exactly, `original_position` is a 1-based offset into that file's diff for
`original_commit_id`, counted from the file's first `@@` header and including hunk headers:

```bash
git show <original_commit_id> --format="" --unified=3 -- <path> \
  | awk '/^@@/{s=1} s{n++; printf "%3d| %s\n", n, $0}'
```

`--unified=3` matters — it matches GitHub's context size. Verified against three real
comments on commit `d69477ad`: positions 21, 45 and 55 each landed on exactly the expected
line.

This counting does not hold for merge commits, where `git show` produces a combined diff.

## Traps

- `line`, `side`, `start_line` and `original_line` are all `null` on pending comments.
  GitHub only resolves line numbers when a review is submitted, so there is no line number
  to read — use `diff_hunk`, or `original_position` with the recipe above.
- `GET /repos/{o}/{r}/pulls/comments/{id}` returns **404** for a pending comment, because
  it isn't published yet. The review-scoped listing is the only way to fetch one.
- `GET /pulls/{N}/comments`, which lists a PR's review comments, does **not** include
  pending comments. Use it for already-published discussion, not for the user's draft.
- After a force-push, pending comments can reference commits no longer in the PR. Check
  each `original_commit_id` against the current commit list; if one is missing, tell the
  user rather than silently mapping it onto the wrong commit.
