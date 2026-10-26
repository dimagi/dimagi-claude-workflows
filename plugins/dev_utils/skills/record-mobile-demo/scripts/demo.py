#!/usr/bin/env python3
"""Drive an Android device or emulator, and record and polish demo videos of a flow."""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import xml.etree.ElementTree as ET
from pathlib import Path

STATE = Path(tempfile.gettempdir()) / "record-mobile-demo-state.json"
KEYS = {
    "back": "KEYCODE_BACK",
    "home": "KEYCODE_HOME",
    "enter": "KEYCODE_ENTER",
    "tab": "KEYCODE_TAB",
    "del": "KEYCODE_DEL",
    "recents": "KEYCODE_APP_SWITCH",
    "menu": "KEYCODE_MENU",
    "search": "KEYCODE_SEARCH",
}
FONTS = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
SHELL_SPECIAL = set("\\()<>|;&*'\"`$~?!#[]{}")
WINDOWS = os.name == "nt"


class Fail(Exception):
    pass


def run(cmd, check=True, timeout=120, binary=False):
    kw = {} if binary else {"text": True, "encoding": "utf-8", "errors": "replace"}
    p = subprocess.run([str(c) for c in cmd], capture_output=True, timeout=timeout, **kw)
    if check and p.returncode != 0:
        err = p.stderr if not binary else p.stderr.decode("utf-8", "replace")
        raise Fail(f"{' '.join(map(str, cmd))} failed: {(err or '').strip()[:600]}")
    return p


def connected():
    lines = run(["adb", "devices"]).stdout.splitlines()[1:]
    return [l.split()[0] for l in lines if l.strip().endswith("\tdevice") or l.strip().endswith(" device")]


def sdk_root():
    for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(var):
            return Path(os.environ[var])
    if WINDOWS:
        return Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk"
    return Path.home() / ("Library/Android/sdk" if sys.platform == "darwin" else "Android/Sdk")


def emulator_bin():
    exe = sdk_root() / "emulator" / ("emulator.exe" if WINDOWS else "emulator")
    if not exe.exists():
        raise Fail(f"Emulator not found at {exe}")
    return exe


class Device:
    def __init__(self, serial=None):
        serial = serial or os.environ.get("ANDROID_SERIAL")
        if not serial:
            devs = connected()
            if not devs:
                raise Fail("No device connected. Plug one in with USB debugging on, or run: demo.py boot <avd>")
            if len(devs) > 1:
                raise Fail(f"Several devices connected ({', '.join(devs)}); pass -s SERIAL")
            serial = devs[0]
        self.serial = serial
        self._size = None

    def adb(self, *args, **kw):
        return run(["adb", "-s", self.serial, *args], **kw)

    def sh(self, cmd, **kw):
        return self.adb("shell", cmd, **kw).stdout

    def size(self):
        if not self._size:
            w, h = map(int, re.findall(r"(\d+)x(\d+)", self.sh("wm size"))[-1])
            self._size = (w, h)
        return self._size

    def dump(self):
        last = ""
        for _ in range(5):
            out = self.adb("exec-out", "uiautomator", "dump", "/dev/tty", check=False).stdout
            start, end = out.find("<hierarchy"), out.rfind("</hierarchy>")
            if start >= 0 and end > start:
                return ET.fromstring(out[start:end + len("</hierarchy>")])
            last = out.strip()
            time.sleep(0.6)
        raise Fail(f"uiautomator dump failed: {last[:300]}")

    def activity(self):
        out = self.sh("dumpsys activity activities | grep -m1 -E 'ResumedActivity'", check=False)
        m = re.search(r"\s(\S+/[^\s}]+)", out)
        name = m.group(1) if m else "?"
        return name + (" (LOCKED)" if self.locked() else "")

    def locked(self):
        out = self.sh("dumpsys window | grep -m1 mCurrentFocus", check=False)
        return "NotificationShade" in out or "Keyguard" in out

    def locate(self, sel, timeout=10, scroll=False):
        if "xy" in sel:
            return tuple(sel["xy"])
        deadline, scrolls = time.time() + timeout, 0
        while True:
            ns = nodes(self.dump())
            hits = find(ns, sel)
            if len(hits) > sel.get("index", 0):
                return hits[sel.get("index", 0)]["center"]
            if scroll and scrolls < 6:
                self.swipe("up")
                scrolls += 1
                time.sleep(0.6)
                continue
            if time.time() > deadline:
                raise Fail(f"Nothing matches {sel}. On screen ({self.activity()}):\n{render(ns, limit=40)}")
            time.sleep(0.4)

    def wait_gone(self, sel, timeout=15):
        deadline = time.time() + timeout
        while find(nodes(self.dump()), sel):
            if time.time() > deadline:
                raise Fail(f"{sel} still on screen after {timeout}s")
            time.sleep(0.5)

    def tap(self, xy):
        self.sh(f"input tap {xy[0]} {xy[1]}")

    def swipe(self, direction=None, coords=None, ms=350):
        if coords:
            x1, y1, x2, y2 = coords
        else:
            w, h = self.size()
            dx, dy = {"up": (0, -h * 0.4), "down": (0, h * 0.4), "left": (-w * 0.6, 0), "right": (w * 0.6, 0)}[direction]
            x1, y1, x2, y2 = int(w / 2 - dx / 2), int(h / 2 - dy / 2), int(w / 2 + dx / 2), int(h / 2 + dy / 2)
        self.sh(f"input swipe {x1} {y1} {x2} {y2} {ms}")

    def type(self, text, chunk=None, delay=0.0):
        if not text.isascii():
            raise Fail("adb can only type ASCII text")
        pieces = [text[i:i + chunk] for i in range(0, len(text), chunk)] if chunk else [text]
        for piece in pieces:
            self.sh("input text " + "".join("%s" if c == " " else ("\\" + c if c in SHELL_SPECIAL else c) for c in piece))
            time.sleep(delay)

    def key(self, name):
        self.sh("input keyevent " + KEYS.get(name.lower(), name))

    def launch(self, target, stop=False):
        pkg = target.split("/")[0]
        if stop:
            self.sh(f"am force-stop {pkg}")
        if "/" in target:
            self.sh(f"am start -n {target}")
        else:
            self.sh(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")


def nodes(root):
    out = []
    for n in root.iter("node"):
        b = re.findall(r"-?\d+", n.get("bounds", ""))
        if len(b) != 4:
            continue
        x1, y1, x2, y2 = map(int, b)
        if x2 <= x1 or y2 <= y1:
            continue
        a = n.attrib
        flag = lambda k: a.get(k) == "true"
        out.append({
            "text": a.get("text", ""),
            "desc": a.get("content-desc", ""),
            "id": a.get("resource-id", ""),
            "cls": a.get("class", "").rsplit(".", 1)[-1],
            "center": ((x1 + x2) // 2, (y1 + y2) // 2),
            "click": flag("clickable") or flag("long-clickable"),
            "scroll": flag("scrollable"),
            "checkable": flag("checkable"),
            "checked": flag("checked"),
            "focused": flag("focused"),
            "selected": flag("selected"),
            "enabled": a.get("enabled") != "false",
        })
    return out


def short_id(rid):
    return rid.split(":id/", 1)[-1]


def find(ns, sel):
    def score(n):
        if "id" in sel:
            return 3 if sel["id"] in (n["id"], short_id(n["id"])) else 0
        want = (sel.get("text") if "text" in sel else sel.get("desc", "")).strip().lower()
        fields = [n["text"], n["desc"]] if "text" in sel else [n["desc"]]
        best = 0
        for f in fields:
            f = f.strip().lower()
            if not f:
                continue
            best = max(best, 3 if f == want else 1 if want in f else 0)
        return best

    scored = [(score(n), n) for n in ns]
    top = max((s for s, _ in scored), default=0)
    return [n for s, n in scored if top and s == top]


def render(ns, limit=None):
    lines = []
    for n in ns:
        sid = short_id(n["id"]) if n["id"] else ""
        interactive = n["click"] or n["scroll"] or n["checkable"]
        if not (n["text"] or n["desc"] or (interactive and sid)):
            continue
        parts = [n["cls"]]
        if n["text"]:
            parts.append(json.dumps(n["text"][:70], ensure_ascii=False))
        if n["desc"] and n["desc"] != n["text"]:
            parts.append("desc=" + json.dumps(n["desc"][:70], ensure_ascii=False))
        if sid:
            parts.append("id=" + sid)
        parts.append("@%d,%d" % n["center"])
        for name, on in (("click", n["click"]), ("scroll", n["scroll"]), ("checked", n["checked"]),
                         ("unchecked", n["checkable"] and not n["checked"]), ("focused", n["focused"]),
                         ("selected", n["selected"]), ("disabled", not n["enabled"])):
            if on:
                parts.append(name)
        lines.append(" ".join(parts))
    if limit and len(lines) > limit:
        lines = lines[:limit] + [f"... {len(lines) - limit} more"]
    return "\n".join(lines)


def execute(dev, step, natural=False):
    a = step["action"]
    if a == "tap":
        dev.tap(dev.locate(step["sel"], timeout=step.get("timeout", 10), scroll=step.get("scroll", False)))
    elif a == "type":
        dev.type(step["text"], *((3, 0.08) if natural else (None, 0)))
    elif a == "key":
        dev.key(step["key"])
    elif a == "swipe":
        dev.swipe(step.get("dir"), step.get("coords"))
    elif a == "wait":
        if step.get("gone"):
            dev.wait_gone(step["sel"], timeout=step.get("timeout", 15))
        else:
            dev.locate(step["sel"], timeout=step.get("timeout", 15))
    elif a == "launch":
        dev.launch(step["target"], step.get("stop", False))
    elif a == "sleep":
        time.sleep(step["secs"])
    else:
        raise Fail(f"Unknown action {a}")


class Recorder:
    def __init__(self, dev, raw, max_size=1280, fps=30):
        self.dev, self.raw, self.max_size, self.fps = dev, Path(raw), max_size, fps
        self.kind = "scrcpy" if shutil.which("scrcpy") else "screenrecord"

    def start(self):
        self.raw.unlink(missing_ok=True)
        self.log = open(self.raw.with_suffix(".rec.log"), "w")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0
        if self.kind == "scrcpy":
            cmd = ["scrcpy", "-s", self.dev.serial, "--no-window", "--no-audio", "--no-control",
                   f"--record={self.raw}", "--record-format=mkv", f"--max-size={self.max_size}",
                   f"--max-fps={self.fps}", "--video-bit-rate=8M"]
        else:
            cmd = ["adb", "-s", self.dev.serial, "shell", "screenrecord", "--bit-rate", "8000000", "/sdcard/record-mobile-demo.mp4"]
        self.proc = subprocess.Popen(cmd, stdout=self.log, stderr=subprocess.STDOUT, creationflags=flags,
                                     start_new_session=not WINDOWS)
        log_path = Path(self.log.name)
        deadline = time.time() + 15
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise Fail(f"{self.kind} exited early, see {self.log.name}")
            if self.kind == "screenrecord" or "Recording started" in log_path.read_text(errors="replace"):
                break
            time.sleep(0.05)
        else:
            raise Fail(f"Recording did not start, see {self.log.name}")
        return time.time()

    def stop(self):
        if self.kind == "scrcpy":
            try:
                self.proc.send_signal(signal.CTRL_BREAK_EVENT if WINDOWS else signal.SIGINT)
                self.proc.wait(10)
            except (subprocess.TimeoutExpired, OSError):
                self.proc.kill()
                self.proc.wait()
        else:
            self.dev.sh("pkill -INT screenrecord", check=False)
            self.proc.wait(10)
            time.sleep(1)
            self.dev.adb("pull", "/sdcard/record-mobile-demo.mp4", str(self.raw))
            self.dev.sh("rm /sdcard/record-mobile-demo.mp4", check=False)
        self.log.close()
        if not self.raw.exists() or self.raw.stat().st_size == 0:
            raise Fail(f"No video was written, see {self.log.name}")


def probe(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
               "-of", "json", path]).stdout
    data = json.loads(out)
    s = data["streams"][0]
    return int(s["width"]), int(s["height"]), float(data["format"].get("duration", 0))


def ff_quote(s):
    return "'" + s.replace("\\", "/").replace("'", "'\\''").replace(":", "\\:") + "'"


def captions_from_timeline(timeline):
    caps = [s for s in timeline.get("steps", []) if s.get("caption")]
    return [(max(0.0, s["shown"]), caps[i + 1]["shown"] if i + 1 < len(caps) else None, s["caption"])
            for i, s in enumerate(caps)]


def polish(raw, out, captions, segments=None, height=1280, crf=28, gif=False, tail=1.0):
    """captions are (start, end or None, text) on the output timeline; segments re-time the raw video."""
    raw, out = Path(raw).resolve(), Path(out).resolve()
    iw, ih, dur = probe(raw)
    oh = min(height, ih) // 2 * 2
    ow = round(iw * oh / ih / 2) * 2
    if segments:
        k = len(segments)
        chains = [f"[0:v]fps=30,scale={ow}:{oh}:flags=lanczos,split={k}" + "".join(f"[i{i}]" for i in range(k))]
        for i, s in enumerate(segments):
            if s[0] == "play":
                _, a, b, sp = s
                chains.append(f"[i{i}]trim=start={a:.3f}:end={b:.3f},setpts=(PTS-STARTPTS)/{sp}[p{i}]")
            else:
                _, t, hold = s
                chains.append(f"[i{i}]trim=start={max(0.0, t - 0.1):.3f}:end={max(0.1, t):.3f},setpts=PTS-STARTPTS,"
                              f"tpad=stop_mode=clone:stop_duration={hold}[p{i}]")
        graph = ";".join(chains) + ";" + "".join(f"[p{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=0,fps=30"
    else:
        graph = f"[0:v]scale={ow}:{oh}:flags=lanczos,tpad=stop_mode=clone:stop_duration={tail}"
    filters = []
    font = next((f for f in FONTS if Path(f).exists()), None)
    work = Path(tempfile.mkdtemp(prefix="record-mobile-demo-"))
    if captions and font:
        size = max(18, round(min(ow, oh) / 24))
        wrap = max(16, int(ow * 0.9 / (size * 0.5)))
        lines = max(len(textwrap.wrap(c[2], wrap)) for c in captions)
        bar = (round(size * (1.5 * lines + 1.2)) + 1) // 2 * 2
        filters.append(f"pad={ow}:{oh + bar}:0:0:color=0x1b1b1f")
        for i, (start, end, text) in enumerate(captions):
            (work / f"cap{i}.txt").write_text("\n".join(textwrap.wrap(text, wrap)), encoding="utf-8", newline="\n")
            when = f"between(t,{start:.2f},{end:.2f})" if end else f"gte(t,{start:.2f})"
            filters.append(
                f"drawtext=fontfile={ff_quote(font)}:textfile=cap{i}.txt:fontsize={size}:fontcolor=white"
                f":line_spacing={size // 5}:x=(w-text_w)/2:y={oh}+({bar}-text_h)/2:enable='{when}'")
    elif captions:
        print("No font found; captions skipped", file=sys.stderr)
    (work / "filter.txt").write_text(graph + "".join("," + f for f in filters) + "[out]", encoding="utf-8")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
                    "-filter_complex_script", "filter.txt", "-map", "[out]", "-r", "30", "-c:v", "libx264",
                    "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
                    str(out)],
                   cwd=work, check=True)
    results = [out]
    if gif:
        g = out.with_suffix(".gif")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", out, "-vf",
             "fps=12,scale=360:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
             g])
        results.append(g)
    shutil.rmtree(work, ignore_errors=True)
    for r in results:
        mb = r.stat().st_size / 1e6
        warn = "  (over GitHub's 10 MB limit: re-run polish with a higher --crf or lower --height)" if mb > 10 else ""
        print(f"{r}  {mb:.1f} MB{warn}")
    fw, fh, fd = probe(out)
    print(f"duration {fd:.1f}s, {fw}x{fh}")


def load_flow(path):
    steps = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    if not steps:
        raise Fail(f"{path} has no steps")
    return steps


def selector(args):
    for k in ("text", "id", "desc"):
        if getattr(args, k, None) is not None:
            sel = {k: getattr(args, k)}
            break
    else:
        if not getattr(args, "xy", None):
            raise Fail("Give --text, --id, --desc or --xy")
        sel = {"xy": [int(v) for v in args.xy.split(",")]}
    if getattr(args, "index", 0):
        sel["index"] = args.index
    return sel


def step_from(args):
    a = args.cmd
    if a == "tap":
        step = {"action": "tap", "sel": selector(args)}
        if args.scroll:
            step["scroll"] = True
    elif a == "wait":
        step = {"action": "wait", "sel": selector(args), "timeout": args.timeout}
        if args.gone:
            step["gone"] = True
    elif a == "type":
        step = {"action": "type", "text": args.value}
    elif a == "key":
        step = {"action": "key", "key": args.value}
    elif a == "swipe":
        step = {"action": "swipe"}
        if args.value in ("up", "down", "left", "right"):
            step["dir"] = args.value
        else:
            step["coords"] = [int(v) for v in args.value.split(",")]
    elif a == "launch":
        step = {"action": "launch", "target": args.value, "stop": args.stop}
    else:
        step = {"action": "sleep", "secs": float(args.value)}
    if getattr(args, "caption", None):
        step["caption"] = args.caption
    if getattr(args, "pause", None) is not None:
        step["pause"] = args.pause
    if getattr(args, "setup", False):
        step["setup"] = True
    return step


def cmd_action(args):
    dev = Device(args.serial)
    step = step_from(args)
    execute(dev, step)
    if args.log:
        with open(args.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(step, ensure_ascii=False) + "\n")
    print("ok" + (f" (logged to {args.log})" if args.log else ""))
    if not args.quiet and step["action"] != "sleep":
        time.sleep(args.settle)
        print(f"[{dev.activity()}]")
        print(render(nodes(dev.dump()), limit=None if args.all else 60))


def cmd_screen(args):
    dev = Device(args.serial)
    print(f"[{dev.activity()}]")
    print(render(nodes(dev.dump()), limit=None if args.all else 60))


def cmd_shot(args):
    dev = Device(args.serial)
    out = Path(args.out).resolve()
    png = dev.adb("exec-out", "screencap", "-p", binary=True).stdout
    tmp = out.with_suffix(".full.png")
    tmp.write_bytes(png)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", tmp, "-vf", f"scale={args.width}:-2", out])
    tmp.unlink()
    print(out)


def cmd_devices(args):
    devs = connected()
    print("connected:", ", ".join(devs) if devs else "none")
    try:
        avds = run([emulator_bin(), "-list-avds"]).stdout.split()
        print("emulators:", ", ".join(a for a in avds if a) or "none")
    except Fail as e:
        print(e)


def cmd_boot(args):
    before = set(connected())
    cmd = [emulator_bin(), "-avd", args.avd, "-no-boot-anim", "-no-audio"]
    if args.snapshot:
        cmd += ["-snapshot", args.snapshot]
    log = open(Path(tempfile.gettempdir()) / f"emulator-{args.avd}.log", "w")
    flags = (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP) if WINDOWS else 0
    subprocess.Popen([str(c) for c in cmd], stdout=log, stderr=subprocess.STDOUT, creationflags=flags,
                     start_new_session=not WINDOWS)
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        new = [d for d in connected() if d not in before and d.startswith("emulator-")]
        if new:
            dev = Device(new[0])
            if dev.sh("getprop sys.boot_completed", check=False).strip() == "1":
                print(f"booted {args.avd} as {dev.serial}")
                return
        time.sleep(2)
    raise Fail(f"{args.avd} did not boot within {args.timeout}s, see {log.name}")


def cmd_snapshot(args):
    dev = Device(args.serial)
    if not dev.serial.startswith("emulator-"):
        raise Fail("Snapshots only work on an emulator")
    out = dev.adb("emu", "avd", "snapshot", args.op, args.name).stdout.strip()
    if "KO" in out:
        raise Fail(out)
    print(f"snapshot {args.op} {args.name}: ok")


def read_state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {}


def cmd_prep(args):
    dev = Device(args.serial)
    state = read_state()
    if dev.serial not in state:
        state[dev.serial] = {"show_touches": dev.sh("settings get system show_touches", check=False).strip()}
        STATE.write_text(json.dumps(state))
    cmds = ["input keyevent KEYCODE_WAKEUP", "wm dismiss-keyguard", "settings put system show_touches 1",
            "svc power stayon true"]
    if not args.no_demo_bar:
        demo = "am broadcast -a com.android.systemui.demo -e command"
        cmds += [
            "settings put global sysui_demo_allowed 1",
            f"{demo} enter",
            f"{demo} clock -e hhmm 1000",
            f"{demo} battery -e level 100 -e plugged false",
            f"{demo} network -e wifi show -e level 4 -e fully true",
            f"{demo} network -e mobile show -e datatype none -e level 4",
            f"{demo} notifications -e visible false",
        ]
    dev.sh(" ; ".join(c + " >/dev/null" for c in cmds), check=False)
    print(f"{dev.serial}: touches shown, screen kept on" + ("" if args.no_demo_bar else ", demo status bar on"))
    time.sleep(0.5)
    if dev.locked():
        print("WARNING: the screen is locked with a PIN or pattern; ask the user to unlock it by hand")


def cmd_reset(args):
    dev = Device(args.serial)
    state = read_state()
    touches = state.pop(dev.serial, {}).get("show_touches", "0")
    touches = touches if touches in ("0", "1") else "0"
    STATE.write_text(json.dumps(state))
    dev.sh(" ; ".join([
        "am broadcast -a com.android.systemui.demo -e command exit >/dev/null",
        f"settings put system show_touches {touches}",
        "svc power stayon false",
    ]), check=False)
    print(f"{dev.serial}: demo mode off, touches restored to {touches}")


def cmd_play(args):
    dev = Device(args.serial)
    steps = load_flow(args.flow)
    setup = [s for s in steps if s.get("setup")]
    steps = [s for s in steps if not s.get("setup")]
    for step in setup:
        execute(dev, step)
        print(f"setup {step['action']}")
    if setup:
        time.sleep(args.settle)
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    rec = None if args.no_record else Recorder(dev, out.with_suffix(".raw.mkv" if shutil.which("scrcpy") else ".raw.mp4"))
    if args.no_record:
        t0 = time.time()
    else:
        t0 = rec.start()
    timeline = []
    try:
        time.sleep(args.lead)
        for i, step in enumerate(steps):
            shown = time.time() - t0
            time.sleep(step.get("pause", args.pace))
            start = time.time() - t0
            execute(dev, step, natural=True)
            timeline.append({"i": i, "action": step["action"], "shown": round(shown, 2), "start": round(start, 2),
                             "end": round(time.time() - t0, 2), "caption": step.get("caption")})
            print(f"{i + 1}/{len(steps)} {step['action']} {step.get('caption') or ''}".rstrip())
        time.sleep(args.tail)
    finally:
        if rec:
            rec.stop()
    if args.no_record:
        print(f"dry run ok, {time.time() - t0:.1f}s")
        return
    data = {"raw": str(rec.raw), "steps": timeline}
    tl = out.with_suffix(".timeline.json")
    tl.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"raw {rec.raw}\ntimeline {tl}")
    if not args.raw_only:
        polish(rec.raw, out, captions_from_timeline(data), None, args.height, args.crf, args.gif)


def cmd_polish(args):
    data = json.loads(Path(args.timeline).read_text(encoding="utf-8"))
    raw = args.raw or data["raw"]
    if data.get("kind") == "maestro":
        segments, captions = retime(data["steps"], probe(raw)[2], args.hold, args.payoff, args.fast_after, args.speed)
        polish(raw, args.out, captions, segments, args.height, args.crf, args.gif)
    else:
        polish(raw, args.out, captions_from_timeline(data), None, args.height, args.crf, args.gif)


COMPOUND = ("runFlow", "repeat", "retry", "applyConfiguration", "defineVariables", "evalScript", "runScript")


def maestro_bin():
    found = shutil.which("maestro")
    if found:
        return found
    for pattern in (".maestro/bin/maestro*", ".maestro*/maestro/bin/maestro*"):
        for cand in sorted(Path.home().glob(pattern), reverse=True):
            if cand.suffix.lower() == (".bat" if WINDOWS else ""):
                return str(cand)
    raise Fail("maestro CLI not found; install it and put its bin folder on PATH")


def maestro_steps(debug_dir, t0):
    steps = []
    for f in Path(debug_dir).rglob("commands-*.json"):
        for e in json.loads(f.read_text(encoding="utf-8")):
            name, body = next(iter(e["command"].items()))
            meta = e.get("metadata") or {}
            if "timestamp" not in meta:
                continue
            start = meta["timestamp"] / 1000 - t0
            steps.append({"name": name, "label": body.get("label") if isinstance(body, dict) else None,
                          "status": meta.get("status"), "start": round(start, 3),
                          "end": round(start + (meta.get("duration") or 0) / 1000, 3)})
    return sorted(steps, key=lambda s: s["start"])


def retime(steps, video_dur, hold=1.2, payoff=3.0, fast_after=5.0, speed=8):
    """Plan the re-timed video: start at the first label, hold after each label, speed up long commands."""
    labelled = [s for s in steps if s["label"] and s["status"] == "COMPLETED"]
    if not labelled:
        raise Fail("No completed step has a label; add label: to the steps the video should show")
    begin = max(0.0, labelled[0]["start"])
    end = min(video_dur, labelled[-1]["end"] + 0.3)
    fast = []
    for s in steps:
        if s["name"].startswith(COMPOUND) or s["end"] - s["start"] < fast_after:
            continue
        a, b = max(begin, s["start"] + 1.5), min(end, s["end"] - 0.5)
        if b - a > 1:
            if fast and a <= fast[-1][1]:
                fast[-1][1] = max(fast[-1][1], b)
            else:
                fast.append([a, b])
    holds = {}
    for s in labelled:
        t = min(s["end"], end)
        holds[t] = max(holds.get(t, 0), payoff if s is labelled[-1] else hold)
    points = sorted({begin, end, *holds, *(p for iv in fast for p in iv)})
    points = [p for p in points if begin <= p <= end]
    segments = []
    for a, b in zip(points, points[1:]):
        if b - a > 0.02:
            sp = speed if any(x <= a + 1e-6 and b <= y + 1e-6 for x, y in fast) else 1
            segments.append(("play", a, b, sp))
        if b in holds:
            segments.append(("hold", b, holds[b]))

    def out_time(t):
        acc = 0.0
        for s in segments:
            if s[0] == "play":
                if t <= s[2]:
                    return acc + max(0.0, t - s[1]) / s[3]
                acc += (s[2] - s[1]) / s[3]
            else:
                acc += s[2]
        return acc

    starts = [out_time(s["start"] + 1e-4) for s in labelled]
    captions = [(starts[i], starts[i + 1] if i + 1 < len(starts) else None, s["label"])
                for i, s in enumerate(labelled)]
    return segments, captions


def cmd_maestro(args):
    dev = Device(args.serial)
    base = [maestro_bin(), "--device", dev.serial, "test", "--no-ansi"]
    pairs = list(args.env)
    if args.env_file:
        pairs = [l.strip() for l in Path(args.env_file).expanduser().read_text(encoding="utf-8").splitlines()
                 if "=" in l and not l.lstrip().startswith("#")] + pairs
    env = [x for e in pairs for x in ("-e", e)]
    if args.setup:
        print(f"setup: {args.setup}")
        p = subprocess.run(base + [args.setup] + env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode:
            raise Fail("setup flow failed:\n" + "\n".join((p.stdout + p.stderr).splitlines()[-20:]))
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    debug = out.with_suffix(".maestro")
    shutil.rmtree(debug, ignore_errors=True)
    rec = Recorder(dev, out.with_suffix(".raw.mkv"))
    t0 = rec.start()
    try:
        time.sleep(0.5)
        p = subprocess.run(base + [args.flow, "--debug-output", str(debug)] + env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        time.sleep(0.5)
    finally:
        rec.stop()
    log = [l for l in (p.stdout + p.stderr).splitlines() if l.strip()]
    print("\n".join(log[-30:]))
    steps = maestro_steps(debug, t0)
    data = {"kind": "maestro", "raw": str(rec.raw), "flow": str(Path(args.flow).resolve()), "steps": steps}
    tl = out.with_suffix(".timeline.json")
    tl.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"raw {rec.raw}\ntimeline {tl}")
    if p.returncode:
        raise Fail("the flow failed, so no demo was made; the raw recording shows what happened")
    segments, captions = retime(steps, probe(rec.raw)[2], args.hold, args.payoff, args.fast_after, args.speed)
    polish(rec.raw, out, captions, segments, args.height, args.crf, args.gif)


def cmd_contact(args):
    video, out = Path(args.video).resolve(), Path(args.out).resolve()
    _, _, dur = probe(video)
    n = args.frames
    cols = min(n, 4)
    rows = -(-n // cols)
    step = max(dur / n, 0.1)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-vf",
         f"fps=1/{step:.3f},scale=320:-2,tile={cols}x{rows}:padding=6:color=white", "-frames:v", "1", out])
    print(f"{out}  ({n} frames, one every {step:.1f}s, left to right)")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("-s", "--serial")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("devices").set_defaults(fn=cmd_devices)
    b = sub.add_parser("boot")
    b.add_argument("avd")
    b.add_argument("--snapshot")
    b.add_argument("--timeout", type=int, default=240)
    b.set_defaults(fn=cmd_boot)
    sn = sub.add_parser("snapshot")
    sn.add_argument("op", choices=["save", "load", "delete"])
    sn.add_argument("name")
    sn.set_defaults(fn=cmd_snapshot)
    pr = sub.add_parser("prep")
    pr.add_argument("--no-demo-bar", action="store_true")
    pr.set_defaults(fn=cmd_prep)
    sub.add_parser("reset").set_defaults(fn=cmd_reset)
    sc = sub.add_parser("screen")
    sc.add_argument("--all", action="store_true")
    sc.set_defaults(fn=cmd_screen)
    sh = sub.add_parser("shot")
    sh.add_argument("out")
    sh.add_argument("--width", type=int, default=540)
    sh.set_defaults(fn=cmd_shot)

    def action(name, value=False, sel=False):
        a = sub.add_parser(name)
        if value:
            a.add_argument("value")
        if sel:
            a.add_argument("--text")
            a.add_argument("--id")
            a.add_argument("--desc")
            a.add_argument("--xy")
            a.add_argument("--index", type=int, default=0)
        a.add_argument("--log", help="append the step to this flow file when it succeeds")
        a.add_argument("--caption")
        a.add_argument("--pause", type=float, help="seconds to linger before this step on replay")
        a.add_argument("--setup", action="store_true", help="on replay, run this step before recording starts")
        a.add_argument("--settle", type=float, default=1.0)
        a.add_argument("--quiet", action="store_true")
        a.add_argument("--all", action="store_true")
        a.set_defaults(fn=cmd_action)
        return a

    action("tap", sel=True).add_argument("--scroll", action="store_true")
    w = action("wait", sel=True)
    w.add_argument("--gone", action="store_true")
    w.add_argument("--timeout", type=float, default=15)
    action("type", value=True)
    action("key", value=True)
    action("swipe", value=True)
    action("launch", value=True).add_argument("--stop", action="store_true")
    action("sleep", value=True)

    pl = sub.add_parser("play")
    pl.add_argument("flow")
    pl.add_argument("--out", required=True)
    pl.add_argument("--pace", type=float, default=1.2)
    pl.add_argument("--lead", type=float, default=1.0)
    pl.add_argument("--tail", type=float, default=2.0)
    pl.add_argument("--settle", type=float, default=2.5, help="seconds to wait after setup steps")
    pl.add_argument("--no-record", action="store_true")
    pl.add_argument("--raw-only", action="store_true")
    pol = sub.add_parser("polish")
    pol.add_argument("timeline")
    pol.add_argument("--raw")
    pol.add_argument("--out", required=True)
    ma = sub.add_parser("maestro", help="record a Maestro flow and re-time it into a demo")
    ma.add_argument("flow")
    ma.add_argument("--out", required=True)
    ma.add_argument("--setup", help="flow to run first, unrecorded")
    ma.add_argument("-e", "--env", action="append", default=[], help="KEY=value passed to maestro")
    ma.add_argument("--env-file", help="KEY=value lines passed to maestro, e.g. a test account kept out of chat")
    for x in (ma, pol):
        x.add_argument("--hold", type=float, default=1.2, help="seconds held after each labelled step")
        x.add_argument("--payoff", type=float, default=3.0, help="seconds held after the last labelled step")
        x.add_argument("--fast-after", type=float, default=5.0, help="speed up commands longer than this")
        x.add_argument("--speed", type=float, default=8)
    for x in (pl, pol, ma):
        x.add_argument("--height", type=int, default=1280)
        x.add_argument("--crf", type=int, default=28)
        x.add_argument("--gif", action="store_true")
    pl.set_defaults(fn=cmd_play)
    pol.set_defaults(fn=cmd_polish)
    ma.set_defaults(fn=cmd_maestro)
    ct = sub.add_parser("contact")
    ct.add_argument("video")
    ct.add_argument("out")
    ct.add_argument("--frames", type=int, default=8)
    ct.set_defaults(fn=cmd_contact)

    args = p.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        args.fn(args)
    except Fail as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
