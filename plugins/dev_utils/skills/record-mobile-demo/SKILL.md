---
name: record-mobile-demo
description: Use when the user wants a demo video (or GIF) of a mobile change - "record a demo", "make a video of this change", "demo this for the PR", "screen-record the new flow". Drives a plugged-in Android device or an emulator through the flow, records a clean replay with scrcpy, and polishes it with captions into a small mp4 ready to drop into a PR.
---

# Record a demo video

The flow is rehearsed once, logging each successful step to a flow file. Then the flow file is
replayed at a natural pace while recording. The video never goes through Claude; Claude only reads
compact screen dumps and, at the end, one contact sheet image.

All commands go through one script (`D` below). Resolve `${CLAUDE_PLUGIN_ROOT}` to its absolute
path first, and use that path in any subagent prompt, since subagents don't have the variable:

```bash
D="python ${CLAUDE_PLUGIN_ROOT}/skills/record-mobile-demo/scripts/demo.py"
```

## Setup

- **Tools:** Python 3, `adb` and `ffmpeg` on PATH, and preferably `scrcpy`. Without scrcpy it
  falls back to `adb screenrecord`, which caps at 3 minutes.
- **Maestro** (for the Maestro path below): QA's pinned version, 1.39.13, either on PATH or
  unzipped to `~/.maestro-1.39.13/`.
- **Staging account** (for the Maestro path): an env file, such as
  `~/.config/record-mobile-demo/staging-account.env`, holding the existing staging PersonalID
  account the demo signs in with:

  ```
  COUNTRY_CODE=...
  PHONE_NUMBER=...
  USERNAME=...
  BACKUP_CODE=...
  ```

  If it's missing, ask the user to create it. Never create, print or read it back yourself.

When a tool is missing, say which one and stop; don't install anything without asking.

Pass `-s SERIAL` before the subcommand when more than one device is connected.

## With a Maestro flow (preferred for Connect and PersonalID)

QA's Maestro suites are the preferred source. Use
[dimagi-qa-ccc](https://github.com/dimagi/dimagi-qa-ccc) (clone it locally) for
Connect and PersonalID, and dimagi-qa-commcare-mobile for core CommCare. The flow is written as a
normal QA test, and `label:` goes on each step the video should show. The video is made from it:

```bash
$D maestro <flow.yaml> --env-file ~/.config/record-mobile-demo/staging-account.env --out <folder>/demo.mp4
```

**How the video is cut from the run:**

- Maestro runs the whole flow while scrcpy records. Its `--debug-output` command log gives each
  step's start time and duration.
- The video starts at the first completed labelled step, so setup subflows (sign-in,
  recovery), which carry no labels, never show, and the flow needs no demo-only code.
- Motion plays at real speed.
- The video holds `--hold` 1.2 s after each labelled step, and `--payoff` 3 s after the last.
- A single command longer than `--fast-after` 5 s plays at `--speed` 8x.
- Each label is the caption from its step until the next label.
- To change the holds without re-running, use
  `$D polish <demo.timeline.json> --out ... [--hold/--payoff/...]`.

**Build:** for the app, build `assembleCccStagingQaAutomation` in commcare-android. Its
application ID is `org.commcare.dalvik`, the same one QA's flows declare, and `IS_QA_AUTOMATION`
skips the biometric unlock gate. Without the release keystore, sign it with the debug key:

```bash
./gradlew assembleCccStagingQaAutomation -Pandroid.injected.signing.store.file=$HOME/.android/debug.keystore \
  -Pandroid.injected.signing.store.password=android -Pandroid.injected.signing.key.alias=androiddebugkey \
  -Pandroid.injected.signing.key.password=android
adb install -r -g app/build/outputs/apk/cccStaging/qaAutomation/app-cccStaging-qaAutomation.apk
```

**Account:** signing up a fresh PersonalID number fails Play Integrity on a side-loaded build.
Demos recover an existing staging account through QA's `shared_signed_in.yaml`, with
COUNTRY_CODE, PHONE_NUMBER, USERNAME and BACKUP_CODE in the env file. Never print that file.
Recovering moves the account onto this device.

**Maestro:** pinned to QA's version, 1.39.13. The script finds it in `~/.maestro-1.39.13/`
when it isn't on PATH.

**Before publishing:** check the contact sheet for personal details (photo, email, phone),
since commcare-android PRs are public.

The rest of this file is the fallback for flows with no Maestro equivalent: a rehearsed adb
flow file.

## 1. Agree on the story

Before touching the device, settle with the user:

- **What the change is.** If they haven't said, read the branch diff (`git diff master...`) and
  propose it.
- **The starting state.** For example: logged in to app X, on the opportunity list.
- **3-8 beats, each with a short caption** (under about 50 characters): "Open the opportunity",
  "Progress bar shows 3 of 5 visits".
- **The payoff screen** to linger on.

Confirm the beats in one short message, then go. Keep demos under about 60 seconds.

## 2. Get a device ready

```bash
$D devices                      # connected devices and available emulators
$D boot Pixel_7_Pro_API_33      # if nothing is connected; waits for boot
```

Use a plugged-in phone if the user asks for one. Otherwise use an emulator.

- **Install the build:** for a build of the current branch, run
  `./gradlew installCommcareDebug` in `commcare-android` filtering the output.
- **Getting into the app:** never type real credentials or a PIN/pattern. If the app needs a
  login or the screen is locked, ask the user to do it by hand, then carry on.
- **Emulator snapshot:** once the emulator is in the starting state, save it, so you can always
  get back there:

  ```bash
  $D snapshot save demo-start
  ```

- **Prep the device:**

  ```bash
  $D prep
  ```

  This shows touch dots, keeps the screen on, and sets a clean status bar (10:00, full battery
  and signal, no notifications). Use `--no-demo-bar` when the status bar is part of the change.

## 3. Rehearse, logging steps

Make a folder for the demo: `~/Videos/demos/<branch-or-topic>/`. Use that folder for the flow file
`flow.jsonl` and every output. Run each step with `--log`. A step is logged only if it succeeds,
and after each action the script prints the new screen, so no separate look is needed.

```bash
F=~/Videos/demos/opp-progress/flow.jsonl
$D launch org.commcare.dalvik.debug --stop --setup --log $F --quiet
$D screen
$D tap --text "Malaria study" --log $F --caption "Open the opportunity"
$D wait --id progress_bar --log $F
$D swipe up --log $F
$D tap --id btn_sync --log $F --caption "Sync pulls the new visits"
$D wait --text "Syncing" --gone --timeout 30 --log $F
$D sleep 0 --pause 3 --log $F --caption "Progress now shows 4 of 5 visits"
```

**Picking elements:**

- `--text` matches text or content-description: exact first, then contains, case-insensitive.
- `--id` takes the short resource id. `--desc` matches the content-description only.
- `--index N` picks among several matches. `--scroll` swipes until the element shows.
- Avoid `--xy` unless there is nothing else to match: selectors survive layout shifts, and
  coordinates don't.

**Step options:**

- `--caption` shows the caption from just before this step until the next captioned step.
- `--pause S` lingers S seconds before the step on replay. The default comes from the `--pace`
  flag of `play`, 1.2 s. Give the payoff a `--pause 2.5`-`4`, or end the flow with
  `sleep 0 --pause 3`.
- `--setup` runs the step before recording starts. Use it for `launch --stop` and for any
  navigation to the starting screen.
- `wait` (and `wait --gone`) handle anything asynchronous: syncs, network calls, dialogs.
  A `tap` already waits up to 10 s for its element.

**Other actions:**

- `type "text"`: ASCII only. Tap the field first.
- `key back|home|enter|...`
- `swipe up|down|left|right`: the finger's direction, so `swipe up` scrolls down the page.
- `swipe x1,y1,x2,y2` for an exact swipe.

**Fixing a bad step:** if a step did the wrong thing, fix the device by hand-run commands
without `--log`, and delete the bad line from the flow file.

**Screenshots:** take `$D shot <png>` only to check something visual, such as a layout or colour
change. The screen dump covers the rest.

## 4. Record

Get the device back to the starting state first:

- **Emulator:** `$D snapshot load demo-start`.
- **Device:** make sure the setup steps reset it, or ask the user if the flow changed data that has
  to be undone.

```bash
$D play $F --out ~/Videos/demos/opp-progress/demo.mp4          # add --gif for a GIF too
$D play $F --out ... --no-record                               # dry run if unsure
```

`play` writes three files:

- `demo.raw.mkv`, the untouched recording.
- `demo.timeline.json`, with the times and captions of each step.
- `demo.mp4`, the polished video: scaled to at most 1280 px tall, a caption strip under the
  screen, a 1 s hold at the end, and H.264 at CRF 28.

**Fixing captions or size without re-recording:** edit the captions in the timeline file, then:

```bash
$D polish ~/Videos/demos/opp-progress/demo.timeline.json --out ~/Videos/demos/opp-progress/demo.mp4 [--crf 32] [--height 960] [--gif]
```

GitHub takes uploads up to 10 MB, and the script warns when a file is over that.

## 5. Check it, then clean up

```bash
$D contact ~/Videos/demos/opp-progress/demo.mp4 ~/Videos/demos/opp-progress/contact.png --frames 8
```

Read the contact sheet: one image, 8 frames across the video. Check that:

- each beat appears,
- captions match what is on screen,
- nothing private shows (real names, phone numbers, notifications).

If a step misfired, fix the flow file and replay. Replays cost almost nothing.

Then run `$D reset`, which turns off demo mode and restores touch dots. On an emulator, also run
`$D snapshot delete demo-start`, unless the user wants to keep the snapshot for more takes.

## 6. Hand it over

Give the user:

- the mp4's full path, size and duration,
- the contact sheet,
- the flow file path, for re-recording after review changes.

`gh` can't attach videos to a PR. The user drags the mp4 into the PR description or a comment, or
asks you to do it through the Chrome tools.

## Keeping it cheap

- **Context:** if this session already carries a lot of context, do steps 3-5 in a
  general-purpose subagent. Give it this skill's path, the beats, the device serial and the output
  folder, and have it return only the paths and any problems.
- **Screen dumps:** rely on the printed screen dump (about 1k tokens) and use `--quiet` on steps
  whose result you already know. Use `screen --all` only when the list is cut off.
- **Images:** the video is never read. Look at one contact sheet, not separate frames.
