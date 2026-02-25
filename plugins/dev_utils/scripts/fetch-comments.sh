#!/usr/bin/env bash
# fetch-comments.sh — gather all PR review data and emit JSON to stdout.
#
# Usage: fetch-comments.sh <owner> <repo> <pr_number>
#
# Output (written to stdout as three top-level JSON keys):
#   {
#     "inline_comments": [...],   # REST pull-request review comments
#     "issue_comments":  [...],   # REST PR-level issue comments
#     "threads":         [...]    # GraphQL review threads with resolution status
#   }
#
# Exit codes: 0 = success, 1 = wrong args, 2 = gh not found / not authed.

set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <owner> <repo> <pr_number>" >&2
  exit 1
fi

OWNER="$1"
REPO_NAME="$2"
PR_NUMBER="$3"
REPO="$OWNER/$REPO_NAME"

if ! command -v gh &>/dev/null; then
  echo "Error: gh CLI not found" >&2
  exit 2
fi

if ! gh auth status &>/dev/null; then
  echo "Error: gh not authenticated — run 'gh auth login'" >&2
  exit 2
fi

# ── 1. Inline review comments (REST) ─────────────────────────────────────────
INLINE=$(gh api "repos/$REPO/pulls/$PR_NUMBER/comments" \
  --paginate \
  --jq '[.[] | {id, in_reply_to_id, user: .user.login, path, line, body, html_url}]')

# ── 2. PR-level issue comments (REST) ────────────────────────────────────────
ISSUE=$(gh api "repos/$REPO/issues/$PR_NUMBER/comments" \
  --paginate \
  --jq '[.[] | {id, user: .user.login, body, html_url}]')

# ── 3. Review threads + resolution status (GraphQL) ──────────────────────────
# NOTE: multiline -f query='...' fails with "UNKNOWN_CHAR" in gh; use single-line.
THREADS=$(gh api graphql \
  -f query="{repository(owner:\"$OWNER\",name:\"$REPO_NAME\"){pullRequest(number:$PR_NUMBER){reviewThreads(first:100){nodes{id isResolved comments(first:1){nodes{databaseId body}}}}}}}" \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[]
         | {thread_id: .id, isResolved, comment_id: .comments.nodes[0].databaseId}]')

# ── Merge into a single JSON object ──────────────────────────────────────────
jq -n \
  --argjson inline  "$INLINE" \
  --argjson issue   "$ISSUE" \
  --argjson threads "$THREADS" \
  '{inline_comments: $inline, issue_comments: $issue, threads: $threads}'
