# Learnings

The measured findings behind SKILL.md's rules. Read only when questioning or re-testing a rule — the rules themselves, with a one-line why, live in SKILL.md. Measured on Playwright 1.61, Chromium, ffmpeg 8.1.

## Capture

- **`page.screencast` is the capture primitive.** It is the same CDP frame stream Playwright MCP's `browser_start_video` uses (identical frame-for-frame on sub-1 s page hops), works from a standalone script, and adds chapter cards (`showChapter`) and overlays (`showOverlay`). Preferred over `context({ recordVideo })`.
- **Never drive a recording one MCP tool call at a time.** Every round-trip between calls is real wall-clock time baked into the continuous capture: ~17 s of intended pacing came out at 71 s (76% dead air). The same steps in one script: 22.5 s.
- **`deviceScaleFactor: 2` gives 2x frames only when headed.** Headless (shell or full Chromium) silently stays at 1x; headed with `size` = 2× viewport gives true 2x. Chromium captures the compositor surface in physical pixels, and headless keeps it at 1x.
- **Playwright's own recorder is VP8 at a flat 1 Mbit/s**, which smears text at 2x, and `screencast.start({ quality })` barely changes it. Hence `onFrame` JPEG frames (quality 100) piped into ffmpeg/libx264. Frames arrive only when the page repaints, so the runner fills a constant-fps timeline by wall clock.
- **Injected DOM and `data:` URLs can be silently missing from the video** while rendering fine in `page.screenshot()` — seen with large, newly injected full-viewport overlays and with `data:text/html` navigations. Real navigations are always captured. Use real HTTP pages and `showOverlay` only.

## Overlays

- **`page.screencast.showOverlay()` is captured, survives navigation, and can carry CSS animations.** Playwright re-adds overlays on each new document. Highlight ring, `@keyframes` ripple and `showChapter` all render in the video. Overlays are `pointer-events: none`; `showOverlay(html, { duration })` blocks for `duration`.
- **`showActions` makes every Playwright action block for its annotation duration.** With `duration: 700`: each `mouse.move` ≈ 700 ms (16 waypoints = 11.3 s), `click` 717 ms, `fill` 708 ms, versus 1 ms for a `showOverlay` update. That is why the cursor is a sticky `showOverlay` re-added per tick, and why `showActions` is never enabled.
- **Inline `<svg>` in `showOverlay` HTML renders only with inline styles.** Playwright's injected `highlight.css` (adopted into the overlay's shadow root) sets `svg { position: absolute; height: 0 }`; an inline `style="position:static;width:…;height:…"` beats it. Other inherited defaults to override on text overlays: `:host { font-size:13px; font-family:system-ui; color:#333 }`.
- **Spring cursor, not a fixed-time ease.** A fixed 0.8 s eased glide ignored distance and could stop a pixel short. The runner uses a spring (tension 470, mass 3, friction 70 at 60 Hz, ζ≈0.93) with the target set from the first tick, then a hard snap and a 120 ms landing beat.

## Rendering

- **Precompute the device frame.** A per-frame `geq` shadow took >2 min for 4 s of 1600×1000 video; the mask, shadow and gradient rendered once as PNGs took 0.8 s. **Gotcha:** `-loop 1` PNG inputs are infinite and `alphamerge` repeats the last frame by default, so the graph never ends — use `alphamerge=shortest=1` and `overlay=shortest=1`.
- **Downscale in ffmpeg's decode filter, not in Python.** Moving the 2x→1.5x scale into ffmpeg cut a 31 s render from 37 s to 7.8 s; Python only touches frames that carry a caption.
- **Caption font.** Helvetica Neue Bold is visibly better weighted and spaced than Arial Bold. SF can't be made bold via a face index and is licensed for Apple platforms only. Elsewhere `render.py` falls back to DejaVu, then Pillow's bundled scalable font.

## commcare-connect gotchas from real recordings

- **Reseed before every Record Pass.** The Verify Run mutates data (accepts invites, creates users); recording on top of it changes the story or fails outright.
- **The org slug is generated from the name** (`slugify_uniquely`), so the seed looks orgs up by name and asserts the slug.
- **Switching identity mid-flow needs `useState: false`.** Otherwise the runner saves the second user's session as the auth state and the next run's admin-only steps fail.
- **`set_password()` logs out every live session of that user** — Django derives the session auth hash from the password hash. The seed only sets the password when it doesn't already match, so reseeding doesn't kill a recording running against the same local DB.
- **allauth bounces unverified emails to a verification page mid-login** → the seed marks every `EmailAddress` verified.
- **Auth-layout pages (login, signup) have no `<main>`** — use `form` as their checkpoint.
- **TomSelect:** see `troubleshooting.md` "TomSelect picker" and use `c.pickTomSelect()`. Two more: TomSelect keeps the typed query after a pick, so a second pick on the same multi-select searches "KenyaUganda" — clear it with `tomselect.setTextboxValue('')` first. A selected `.item` carries a `×`, so assert with `toContainText`, not exact text. A value preselected by the seed is hidden from its own dropdown.
- **A 500 on every page under `DEBUG=False`** is usually a stale staticfiles manifest → `npm run build` then `./manage.py collectstatic`.
- **The test-data warning fires on Django admin's "Is test" label** — expected there, not a seed problem.
- **The shared dev DB leaks other data** into admin lists (e.g. other workspaces' invites). Filter or search the list on camera rather than deleting someone else's rows.
