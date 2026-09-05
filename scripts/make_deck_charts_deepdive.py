# -*- coding: utf-8 -*-
"""深讲版 PPT 图表集 → docs/marketing/deck_assets/dd_*.png

数字口径全部取自定案正本:
  归因链 42.6→70.0(+27.4 方法)→75.4(+5.4 判分修正)(arm_a_final_verdict.md)
  六型基线→终局(arm_a_final_verdict.md)· 检索 0.784→0.890(headhead json)
  对打 P@1/P@5/MRR(同上)· J-K 双判官曲线(paper2 Table round3)
  延迟 web p95 0.339/ent 0.798 vs 26.9(SCOREBOARD §2)
  LME-V2 untuned 19.6/12.8 → tuned 40.0/38.4(SCOREBOARD §1)
  官方坐标系散点(ATTRIBUTION.md 2026-09-03 节)
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "docs", "marketing", "deck_assets"))
os.makedirs(OUT, exist_ok=True)

BG, PANEL, FG, MUT = "#f6f8fa", "#eef1f4", "#1f2328", "#57606a"  # v3:图底非纯白,页面装裱有对比
GREEN, BLUE, RED, YELLOW, PURPLE = "#1a7f37", "#0969da", "#cf222e", "#9a6700", "#8250df"
LINE = "#d0d7de"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": PANEL, "savefig.facecolor": BG,
    "text.color": FG, "axes.edgecolor": LINE, "axes.labelcolor": FG,
    "xtick.color": FG, "ytick.color": FG,
    "font.family": ["Microsoft YaHei"], "font.size": 14,
    "axes.unicode_minus": False,
})
DPI = 150


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=DPI, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print("wrote", name)


def strip(ax):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)


# ── 1. 归因链瀑布:42.6 → +27.4 → +5.4 → 75.4 ──────────────
def waterfall():
    fig, ax = plt.subplots(figsize=(12.2, 6.2))
    strip(ax)
    labels = ["基线\n8/29", "摘要层(方法)\n9/3", "判分修正(测量)\n9/4", "定案\n75.4%"]
    base = 42.6
    bottoms = [0, base, base + 27.4, 0]
    heights = [base, 27.4, 5.4, 75.4]
    colors = [MUT, GREEN, BLUE, GREEN]
    x = np.arange(4)
    bars = ax.bar(x, heights, bottom=bottoms, width=0.58, color=colors,
                  edgecolor="white", linewidth=1.5)
    for i, (b, h) in enumerate(zip(bottoms, heights)):
        top = b + h
        txt = f"{h:.1f}%" if i in (0, 3) else f"+{h:.1f}pt"
        ax.text(i, top + 1.8, txt, ha="center", fontsize=22, fontweight="bold",
                color=colors[i])
    ax.plot([0.29, 0.71], [base, base], color=MUT, lw=1.4, ls="--")
    ax.plot([1.29, 1.71], [base + 27.4, base + 27.4], color=MUT, lw=1.4, ls="--")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=15)
    ax.set_ylim(0, 92)
    ax.set_ylabel("e2e 正确率(500 题,%)(%)", fontsize=13)
    ax.set_title("+32.8pt = 方法效应 27.4pt + 测量修正 5.4pt(拆开报,不混功)",
                 fontsize=18, fontweight="bold", pad=16)
    ax.text(1, base + 13, "三弱型路由摘要卡\n预注册三态门全过", ha="center",
            fontsize=12.5, color="white", fontweight="bold")
    ax.text(2, base + 27.4 + 2.7, "71 题断连重判\n不是方法效应", ha="center",
            fontsize=12.5, color="white", fontweight="bold")
    save(fig, "dd_waterfall.png")


# ── 2. 六型基线→终局 双条 ─────────────────────────────────
def sixtypes():
    fig, ax = plt.subplots(figsize=(12.2, 6.2))
    strip(ax)
    types = ["ssu\n单会话-用户", "ssp\n单会话-偏好", "ku\n知识更新",
             "ssa\n单会话-助手", "ms\n多会话", "tr\n时序推理"]
    base = [0.957, 0.800, 0.731, 0.250, 0.226, 0.158]
    final = [0.971, 0.800, 0.808, 0.839, 0.692, 0.624]
    y = np.arange(6)[::-1]
    h = 0.34
    ax.barh(y + h / 2 + 0.02, base, height=h, color="#c9d1d9", label="基线 8/29")
    ax.barh(y - h / 2 - 0.02, final, height=h, color=GREEN, label="终局 9/4 重判口径")
    for yi, b, f in zip(y, base, final):
        ax.text(b + 0.012, yi + h / 2 + 0.02, f"{b:.3f}", va="center", fontsize=12, color=MUT)
        ax.text(f + 0.012, yi - h / 2 - 0.02, f"{f:.3f}", va="center", fontsize=13,
                fontweight="bold", color=GREEN)
        if f - b > 0.005:
            ax.text(1.005, yi, f"+{(f - b) * 100:.0f}pt", va="center", fontsize=13,
                    fontweight="bold", color=BLUE)
    ax.set_yticks(y)
    ax.set_yticklabels(types, fontsize=13.5)
    ax.set_xlim(0, 1.12)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.legend(loc="lower right", fontsize=13, frameon=False)
    ax.set_title("六型分型:改动集中在三弱型,强项 context 字节不变",
                 fontsize=18, fontweight="bold", pad=14)
    save(fig, "dd_sixtypes.png")


# ── 3. 检索演进阶梯 0.784→0.890 ───────────────────────────
def ladder():
    fig, ax = plt.subplots(figsize=(12.2, 6.0))
    strip(ax)
    steps = ["m3-only\nK20 混合", "+ ssu/ssp\n分型路由", "+ ku 路由", "+ 日期锚定"]
    vals = [0.784, 0.848, 0.876, 0.890]
    x = np.arange(4)
    ax.plot(x, vals, color=GREEN, lw=3, marker="o", markersize=11,
            markerfacecolor="white", markeredgewidth=3, markeredgecolor=GREEN)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.012, f"{v:.3f}", ha="center", fontsize=20,
                fontweight="bold", color=GREEN)
    ax.axhline(0.774, color=RED, lw=2, ls="--", alpha=0.75)
    ax.text(3.42, 0.770, "mem0 2.0.19\n0.774", fontsize=13, color=RED, va="top")
    ax.annotate("纯基建不赢\n赢在路由", xy=(0, 0.784), xytext=(0.55, 0.735),
                fontsize=14, color=MUT,
                arrowprops=dict(arrowstyle="->", color=MUT))
    ax.set_xticks(x)
    ax.set_xticklabels(steps, fontsize=14)
    ax.set_ylim(0.70, 0.93)
    ax.set_ylabel("检索 P@1(500 题)", fontsize=13)
    ax.set_title("检索层四步演进:每一步的增量都可归因", fontsize=18,
                 fontweight="bold", pad=14)
    save(fig, "dd_ladder.png")


# ── 4. 对打三指标双柱 ─────────────────────────────────────
def head2head():
    fig, ax = plt.subplots(figsize=(12.2, 6.0))
    strip(ax)
    metrics = ["P@1", "P@5", "MRR"]
    ours = [0.890, 0.978, 0.929]
    theirs = [0.774, 0.916, 0.834]
    x = np.arange(3)
    w = 0.32
    b1 = ax.bar(x - w / 2, ours, w, color=GREEN, label="compass")
    b2 = ax.bar(x + w / 2, theirs, w, color="#8c959f", label="mem0 2.0.19 复现")
    for b, v in list(zip(b1, ours)) + list(zip(b2, theirs)):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}",
                ha="center", fontsize=17, fontweight="bold",
                color=GREEN if v in ours else MUT)
    for i, (o, t) in enumerate(zip(ours, theirs)):
        ax.text(i, max(o, t) + 0.075, f"+{(o - t) * 100:.1f}pt", ha="center",
                fontsize=15, fontweight="bold", color=BLUE)
    ax.set_xticks(x)
    ax.set_xticklabels(["P@1", "P@5", "MRR"], fontsize=16)
    ax.set_ylim(0, 1.14)
    ax.legend(fontsize=14, frameon=False, loc="upper left")
    ax.set_title("同题同判据对打(各用默认嵌入)· 三项全赢 · ≈$3.50 可复现",
                 fontsize=18, fontweight="bold", pad=14)
    save(fig, "dd_head2head.png")


# ── 5. J-K 判官通过率曲线 ─────────────────────────────────
def jk_curves():
    fig, ax = plt.subplots(figsize=(12.2, 6.0))
    strip(ax)
    x = [0.1, 1.0, 10.0]
    kimi = [48, 14, 0]
    minimax = [37, 12, 0]
    ax.plot(x, kimi, color=PURPLE, lw=3, marker="o", markersize=9, label="Kimi k3")
    ax.plot(x, minimax, color=BLUE, lw=3, marker="s", markersize=9, label="MiniMax-M3")
    for xi, yi in zip(x, kimi):
        ax.text(xi, yi + 2.5, f"{yi}%", ha="center", fontsize=15, fontweight="bold", color=PURPLE)
    for xi, yi in zip(x, minimax):
        ax.text(xi, yi - 4.5, f"{yi}%", ha="center", fontsize=15, fontweight="bold", color=BLUE)
    ax.axvspan(0.08, 1.0, color="#fff8c4", alpha=0.6, zorder=0)
    ax.text(0.32, 41, "盲区\n±0.1%~1%", fontsize=15, color=YELLOW, fontweight="bold")
    ax.set_xscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(["±0.1%", "±1%", "±10%"], fontsize=14)
    ax.set_ylim(-8, 58)
    ax.set_ylabel("污染通过率(%)", fontsize=13)
    ax.set_xlabel("数值扰动幅度(对数轴)", fontsize=13)
    ax.legend(fontsize=14, frameon=False, loc="upper right")
    ax.set_title("J-K 知识边界盲区:2,600 次真实调用 · 跨判官族的结构性边界(≤11pp)",
                 fontsize=17, fontweight="bold", pad=14)
    save(fig, "dd_jk.png")


# ── 6. 延迟对比(log 轴)──────────────────────────────────
def latency():
    fig, ax = plt.subplots(figsize=(12.2, 5.6))
    strip(ax)
    names = ["compass web\np95", "compass ent\np95", "AgentRunbook-R\n(LLM controller)"]
    vals = [0.339, 0.798, 26.9]
    colors = [GREEN, GREEN, "#8c959f"]
    y = np.arange(3)[::-1]
    bars = ax.barh(y, vals, height=0.52, color=colors)
    ax.set_xscale("log")
    for yi, v in zip(y, vals):
        ax.text(v * 1.15, yi, f"{v}s", va="center", fontsize=19, fontweight="bold",
                color=FG)
    ax.annotate("≈ 80×", xy=(26.9, y[2] + 0.28), xytext=(4.5, y[2] + 0.44),
                fontsize=26, fontweight="bold", color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=2.5))
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=14)
    ax.set_xlim(0.1, 120)
    ax.set_xlabel("memory_query p95(秒,对数轴)", fontsize=13)
    ax.set_title("延迟:智能放在不花钱的时刻 —— 不靠 cache 不靠捷径",
                 fontsize=18, fontweight="bold", pad=14)
    save(fig, "dd_latency.png")


# ── 7. LME-V2 untuned→tuned 双域 ──────────────────────────
def lmev2():
    fig, ax = plt.subplots(figsize=(12.2, 6.0))
    strip(ax)
    domains = ["web(240 题)", "ent(211 题)"]
    untuned = [19.6, 12.8]
    tuned = [40.0, 38.4]
    x = np.arange(2)
    w = 0.3
    b1 = ax.bar(x - w / 2, untuned, w, color="#c9d1d9", label="untuned 首跑基线")
    b2 = ax.bar(x + w / 2, tuned, w, color=GREEN, label="d12 调优 + 重判(现役)")
    for b, v in list(zip(b1, untuned)) + list(zip(b2, tuned)):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v:.1f}%", ha="center",
                fontsize=19, fontweight="bold")
    for i, (u, t) in enumerate(zip(untuned, tuned)):
        ax.text(i, max(u, t) + 5.5, f"×{t / u:.1f}", ha="center", fontsize=17,
                fontweight="bold", color=BLUE)
    ax.set_xticks(x)
    ax.set_xticklabels(domains, fontsize=15)
    ax.set_ylim(0, 52)
    ax.set_ylabel("full 口径正确率(%)", fontsize=13)
    ax.legend(fontsize=13.5, frameon=False, loc="upper right")
    ax.set_title("LME-V2(上游官方基准 451 题):刀1 abstention 口径 + 刀2 检索单元 + 判分修正",
                 fontsize=16.5, fontweight="bold", pad=14)
    save(fig, "dd_lmev2.png")


# ── 8. 官方坐标系:v4 效率前沿叙事(诚实坐标+差距来源+攻坚路径)──
def official_map():
    fig, ax = plt.subplots(figsize=(12.2, 6.4))
    strip(ax)
    # (延迟秒, 准确率%, 名称, 颜色)
    pts = [
        (0.1, 1.3, "No retrieval", "#c9d1d9"),
        (0.15, 42.8, "RAG query→slice", "#8c959f"),
        (0.2, 51.0, "RAG slice+notes", "#8c959f"),
        (26.9, 58.6, "AgentRunbook-R", "#8c959f"),
        (177, 69.9, "Codex", "#8c959f"),
        (108, 74.9, "AgentRunbook-C", "#8c959f"),
        (0.57, 39.3, "compass(d12)", GREEN),
    ]
    # 官方高预算区(右侧淡黄)
    ax.axvspan(15, 500, color="#fff3d6", alpha=0.55, zorder=0)
    ax.text(80, 8, "官方高预算区\n200k ctx · 108-177s/查", fontsize=12.5,
            color=YELLOW, ha="center", fontweight="bold")
    # 最弱 RAG 参考线(中性语言)
    ax.axhline(42.8, color=LINE, lw=1.1, ls=":")
    ax.text(0.062, 43.9, "最弱 RAG 基线 42.8(同为 200k 预算口径)", fontsize=11.5, color=MUT)
    for sec, acc, name, c in pts:
        big = c == GREEN
        ax.scatter(sec, acc, s=700 if big else 300, color=c, zorder=3,
                   edgecolor="white", linewidth=2, marker="*" if big else "o")
        dy = -7.0 if name == "No retrieval" else 4.0
        ax.text(sec * 1.18, acc + dy, name, fontsize=14,
                fontweight="bold" if big else "normal",
                color=GREEN if big else MUT)
    # compass 差异化标注
    ax.annotate("预算 24k = 官方 1/8\n延迟 0.57s = 1/47 ~ 1/188", xy=(0.62, 39.0),
                xytext=(1.35, 17), fontsize=13.5, color=GREEN, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=2))
    # 主攻坚路径箭头
    ax.annotate("", xy=(20.5, 56.2), xytext=(1.05, 43.2),
                arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=2.4, ls="--"))
    ax.text(2.6, 51.0, "主攻坚:三池设计移植\n目标 55-60%(超 AgentRunbook-R)",
            fontsize=13, color=BLUE, fontweight="bold")
    # 口径差异注(为什么不是同一场考试)
    ax.text(0.062, 83.5, "分数口径差异:compass 全题 LLM judge(更严)vs 官方程序化为主 —— 分数不可直接互比,单位预算/单位时间的效率可以",
            fontsize=11.8, color=MUT)
    ax.set_xlim(0.05, 500)
    ax.set_ylim(-2, 90)
    ax.set_xlabel("每查询延迟(秒,对数轴)", fontsize=13)
    ax.set_ylabel("LME-V2 Small Overall(%)", fontsize=13)
    ax.set_title("官方坐标系:坐标、差距来源与攻坚路径 —— 差异化在效率轴,不靠榜单名次",
                 fontsize=16.5, fontweight="bold", pad=14)
    save(fig, "dd_official_map.png")


if __name__ == "__main__":
    waterfall()
    sixtypes()
    ladder()
    head2head()
    jk_curves()
    latency()
    lmev2()
    official_map()
    print("ALL DONE")
