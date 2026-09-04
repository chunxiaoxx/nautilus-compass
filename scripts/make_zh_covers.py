# -*- coding: utf-8 -*-
"""中文圈封面图 → docs/marketing/zh_covers/*.png

公众号头条封面 900×383(2.35:1)+ 朋友圈/群转发方图 1080×1080。
内容宪法第 5 条:手机小图预览可读——品牌名 ≥22px、主标题 ≥56px 等效字号。
落断言①(覆写)为主视觉,副句带断言②。纲见 narrative_core_20260905.md。
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "docs", "marketing", "zh_covers"))
os.makedirs(OUT, exist_ok=True)

BG, FG, MUT = "#0d1117", "#e6edf3", "#aab4c4"
GREEN, RED, YELLOW = "#3fb950", "#f85149", "#d29922"
LINE = "#30363d"

plt.rcParams.update({"font.family": ["Microsoft YaHei"], "axes.unicode_minus": False})


def cover(name, figsize, title_sizes, sub_size, brand_size, layout="wide"):
    fig = plt.figure(figsize=figsize)
    fig.patch.set_facecolor(BG)
    # 顶部/底部边线
    h = figsize[1]
    fig.add_artist(plt.Line2D([0.06, 0.94], [0.12, 0.12], color=LINE, lw=1.2,
                              transform=fig.transFigure))

    if layout == "wide":
        # 横版:左标题右品牌
        fig.text(0.06, 0.68, "你的 agent,", fontsize=title_sizes, color=FG,
                 fontweight="bold", va="center")
        fig.text(0.06, 0.34, "正在忘记你。", fontsize=title_sizes, color=RED,
                 fontweight="bold", va="center")
        fig.text(0.62, 0.60, "写入时压缩", fontsize=sub_size, color=MUT, va="center")
        fig.text(0.62, 0.44, "= 对未来的盲目下注", fontsize=sub_size, color=YELLOW,
                 va="center", fontweight="bold")
        fig.text(0.06, 0.88, "nautilus-compass", fontsize=brand_size, color=GREEN,
                 fontweight="bold", va="center")
        fig.text(0.62, 0.24, "agent memory · 本地优先", fontsize=sub_size * 0.8,
                 color=MUT, va="center")
    else:
        # 方版:居中堆叠
        fig.text(0.5, 0.80, "nautilus-compass", fontsize=brand_size, color=GREEN,
                 fontweight="bold", ha="center", va="center")
        fig.add_artist(plt.Line2D([0.38, 0.62], [0.745, 0.745], color=LINE, lw=1.2,
                                  transform=fig.transFigure))
        fig.text(0.5, 0.60, "你的 agent,", fontsize=title_sizes, color=FG,
                 fontweight="bold", ha="center", va="center")
        fig.text(0.5, 0.46, "正在忘记你。", fontsize=title_sizes, color=RED,
                 fontweight="bold", ha="center", va="center")
        fig.text(0.5, 0.30, "写入时压缩 = 对未来的盲目下注", fontsize=sub_size,
                 color=YELLOW, ha="center", va="center", fontweight="bold")
        fig.text(0.5, 0.20, "写入 0 LLM 调用 · 记忆留在本地", fontsize=sub_size * 0.85,
                 color=MUT, ha="center", va="center")
        fig.text(0.5, 0.08, "github.com/chunxiaoxx/nautilus-compass", fontsize=11,
                 color=MUT, ha="center", va="center")

    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=100, facecolor=BG)
    plt.close(fig)
    print("wrote", name)


# 公众号头条封面:2.35:1(900×383)。主标题 42pt≈56px@900px,品牌 20pt≈27px
cover("wechat_cover_900x383.png", (9.0, 3.83), 42, 17, 20, layout="wide")

# 转发方图 1080×1080:主标题 56pt,品牌 26pt
cover("square_1080.png", (10.8, 10.8), 56, 21, 26, layout="square")

print("all covers →", OUT)
