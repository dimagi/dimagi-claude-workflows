#!/bin/bash
# Show test failures for a GitHub Actions CI run on a PR.
# Usage: scripts/pr-failures.sh [<pr_number> [<repo>]]
# If no PR number is given, uses the current branch's open PR.
# If no repo is given, uses the current directory's repo.

set -euo pipefail

if ! command -v gh &>/dev/null; then
    echo "Error: 'gh' (GitHub CLI) is not installed." >&2
    echo "Install it from https://cli.github.com/" >&2
    exit 1
fi

PR=${1:-}
REPO=${2:-$(gh repo view --json nameWithOwner -q ".nameWithOwner")}

gh_exit=0
if [[ -n "$PR" ]]; then
    FAILED=$(gh pr checks "$PR" --repo "$REPO" | awk -F'\t' '$2 == "fail"') || gh_exit=$?
else
    FAILED=$(gh pr checks | awk -F'\t' '$2 == "fail"') || gh_exit=$?
fi

# Non-zero exit + no tab-separated output = real gh error (already printed to stderr)
if [[ $gh_exit -ne 0 && -z "$FAILED" ]]; then
    exit 1
fi

if [[ -z "$FAILED" ]]; then
    echo "No failed checks${PR:+ for PR #$PR}."
    exit 0
fi

echo "Failed checks:"
echo "$FAILED" | awk -F'\t' '{print "  " $1}'

# Extract run ID + job ID pairs from GitHub Actions URLs (runs/<id>/job/<id>)
# Format: "<run_id> <job_id>" per line
RUN_JOB_PAIRS=$(echo "$FAILED" | grep -oE 'runs/[0-9]+/job/[0-9]+' \
    | sed 's|runs/\([0-9]*\)/job/\([0-9]*\)|\1 \2|' | sort -u) || true

if [[ -z "$RUN_JOB_PAIRS" ]]; then
    echo ""
    echo "Could not extract run/job IDs. Check URLs manually:"
    echo "$FAILED" | awk '{print "  " $NF}'
    exit 1
fi

echo ""
echo "Failures:"
while IFS=' ' read -r RUN_ID JOB_ID; do
    gh api "repos/$REPO/actions/jobs/$JOB_ID/logs" 2>&1 \
        | sed 's/^[0-9T:.-]*Z //' \
        | grep -E "(^FAILED |##\[error\])" || true
done <<< "$RUN_JOB_PAIRS"
