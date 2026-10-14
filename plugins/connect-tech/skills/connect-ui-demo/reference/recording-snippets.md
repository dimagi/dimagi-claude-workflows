# Recording & Render Snippets

Copy-paste material for `flow.mjs` and `render.py`. Only read this file while actually writing the script or choosing render flags — SKILL.md's Execution Flow is enough for every other step. The runner itself — demo helpers (`d.click/type/select/goto`), cursor, ring, ripple, caption holds and the `steps.json` writer — is `runner.mjs`; its schema and options are in `reference/verify-runner.md`.

## Overlay snippets

Capture, cursor, ring and ripple are handled by `runner.mjs` (rationale in `reference/learnings.md`). For extra visuals use only `page.screencast.showOverlay(html, { duration? })`; inline `<svg>` needs `style="position:static;width:…;height:…"` and text overlays need explicit font/colour. A sticky overlay (no `duration`) returns a disposable (`await tag.dispose()`); with `duration` it awaits, doubling as a pacing pause.

```js
// persistent badge
const badge = await page.screencast.showOverlay(`<div style="position:absolute;top:14px;right:14px;padding:6px 12px;background:rgba(17,24,39,.85);color:#fff;border-radius:10px;font:600 15px system-ui">NEW · admin notification</div>`);

// element callout from a locator's bounding box
const b = await page.locator(sel).boundingBox();
await page.screencast.showOverlay(`
  <div style="position:absolute;left:${b.x-6}px;top:${b.y-6}px;width:${b.width+12}px;height:${b.height+12}px;border:3px solid #ed6a14;border-radius:10px;box-shadow:0 0 0 2px #fff"></div>
  <div style="position:absolute;left:${b.x + b.width/2}px;top:${b.y + b.height + 10}px;transform:translateX(-50%);padding:6px 10px;background:#111827;color:#fff;border-radius:8px;font:600 14px system-ui;white-space:nowrap">Both admins are listed here</div>`,
  { duration: 1800 });
```

## `render.py` — Post-Process

```bash
PY=../venv/bin/python   # from the task folder, <repo>/.ui-demo/<task>/
$PY render.py --task .                       # final.mp4 + poster.png + render.json (frame on, captions on, x264)
$PY render.py --task . --fast                # quick preview (VideoToolbox on macOS, libx264 ultrafast elsewhere) while iterating captions
$PY render.py --task . --action-speed 1.5    # typing/navigation segments 1.5x; caption holds stay 1x
$PY render.py --task . --no-frame            # bare 1920x1200, e.g. for embedding in slides
$PY render.py --task . --scale 1             # 1280x800 output, smaller file
$PY render.py --task . --spot-dim 0          # no spotlight dim
$PY render.py --task . --bg light            # light gradient frame
$PY render.py --task . --crf 21 --max-mb 8   # tighter size budget
```

What it does, in one decode→Python→encode pass (source of truth is the docstring in `render.py`):

1. **Time map**: action segments `[actionStart, actionEnd]` ≥1 s long run at `--action-speed`; everything else at 1x. Caption windows are remapped through the same map. Frames are dropped, never duplicated (no slow-down).
1b. **2x → `--scale`**: ffmpeg downscales the 2560×1600 source to 1.5× the CSS size (1920×1200) during decode (`scale=…:flags=lanczos`, bilinear under `--fast`), so Python receives output-size frames and passes overlay-free frames through untouched.
1c. **Spotlight**: for each `spots` entry, a precomputed feathered L-mask (40% dim, hole = box + 8 px) composited with black; 0.2 s fades; skipped for boxes >40% of the frame; ends at the next navigation.
2. **Intent pill** during `[actionStart, actionEnd]` (one line, 3% of frame height, orange dot), then the **caption** card = dark translucent box, orange accent bar, white **Helvetica Neue Bold** title (4.4% of frame height), grey Helvetica Neue subtitle (2.6%), rounded corners, 0.2 s fades. Flipped to the top when the step's clicked target sits in the bottom 28% of the frame. Bottom-centre inside a 5% safe margin; top (`9%` down) when `captionPos: 'top'`, when the clicked target sits below 72% of the frame and the step did not navigate, or when the step's `result` box overlaps the bottom caption band (78–95%) but not the top one (9–26%). Wraps to at most two lines per block at 80% frame width.
3. **Device frame**: 5% padding, linear gradient background, rounded video corners (r ≈ 2% of height), soft shadow. Background/mask/shadow are rendered **once** as PNGs (the per-frame `geq` variant is 100× slower — `reference/learnings.md`).
4. **Encode**: `libx264 -crf 19 -preset slow -tune stillimage -pix_fmt yuv420p -g 30 -movflags +faststart` → plays inline on Slack, Jira, Confluence, GitHub. `--fast` = `h264_videotoolbox -b:v 6M` on macOS, `libx264 -preset ultrafast` where VideoToolbox is missing.
5. **Budget**: > `--max-mb` (default 10, GitHub's free-plan attachment cap) → one automatic re-encode at `crf+3`. `render.json` records `over_budget`.
6. **Poster**: `poster.png` from t≈1 s (the intro card).

Typical cost: a 57 s 2560×1600 recording → ~20 s with libx264 slow at 1920×1200 (5.6 MB with `--action-speed 1.5`). Python only paints frames with an intent, caption or spotlight.

## Manual ffmpeg equivalents (when you need one piece, not the pipeline)

```bash
# probe
ffprobe -v error -show_entries stream=width,height,r_frame_rate:format=duration -of default=noprint_wrappers=1 output/final.mp4

# sample a frame — -ss AFTER -i for frame accuracy; always downscale before viewing (image tokens ∝ pixel area)
ffmpeg -y -i output/final.mp4 -ss 5 -frames:v 1 -vf scale=800:-1 frame.png

# scene-change spread (corruption check — should spread across the whole duration, not cluster early)
ffmpeg -y -i output/raw.mp4 -vf "select='gt(scene,0.01)',showinfo" -vsync vfr -f null - 2>&1 | grep pts_time | sed -E 's/.*pts_time:([0-9.]+).*/\1/'

# flat speed-up of an already-rendered file (captions speed up too)
ffmpeg -y -i output/final.mp4 -filter:v "setpts=PTS/1.5" -an -c:v libx264 -crf 19 -preset slow -tune stillimage -pix_fmt yuv420p -movflags +faststart final_1.5x.mp4

# GIF for a README/PR hero (only for <15 s silent clips; 5–10x larger than mp4)
ffmpeg -y -i output/final.mp4 -vf "fps=12,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" demo.gif

# clip a section (e.g. the one step a reviewer asked about)
ffmpeg -y -ss 12 -to 24 -i output/final.mp4 -c copy clip.mp4
```
