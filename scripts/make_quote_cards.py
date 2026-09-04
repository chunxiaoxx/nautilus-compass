# -*- coding: utf-8 -*-
"""公众号/朋友圈金句卡 ×5 → docs/marketing/quote_cards/*.png

一卡一断言,文案取自 zh_wechat_tech_20260905.md 的【金句卡】标记
+ 第 5 张(判分卫生)为系列第二篇预告,纲见 narrative_core_20260905.md。
尺寸 1080×1440(3:4),深色品牌视觉,可直接截图传播。
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "docs", "marketing", "quote_cards"))
os.makedirs(OUT, exist_ok=True)

BG, FG, MUT = "#0d1117", "#e6edf3", "#8b949e"
GREEN, BLUE, RED, YELLOW = "#3fb950", "#58a6ff", "#f85149", "#d29922"
LINE = "#30363d"
DPI = 120  # 9x12 in -> 1080x1440

plt.rcParams.update({
    "font.family": ["Microsoft YaHei"], "axes.unicode_minus": False,
})


def card(name, lines, anchor, footer_note=""):
    """lines: [(text, color, size, bold)]; anchor: 底部证据锚。"""
    fig = plt.figure(figsize=(9, 12))
    fig.patch.set_facecolor(BG)
    # 内框
    fig.add_artist(FancyBboxPatch((0.045, 0.035), 0.91, 0.93, boxstyle="round,pad=0.01",
                                  fc="none", ec=LINE, lw=1.6, transform=fig.transFigure))
    # 左强调条
    fig.add_artist(plt.Line2D([0.085, 0.085], [0.72, 0.30], color=GREEN, lw=5,
                              transform=fig.transFigure, solid_capstyle="round"))
    # 品牌行(顶部)
    fig.text(0.5, 0.925, "nautilus-compass · agent memory", ha="center",
             fontsize=15, color=MUT)
    fig.text(0.5, 0.906, "—" * 14, ha="center", fontsize=11, color=LINE)

    # 大引号装饰
    fig.text(0.12, 0.83, "“", ha="left", fontsize=110, color="#1f2630")

    # 金句主体(垂直居中于 0.28-0.72 区间)
    n = len(lines)
    top, bottom = 0.66, 0.34
    if n == 1:
        ys = [0.5]
    else:
        step = (top - bottom) / (n - 1)
        ys = [top - i * step for i in range(n)]
    for (text, color, size, bold), y in zip(lines, ys):
        fig.text(0.135, y, text, ha="left", va="center", fontsize=size,
                 color=color, fontweight="bold" if bold else "normal")

    # 证据锚 + 页脚
    fig.text(0.5, 0.155, anchor, ha="center", fontsize=15.5, color=FG, alpha=0.85)
    if footer_note:
        fig.text(0.5, 0.125, footer_note, ha="center", fontsize=13, color=MUT)
    fig.add_artist(plt.Line2D([0.30, 0.70], [0.095, 0.095], color=LINE, lw=1.2,
                              transform=fig.transFigure))
    fig.text(0.5, 0.07, "github.com/chunxiaoxx/nautilus-compass", ha="center",
             fontsize=13.5, color=MUT)

    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=DPI, facecolor=BG)
    plt.close(fig)
    print("wrote", name)


# 卡 1 · 断言①覆写问题(文中金句 1)
card(
    "card1_overwrite.png",
    [("AI 不是没有记忆,", FG, 44, True),
     ("是把你的新话,冲掉了你的旧话。", GREEN, 44, True)],
    "ICLR 2025 LongMemEval:人工翻查 ChatGPT 长对话——关键信息被后续内容覆写",
)

# 卡 2 · 断言②盲目下注(文中金句 2)
card(
    "card2_blind_bet.png",
    [("写入时压缩,", FG, 46, True),
     ("是替未来的自己盲目下注。", RED, 46, True),
     ("赌桌对面,站着你想象不到的提问。", MUT, 26, False)],
    "未来查询分布不可知 · 原文是唯一可重新索引的表示 · 成本曲线方向反了",
)

# 卡 3 · 断言③反架构(文中金句 3)
card(
    "card3_zero_llm.png",
    [("写入路径零 LLM 调用;", FG, 44, True),
     ("全部智能,放在读取端。", BLUE, 46, True)],
    "同样的记忆,同样的 500 题:e2e 42.6% → 75.4%(双口径披露)",
    "写入免费、无损、永远 —— p95 延迟比 LLM controller 快约 80×",
)

# 卡 4 · 断言⑤dogfood(文中金句 4)
card(
    "card4_dogfood.png",
    [("评判一个记忆系统,别看宣传页,", FG, 38, True),
     ("看造它的组织用不用它。", YELLOW, 46, True)],
    "130 天 · 771 commits · 603 次由 agent 舰队提交",
    "整个组织的记忆与经验继承,跑在它自己上面",
)

# 卡 5 · 断言④判分卫生(系列第二篇预告)
card(
    "card5_judge.png",
    [("判官会静默失败;", FG, 44, True),
     ("不抓,你的排行榜就是虚构的。", RED, 44, True)],
    "我们抓了自己判官 5 次——一次断连把 14.2% 的题静默记成错答",
    "判分协议全公开 · 预注册锚 · 双口径强制(下篇详解)",
)

print("all cards →", OUT)
