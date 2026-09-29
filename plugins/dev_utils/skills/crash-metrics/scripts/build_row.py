#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Validate scraped Crashlytics metrics and assemble the spreadsheet row.

Reads a JSON payload on stdin, writes a preview table plus the exact
updateGoogleSheet arguments to stdout. Exits non-zero if validation fails.

Usage:
    uv run build_row.py [--sheet-id ID] < payload.json

The target spreadsheet is taken from --sheet-id, or the CRASH_METRICS_SHEET_ID
environment variable. It is deliberately not hardcoded: this repo is public.

Payload shape:
{
  "app": "commcare" | "lts",
  "next_row": 28,
  "date": "2026-09-03",              # optional, defaults to today
  "prev_row": ["3 Aug, 2026", ...],  # optional, columns A:M from the sheet
  "views": {
    "crash_90d": {<extractor output>},
    "crash_30d": {...},
    "anr_90d":   {...},
    "anr_30d":   {...}
  }
}
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date

TABS = {"commcare": "CommCare Crashes", "lts": "CommCare LTS Crashes"}
GOAL, ALERT = "95.00%", "93.50%"
FLAG_PCT = 20.0

COUNT_RE = re.compile(r"^[\d.]+[KM]?$")
PCT_RE = re.compile(r"^\d+\.\d+$")

# view key -> (expected eventType, expected window)
VIEWS = {
    "crash_90d": ("Crashes", 90),
    "crash_30d": ("Crashes", 30),
    "anr_90d": ("ANRs", 90),
    "anr_30d": ("ANRs", 30),
}

HEADERS = [
    "Date", "90d Crash free Users", "Goal", "Alert in slack",
    "90d Crashes", "90d Crash users", "30d Crash free Users",
    "30d Crashes", "30d Crash users", "90d ANR", "90d ANR Users",
    "30d ANR", "30d ANR Users",
]
COLS = "ABCDEFGHIJKLM"


def fail(errors):
    print("VALIDATION FAILED\n", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)


def expand(v):
    """'2.7K' -> 2700.0, '741' -> 741.0. Returns None if unparseable."""
    m = re.fullmatch(r"([\d.]+)([KM]?)", v.strip())
    if not m:
        return None
    try:
        n = float(m.group(1))
    except ValueError:
        return None
    return n * {"": 1, "K": 1_000, "M": 1_000_000}[m.group(2)]


def fmt_date(iso):
    d = date.fromisoformat(iso) if iso else date.today()
    return f"{d.day} {d:%b}, {d.year}"


def validate(views):
    errors = []
    for key, (want_type, want_days) in VIEWS.items():
        v = views.get(key)
        if not v:
            errors.append(f"{key}: missing from payload")
            continue

        if v.get("stillLoading"):
            errors.append(f"{key}: page still loading - re-run the extractor")

        got_type = v.get("eventType")
        if got_type != want_type:
            errors.append(
                f"{key}: eventType is {got_type!r}, expected {want_type!r} "
                "(URL was likely rewritten - check types= casing)"
            )

        rng = v.get("range") or ""
        if f"Last {want_days} days" not in rng:
            errors.append(f"{key}: range is {rng!r}, expected 'Last {want_days} days'")

        for field in ("events", "users"):
            raw = v.get(field)
            if raw is None:
                errors.append(f"{key}.{field}: null - extractor found no value")
            elif not COUNT_RE.match(str(raw)):
                errors.append(f"{key}.{field}: {raw!r} is not a valid count")

        if key.startswith("crash_"):
            pct = v.get("crashFreeUsersPct")
            if pct is None:
                errors.append(f"{key}.crashFreeUsersPct: null - tile not read")
            elif not PCT_RE.match(str(pct)):
                errors.append(f"{key}.crashFreeUsersPct: {pct!r} is not a valid percentage")
    return errors


def assemble(views, iso_date):
    c90, c30 = views["crash_90d"], views["crash_30d"]
    a90, a30 = views["anr_90d"], views["anr_30d"]
    return [
        fmt_date(iso_date),
        f"{c90['crashFreeUsersPct']}%",
        GOAL,
        ALERT,
        c90["events"], c90["users"],
        f"{c30['crashFreeUsersPct']}%",
        c30["events"], c30["users"],
        a90["events"], a90["users"],
        a30["events"], a30["users"],
    ]


def deltas(row, prev):
    """Yield (col, header, prev, new, note) for each column."""
    out = []
    for i, (col, hdr, new) in enumerate(zip(COLS, HEADERS, row)):
        old = prev[i] if prev and i < len(prev) else ""
        note = ""
        if old and new and i not in (0, 2, 3):
            if new.endswith("%") and old.endswith("%"):
                try:
                    diff = float(new[:-1]) - float(old[:-1])
                    note = f"{diff:+.2f}pp"
                except ValueError:
                    pass
            else:
                a, b = expand(old), expand(new)
                if a and b:
                    pct = (b - a) / a * 100
                    note = f"{pct:+.0f}%" + ("  <-- FLAG" if abs(pct) > FLAG_PCT else "")
        out.append((col, hdr, old, new, note))
    return out


def resolve_sheet_id(explicit):
    sheet_id = explicit or os.environ.get("CRASH_METRICS_SHEET_ID")
    if not sheet_id:
        fail(["no spreadsheet id: pass --sheet-id or set CRASH_METRICS_SHEET_ID"])
    return sheet_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet-id", default=None,
                        help="target spreadsheet id "
                             "(default: $CRASH_METRICS_SHEET_ID)")
    args = parser.parse_args()
    sheet_id = resolve_sheet_id(args.sheet_id)

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        fail([f"stdin is not valid JSON: {e}"])

    app = payload.get("app")
    if app not in TABS:
        fail([f"app must be one of {sorted(TABS)}, got {app!r}"])

    next_row = payload.get("next_row")
    if not isinstance(next_row, int) or next_row < 2:
        fail([f"next_row must be an integer >= 2, got {next_row!r}"])

    views = payload.get("views") or {}
    errors = validate(views)
    if errors:
        fail(errors)

    row = assemble(views, payload.get("date"))

    # Formula-injection guard: the write uses USER_ENTERED.
    bad = [v for v in row if str(v).lstrip().startswith(("=", "+", "@"))]
    if bad:
        fail([f"value would be parsed as a formula: {v!r}" for v in bad])

    prev = payload.get("prev_row")
    rows = deltas(row, prev)
    tab = TABS[app]
    rng = f"{tab}!A{next_row}:M{next_row}"

    w = max(len(h) for h in HEADERS)
    print(f"Target: {rng}\n")
    print(f"{'Col':<4} {'Header':<{w}} {'Previous':>10}  {'New':>10}   Change")
    print("-" * (w + 44))
    for col, hdr, old, new, note in rows:
        print(f"{col:<4} {hdr:<{w}} {old:>10}  {new:>10}   {note}")

    flagged = [r[1] for r in rows if "FLAG" in r[4]]
    print()
    if flagged:
        print(f"{len(flagged)} column(s) moved more than {FLAG_PCT:.0f}%: "
              + ", ".join(flagged))
        print("Report these to the user before writing.")
    else:
        print("All deltas within threshold.")

    print("\nupdateGoogleSheet arguments:")
    print(json.dumps({
        "spreadsheetId": sheet_id,
        "range": rng,
        "valueInputOption": "USER_ENTERED",
        "data": [row],
    }, indent=2))


if __name__ == "__main__":
    main()
