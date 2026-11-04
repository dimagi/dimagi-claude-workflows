#!/usr/bin/env python3
"""Drive an Android device or emulator, and record and polish demo videos of a flow."""
import argparse
import importlib.util
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
EDGE_VOICE = "en-US-JennyNeural"
SPEECH_GAP = 0.4


class Fail(Exception):
    pass


def run(cmd, check=True, timeout=120, binary=False, env=None):
    text_options = {} if binary else {"text": True, "encoding": "utf-8", "errors": "replace"}
    result = subprocess.run([str(part) for part in cmd], capture_output=True, timeout=timeout, env=env,
                            **text_options)
    if check and result.returncode != 0:
        stderr = result.stderr if not binary else result.stderr.decode("utf-8", "replace")
        raise Fail(f"{' '.join(map(str, cmd))} failed: {(stderr or '').strip()[:600]}")
    return result


def connected():
    lines = run(["adb", "devices"]).stdout.splitlines()[1:]
    return [line.split()[0] for line in lines
            if line.strip().endswith("\tdevice") or line.strip().endswith(" device")]


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
            devices = connected()
            if not devices:
                raise Fail("No device connected. Plug one in with USB debugging on, or run: demo.py boot <avd>")
            if len(devices) > 1:
                raise Fail(f"Several devices connected ({', '.join(devices)}); pass -s SERIAL")
            serial = devices[0]
        self.serial = serial
        self._size = None

    def adb(self, *args, **kwargs):
        return run(["adb", "-s", self.serial, *args], **kwargs)

    def sh(self, cmd, **kwargs):
        return self.adb("shell", cmd, **kwargs).stdout

    def size(self):
        if not self._size:
            width, height = map(int, re.findall(r"(\d+)x(\d+)", self.sh("wm size"))[-1])
            self._size = (width, height)
        return self._size

    def dump(self):
        last_output = ""
        for _ in range(5):
            output = self.adb("exec-out", "uiautomator", "dump", "/dev/tty", check=False).stdout
            start, end = output.find("<hierarchy"), output.rfind("</hierarchy>")
            if start >= 0 and end > start:
                return ET.fromstring(output[start:end + len("</hierarchy>")])
            last_output = output.strip()
            time.sleep(0.6)
        raise Fail(f"uiautomator dump failed: {last_output[:300]}")

    def activity(self):
        output = self.sh("dumpsys activity activities | grep -m1 -E 'ResumedActivity'", check=False)
        match = re.search(r"\s(\S+/[^\s}]+)", output)
        name = match.group(1) if match else "?"
        return name + (" (LOCKED)" if self.locked() else "")

    def locked(self):
        output = self.sh("dumpsys window | grep -m1 mCurrentFocus", check=False)
        return "NotificationShade" in output or "Keyguard" in output

    def locate(self, sel, timeout=10, scroll=False):
        if "xy" in sel:
            return tuple(sel["xy"])
        deadline, scrolls = time.time() + timeout, 0
        while True:
            screen_nodes = nodes(self.dump())
            matches = find(screen_nodes, sel)
            if len(matches) > sel.get("index", 0):
                return matches[sel.get("index", 0)]["center"]
            if scroll and scrolls < 6:
                self.swipe("up")
                scrolls += 1
                time.sleep(0.6)
                continue
            if time.time() > deadline:
                raise Fail(f"Nothing matches {sel}. On screen ({self.activity()}):\n{render(screen_nodes, limit=40)}")
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
            width, height = self.size()
            dx, dy = {"up": (0, -height * 0.4), "down": (0, height * 0.4),
                      "left": (-width * 0.6, 0), "right": (width * 0.6, 0)}[direction]
            x1, y1 = int(width / 2 - dx / 2), int(height / 2 - dy / 2)
            x2, y2 = int(width / 2 + dx / 2), int(height / 2 + dy / 2)
        self.sh(f"input swipe {x1} {y1} {x2} {y2} {ms}")

    def type(self, text, chunk=None, delay=0.0):
        if not text.isascii():
            raise Fail("adb can only type ASCII text")
        pieces = [text[i:i + chunk] for i in range(0, len(text), chunk)] if chunk else [text]
        for piece in pieces:
            escaped = "".join("%s" if char == " " else ("\\" + char if char in SHELL_SPECIAL else char)
                              for char in piece)
            self.sh("input text " + escaped)
            time.sleep(delay)

    def key(self, name):
        self.sh("input keyevent " + KEYS.get(name.lower(), name))

    def launch(self, target, stop=False):
        package = target.split("/")[0]
        if stop:
            self.sh(f"am force-stop {package}")
        if "/" in target:
            self.sh(f"am start -n {target}")
        else:
            self.sh(f"monkey -p {package} -c android.intent.category.LAUNCHER 1")


def nodes(root):
    found = []
    for node in root.iter("node"):
        bounds = re.findall(r"-?\d+", node.get("bounds", ""))
        if len(bounds) != 4:
            continue
        x1, y1, x2, y2 = map(int, bounds)
        if x2 <= x1 or y2 <= y1:
            continue
        attrs = node.attrib

        def flag(name):
            return attrs.get(name) == "true"

        found.append({
            "text": attrs.get("text", ""),
            "desc": attrs.get("content-desc", ""),
            "id": attrs.get("resource-id", ""),
            "cls": attrs.get("class", "").rsplit(".", 1)[-1],
            "center": ((x1 + x2) // 2, (y1 + y2) // 2),
            "click": flag("clickable") or flag("long-clickable"),
            "scroll": flag("scrollable"),
            "checkable": flag("checkable"),
            "checked": flag("checked"),
            "focused": flag("focused"),
            "selected": flag("selected"),
            "enabled": attrs.get("enabled") != "false",
        })
    return found


def short_id(resource_id):
    return resource_id.split(":id/", 1)[-1]


def find(screen_nodes, sel):
    def score(node):
        if "id" in sel:
            return 3 if sel["id"] in (node["id"], short_id(node["id"])) else 0
        wanted = (sel.get("text") if "text" in sel else sel.get("desc", "")).strip().lower()
        fields = [node["text"], node["desc"]] if "text" in sel else [node["desc"]]
        best = 0
        for field in fields:
            field = field.strip().lower()
            if not field:
                continue
            best = max(best, 3 if field == wanted else 1 if wanted in field else 0)
        return best

    scored = [(score(node), node) for node in screen_nodes]
    top = max((points for points, _ in scored), default=0)
    return [node for points, node in scored if top and points == top]


def render(screen_nodes, limit=None):
    lines = []
    for node in screen_nodes:
        sid = short_id(node["id"]) if node["id"] else ""
        interactive = node["click"] or node["scroll"] or node["checkable"]
        if not (node["text"] or node["desc"] or (interactive and sid)):
            continue
        parts = [node["cls"]]
        if node["text"]:
            parts.append(json.dumps(node["text"][:70], ensure_ascii=False))
        if node["desc"] and node["desc"] != node["text"]:
            parts.append("desc=" + json.dumps(node["desc"][:70], ensure_ascii=False))
        if sid:
            parts.append("id=" + sid)
        parts.append("@%d,%d" % node["center"])
        for name, on in (("click", node["click"]), ("scroll", node["scroll"]), ("checked", node["checked"]),
                         ("unchecked", node["checkable"] and not node["checked"]), ("focused", node["focused"]),
                         ("selected", node["selected"]), ("disabled", not node["enabled"])):
            if on:
                parts.append(name)
        lines.append(" ".join(parts))
    if limit and len(lines) > limit:
        lines = lines[:limit] + [f"... {len(lines) - limit} more"]
    return "\n".join(lines)


def execute(dev, step, natural=False):
    action = step["action"]
    if action == "tap":
        dev.tap(dev.locate(step["sel"], timeout=step.get("timeout", 10), scroll=step.get("scroll", False)))
    elif action == "type":
        dev.type(step["text"], *((3, 0.08) if natural else (None, 0)))
    elif action == "key":
        dev.key(step["key"])
    elif action == "swipe":
        dev.swipe(step.get("dir"), step.get("coords"))
    elif action == "wait":
        if step.get("gone"):
            dev.wait_gone(step["sel"], timeout=step.get("timeout", 15))
        else:
            dev.locate(step["sel"], timeout=step.get("timeout", 15))
    elif action == "launch":
        dev.launch(step["target"], step.get("stop", False))
    elif action == "sleep":
        time.sleep(step["secs"])
    else:
        raise Fail(f"Unknown action {action}")


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
            cmd = ["adb", "-s", self.dev.serial, "shell", "screenrecord", "--bit-rate", "8000000",
                   "/sdcard/record-mobile-demo.mp4"]
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
    output = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                  "stream=width,height:format=duration", "-of", "json", path]).stdout
    data = json.loads(output)
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"]), float(data["format"].get("duration", 0))


def ff_quote(value):
    return "'" + value.replace("\\", "/").replace("'", "'\\''").replace(":", "\\:") + "'"


def captions_from_timeline(timeline):
    captioned = [step for step in timeline.get("steps", []) if step.get("caption")]
    return [(max(0.0, step["shown"]), captioned[i + 1]["shown"] if i + 1 < len(captioned) else None, step["caption"])
            for i, step in enumerate(captioned)]


def narration_graph(captions, narration):
    """Delay each spoken line to its caption's start and mix them into one track."""
    chains = [f"[{i + 1}:a]adelay=delays={round(start * 1000)}:all=1[v{i}]" for i, (start, _, _) in enumerate(captions)]
    count = len(narration)
    if count == 1:
        return chains[0].replace("[v0]", "[aout]")
    return ";".join(chains) + ";" + "".join(f"[v{i}]" for i in range(count)) + \
        f"amix=inputs={count}:normalize=0:dropout_transition=0[aout]"


def polish(raw, out, captions, segments=None, height=1280, crf=28, gif=False, tail=1.0, narration=None):
    """captions are (start, end or None, text) on the output timeline; segments re-time the raw video.

    narration gives one audio clip per caption, played from the caption's start.
    """
    raw, out = Path(raw).resolve(), Path(out).resolve()
    raw_width, raw_height, _ = probe(raw)
    out_height = min(height, raw_height) // 2 * 2
    out_width = round(raw_width * out_height / raw_height / 2) * 2
    if segments:
        count = len(segments)
        chains = [f"[0:v]fps=30,scale={out_width}:{out_height}:flags=lanczos,split={count}"
                  + "".join(f"[i{i}]" for i in range(count))]
        for i, segment in enumerate(segments):
            if segment[0] == "play":
                _, seg_start, seg_end, speed = segment
                chains.append(f"[i{i}]trim=start={seg_start:.3f}:end={seg_end:.3f},setpts=(PTS-STARTPTS)/{speed}[p{i}]")
            else:
                _, at, hold = segment
                chains.append(f"[i{i}]trim=start={max(0.0, at - 0.1):.3f}:end={max(0.1, at):.3f},setpts=PTS-STARTPTS,"
                              f"tpad=stop_mode=clone:stop_duration={hold}[p{i}]")
        graph = (";".join(chains) + ";" + "".join(f"[p{i}]" for i in range(count))
                 + f"concat=n={count}:v=1:a=0,fps=30")
    else:
        graph = f"[0:v]scale={out_width}:{out_height}:flags=lanczos,tpad=stop_mode=clone:stop_duration={tail}"
    filters = []
    font = next((path for path in FONTS if Path(path).exists()), None)
    work = Path(tempfile.mkdtemp(prefix="record-mobile-demo-"))
    if captions and font:
        font_size = max(18, round(min(out_width, out_height) / 24))
        wrap_width = max(16, int(out_width * 0.9 / (font_size * 0.5)))
        max_lines = max(len(textwrap.wrap(text, wrap_width)) for _, _, text in captions)
        bar_height = (round(font_size * (1.5 * max_lines + 1.2)) + 1) // 2 * 2
        filters.append(f"pad={out_width}:{out_height + bar_height}:0:0:color=0x1b1b1f")
        for i, (start, end, text) in enumerate(captions):
            (work / f"cap{i}.txt").write_text("\n".join(textwrap.wrap(text, wrap_width)), encoding="utf-8", newline="\n")
            when = f"between(t,{start:.2f},{end:.2f})" if end else f"gte(t,{start:.2f})"
            filters.append(
                f"drawtext=fontfile={ff_quote(font)}:textfile=cap{i}.txt:fontsize={font_size}:fontcolor=white"
                f":line_spacing={font_size // 5}:x=(w-text_w)/2:y={out_height}+({bar_height}-text_h)/2:enable='{when}'")
    elif captions:
        print("No font found; captions skipped", file=sys.stderr)
    video_graph = graph + "".join("," + f for f in filters) + "[out]"
    if narration:
        inputs = [arg for clip in narration for arg in ("-i", str(clip))]
        audio = ["-map", "[aout]", "-c:a", "aac", "-b:a", "96k"]
        video_graph += ";" + narration_graph(captions, narration)
    else:
        inputs, audio = [], ["-an"]
    (work / "filter.txt").write_text(video_graph, encoding="utf-8")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw), *inputs,
                    "-filter_complex_script", "filter.txt", "-map", "[out]", "-r", "30", "-c:v", "libx264",
                    "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", *audio,
                    str(out)],
                   cwd=work, check=True)
    results = [out]
    if gif:
        gif_path = out.with_suffix(".gif")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", out, "-vf",
             "fps=12,scale=360:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];"
             "[b][p]paletteuse=dither=bayer:bayer_scale=4",
             gif_path])
        results.append(gif_path)
    shutil.rmtree(work, ignore_errors=True)
    for result in results:
        megabytes = result.stat().st_size / 1e6
        warning = ("  (over GitHub's 10 MB limit: re-run polish with a higher --crf or lower --height)"
                   if megabytes > 10 else "")
        print(f"{result}  {megabytes:.1f} MB{warning}")
    final_width, final_height, final_duration = probe(out)
    print(f"duration {final_duration:.1f}s, {final_width}x{final_height}")


def load_flow(path):
    steps = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not steps:
        raise Fail(f"{path} has no steps")
    return steps


def selector(args):
    for kind in ("text", "id", "desc"):
        if getattr(args, kind, None) is not None:
            sel = {kind: getattr(args, kind)}
            break
    else:
        if not getattr(args, "xy", None):
            raise Fail("Give --text, --id, --desc or --xy")
        sel = {"xy": [int(value) for value in args.xy.split(",")]}
    if getattr(args, "index", 0):
        sel["index"] = args.index
    return sel


def step_from(args):
    action = args.cmd
    if action == "tap":
        step = {"action": "tap", "sel": selector(args)}
        if args.scroll:
            step["scroll"] = True
    elif action == "wait":
        step = {"action": "wait", "sel": selector(args), "timeout": args.timeout}
        if args.gone:
            step["gone"] = True
    elif action == "type":
        step = {"action": "type", "text": args.value}
    elif action == "key":
        step = {"action": "key", "key": args.value}
    elif action == "swipe":
        step = {"action": "swipe"}
        if args.value in ("up", "down", "left", "right"):
            step["dir"] = args.value
        else:
            step["coords"] = [int(value) for value in args.value.split(",")]
    elif action == "launch":
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
        with open(args.log, "a", encoding="utf-8") as flow_file:
            flow_file.write(json.dumps(step, ensure_ascii=False) + "\n")
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
    full_size = out.with_suffix(".full.png")
    full_size.write_bytes(png)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", full_size, "-vf", f"scale={args.width}:-2", out])
    full_size.unlink()
    print(out)


def cmd_devices(args):
    devices = connected()
    print("connected:", ", ".join(devices) if devices else "none")
    try:
        avds = run([emulator_bin(), "-list-avds"]).stdout.split()
        print("emulators:", ", ".join(avd for avd in avds if avd) or "none")
    except Fail as error:
        print(error)


def cmd_boot(args):
    before = set(connected())
    cmd = [emulator_bin(), "-avd", args.avd, "-no-boot-anim", "-no-audio"]
    if args.snapshot:
        cmd += ["-snapshot", args.snapshot]
    log = open(Path(tempfile.gettempdir()) / f"emulator-{args.avd}.log", "w")
    flags = (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP) if WINDOWS else 0
    subprocess.Popen([str(part) for part in cmd], stdout=log, stderr=subprocess.STDOUT, creationflags=flags,
                     start_new_session=not WINDOWS)
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        new_devices = [serial for serial in connected() if serial not in before and serial.startswith("emulator-")]
        if new_devices:
            dev = Device(new_devices[0])
            if dev.sh("getprop sys.boot_completed", check=False).strip() == "1":
                print(f"booted {args.avd} as {dev.serial}")
                return
        time.sleep(2)
    raise Fail(f"{args.avd} did not boot within {args.timeout}s, see {log.name}")


def cmd_snapshot(args):
    dev = Device(args.serial)
    if not dev.serial.startswith("emulator-"):
        raise Fail("Snapshots only work on an emulator")
    output = dev.adb("emu", "avd", "snapshot", args.op, args.name).stdout.strip()
    if "KO" in output:
        raise Fail(output)
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
    dev.sh(" ; ".join(cmd + " >/dev/null" for cmd in cmds), check=False)
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
    setup = [step for step in steps if step.get("setup")]
    steps = [step for step in steps if not step.get("setup")]
    for step in setup:
        execute(dev, step)
        print(f"setup {step['action']}")
    if setup:
        time.sleep(args.settle)
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    recorder = None if args.no_record else Recorder(dev, out.with_suffix(".raw.mkv" if shutil.which("scrcpy") else ".raw.mp4"))
    if args.no_record:
        t0 = time.time()
    else:
        t0 = recorder.start()
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
        if recorder:
            recorder.stop()
    if args.no_record:
        print(f"dry run ok, {time.time() - t0:.1f}s")
        return
    data = {"raw": str(recorder.raw), "steps": timeline}
    timeline_path = out.with_suffix(".timeline.json")
    timeline_path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"raw {recorder.raw}\ntimeline {timeline_path}")
    if not args.raw_only:
        finish(data, recorder.raw, out, args)


def cmd_polish(args):
    data = json.loads(Path(args.timeline).read_text(encoding="utf-8"))
    finish(data, args.raw or data["raw"], args.out, args)


COMPOUND = ("runFlow", "repeat", "retry", "applyConfiguration", "defineVariables", "evalScript", "runScript")


def maestro_bin():
    found = shutil.which("maestro")
    if found:
        return found
    for pattern in (".maestro/bin/maestro*", ".maestro*/maestro/bin/maestro*"):
        for candidate in sorted(Path.home().glob(pattern), reverse=True):
            if candidate.suffix.lower() == (".bat" if WINDOWS else ""):
                return str(candidate)
    raise Fail("maestro CLI not found; install it and put its bin folder on PATH")


def maestro_steps(debug_dir, t0):
    steps = []
    for commands_file in Path(debug_dir).rglob("commands-*.json"):
        for entry in json.loads(commands_file.read_text(encoding="utf-8")):
            name, body = next(iter(entry["command"].items()))
            meta = entry.get("metadata") or {}
            if "timestamp" not in meta:
                continue
            start = meta["timestamp"] / 1000 - t0
            steps.append({"name": name, "label": body.get("label") if isinstance(body, dict) else None,
                          "status": meta.get("status"), "start": round(start, 3),
                          "end": round(start + (meta.get("duration") or 0) / 1000, 3)})
    return sorted(steps, key=lambda step: step["start"])


def labeled_steps(steps):
    return [step for step in steps if step["label"] and step["status"] == "COMPLETED"]


def segments_for(begin, end, holds, fast_spans=(), speed=1):
    cut_points = sorted({begin, end, *holds, *(point for span in fast_spans for point in span)})
    cut_points = [point for point in cut_points if begin <= point <= end]
    segments = []
    for seg_start, seg_end in zip(cut_points, cut_points[1:]):
        if seg_end - seg_start > 0.02:
            in_fast_span = any(span_start <= seg_start + 1e-6 and seg_end <= span_end + 1e-6
                               for span_start, span_end in fast_spans)
            segments.append(("play", seg_start, seg_end, speed if in_fast_span else 1))
        if seg_end in holds:
            segments.append(("hold", seg_end, holds[seg_end]))
    return segments


def out_time(segments, raw_time):
    """Map a time in the raw recording to the same moment in the re-timed video."""
    elapsed = 0.0
    for segment in segments:
        if segment[0] == "play":
            _, seg_start, seg_end, seg_speed = segment
            if raw_time <= seg_end:
                return elapsed + max(0.0, raw_time - seg_start) / seg_speed
            elapsed += (seg_end - seg_start) / seg_speed
        else:
            elapsed += segment[2]
    return elapsed


def fit_speech(make_segments, holds, starts, slots, speech):
    """Lengthen holds until each caption stays up long enough for its spoken line.

    starts are the raw times the captions appear; slots[i] is the raw time where caption i's extra
    hold goes, between its start and the next caption's.
    """
    for _ in range(len(starts) + 2):
        segments = make_segments(holds)
        shown = [out_time(segments, start) for start in starts] + [out_time(segments, float("inf"))]
        short = False
        for i, seconds in enumerate(speech):
            missing = seconds + SPEECH_GAP - (shown[i + 1] - shown[i])
            if missing > 0.01:
                holds[slots[i]] = holds.get(slots[i], 0) + missing
                short = True
        if not short:
            return segments
    return make_segments(holds)


def retime(steps, video_dur, hold=1.2, payoff=3.0, fast_after=5.0, speed=8, speech=None):
    """Plan the re-timed video: start at the first label, hold after each label, speed up long commands.

    speech gives the seconds each label's spoken line lasts; holds grow so no line is cut off.
    """
    labeled = labeled_steps(steps)
    if not labeled:
        raise Fail("No completed step has a label; add label: to the steps the video should show")
    begin = max(0.0, labeled[0]["start"])
    end = min(video_dur, labeled[-1]["end"] + 0.3)
    fast_spans = []
    for step in steps:
        if step["name"].startswith(COMPOUND) or step["end"] - step["start"] < fast_after:
            continue
        span_start, span_end = max(begin, step["start"] + 1.5), min(end, step["end"] - 0.5)
        if span_end - span_start > 1:
            if fast_spans and span_start <= fast_spans[-1][1]:
                fast_spans[-1][1] = max(fast_spans[-1][1], span_end)
            else:
                fast_spans.append([span_start, span_end])
    holds = {}
    hold_ats = [min(step["end"], end) for step in labeled]
    for step, hold_at in zip(labeled, hold_ats):
        holds[hold_at] = max(holds.get(hold_at, 0), payoff if step is labeled[-1] else hold)

    def make_segments(current_holds):
        return segments_for(begin, end, current_holds, fast_spans, speed)

    raw_starts = [step["start"] + 1e-4 for step in labeled]
    if speech:
        slots = [hold_ats[i] if i + 1 == len(labeled) or hold_ats[i] <= labeled[i + 1]["start"]
                 else labeled[i + 1]["start"] for i in range(len(labeled))]
        segments = fit_speech(make_segments, holds, raw_starts, slots, speech)
    else:
        segments = make_segments(holds)
    starts = [out_time(segments, raw_start) for raw_start in raw_starts]
    captions = [(starts[i], starts[i + 1] if i + 1 < len(starts) else None, step["label"])
                for i, step in enumerate(labeled)]
    return segments, captions


def stretch(captions, video_dur, speech, tail=1.0):
    """Re-time a rehearsed recording so each caption stays up until its spoken line ends."""
    raw_starts = [start + 1e-4 for start, _, _ in captions]
    slots = [captions[i + 1][0] if i + 1 < len(captions) else video_dur for i in range(len(captions))]
    segments = fit_speech(lambda holds: segments_for(0.0, video_dur, holds), {video_dur: tail},
                          raw_starts, slots, speech)
    starts = [out_time(segments, raw_start) for raw_start in raw_starts]
    return segments, [(starts[i], starts[i + 1] if i + 1 < len(starts) else None, text)
                      for i, (_, _, text) in enumerate(captions)]


def speech_command(text, stem, voice):
    if shutil.which("edge-tts") or importlib.util.find_spec("edge_tts"):
        base = ["edge-tts"] if shutil.which("edge-tts") else [sys.executable, "-m", "edge_tts"]
        path = stem.with_suffix(".mp3")
        return "edge-tts", base + ["--voice", voice or EDGE_VOICE, "--text", text, "--write-media", path], path, None
    if sys.platform == "darwin":
        path = stem.with_suffix(".aiff")
        return "say", ["say", *(["-v", voice] if voice else []), "-o", path, text], path, None
    if WINDOWS:
        path = stem.with_suffix(".wav")
        script = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                  "if ($env:DEMO_VOICE) { $s.SelectVoice($env:DEMO_VOICE) }; $s.SetOutputToWaveFile($env:DEMO_SPEECH_OUT); "
                  "$s.Speak($env:DEMO_SPEECH_TEXT); $s.Dispose()")
        env = {**os.environ, "DEMO_SPEECH_OUT": str(path), "DEMO_SPEECH_TEXT": text, "DEMO_VOICE": voice or ""}
        return "the Windows voice", ["powershell", "-NoProfile", "-NonInteractive", "-Command", script], path, env
    raise Fail("--narrate needs a speech engine: pip install edge-tts")


def narrate(texts, work, voice):
    """Speak each text into an audio clip; returns (path, seconds) per text."""
    clips, engine = [], None
    for i, text in enumerate(texts):
        engine, cmd, path, env = speech_command(text, work / f"line{i}", voice)
        run(cmd, env=env)
        output = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path]).stdout
        clips.append((path, float(json.loads(output)["format"]["duration"])))
    if engine:
        print(f"narration: {len(clips)} lines spoken with {engine}")
    return clips


def finish(data, raw, out, args):
    """Turn a recorded timeline into the final video: re-time Maestro runs and fit any narration."""
    work = Path(tempfile.mkdtemp(prefix="record-mobile-demo-voice-")) if args.narrate else None
    try:
        if data.get("kind") == "maestro":
            texts = [step["label"] for step in labeled_steps(data["steps"])]
            clips = narrate(texts, work, args.voice) if work else None
            segments, captions = retime(data["steps"], probe(raw)[2], args.hold, args.payoff, args.fast_after,
                                        args.speed, [seconds for _, seconds in clips] if clips else None)
        else:
            segments, captions = None, captions_from_timeline(data)
            clips = narrate([text for _, _, text in captions], work, args.voice) if work else None
            if clips:
                segments, captions = stretch(captions, probe(raw)[2], [seconds for _, seconds in clips])
        polish(raw, out, captions, segments, args.height, args.crf, args.gif,
               narration=[path for path, _ in clips] if clips else None)
    finally:
        if work:
            shutil.rmtree(work, ignore_errors=True)


def cmd_maestro(args):
    dev = Device(args.serial)
    base = [maestro_bin(), "--device", dev.serial, "test", "--no-ansi"]
    pairs = list(args.env)
    if args.env_file:
        pairs = [line.strip() for line in Path(args.env_file).expanduser().read_text(encoding="utf-8").splitlines()
                 if "=" in line and not line.lstrip().startswith("#")] + pairs
    env = [flag for pair in pairs for flag in ("-e", pair)]
    if args.setup:
        print(f"setup: {args.setup}")
        result = subprocess.run(base + [args.setup] + env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        if result.returncode:
            raise Fail("setup flow failed:\n" + "\n".join((result.stdout + result.stderr).splitlines()[-20:]))
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    debug = out.with_suffix(".maestro")
    shutil.rmtree(debug, ignore_errors=True)
    recorder = Recorder(dev, out.with_suffix(".raw.mkv"))
    t0 = recorder.start()
    try:
        time.sleep(0.5)
        result = subprocess.run(base + [args.flow, "--debug-output", str(debug)] + env,
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        time.sleep(0.5)
    finally:
        recorder.stop()
    log = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
    print("\n".join(log[-30:]))
    steps = maestro_steps(debug, t0)
    data = {"kind": "maestro", "raw": str(recorder.raw), "flow": str(Path(args.flow).resolve()), "steps": steps}
    timeline_path = out.with_suffix(".timeline.json")
    timeline_path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"raw {recorder.raw}\ntimeline {timeline_path}")
    if result.returncode:
        raise Fail("the flow failed, so no demo was made; the raw recording shows what happened")
    finish(data, recorder.raw, out, args)


def cmd_contact(args):
    video, out = Path(args.video).resolve(), Path(args.out).resolve()
    _, _, duration = probe(video)
    frames = args.frames
    cols = min(frames, 4)
    rows = -(-frames // cols)
    interval = max(duration / frames, 0.1)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-vf",
         f"fps=1/{interval:.3f},scale=320:-2,tile={cols}x{rows}:padding=6:color=white", "-frames:v", "1", out])
    print(f"{out}  ({frames} frames, one every {interval:.1f}s, left to right)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--serial")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("devices").set_defaults(fn=cmd_devices)
    boot = sub.add_parser("boot")
    boot.add_argument("avd")
    boot.add_argument("--snapshot")
    boot.add_argument("--timeout", type=int, default=240)
    boot.set_defaults(fn=cmd_boot)
    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("op", choices=["save", "load", "delete"])
    snapshot.add_argument("name")
    snapshot.set_defaults(fn=cmd_snapshot)
    prep = sub.add_parser("prep")
    prep.add_argument("--no-demo-bar", action="store_true")
    prep.set_defaults(fn=cmd_prep)
    sub.add_parser("reset").set_defaults(fn=cmd_reset)
    screen = sub.add_parser("screen")
    screen.add_argument("--all", action="store_true")
    screen.set_defaults(fn=cmd_screen)
    shot = sub.add_parser("shot")
    shot.add_argument("out")
    shot.add_argument("--width", type=int, default=540)
    shot.set_defaults(fn=cmd_shot)

    def action(name, value=False, sel=False):
        action_parser = sub.add_parser(name)
        if value:
            action_parser.add_argument("value")
        if sel:
            action_parser.add_argument("--text")
            action_parser.add_argument("--id")
            action_parser.add_argument("--desc")
            action_parser.add_argument("--xy")
            action_parser.add_argument("--index", type=int, default=0)
        action_parser.add_argument("--log", help="append the step to this flow file when it succeeds")
        action_parser.add_argument("--caption")
        action_parser.add_argument("--pause", type=float, help="seconds to linger before this step on replay")
        action_parser.add_argument("--setup", action="store_true", help="on replay, run this step before recording starts")
        action_parser.add_argument("--settle", type=float, default=1.0)
        action_parser.add_argument("--quiet", action="store_true")
        action_parser.add_argument("--all", action="store_true")
        action_parser.set_defaults(fn=cmd_action)
        return action_parser

    action("tap", sel=True).add_argument("--scroll", action="store_true")
    wait = action("wait", sel=True)
    wait.add_argument("--gone", action="store_true")
    wait.add_argument("--timeout", type=float, default=15)
    action("type", value=True)
    action("key", value=True)
    action("swipe", value=True)
    action("launch", value=True).add_argument("--stop", action="store_true")
    action("sleep", value=True)

    play = sub.add_parser("play")
    play.add_argument("flow")
    play.add_argument("--out", required=True)
    play.add_argument("--pace", type=float, default=1.2)
    play.add_argument("--lead", type=float, default=1.0)
    play.add_argument("--tail", type=float, default=2.0)
    play.add_argument("--settle", type=float, default=2.5, help="seconds to wait after setup steps")
    play.add_argument("--no-record", action="store_true")
    play.add_argument("--raw-only", action="store_true")
    polish_parser = sub.add_parser("polish")
    polish_parser.add_argument("timeline")
    polish_parser.add_argument("--raw")
    polish_parser.add_argument("--out", required=True)
    maestro = sub.add_parser("maestro", help="record a Maestro flow and re-time it into a demo")
    maestro.add_argument("flow")
    maestro.add_argument("--out", required=True)
    maestro.add_argument("--setup", help="flow to run first, unrecorded")
    maestro.add_argument("-e", "--env", action="append", default=[], help="KEY=value passed to maestro")
    maestro.add_argument("--env-file", help="KEY=value lines passed to maestro, e.g. a test account kept out of chat")
    for retiming_parser in (maestro, polish_parser):
        retiming_parser.add_argument("--hold", type=float, default=1.2, help="seconds held after each labeled step")
        retiming_parser.add_argument("--payoff", type=float, default=3.0, help="seconds held after the last labeled step")
        retiming_parser.add_argument("--fast-after", type=float, default=5.0, help="speed up commands longer than this")
        retiming_parser.add_argument("--speed", type=float, default=8)
    for output_parser in (play, polish_parser, maestro):
        output_parser.add_argument("--height", type=int, default=1280)
        output_parser.add_argument("--crf", type=int, default=28)
        output_parser.add_argument("--gif", action="store_true")
        output_parser.add_argument("--narrate", action="store_true", help="speak each caption over the video")
        output_parser.add_argument("--voice", help=f"speech voice; for edge-tts the default is {EDGE_VOICE}")
    play.set_defaults(fn=cmd_play)
    polish_parser.set_defaults(fn=cmd_polish)
    maestro.set_defaults(fn=cmd_maestro)
    contact = sub.add_parser("contact")
    contact.add_argument("video")
    contact.add_argument("out")
    contact.add_argument("--frames", type=int, default=8)
    contact.set_defaults(fn=cmd_contact)

    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        args.fn(args)
    except Fail as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
