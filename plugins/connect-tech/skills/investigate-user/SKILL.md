---
name: investigate-user
description: >
  Use when a support ticket or a teammate asks what happened to one PersonalID or Connect
  user on the CommCare app - "look into this user", "investigate <username>", "what did this
  device do", "why can't this user get an OTP", "is anything odd about this account". Takes
  a PersonalID username or a CommCare device id, and optionally a date range, runs the
  investigate-user BigQuery queries, and writes a short report of what the user did, what
  failed, their crashes and anything unusual, as counts and flags with no PHI repeated.
argument-hint: "<PersonalID username | device id> [start date] [end date]"
---

# Investigate a user

Looks at one user's app activity in BigQuery and says what stands out. It runs the four
queries in `mobile/investigate_user/` of
[dimagi/commcare_analytics_queries](https://github.com/dimagi/commcare_analytics_queries)
and turns their rows into a short report. Read that folder's `README.md` once per session:
it says what each query returns and what it cannot tell.

This is v1, BigQuery only. It sees what the CommCare app logged to GA4 and Crashlytics. It
does not see the PersonalID server (account state, OTP counters, backup code, sessions) or
the Connect server (opportunities, visits, payments). Say so in every report, so nobody
reads a clean report as a clean account.

## How a user and a device are linked

GA4 gives every CommCare event two user properties:

- `user_cid`, the **PersonalID username**, set only while a PersonalID user is logged in.
  The queries call it `user_cid`; it is the same value as the username.
- `device_id`, the CommCare device id without its `commcare_` prefix.

Crashlytics carries the full `commcare_<uuid>` in its `device_id` custom key, so the devices
GA4 finds lead to their crashes. Activity before login or after logout has no `user_cid`.

## Privacy

The rows hold ids, dates, counts and flags. The report keeps to those.

- The PersonalID username and device ids may appear in the report.
- Never repeat a name, phone number, email, location, photo, message text or exception
  message, even when the ticket or the user gave it to you. If the user only has a phone
  number or a name, ask for the username or a device id instead: the queries cannot take
  either, and they must never be pasted into the SQL.
- Keep the query output in a scratch folder outside every repo (the session scratchpad if
  there is one). This skill's repo is public: never commit ids or results to it.
- Post nothing anywhere (Jira, Slack, a PR) unless the user asks. When they want it in a
  ticket, paste the report, never the raw rows.
- Write "unusual" and "possible explanations". Never "fraud" or "abuse": the data cannot
  tell intent.

## The queries

All four run in the BigQuery project **`commcare-a57e4`** and take named parameters.

| File | Reads | Parameters |
|---|---|---|
| `device_users.sql` | GA4, `commcare-a57e4.analytics_153906101.events_intraday_*` | `device_id` (STRING), `start_date` (DATE), `end_date` (DATE) |
| `user_devices.sql` | GA4, `commcare-a57e4.analytics_153906101.events_intraday_*` | `user_cid` (STRING), `start_date` (DATE), `end_date` (DATE) |
| `user_activity.sql` | GA4, `commcare-a57e4.analytics_153906101.events_intraday_*` | `user_cid` (STRING), `start_date` (DATE), `end_date` (DATE) |
| `user_crashes.sql` | Crashlytics, `commcare-a57e4.firebase_crashlytics.org_commcare_dalvik_ANDROID` | `device_ids` (ARRAY&lt;STRING&gt;), `user_cid` (STRING), `start_date` (DATE), `end_date` (DATE) |

- `device_id` and the entries of `device_ids` may be given with or without `commcare_`.
- `start_date` and `end_date` are inclusive. GA4 days are export days (the table suffix), and
  Crashlytics days come from its `event_timestamp`.
- CommCare only. CommCare LTS has no GA4 stream and a different Crashlytics table.
- GA4 keeps 180 days and Crashlytics about 90.

**Cost.** The three GA4 queries read `user_properties` for every day in the window, whoever
is asked about. Dry runs in November 2026 priced a two-week window at about 45 GB each for
`device_users.sql` and `user_devices.sql`, and 75 GB for `user_activity.sql`, which also
reads the event parameters: about 120 GB (roughly $0.70) from a username, 165 GB (roughly
$1) from a device id. `user_crashes.sql` reads about 0.1 GB. Keep the window as short as the
question allows.

## Steps

### 1. Settle the inputs

| Input | Where it comes from |
|---|---|
| Who | a PersonalID username, or a CommCare device id (`commcare_<uuid>`, or the bare uuid). Both are fine; start from the one given |
| Window | the dates the user or ticket names. Otherwise the 14 days up to today. Widen it only when the problem started earlier, and keep it under about five weeks unless the user agrees to the cost |

### 2. Find the queries

Use a local checkout of `commcare_analytics_queries` when the user has one (ask for its path
if it is not obvious). Run the files from its `master` branch, read with `git show`, so a
feature branch checked out there does not change them. Pull `master` first if it may be
behind GitHub:

```bash
mkdir -p <scratch>/investigate-user/sql
for f in device_users user_devices user_activity user_crashes; do
  git -C <checkout> show master:mobile/investigate_user/$f.sql > <scratch>/investigate-user/sql/$f.sql
done
```

Without a checkout, fetch the same four files with
`gh api repos/dimagi/commcare_analytics_queries/contents/mobile/investigate_user/<file> -H "Accept: application/vnd.github.raw"`.
Never copy the SQL into this skill or edit it: changes belong in the analytics repo.

### 3. Check that bq works

Run `bq version`. bq needs the Google Cloud SDK and a signed-in account with BigQuery access
to `commcare-a57e4`.

- If it asks to reauthenticate, have the user run `! gcloud auth login`.
- If it fails with `python3...: command not found` or similar (common on Windows), set
  `CLOUDSDK_PYTHON` to a Python 3 on the machine in the same command, for example
  `export CLOUDSDK_PYTHON=/c/Python314/python.exe`.
- No default project is assumed: every command passes `--project_id=commcare-a57e4`.

With no way to reach BigQuery, say so in one line and stop.

### 4. Dry-run, then run

Run every command from a POSIX shell (Git Bash on Windows): the SQL goes in on stdin,
because a file starting with `--` reads as a flag. `<sql>` is `<scratch>/investigate-user/sql`
and `<out>` is `<scratch>/investigate-user`. Dates are `YYYY-MM-DD`.

Dry-run each query first: the same command with `--dry_run` added and without the `> file`
redirect. It is free, and because these are single statements it prices the real query
(`totalBytesProcessed`). If a query would read more than 200 GB, stop and agree a shorter
window or the cost with the user before running anything. `--maximum_bytes_billed` stops a
run that would go past 200 GB anyway; raise it only once the user has agreed.

`--max_rows=100000` matters: bq prints only 100 rows by default, and `user_activity` returns
one row per day, device, version and category.

**a. From a device id only: who used the device.**

```bash
bq --project_id=commcare-a57e4 query --use_legacy_sql=false --format=json --max_rows=100000 \
  --maximum_bytes_billed=200000000000 \
  --parameter=device_id::<device id> \
  --parameter=start_date:DATE:<start> --parameter=end_date:DATE:<end> \
  < <sql>/device_users.sql > <out>/device_users.json
```

One row per `user_cid` seen on the device, and a row with a NULL `user_cid` for logged-out
use. One user: carry on with that username. Several: tell the user how many and how their
dates overlap, and ask which to follow (or follow each). None but the NULL row: nobody was
logged in to PersonalID on the device in the window; skip b and c, run d with
`--parameter=user_cid::` (empty), and say the report covers the device alone.

Starting from a username, skip this step.

**b. The user's devices.**

```bash
bq --project_id=commcare-a57e4 query --use_legacy_sql=false --format=json --max_rows=100000 \
  --maximum_bytes_billed=200000000000 \
  --parameter=user_cid::<username> \
  --parameter=start_date:DATE:<start> --parameter=end_date:DATE:<end> \
  < <sql>/user_devices.sql > <out>/user_devices.json
```

No rows means the username logged no event in the window: check its spelling and the window
before reporting that.

**c. What the user did and what failed.**

```bash
bq --project_id=commcare-a57e4 query --use_legacy_sql=false --format=json --max_rows=100000 \
  --maximum_bytes_billed=200000000000 \
  --parameter=user_cid::<username> \
  --parameter=start_date:DATE:<start> --parameter=end_date:DATE:<end> \
  < <sql>/user_activity.sql > <out>/user_activity.json
```

**d. Crashes on those devices.** Pass every `device_id` from b (and the device from a, if
the user started there):

```bash
bq --project_id=commcare-a57e4 query --use_legacy_sql=false --format=json --max_rows=100000 \
  --maximum_bytes_billed=200000000000 \
  --parameter='device_ids:ARRAY<STRING>:["commcare_<uuid 1>","commcare_<uuid 2>"]' \
  --parameter=user_cid::<username> \
  --parameter=start_date:DATE:<start> --parameter=end_date:DATE:<end> \
  < <sql>/user_crashes.sql > <out>/user_crashes.json
```

Optional, when b shows a shared device and the question needs the other users: run a on
that device. It costs another full GA4 read, so ask first.

### 5. Total the activity

Do not add up rows by hand. bq's JSON gives numbers as strings and leaves NULL counts as
`null`. Total `user_activity.json` by category:

```bash
python - <out>/user_activity.json <<'EOF'
import json, sys
from collections import defaultdict
rows = json.load(open(sys.argv[1]))
num = lambda v: int(v) if v not in (None, "") else None
tot = defaultdict(lambda: {"events": 0, "attempts": None, "failures": None, "days": set(), "worst_day": (0, None)})
for r in rows:
    t = tot[r["category"]]
    t["events"] += num(r["events"])
    t["days"].add(r["export_date"])
    for k in ("attempts", "failures"):
        v = num(r.get(k))
        if v is not None:
            t[k] = (t[k] or 0) + v
    f = num(r.get("failures")) or 0
    if f > t["worst_day"][0]:
        t["worst_day"] = (f, r["export_date"])
print("category | events | attempts | failures | failure rate | days | most failures in a day")
for c, t in sorted(tot.items()):
    rate = f"{t['failures'] / t['attempts']:.0%}" if t["attempts"] and t["failures"] is not None else "-"
    print(c, t["events"], t["attempts"], t["failures"], rate, len(t["days"]), t["worst_day"], sep=" | ")
print("devices:", sorted({r["device_id"] for r in rows}))
print("versions:", sorted({r["app_version"] for r in rows}))
EOF
```

Group by `device_id` or `app_version` the same way when a failure sits on one device or one
version.

### 6. Read it

**Categories.** `user_activity.sql` sorts events exactly as
`mobile/release_health/release_health_ga4_failures.sql` does; that folder's README has the
full table. In short (if the `investigate_user` README you fetched lists other categories,
it wins over this table):

| Category | Failure when |
|---|---|
| `all_events`, `session_start`, `screen_view`, `first_open`, `app_update` | counts only, no failures |
| `app_exception` | every event |
| `sync` / `sync_non_network` | sync failed / failed for a reason other than no network, unreachable host, timeout, captive portal or cancel |
| `form_upload` / `form_upload_non_network` | not a full success / and not a transport or captive portal failure |
| `form_quarantine` | a form was quarantined other than by hand |
| `corrupt_app_state`, `update_stage_failure`, `update_reset` | every event |
| `in_app_update` | the in-app update failed |
| `personalid_config_failure` | every event |
| `otp_request` | an OTP request failed, as the user saw it (Firebase handoffs left out) |
| `otp_request_firebase`, `otp_request_personalid`, `otp_request_email` | `otp_request` split by method; the three add up to it |
| `otp_request_firebase_handoff` | a Firebase phone request failed and handed off to PersonalID SMS within 120 seconds. Its attempts are every Firebase request, so its rate is the share that handed off. Not a failure the user saw on its own |
| `otp_verify` | a code was rejected, including wrong codes typed by the user |
| `personalid_recovery` | account recovery failed |
| `connect_api_jobs`, `connect_api_start_learning`, `connect_api_claim_job`, `connect_api_payment_confirmation` | the Connect API call failed |
| `connect_api_learn_progress`, `connect_api_delivery_progress` | the call failed; no attempts, because their successes are logged unevenly, so give counts, never a rate |

**Red flags.** Check each against the rows, and list the ones that hold with the numbers
behind them. A flag is a reason to look, not a finding.

- **OTP trouble.** `otp_request` failures, by method; many requests on one day (each phone
  request can cost an SMS); `otp_verify` failure rate high (wrong codes, or codes that never
  arrived); Firebase requests that keep handing off; requests with no verify after them.
- **PersonalID setup or recovery failing.** Any `personalid_config_failure`, or
  `personalid_recovery` failures.
- **Several devices.** More than one row in `user_devices`, especially new devices late in
  the window or devices used on the same days.
- **Shared or passed-on devices.** `is_shared_device` (other PersonalID users on it);
  `used_after_user_left` (the device went on without this user); in `device_users`,
  `users_on_device` above 1.
- **Reinstalls or cleared data.** `app_instances` above 1 on one device, or `first_open`
  events after the first day.
- **Stuck outside the app.** Many `logged_out_events` next to few logged-in events, which
  can mean the user cannot get through login or PersonalID setup.
- **Demo or test flags.** `any_demo_user` on what should be a real account, or
  `any_ccc_enabled` false where the user is meant to be on Connect.
- **Old or mixed versions.** An app version well behind the current release, or several
  versions on one device in the window.
- **App state trouble.** `corrupt_app_state`, `update_stage_failure`, `update_reset`,
  `in_app_update` failures, `form_quarantine`.
- **Work not reaching the server.** `sync_non_network` or `form_upload_non_network`
  failures. The plain `sync` and `form_upload` rows are mostly the user's signal.
- **Connect API failures.** Failures on `connect_api_*`, especially `claim_job`,
  `start_learning` and `payment_confirmation`, which stop the user's work or pay.
- **Crashes.** Issues with `error_type` FATAL or ANR (NON_FATAL are logged errors, often
  harmless); an issue on several `days_with_events` (keeps coming back); `app_exception`
  events in GA4. On a shared device, `events_user_id_is_other` above 0 means some crashes
  were someone else's.
- **Silence.** No events at all for days inside the window, or nothing after a failure, can
  mean the user gave up.

**What is unusual.** Beyond the flags, say what does not fit a normal week: a burst of
activity on one day, a failure that starts on the day the version changed, activity at the
same time on two devices, or anything the ticket's story and the data disagree on.

### 7. Write the report

Short, plain, and in the conversation. Counts and flags only.

```
## <username or device id>, <start> to <end>

<Two or three sentences: what the user mainly did, the main problem the data shows (or
that it shows none), and the most likely explanation.>

**Devices.** <n> device(s): <device id>, <first>-<last>, <active days>, versions <...>
[, shared with <n> other user(s)] [, used after the user left].

**Activity.** <active days> days, <sessions> sessions, <screen views> screens.

**Failures.**
| Category | Attempts | Failures | Rate | Days |
(only categories with failures)

**OTP.** <requests by method and how many failed; handoffs; verify attempts and failures;
the worst day>.

**Crashes.** <n> issue(s), <events> events on <days> days.
| Issue id | Error type | Title | Events | Days | Versions |

**Red flags.** <one line each, with the numbers; "None" if none hold>.

**Unusual.** <what does not fit, or "Nothing stands out">.

**Not checked.** PersonalID server (account state, OTP limits, backup code), the Connect
server (opportunities, visits, payments), CommCare HQ, and anything outside <start>-<end>.
Queries: <which ran>, <GB read in all>.
```

The issue title is the exception class and frame, which is fine to show. Never show the
issue subtitle (it can carry an exception message); give the `issue_id` so the reader can
open the issue in the Crashlytics console.

Write the report to a file only when the user asks, outside every repo.

## What this cannot tell

- **Before login and after logout** there is no `user_cid`; those events show only as
  `logged_out_events` and the NULL row of `device_users`.
- **A crash cannot be pinned on one user of a shared device.** `user_crashes` joins by
  device. The Crashlytics user id is the CommCare username while one is logged in, and the
  PersonalID username otherwise, so `events_user_id_is_user` confirms only some.
- **The server side is not here**: why an OTP was refused, whether the account is locked or
  has a backup code, and anything about opportunities, visits or payments.
- **Days are GA4 export days**, in the property's time zone rather than the user's, so a
  user's evening can land on the next day.
