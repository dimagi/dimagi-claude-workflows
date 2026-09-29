---
name: crash-metrics
description: Use when the user wants to record Firebase Crashlytics metrics into the "CommCare Mobile Metrics" spreadsheet - appending a dated row of 30/90-day crash-free users, crash counts, crash users, ANRs and ANR users for CommCare and/or CommCare LTS. Triggers on "update the crash metrics", "log this week's crash numbers", "update the crashes sheet", or any request to refresh the CommCare Crashes / LTS Crashes tabs.
---

# Update CommCare Crash Metrics

## Overview

Reads six metrics per app from the Firebase Crashlytics console (via Chrome browser
automation) and appends one dated row to the **CommCare Mobile Metrics** spreadsheet.

The Crashlytics REST API cannot produce this row: it returns event/user counts grouped
by *issue* only, with no totals and no crash-free-users metric. The console dashboard is
the source of truth, so this skill scrapes the same tiles a human reads by hand.

`scripts/build_row.py` does all validation, delta math and row assembly - use it
rather than computing anything by hand.

Always **preview the row and get explicit confirmation before writing.**

## Setup

The target spreadsheet is **CommCare Mobile Metrics**. Its id is not stored in this
repo, which is public. Set it once:

```bash
export CRASH_METRICS_SHEET_ID=<id from the sheet URL>
```

If it is unset the script exits 1 and says so. Ask the user for the id rather than
guessing, and do not write it into a file in this repo.

## Constants

| Thing | Value |
|---|---|
| Spreadsheet | `$CRASH_METRICS_SHEET_ID` (see Setup) |
| Firebase project | `commcare-a57e4` |
| CommCare app | `android:org.commcare.dalvik` -> tab **CommCare Crashes** |
| CommCare LTS app | `android:org.commcare.lts` -> tab **CommCare LTS Crashes** |

Both tabs share an identical 14-column schema. The two archive tabs are historical; never write to them.

## Column layout (A-N)

Data rows fill **A:M only** - column N ("GOAL") is left empty.

| Col | Header | Source |
|---|---|---|
| A | Date | today, formatted `3 Sep, 2026` |
| B | 90 days Crash free Users | 90d + Crashes -> crash-free users tile |
| C | Goal | constant `95.00%` |
| D | Alert in slack | constant `93.50%` |
| E | 90 days - Crashes | 90d + Crashes -> Trends events |
| F | 90 days - Crash users | 90d + Crashes -> Trends users |
| G | 30 days Crash free Users | 30d + Crashes -> crash-free users tile |
| H | 30 days - Crashes | 30d + Crashes -> Trends events |
| I | 30 days - Crash users | 30d + Crashes -> Trends users |
| J | 90 days - ANR | 90d + ANRs -> Trends events |
| K | 90 days - ANR Users | 90d + ANRs -> Trends users |
| L | 30 days - ANR | 30d + ANRs -> Trends events |
| M | 30 days - ANR Users | 30d + ANRs -> Trends users |

So each app needs **4 page loads**: {30d, 90d} x {crash, ANR}. The crash-free-users tile
does not exist on the ANR views - only Trends events/users are read there.

## Step 1 - Scope and duplicate check

1. Ask which app(s) unless the user already said: CommCare, LTS, or both. Default to both.
2. For each target tab, read the tail to find the last populated row and check whether
   today already has a row:

   `getGoogleSheetContent` with range `CommCare Crashes!A1:M40`

3. If today's date is already present, **stop and tell the user** rather than adding a
   duplicate. Offer to overwrite that row instead.
4. Note the next empty row number - that is the write target.

## Step 2 - Scrape Crashlytics

Invoke the `claude-in-chrome` skill first, then `tabs_context_mcp`, then create one tab
and reuse it for all page loads.

URL template:

```
https://console.firebase.google.com/project/commcare-a57e4/crashlytics/app/<APP>/issues?state=open&time=<TIME>&types=<TYPES>&tag=all&sort=eventCount
```

- `<APP>` = `android:org.commcare.dalvik` or `android:org.commcare.lts`
- `<TIME>` = `30d` or `90d`
- `<TYPES>` = `crash` (lowercase) or `ANR` (**uppercase - see Gotchas**)

After each `navigate`, **wait ~8-10s** for the Angular app to finish loading, then run
this extractor with `javascript_tool`. Re-run it if `stillLoading` is true or values are null.

```js
(() => {
  const leaves = l => [...document.querySelectorAll('*')].filter(
    e => e.children.length === 0 && e.textContent.trim() === l);
  const upFrom = (el, test) => {
    for (let p = el, i = 0; p && i < 8; p = p.parentElement, i++)
      if (p.innerText && test(p.innerText)) return p;
    return null;
  };
  const num = /^[\d.]+[KM]?$/;

  // Trends card -> first two numeric leaf nodes are [events, users]
  const tCard = upFrom(leaves('Trends')[0], t => /Users/.test(t) && /\d/.test(t));
  const tNums = [...tCard.querySelectorAll('*')]
    .filter(e => !e.children.length).map(e => e.textContent.trim())
    .filter(t => num.test(t));

  // Crash-free users tile (absent on the ANR views)
  const cfLeaf = leaves('Crash-free users')[0];
  const cfCard = cfLeaf ? upFrom(cfLeaf, t => /%/.test(t)) : null;
  const cfPct = cfCard ? (cfCard.innerText.match(/(\d+\.\d+)%/) || [])[1] : null;

  return JSON.stringify({
    range: (document.body.innerText.match(/Last \d+ days\n[^\n]+/) || [])[0]?.replace('\n', ' '),
    eventType: (document.body.innerText.match(/Event type = "([^"]+)"/) || [])[1],
    crashFreeUsersPct: cfPct,
    events: tNums[0] ?? null,
    users: tNums[1] ?? null,
    stillLoading: !!document.querySelector('mat-spinner, .mat-mdc-progress-spinner')
  }, null, 1);
})();
```

Close the tab when done.

## Step 3 - Validate and assemble (scripted)

**Do not do this arithmetic by hand.** Write the four scraped view objects into a payload
and pipe it through `build_row.py`, which lives beside this file. It validates every field,
computes deltas against the previous row, renders the preview table, and emits the exact
`updateGoogleSheet` arguments.

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/build_row.py < payload.json
```

Payload (write it to the session scratchpad, not `/tmp` - that does not persist between
Bash calls):

```json
{
  "app": "lts",
  "next_row": 3,
  "date": "2026-09-03",
  "prev_row": ["3 Aug, 2026","96.19%","95.00%","93.50%","1.7K","619",
               "95.86%","823","351","341","100","341","100"],
  "views": {
    "crash_90d": { <extractor output for 90d + crash> },
    "crash_30d": { <extractor output for 30d + crash> },
    "anr_90d":   { <extractor output for 90d + ANR> },
    "anr_30d":   { <extractor output for 30d + ANR> }
  }
}
```

`app` is `commcare` or `lts`; `date` defaults to today if omitted; `prev_row` is columns
A:M of the last populated row and may be omitted (you then get no delta column).

The script enforces, and exits 1 with errors on stderr if any fail:

- each view present and not `stillLoading`
- `eventType` matches the view requested - **this is what catches the `types=anr` trap**
- `range` matches the window requested
- counts match `^[\d.]+[KM]?$`, percentages match `^\d+\.\d+$`
- no value that would be parsed as a formula under USER_ENTERED
- crash-free-users tile actually read on both crash views

On a non-zero exit, fix the cause - usually re-scraping one view - and re-run. **Never
hand-assemble the row to work around a validation failure.**

## Step 4 - Preview and confirm

Show the script's table as-is, including any flagged columns (moves over 20%). Wait for
explicit approval.

## Step 5 - Write

Pass the arguments the script emitted straight to `updateGoogleSheet`, unmodified:

```
updateGoogleSheet
  spreadsheetId: <as emitted by the script>
  range: <Tab>!A<row>:M<row>
  valueInputOption: USER_ENTERED
  data: [[ ... ]]
```

`USER_ENTERED` is deliberate: it makes percentages land as percent-formatted numbers just
as typing them by hand would, while `86K` stays text (Sheets cannot parse it as a number),
matching the existing column contents.

Then read the row back and confirm it landed correctly.

## Gotchas

- **`types=ANR` must be uppercase.** `types=anr` is silently rejected and the console
  rewrites the URL back to `types=crash` - you will scrape crash numbers and label them
  ANRs. Always verify the `eventType` the extractor returns.
- **The page needs a real wait.** Immediately after navigate the tiles render as `...`
  with spinners. Check `stillLoading` and that values are non-null.
- Percentages come from the **Crash-free users** tab of that tile, not Crash-free sessions.
- Counts are read pre-rounded by the console (`86K`, `6.4K`) - that is intentional and
  matches how the sheet has always been kept. Do not try to expand them.
- The date column has one legacy row formatted `3rd Aug, 2026`; use the dominant
  `3 Sep, 2026` form for new rows.
- Requires an already-authenticated Firebase console session in Chrome. If the page shows
  a login screen, stop and ask the user to sign in - do not attempt to authenticate.
