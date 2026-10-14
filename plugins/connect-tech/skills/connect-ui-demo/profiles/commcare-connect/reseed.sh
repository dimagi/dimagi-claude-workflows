#!/bin/bash
# reseed.sh — reset demo data (org, users, invites). Idempotent; safe to run before every take.
set -u
PROFILE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="${CONNECT_REPO:-$(git -C "$PROFILE_DIR" rev-parse --show-toplevel)}"
cd "$REPO" || { echo "repo not found: $REPO"; exit 1; }
# shellcheck disable=SC1091
source .venv/bin/activate || { echo "no .venv in $REPO — run: uv sync"; exit 1; }
PYTHONPATH="$PROFILE_DIR" DJANGO_SETTINGS_MODULE=record_settings ./manage.py shell < "$PROFILE_DIR/seed.py" 2>&1 | tail -1
