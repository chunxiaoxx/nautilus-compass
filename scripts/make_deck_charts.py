# -*- coding: utf-8 -*-
"""演讲 PPT 深色图表集 → docs/marketing/deck_assets/*.png

数字口径全部取自 docs/nautilusmem/SCOREBOARD.md 定案成绩册:
  e2e 42.6→75.4(81.6 剔判官故障)· 分型六值 · P@1 0.890 vs 0.774
  LOCOMO 0.644 vs 0.592 · EverMemBench 44.4-47.3 · LME-V2 40.0/38.4
  p95 0.34-0.80s vs 26.9s · drift AUC 0.83 · 130d/771/603
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import numpy as np

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "docs", "marketing", "deck_assets"))
os.makedirs(OUT, exist_ok=True)

# ── 深色主题(GitHub dark 系)─────────────────────────────
BG, PANEL, FG, MUT = "#ffffff", "#f6f8fa", "#1f2328", "#57606a"
GREEN, BLUE, RED, YELLOW, PURPLE = "#1a7f37", "#0969da", "#cf222e", "#9a6700", "#8250df"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": PANEL, "savefig.facecolor": BG,
    "text.color": FG, "axes.edgecolor": MUT, "axes.labelcolor": FG,
    "xtick.color": FG, "ytick.color": FG,
    "font.family": ["Microsoft YaHei"], "font.size": 14,
    "axes.unicode_minus": False,
})
DPI = 150
FIGSIZE = (12.8, 6.9)  # 16:9 减边


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("wrote", name)


def new_ax(figsize=FIGSIZE):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor(PANEL)
    return fig, ax


def strip(ax):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)


def box(ax, x, y, w, h, fc, ec, lw=2.2, alpha=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015",
                                fc=fc, ec=ec, lw=lw, alpha=alpha))


def arrow(ax, x1, y1, x2, y2, color=MUT, lw=2.4, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=22, color=color, lw=lw))


# ── 1. 盲目下注(写入时压缩 vs 未来查询)──────────────────
def blind_bet():
    fig, ax = new_ax()
    strip(ax)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.axis("off")

    ax.plot([0.7, 9.3], [4.75, 4.75], color=MUT, lw=2, ls="--", alpha=0.6)
    ax.text(5.0, 9.55, "写入时压缩 = 对未来的盲目下注", ha="center",
            fontsize=25, fontweight="bold")

    # 左:写入时刻(v3:框加大 + va='top' 显式定位,数学保证不重叠)
    box(ax, 0.55, 5.05, 4.1, 3.55, PANEL, GREEN)
    ax.text(2.6, 8.25, "写入时刻", ha="center", va="top", fontsize=18,
            color=GREEN, fontweight="bold")
    ax.text(2.6, 7.35, "压缩 / 提炼在此发生\n信息被冻结在当初那个\n模型的认知水平",
            ha="center", va="top", fontsize=14)

    # 右:未来查询
    box(ax, 5.35, 5.05, 4.1, 3.55, PANEL, RED)
    ax.text(7.4, 8.25, "未来查询", ha="center", va="top", fontsize=18,
            color=RED, fontweight="bold")
    ax.text(7.4, 7.35, "没人知道会被问什么\n分布不可知\n今天赌不中明天的题",
            ha="center", va="top", fontsize=14)

    ax.text(5.0, 4.15, "×  赌注在结构上就赢不了", ha="center", fontsize=21,
            color=RED, fontweight="bold")

    # 成本曲线方向
    box(ax, 0.55, 0.5, 8.9, 2.9, PANEL, MUT)
    ax.text(1.0, 2.85, "而且成本曲线方向反了", fontsize=16, color=YELLOW,
            fontweight="bold", va="top")
    xs = np.linspace(6.7, 8.9, 100)
    ax.plot(xs, 0.95 + 1.45 * np.exp(-2.2 * (xs - 6.7)), color=GREEN, lw=3)
    ax.text(7.9, 0.55, "存储 → 0", color=GREEN, fontsize=13, ha="center")
    ax.plot([0.95, 3.3], [1.7, 1.7], color=RED, lw=3)
    ax.text(2.1, 1.0, "LLM 调用恒贵", color=RED, fontsize=13, ha="center")
    ax.text(5.0, 1.15, "把便宜的(原文)换成昂贵的(提炼物)\n= 双输", color=MUT,
            fontsize=13.5, ha="center", va="top")
    save(fig, "blind_bet.png")


# ── 2. 六层架构图 ────────────────────────────────────────
def arch():
    fig, ax = new_ax((12.8, 7.2))
    strip(ax)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.axis("off")
    ax.text(5.0, 9.55, "nautilus-compass · 反架构:写入零智能,读取全智能",
            ha="center", fontsize=22, fontweight="bold")

    # 横贯层(治理/进化)
    box(ax, 0.6, 7.5, 8.8, 1.35, PANEL, YELLOW)
    ax.text(0.95, 8.35, "治理", fontsize=16, color=YELLOW, fontweight="bold", va="center")
    ax.text(5.3, 8.35, "drift 检测(AUC 0.83)· 合约审计 · scoped 多租户 · 判分卫生学",
            fontsize=15, va="center")
    box(ax, 0.6, 5.9, 8.8, 1.35, PANEL, PURPLE)
    ax.text(0.95, 6.75, "进化", fontsize=16, color=PURPLE, fontweight="bold", va="center")
    ax.text(5.3, 6.75, "跨 agent 记忆胶囊:验证后写回(reward ≥ 1.0 防毒门)→ 按需继承",
            fontsize=15, va="center")

    # 写入侧
    box(ax, 0.6, 0.6, 3.6, 4.6, "#dafbe1", GREEN)
    ax.text(2.4, 4.7, "写入侧 · 0 LLM 调用", ha="center", fontsize=16.5,
            color=GREEN, fontweight="bold")
    box(ax, 0.95, 3.0, 2.9, 1.2, PANEL, MUT, lw=1.2)
    ax.text(2.4, 3.8, "格式", ha="center", fontsize=14.5, fontweight="bold")
    ax.text(2.4, 3.3, "OKF 兼容", ha="center", fontsize=13, color=MUT)
    box(ax, 0.95, 1.0, 2.9, 1.6, PANEL, MUT, lw=1.2)
    ax.text(2.4, 2.15, "存储", ha="center", fontsize=14.5, fontweight="bold")
    ax.text(2.4, 1.45, "原文 verbatim · 本地 BGE-m3\n零 LLM · 零上云", ha="center",
            fontsize=12.5, color=MUT)
    arrow(ax, 2.4, 3.0, 2.4, 2.65, GREEN)

    # 读取侧
    box(ax, 5.8, 0.6, 3.6, 4.6, "#ddf4ff", BLUE)
    ax.text(7.6, 4.7, "读取侧 · 全部智能", ha="center", fontsize=16.5,
            color=BLUE, fontweight="bold")
    box(ax, 6.15, 3.0, 2.9, 1.2, PANEL, MUT, lw=1.2)
    ax.text(7.6, 3.8, "召回", ha="center", fontsize=14.5, fontweight="bold")
    ax.text(7.6, 3.3, "6 型路由 → BM25+dense(RRF)· 日期锚定", ha="center",
            fontsize=11.5, color=MUT)
    box(ax, 6.15, 1.0, 2.9, 1.6, PANEL, MUT, lw=1.2)
    ax.text(7.6, 2.15, "组装", ha="center", fontsize=14.5, fontweight="bold")
    ax.text(7.6, 1.45, "分题型摘要卡 · 日期时间线", ha="center", fontsize=12.5, color=MUT)
    arrow(ax, 7.6, 3.0, 7.6, 2.65, BLUE)
    arrow(ax, 9.4, 1.8, 9.95, 1.8, BLUE)
    ax.text(9.65, 2.15, "answer", fontsize=12, color=BLUE, ha="center")

    ax.text(5.0, 0.25, "写入:免费、无损、永远 —— 智能全部在读取端",
            ha="center", fontsize=15, color=FG, fontweight="bold")
    save(fig, "arch.png")


# ── 3. 成本曲线方向反了 ──────────────────────────────────
def cost_curve():
    fig, ax = new_ax()
    strip(ax)
    xs = np.linspace(0, 10, 200)
    ax.plot(xs, 8 * np.exp(-0.42 * xs) + 0.4, color=GREEN, lw=3.5, label="存储成本(原文 verbatim)")
    ax.plot(xs, np.full_like(xs, 6.2), color=RED, lw=3.5, label="LLM 调用成本(写入时压缩/提炼)")
    ax.fill_between(xs, 0, 8 * np.exp(-0.42 * xs) + 0.4, color=GREEN, alpha=0.08)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlabel("时间 / 规模", fontsize=14, color=MUT)
    ax.set_ylabel("单位记忆成本", fontsize=14, color=MUT)
    ax.text(8.0, 1.6, "存储 → 0", color=GREEN, fontsize=17, fontweight="bold")
    ax.text(1.0, 6.7, "LLM 调用恒贵", color=RED, fontsize=17, fontweight="bold")
    ax.text(5.0, 9.3, "成本曲线方向反了:行业默认把智能放在最贵的那一端",
            ha="center", fontsize=21, fontweight="bold")
    ax.legend(loc="center right", framealpha=0.15, fontsize=14)
    save(fig, "cost_curve.png")


# ── 4. 读取端管线 ────────────────────────────────────────
def pipeline():
    fig, ax = new_ax((12.8, 6.0))
    strip(ax)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.axis("off")
    ax.text(5.0, 9.4, "读取端四件套:e2e 42.6% → 75.4% 的全部来源", ha="center",
            fontsize=22, fontweight="bold")

    steps = [
        ("query", "用户问题\n(判据先预注册)", MUT),
        ("① 六型路由", "陈述型→turn 级块\n跨会话型→摘要卡", BLUE),
        ("② BM25+dense\nRRF 融合", "词面扛精确标识符\n向量扛语义", BLUE),
        ("③ 日期锚定", "before/after\n问题拿时序把手", BLUE),
        ("④ 摘要卡组装", "分型装配\n42.6→75.4", GREEN),
    ]
    xs = [0.25, 2.2, 4.05, 5.9, 7.85]
    w, y, h = 1.7, 3.6, 3.1
    for (title, sub, c), x in zip(steps, xs):
        box(ax, x, y, w, h, PANEL, c, lw=2.4)
        ax.text(x + w / 2, y + h * 0.68, title, ha="center", fontsize=14,
                fontweight="bold", color=c)
        ax.text(x + w / 2, y + h * 0.26, sub, ha="center", fontsize=11.5, color=MUT)
    for x in xs[:-1]:
        arrow(ax, x + w + 0.03, y + h / 2, x + w + 0.22, y + h / 2, FG)

    ax.text(5.0, 2.1, "同样公开的负结果(预注册否决):", ha="center", fontsize=14.5, color=MUT)
    ax.text(5.0, 1.15, "rerank 有害(−2pt)  ·  K=50 无增益  ·  小 embedder 更差",
            ha="center", fontsize=15.5, color=YELLOW)
    save(fig, "pipeline.png")


# ── 5. e2e 主图 ─────────────────────────────────────────
def e2e():
    fig, ax = new_ax((12.8, 6.6))
    strip(ax)
    bars = [
        ("routing 前\n(裸检索)", 42.6, MUT),
        ("routing 后\n(定案)", 75.4, GREEN),
        ("剔除 71 道\n判官故障题", 81.6, "#1a7f37"),
    ]
    x = [0, 1, 2]
    vals = [b[1] for b in bars]
    cols = [b[2] for b in bars]
    ax.bar(x, vals, width=0.52, color=cols, alpha=0.92, edgecolor=BG)
    ax.bar([2], [100], width=0.52, color="none", edgecolor="#1a7f37",
           ls=(0, (4, 3)), lw=1.6, alpha=0.65)
    for i, v in enumerate(vals):
        ax.text(i, v + 2.2, f"{v}%", ha="center", fontsize=25, fontweight="bold", color=cols[i])
    ax.text(1, 40, "+32.8pt", ha="center", fontsize=17, color=YELLOW, fontweight="bold")
    ax.text(2, 60, "双口径强制披露\n(不是藏,是报)", ha="center", fontsize=12.5,
            color="#116329", style="italic")
    ax.set_xticks(x)
    ax.set_xticklabels([b[0] for b in bars], fontsize=15)
    ax.set_ylim(0, 100)
    ax.set_ylabel("LongMemEval-S e2e · 500 题", fontsize=14)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.axhline(100, color=BG, lw=0)
    ax.set_title("同样的记忆,同样的题 —— 变的只是读取端路由",
                 fontsize=21, fontweight="bold", pad=16)
    save(fig, "e2e.png")


# ── 6. 六分型 ───────────────────────────────────────────
def breakdown():
    fig, ax = new_ax()
    strip(ax)
    types = [
        ("SSU 单会话-用户", 97.1), ("SSA 单会话-助手", 83.9),
        ("KU 知识更新", 80.8), ("SSP 单会话-偏好", 80.0),
        ("MS 多会话", 69.2), ("TR 时序推理", 62.4),
    ]
    names = [t[0] for t in types][::-1]
    vals = [t[1] for t in types][::-1]
    cols = [GREEN if v >= 80 else (YELLOW if v >= 65 else "#e2823f") for v in vals]
    ax.barh(names, vals, height=0.6, color=cols, alpha=0.92)
    for i, v in enumerate(vals):
        ax.text(v + 1.1, i, f"{v}%", va="center", fontsize=17, fontweight="bold", color=FG)
    ax.set_xlim(0, 108)
    ax.set_xlabel("重判口径 · n=500(定案成绩册 SCOREBOARD)", fontsize=13, color=MUT)
    ax.set_title("六分型成绩单:哪里强、哪里是下一步(tr 62.4 = 已知短板,不藏)",
                 fontsize=19, fontweight="bold", pad=14)
    ax.tick_params(axis="y", labelsize=14)
    save(fig, "breakdown.png")


# ── 7. 检索对打 ─────────────────────────────────────────
def headtohead():
    fig, ax = new_ax()
    strip(ax)
    groups = ["P@1", "P@5", "MRR"]
    ours = [0.890, 0.978, 0.929]
    theirs = [0.774, 0.916, 0.834]
    x = np.arange(3)
    w = 0.32
    ax.bar(x - w / 2, ours, w, color=GREEN, label="nautilus-compass", alpha=0.95)
    ax.bar(x + w / 2, theirs, w, color="#8c959f", label="mem0 2.0.19(我方复现)", alpha=0.95)
    for i, (o, t) in enumerate(zip(ours, theirs)):
        ax.text(i - w / 2, o + 0.015, f"{o:.3f}", ha="center", fontsize=15,
                fontweight="bold", color=GREEN)
        ax.text(i + w / 2, t + 0.015, f"{t:.3f}", ha="center", fontsize=15, color=MUT)
    ax.text(0, 0.60, "+11.6pt", ha="center", fontsize=16, color=YELLOW, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(groups, fontsize=17)
    ax.set_ylim(0, 1.1)
    ax.set_title("唯一站得住的对打:同 500 题 · 同判据 · BGE-m3 双方",
                 fontsize=21, fontweight="bold", pad=14)
    ax.legend(fontsize=14, loc="lower right", framealpha=0.15)
    ax.text(0.5, -0.16, "复现脚本开源 · ≈$3.50 GPU 时 · 欢迎重跑",
            transform=ax.transAxes, ha="center", fontsize=14, color=MUT)
    save(fig, "headtohead.png")


# ── 8. EverMemBench 客场 ────────────────────────────────
def evermem():
    fig, ax = new_ax((12.8, 6.6))
    strip(ax)
    names = ["nautilus-compass", "MemOS", "Zep", "Mem0"]
    vals = [45.9, 42.55, 39.97, 37.09]
    cols = [GREEN, "#8c959f", "#8c959f", "#8c959f"]
    ax.bar(names, vals, width=0.5, color=cols, alpha=0.95)
    # 区间带 44.4-47.3
    ax.errorbar([0], [45.9], yerr=[[45.9 - 44.4], [47.3 - 45.9]], fmt="none",
                ecolor=YELLOW, elinewidth=3, capsize=9, capthick=3)
    ax.text(0, 48.6, "44.4 – 47.3", ha="center", fontsize=19, fontweight="bold", color=GREEN)
    for i, v in enumerate(vals[1:], start=1):
        ax.text(i, v + 0.7, f"{v:.2f}", ha="center", fontsize=15, color=MUT)
    ax.set_ylim(30, 52)
    ax.set_ylabel("EverMemBench(各方法报告值)", fontsize=13.5)
    ax.set_title("客场作战:第三方 EverMemBench 榜单口径", fontsize=21,
                 fontweight="bold", pad=14)
    ax.text(0.5, -0.14, "LOCOMO 客场(n=1986):P@1 0.644 vs mem0 0.592 —— 换一张卷子,结论不掉",
            transform=ax.transAxes, ha="center", fontsize=14.5, color=FG)
    save(fig, "evermem.png")


# ── 9. LME-V2 官方基准 ──────────────────────────────────
def lmev2():
    fig, ax = new_ax()
    strip(ax)
    x = np.arange(2)
    w = 0.3
    untuned = [19.6, 12.8]
    tuned = [40.0, 38.4]
    ax.bar(x - w / 2, untuned, w, color="#8c959f", label="untuned(首跑基线)")
    ax.bar(x + w / 2, tuned, w, color=GREEN, label="三刀调优后(定案)")
    for i in range(2):
        ax.text(i - w / 2, untuned[i] + 1, f"{untuned[i]}%", ha="center", fontsize=15, color=MUT)
        ax.text(i + w / 2, tuned[i] + 1, f"{tuned[i]}%", ha="center", fontsize=16,
                fontweight="bold", color=GREEN)
    ax.set_xticks(x)
    ax.set_xticklabels(["web 域", "enterprise 域"], fontsize=17)
    ax.set_ylim(0, 50)
    ax.set_ylabel("LME-V2(上游官方基准 · 451 题)")
    ax.set_title("LME-V2 官方基准:untuned → 定案,双域翻倍以上(归因上游,不抢功)",
                 fontsize=19, fontweight="bold", pad=14)
    ax.legend(fontsize=14, framealpha=0.15)
    save(fig, "lmev2.png")


# ── 10. 延迟对比 ────────────────────────────────────────
def latency():
    fig, ax = new_ax()
    strip(ax)
    ax.set_xscale("log")
    ax.set_xlim(0.05, 200)
    ax.barh([1], [0.57], height=0.42, color=GREEN, alpha=0.95)
    ax.barh([0], [26.9], height=0.42, color="#8c959f", alpha=0.95)
    ax.errorbar([0.57], [1], xerr=[[0.57 - 0.34], [0.80 - 0.57]], fmt="none",
                ecolor="#116329", elinewidth=3, capsize=8, capthick=3)
    ax.text(0.62, 1.32, "0.34 – 0.80 s", fontsize=19, fontweight="bold", color=GREEN)
    ax.text(29, 0.32, "26.9 s", fontsize=19, fontweight="bold", color="#424a53")
    ax.set_yticks([1, 0])
    ax.set_yticklabels(["nautilus-compass\n(读取端路由,无 LLM)", "LLM-controller 型\n(写入时压缩阵营)"],
                       fontsize=14)
    ax.set_xlabel("e2e 延迟 p95(秒,对数轴)", fontsize=13.5)
    ax.set_title("p95 延迟 ≈ 80× 差距:把智能放对时刻的自然结果", fontsize=21,
                 fontweight="bold", pad=14)
    ax.text(1.15, 0.55, "≈80×", fontsize=30, color=YELLOW, fontweight="bold")
    save(fig, "latency.png")


# ── 11. 判分卫生:抓了自己判官 5 次 ──────────────────────
def judge_cards():
    fig, ax = new_ax((12.8, 6.6))
    strip(ax)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.axis("off")
    ax.text(5.0, 9.4, "判分卫生学:我们抓了自己判官 5 次", ha="center",
            fontsize=23, fontweight="bold")
    ax.text(5.0, 8.35, "判官会静默失败 —— 不抓,你的排行榜就是虚构的",
            ha="center", fontsize=15, color=RED)

    cards = [
        ("网关断连", "71 题被静默记成错答\n= 整卷 14.2%"),
        ("401 变量名坑", "harness 默认读 OPENAI_API_KEY\nsource ARK 变量 = 全员 401"),
        ("预算被吃满", "judge 4096 token 被\nreasoning 吃满 → 系统性压 0"),
        ("并发写文件", "双进程同写一文件\n结果互相覆盖"),
    ]
    pos = [(0.7, 4.4), (5.15, 4.4), (0.7, 1.7), (5.15, 1.7)]
    for (title, body), (x, y) in zip(cards, pos):
        box(ax, x, y, 4.15, 2.3, PANEL, RED, lw=1.8)
        ax.text(x + 0.3, y + 1.75, "× " + title, fontsize=15.5, color=RED, fontweight="bold")
        ax.text(x + 0.3, y + 0.75, body, fontsize=12.5, color=MUT)

    box(ax, 3.1, 0.25, 3.8, 0.95, "#dafbe1", GREEN, lw=1.8)
    ax.text(5.0, 0.72, "→ 协议:预注册锚 · 冒烟测试 · 双口径 · Wilson CI",
            ha="center", fontsize=14, color=GREEN, fontweight="bold")
    save(fig, "judge_cards.png")


# ── 12. dogfood ─────────────────────────────────────────
def dogfood():
    fig, ax = new_ax()
    strip(ax)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.axis("off")
    ax.text(5.0, 9.4, "dogfood:造它的组织,本身就长在它上面", ha="center",
            fontsize=23, fontweight="bold")

    stats = [("130", "天", BLUE), ("771", "commits", GREEN), ("603", "由 agent 舰队提交", PURPLE)]
    for (num, label, c), x in zip(stats, [2.0, 5.0, 8.0]):
        ax.text(x, 6.6, num, ha="center", fontsize=46, fontweight="bold", color=c)
        ax.text(x, 5.6, label, ha="center", fontsize=15, color=MUT)

    # 甜甜圈:78% agent 提交
    axc = fig.add_axes([0.36, 0.06, 0.28, 0.36])
    axc.set_facecolor(BG)
    axc.pie([603, 168], colors=[PURPLE, "#d0d7de"], startangle=90,
            wedgeprops={"width": 0.32})
    axc.text(0, 0, "78%\nagent 提交", ha="center", va="center",
             fontsize=15, fontweight="bold")
    ax.text(5.0, 1.15, "nautilus 智涌平台:多 agent 调度 · compass 记忆胶囊:验证过的经验才写回",
            ha="center", fontsize=14.5, color=MUT)
    save(fig, "dogfood.png")


# ── 13. demo 终端模拟(D1 跨会话,与 demo_recording_script.md 同源)──
def demo_terminal():
    fig, ax = new_ax((12.8, 7.2))
    strip(ax)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.axis("off")

    # 窗体
    box(ax, 0.35, 0.35, 9.3, 9.0, "#0b0f14", "#d0d7de", lw=2)
    ax.add_patch(FancyBboxPatch((0.35, 8.55), 9.3, 0.8, boxstyle="round,pad=0.015",
                                fc="#f6f8fa", ec="#d0d7de", lw=1.5))
    for i, c in enumerate([RED, YELLOW, GREEN]):
        ax.add_patch(Circle((0.85 + i * 0.38, 8.95), 0.115, fc=c, ec="none"))
    ax.text(5.0, 8.93, "terminal — nautilus-compass (fully local)", ha="center",
            fontsize=12.5, color=MUT, family=["Consolas", "Microsoft YaHei"])

    lines = [
        ("$ ", GREEN, "compass ingest --session s1 ", FG, "\"用户周二早上遛狗,狗叫 Momo\"", "#e3b341"),
        ("   √ stored verbatim · 0 LLM calls · 0.3s", GREEN, "", "", "", ""),
        ("$ ", GREEN, "compass ingest --session s2 ", FG, "\"在学 Rust,目标重写公司数据处理管线\"", "#e3b341"),
        ("   √ stored verbatim · 0 LLM calls", GREEN, "", "", "", ""),
        ("$ ", GREEN, "compass ingest --session s3 ", FG, "\"每周一例会总被临时取消\"", "#e3b341"),
        ("   √ stored verbatim · 0 LLM calls", GREEN, "", "", "", ""),
        ("", "", "", "", "", ""),
        ("# ─── 三周后 · 全新会话 ───────────────────────────", MUT, "", "", "", ""),
        ("$ ", GREEN, "compass recall ", FG, "\"What does the user do on Tuesday mornings?\"", "#e3b341"),
        ("   → session-1: \"周二早上遛狗,狗叫 Momo\"  ", FG, "score 0.89", BLUE, "", ""),
        ("   √ cross-session hit · routed retrieval · p95 0.34s", GREEN, "", "", "", ""),
        ("", "", "", "", "", ""),
        ("$ ", GREEN, "compass recall  ", FG, "# control: 全新空记忆,同一问题 → (empty)", MUT),
    ]
    y = 8.0
    MONO = ["Consolas", "Microsoft YaHei"]
    for parts in lines:
        seg = [parts[0], parts[2], parts[4]]
        col = [parts[1], parts[3], parts[5]]
        if any(seg):
            xoff = 0.75
            for s, c in zip(seg, col):
                if s:
                    ax.text(xoff, y, s, fontsize=14.5, color=c, family=MONO,
                            fontweight="bold", va="top")
                    xoff += 0.148 * len(s)
        y -= 0.62

    ax.text(5.0, 0.12, "demo 流程示意(与 demo_recording_script.md 同源 · 现场跑真实终端)",
            ha="center", fontsize=11.5, color=MUT, style="italic")
    save(fig, "demo_terminal.png")


if __name__ == "__main__":
    blind_bet()
    arch()
    cost_curve()
    pipeline()
    e2e()
    breakdown()
    headtohead()
    evermem()
    lmev2()
    latency()
    judge_cards()
    dogfood()
    demo_terminal()
    print("all charts →", OUT)
