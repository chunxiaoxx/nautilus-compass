#!/usr/bin/env python
"""Render the D1 demo as an animated GIF (typewriter terminal, no screen-recorder).

Drives tools/demo_d1.py for real output, then draws a fake-terminal animation
with Pillow. Zero external deps beyond Pillow (no ffmpeg / ttyd / WSL needed).

Usage:
  python tools/demo_d1_video.py            # renders docs/marketing/deck_assets/demo_d1.gif
  python tools/demo_d1_video.py --dry      # run commands, print collected script, no render
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/marketing/deck_assets/demo_d1.gif"

# ── look & feel (GitHub-dark, matches landing) ──────────────────────
BG, FG, GREEN, DIM, BAR = "#0d1117", "#e6edf3", "#3fb950", "#8b949e", "#161b22"
BORDER = "#30363d"
W = 1080
MAX_OUT_CHARS = 108  # 17px Consolas ≈ 9.4px/char → ~1010px, fits the canvas
FONT_PATH = r"C:\Windows\Fonts\consola.ttf"
FS = 19  # prompt/command font size
LINE_H = 27
PAD = 18
TYPE_MS = 60      # per typing step (3 chars advance per frame)
CHARS_PER_STEP = 3
LINE_MS = 420     # per output line reveal
HOLD_MS = 2300    # hold after each command's output completes
FINAL_HOLD_MS = 3200  # the control段 NO ANSWER beat stays longest
CARDS_MS = 2400   # intro / outro card duration

INTRO = "nautilus-compass — agent memory that survives sessions · zero LLM calls at write time"
OUTRO_LINES = ["Modified MIT · self-host free forever",
               "github.com/chunxiaoxx/nautilus-compass",
               "hosted open beta: compass.nautilus.social"]
CMDS = [
    ("python tools/demo_d1.py write 1", "session-1: dog walk on Tuesday (Momo)"),
    ("python tools/demo_d1.py write 2", "session-2: learning Rust"),
    ("python tools/demo_d1.py write 3", "session-3: Monday standup"),
    ("python tools/demo_d1.py ask", "cross-session question"),
    ("python tools/demo_d1.py control", "control space: same question"),
]


def run_demo() -> list[tuple[str, list[str]]]:
    """Drive demo_d1.py for REAL output; return [(cmd, output_lines)]."""
    subprocess.run([sys.executable, str(ROOT / "tools/demo_d1.py"), "reset"],
                   capture_output=True, text=True, cwd=ROOT)
    segs: list[tuple[str, list[str]]] = []
    for cmd, _ in CMDS:
        r = subprocess.run([sys.executable, cmd.split(" ", 1)[1] and
                            str(ROOT / "tools/demo_d1.py")] + cmd.split(" ")[2:],
                           capture_output=True, text=True, cwd=ROOT,
                           shell=False)
        lines = [ln[:MAX_OUT_CHARS] + ("…" if len(ln) > MAX_OUT_CHARS else "")
                 for ln in (r.stdout or "").splitlines() if ln.strip()]
        segs.append((cmd, lines))
        time.sleep(0.3)
    return segs


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def render(segs: list[tuple[str, list[str]]]) -> None:
    n_lines = 1 + sum(2 + len(out) + 1 for _, out in segs) + 3
    H = max(420, 64 + n_lines * LINE_H + PAD)
    f_cmd, f_out = _font(FS), _font(FS - 2)
    frames: list[Image.Image] = []

    def base(caption: str | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 34], fill=BAR)
        d.rectangle([0, 34, W, 35], fill=BORDER)
        for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
            d.ellipse([14 + i * 22, 11, 24 + i * 22, 21], fill=c)
        title = "nautilus-compass — demo (local daemon, real output)"
        d.text((W // 2 - len(title) * 4, 9), title, font=_font(13), fill=DIM)
        return img, d

    def add_frame(img: Image.Image, ms: int) -> None:
        frames.append(img.copy())
        durations.append(ms)  # Pillow treats list duration as milliseconds

    durations: list[int] = []

    def text_row(d: ImageDraw.ImageDraw, y: int, s: str, font, color) -> int:
        d.text((PAD, y), s, font=font, fill=color)
        return y + LINE_H

    def out_color(s: str):
        return GREEN if s.startswith("[ok]") or "->" in s else (
            FG if s[:1].isdigit() else DIM)

    def draw_seg(d: ImageDraw.ImageDraw, y: int, cmd: str, out: list[str],
                 upto: int | None = None, partial: str = "") -> int:
        """Draw one command segment; upto = how many output lines shown."""
        y = text_row(d, y, "$ " + (partial or cmd), f_cmd, FG)
        for ln in out if upto is None else out[:upto]:
            y = text_row(d, y, ln, f_out, out_color(ln))
        return y + LINE_H // 2  # breathing room between segments

    # intro card
    img, d = base()
    d.text((PAD + 20, H // 2 - 20), INTRO, font=f_cmd, fill=FG)
    add_frame(img, CARDS_MS)

    y = 50
    history: list[tuple[str, list[str]]] = []
    for si, (cmd, out) in enumerate(segs):
        for k in range(CHARS_PER_STEP, len(cmd) + 1, CHARS_PER_STEP):
            img, d = base()
            y2 = y
            for hc, ho in history:
                y2 = draw_seg(d, y2, hc, ho)
            draw_seg(d, y2, cmd, [], partial=cmd[:k] + "█")
            add_frame(img, TYPE_MS)
        for li in range(1, len(out) + 1):
            img, d = base()
            y2 = y
            for hc, ho in history:
                y2 = draw_seg(d, y2, hc, ho)
            draw_seg(d, y2, cmd, out, upto=li)
            add_frame(img, LINE_MS)
        img, d = base()
        y2 = y
        for hc, ho in history:
            y2 = draw_seg(d, y2, hc, ho)
        draw_seg(d, y2, cmd, out)
        add_frame(img, FINAL_HOLD_MS if si == len(segs) - 1 else HOLD_MS)
        history.append((cmd, out))

    # outro card
    img, d = base()
    for i, ln in enumerate(OUTRO_LINES):
        d.text((PAD + 20, H // 2 - 40 + i * LINE_H), ln, font=f_cmd,
               fill=FG if i else GREEN)
    add_frame(img, CARDS_MS)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUT, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)
    est_s = sum(durations) / 1000
    print(f"[ok] {len(frames)} frames -> {OUT} ({OUT.stat().st_size//1024} KB, ~{est_s:.0f}s)")


def main() -> int:
    if "--dry" in sys.argv:
        for cmd, out in run_demo():
            print("$", cmd)
            for ln in out:
                print("  ", ln)
        return 0
    render(run_demo())
    return 0


if __name__ == "__main__":
    sys.exit(main())
