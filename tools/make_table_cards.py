#!/usr/bin/env python
"""Score-table cards (EN+ZH) as PNGs — solves copy-paste mangling on social platforms.

Renders the head-to-head table as images, matching the GitHub-dark look used by
landing/demo GIF/quote cards. Numbers injected from the scoreboard constants below
(content_hub §3 口径卡 — single source, do not hand-edit elsewhere).
Usage: python tools/make_table_cards.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs/marketing/deck_assets"
BG, CARD, BORDER, FG, DIM, GREEN, RED = ("#0d1117", "#161b22", "#30363d",
                                         "#e6edf3", "#8b949e", "#3fb950", "#f85149")
FONT = r"C:\Windows\Fonts\consola.ttf"
FONT_ZH = r"C:\Windows\Fonts\msyh.ttc"  # 微软雅黑 for the ZH card
W = 1080
PAD = 46
ROW_H = 56
HEAD_H = 84
TITLE_FS, HEAD_FS, ROW_FS = 34, 24, 23

ROWS_EN = [
    ("Benchmark", "compass", "mem0 2.0.19", "Delta", True),
    ("LongMemEval-S · 500 q · P@1", "0.890", "0.774", "+11.6pt", False),
    ("LongMemEval-S · P@5", "0.978", "0.916", "+6.2pt", False),
    ("LongMemEval-S · MRR", "0.929", "0.834", "+9.5pt", False),
    ("LOCOMO-10 · n=1986 · P@1", "0.644", "0.592", "+5.2pt", False),
    ("LongMemEval-M · 500 q · P@5", "0.888", "—", "×12 corpus", False),
]
ROWS_ZH = [
    ("基准", "compass", "mem0 2.0.19", "领先", True),
    ("LongMemEval-S · 500题 · P@1", "0.890", "0.774", "+11.6pt", False),
    ("LongMemEval-S · P@5", "0.978", "0.916", "+6.2pt", False),
    ("LongMemEval-S · MRR", "0.929", "0.834", "+9.5pt", False),
    ("LOCOMO-10 · n=1986 · P@1", "0.644", "0.592", "+5.2pt", False),
    ("LongMemEval-M · 500题 · P@5", "0.888", "—", "泛化×12", False),
]
COL_X = [PAD, 550, 730, 900]
FOOT_EN = "same questions · same criteria · each on its default embedder · reproduce ~$3.50"
FOOT_ZH = "同题同判据 · 各用默认嵌入 · 复现成本约 $3.50"


def render(path: str, title: str, rows, foot: str, zh: bool = False) -> None:
    font_p = FONT_ZH if zh else FONT
    f_title = ImageFont.truetype(FONT_ZH if zh else FONT, TITLE_FS)
    f_head = ImageFont.truetype(font_p, HEAD_FS)
    f_row = ImageFont.truetype(font_p, ROW_FS)
    f_foot = ImageFont.truetype(font_p, 19)
    H = HEAD_H + ROW_H * len(rows) + 96
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((PAD, 26), title, font=f_title, fill=FG)
    d.line([(PAD, 78), (W - PAD, 78)], fill=BORDER, width=2)
    for ri, (c0, c1, c2, c3, is_head) in enumerate(rows):
        y = HEAD_H + ri * ROW_H
        if is_head:
            d.rectangle([PAD, y, W - PAD, y + ROW_H - 8], fill=CARD)
        if ri > 0 and not is_head:
            d.line([(PAD, y), (W - PAD, y)], fill=BORDER, width=1)
        base = DIM if is_head else FG
        d.text((COL_X[0], y + 14), c0, font=f_head if is_head else f_row,
               fill=DIM if not is_head else DIM)
        win = (not is_head) and c1 != "—"
        d.text((COL_X[1], y + 14), c1, font=f_head if is_head else f_row,
               fill=GREEN if win else base)
        d.text((COL_X[2], y + 14), c2, font=f_head if is_head else f_row, fill=base)
        d.text((COL_X[3], y + 14), c3, font=f_head if is_head else f_row,
               fill=GREEN if c3.startswith("+") else base)
    fy = HEAD_H + ROW_H * len(rows) + 18
    d.line([(PAD, fy - 6), (W - PAD, fy - 6)], fill=BORDER, width=1)
    d.text((PAD, fy + 10), foot, font=f_foot, fill=DIM)
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / path)
    print(f"[ok] {path} {img.size}")


def main() -> int:
    render("table_headtohead_en.png", "Head-to-head · retrieval layer", ROWS_EN, FOOT_EN)
    render("table_headtohead_zh.png", "检索层对打 · 全量 500 题", ROWS_ZH, FOOT_ZH, zh=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
