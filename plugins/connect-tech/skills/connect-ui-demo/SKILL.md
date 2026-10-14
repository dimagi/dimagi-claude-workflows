---
name: connect-ui-demo
description: "Verify a commcare-connect UI flow and produce a polished, share-ready demo video (captions, cursor, intro/outro, device frame, mp4). A script-driven Verify Run proves the flow works before a single headed Record Pass. Use only when the user explicitly asks for a demo/recording or names this skill."
---

# UI Demo — verified flow, demo-grade recording

Goal: a verified UI recording a PM or stakeholder can watch once on Slack/Jira/GitHub and understand, with minimal retries, runtime and tokens.

Core idea: **the script owns browser state, not the conversation.** `flow.mjs` performs navigation, waits, assertions, retries and DOM inspection internally and returns a structured JSON report; context receives reports and small checkpoint snapshots, never per-action page state. Playwright MCP is a discovery fallback only. Every default below (cursor, spotlight, captions, overlays, 2x capture) is measured — see `reference/learnings.md`. Polish is on by default under `--record`; the Verify Run stays plain and fast.

## Passes

- **Verify Run** — `node flow.mjs`: headless, assertion-instrumented run of the script that will record; emits `output/report.json`. Iterate until clean.
- **Record Pass** — `node flow.mjs --record`: headed, 2x; produces `raw.mp4` + `steps.json`.
- **Post-Process** — `render.py` on existing artifacts (speed, captions, frame, encode); never touches the browser.
- **Spot-Check** — quick look at `final.mp4`; not a re-investigation.

## Golden Rules

1. **Never record an unverified workflow.** Record only after a clean Verify Run report *and* a checkpoint review (mechanical + semantic proof).
2. **Draft from source, verify by script.** Read templates/views, write the complete `flow.mjs` (every step with assertion, caption, checkpoints), iterate the Verify Run. Playwright MCP only when source can't determine a segment's selectors, or a step failed two fixes and the report's failure context doesn't explain why — scoped to that segment. It never blocks the Record Pass (`reference/troubleshooting.md`).
3. **Context receives reports, not pages.** Debug from the report's failure context; judge semantics from checkpoint snapshots.
4. **Record once, render freely.** `raw.mp4` + `steps.json` are a durable pair: never delete them, never regenerate just to restyle, overwrite only together and only when the workflow under test changed. Caption wording/position, speed, frame and encode changes are `steps.json` edits or `render.py` flags + a re-render.
5. **It has to read as a demo, not a test.** Realistic names/orgs/emails, no debug toolbar, 6–10 steps (the runner warns past 12; split into two videos), every step captioned in plain language a PM understands.

Capture is `page.screencast` — never MCP's `browser_video_*` tools (tool round-trips bake into the capture as dead air). Overlays only via `page.screencast.showOverlay/showChapter`, never `page.evaluate` DOM injection; real HTTP navigation only, never `data:` URLs (both silently missing from capture).

## Setup (once per task)

Run `preflight.sh` first (Node 20+, Python 3 venv, ffmpeg with libx264, the repo's `.venv`, a display for the headed Record Pass); it prints what to install. Playwright ≥1.61 is required (`showOverlay`) and is installed by the block below.

Kick off `./serve.sh` and `./reseed.sh` in the background *before* reading any code, and draft `flow.mjs` while they run. `curl` readiness right before the first Verify Run.

Run everything from inside the commcare-connect checkout (the project). The workspace is persistent at `<repo>/.ui-demo/`, git-ignored by its own `.gitignore` (`*`): shared `node_modules/` + `venv/` at the root, one subfolder per task (ticket ID verbatim, else a short kebab-case slug) holding `flow.mjs`, the copied `runner.mjs`/`render.py`/profile files, and `output/` (`raw.mp4`, `steps.json` durable; `report.json`, `state.json`, `final.mp4`, `poster.png`, `render.json` derived).

```bash
REPO=$(git rev-parse --show-toplevel)
RECORD_DIR="$REPO/.ui-demo"
TASK_DIR="$RECORD_DIR/<task-id-or-slug>"
SKILL="<base directory of this skill>"   # shown as "Base directory for this skill" when it loads; works wherever it is installed
"$SKILL/preflight.sh" || { echo "fix the ✗ lines above, then re-run setup"; exit 1; }
mkdir -p "$RECORD_DIR" && [ -f "$RECORD_DIR/.gitignore" ] || echo '*' > "$RECORD_DIR/.gitignore"
if [ ! -d "$RECORD_DIR/node_modules" ]; then
  cd "$RECORD_DIR" && npm init -y && npm install playwright @playwright/test
  python3 -m venv venv && source venv/bin/activate && pip install --quiet pillow
fi
[ -d "$RECORD_DIR/node_modules/@playwright/test" ] || (cd "$RECORD_DIR" && npm install @playwright/test)
(cd "$RECORD_DIR" && npx playwright install chromium)   # no-op when present
mkdir -p "$TASK_DIR/output" && cp $SKILL/runner.mjs $SKILL/render.py "$TASK_DIR/" && cd "$TASK_DIR"
cp $SKILL/profiles/commcare-connect/{connect.mjs,record_settings.py,seed.py,serve.sh,reseed.sh} . && chmod +x serve.sh reseed.sh
cp $SKILL/profiles/commcare-connect/flow.example.mjs flow.mjs
./serve.sh 8010 && ./reseed.sh        # runserver (DEBUG off, email → console), realistic data
```

**Reseed before every Record Pass** — a Verify Run mutates data (accepts invites, creates users). Touch only the active task folder; never remove shared tooling, other task folders, or the active durable pair.

## 1. Seed data that reads as real

`profiles/commcare-connect/seed.py` provides the **Child Health Campaign** workspace (plus Kangaroo Mother Care and Mother Baby Wellness) with role-coded people: Asha Admin, Ravi Admin, Meera Member, Vikram Viewer, Isha Invitee (has an account, not a member) and Neel New (no account). Name and email say the role, so no legend is needed. Extend with a task-local `seed_extra.py` for feature-specific rows (opportunities, visits, payments). Never `test123`, `example.com`, `uitest.local` — viewers translate "demo/test" into "fake"; the runner warns when such tokens are visible in checkpoints.

## 2. Draft `flow.mjs` from source

`import { run, expect } from './runner.mjs'`, the profile helpers (`import * as c from './connect.mjs'`), then `INTRO`, `OUTRO`, `STEPS`, `await run({...}, import.meta.url)`. Schema in `reference/verify-runner.md`; working examples in `profiles/commcare-connect/` (`flow.example.mjs` login on camera, `flow.feature-example.mjs` signed in off camera).

- **Start where the feature starts.** Sign in off camera with `preAuth: (p) => c.quickLogin(p, c.USERS.admin)` and open the feature page as `firstUrl`. Put login in `STEPS` only when signing in is the story (auth, invites, permissions).
- **Merge setup-only clicks** into one step; the viewer needs outcomes, not every click.
- Every step has `run(page, d)` using `d.click/type/select/goto` and an `assert` that proves the *outcome*, not just that an element exists.
- `intent` — ≤42 chars, what is about to happen, shown as a pill during the action ("Invite Isha as a Member"). Dropped when the action is under 0.8 s; the runner warns on a captioned step without one.
- `caption: [title, subtitle]` — title ≤42 chars, plain language ("Invite sent to Isha", not "Invitation record created"). Subtitle = *why it matters to the user*, not a second description of the screen ("Both will hear when someone joins"). Hold time is derived from text length.
- A `checkpoint` region on each page whose outcome matters (2–3 per flow), scoped to the main content area; the renderer flips captions off the clicked target and off the checkpoint. `captionPos: 'top'` only to override.
- `INTRO`/`OUTRO` follow one arc — **problem → walkthrough → result**. Intro names the need ("Know when your invite is accepted"), description says what was missing before (for a bug fix, the broken behaviour). Outro states what is now true ("Isha joined, and both admins know"), not "Done".
- Selectors come from code; the Verify Run confirms them. No fixed sleeps.

## 3. Verify Run loop

`node flow.mjs` — headless, no video, prints `report.json`.

- **On failure:** fix from the report's assertion error, URL/title, `ariaSnapshot`, console errors and failed requests, then re-run. `preAuth` is reused via `state.json` (`useState: false` for flows that sign in on camera or switch identity); `--from=<step>` resumes only when earlier steps have no needed side effects.
- **On a clean report:** start `./reseed.sh` in the background, then read each `checkpoint` snapshot (right data, right values, no error banners) and `report.warnings` — step-count, caption-length and test-data warnings are demo-quality defects; fix before recording. If you fix and re-verify, reseed again.

Exit criteria: clean report + checkpoints reviewed + no unexpected console errors/failed requests + no unaccepted warnings.

## 4. Record Pass

`node flow.mjs --record` in the background (needs no supervision; recording is real time). It starts from a fresh non-`storageState` context so login is actually shown. Meanwhile draft the delivery message and pick render flags.

## 5. Post-Process

```bash
../venv/bin/python render.py --task .            # final.mp4 + poster.png + render.json
../venv/bin/python render.py --task . --fast     # preview encode while iterating captions
```

Defaults: 1920×1200, spotlight on, intent pills + captions, dark device frame, 30 fps, `libx264 -crf 19`, 10 MB budget with one automatic `crf+3` retry. Flags and details: `reference/recording-snippets.md`. Caption wording lives in `steps.json`.

## 6. Spot-Check

Check `render.json` (`duration_s` plausible vs. Record Pass wall-clock, `over_budget: false`), then sample the first second (intro card visible) and the last second (outro card): `ffmpeg -ss <t> -i output/final.mp4 -frames:v 1 -vf scale=800:-1 frame.png` — always downscale. Each frame shows the expected page, a legible caption not covering its target, and the frame. If a caption covers content, set `captionPos` in `steps.json` and re-render. If something is wrong (duration far off, blank/stale frame), see `reference/troubleshooting.md`. Never deliver an unverified recording.

## 7. Cleanup & deliver

After the Spot-Check passes: delete seeded/test rows the flow created, `output/fail-*.png`, servers started for this recording (`./serve.sh stop <port>`, confirm down with `curl`), and stray `.playwright-mcp/`. Keep shared tooling and every task's `flow.mjs`, `render.py`, seed scripts and durable pair. `git status --porcelain` should show nothing from `.ui-demo/`.

Deliver `final.mp4` (plays inline on Slack, Jira, Confluence, GitHub), plus `poster.png` where a still is enough. Mention duration and step count in one line.

## Reference

- `reference/verify-runner.md` — **the core**: STEPS schema, demo helpers, `run()` options, `steps.json`, report + warnings, `--from` resume, `storageState` reuse.
- `reference/recording-snippets.md` — overlay snippets, `render.py` options, ffmpeg one-liners.
- `reference/troubleshooting.md` — MCP unavailable, blocked verification, corrupted recording, TomSelect, zsh gotcha.
- `reference/learnings.md` — measured findings behind the rules + commcare-connect gotchas.
- `profiles/commcare-connect/` — `README.md`, `connect.mjs`, `seed.py`, `record_settings.py`, `serve.sh` (port check, DEBUG off, `--insecure` when the whitenoise manifest is missing, readiness wait), `reseed.sh`, example flows.
