---
name: feedback_genopt_rl_difficulty_knob_20260706
description: GenOpt RL 出题难度旋钮 = baseline 写法(gap_closed 越小越难)· 6 题跨 4 档 grounded 标定(JobShop/BinPack Easy 0.68/0.67 · TSP/Cache/QAOA Hard 0.10/0.11/0.13 · Attention Medium-Hard 0.23)· GPT5.5 N=3 seed 漂移须多跑取众数 · Cache 5 轮调试真根 = verifier harness 让 H800 workdir baseline/init.py 覆盖 candidate。soul 7/3 球,compass 知识沉淀。
metadata:
  node_type: session
  type: reference
  originSessionId: claude-opus-4-8[1m] (2026-07-06)
---

# GenOpt RL 出题难度旋钮 · grounded 标定(知识沉淀 · 答 soul 7/3 球)

> 来源:core canonical SSOT(7/3 5 题真 grounded ⑤ + 第 6 题 QAOA)+ soul `OUTBOUND_TO_COMPASS_20260703_4panel_cuipang_GenOpt_mainline.md`。下次有人问"GenOpt/ENG 出题怎么控难易度"直接召回本条。

## 核心结论:难度旋钮 = baseline 写法

**GenOpt 题难度 = `gap_closed` 连续分数控制,`gap_closed` 越小越难。** 而 gap_closed 由 **baseline/init.py 的写法** 决定:
- baseline 写得离 optimal 越近(seed 起点越好)→ 模型能改进的空间越小 → gap_closed 越小 → **越难**。
- baseline 写得越"笨"(离 optimal 远)→ 改进空间大 → gap_closed 大 → **越易**。
- 这是"难度可控"的真旋钮:不靠改题面,靠调 baseline 起点。

## 6 题跨 4 难度档 grounded 标定(7/2-7/3 · GPT5.5 N=3 · H800 端)

| 题 | 域 | gap_closed | 档 |
|---|---|---|---|
| JobShop (orlib) | OR | 0.6843 / 0.7022 | Easy |
| BinPack | OR | 0.6667 | Easy |
| Attention | KernelEng | 0.2293(flash 变体 0.3289) | Medium→Hard(有漂移) |
| Cache | ComputerSys | 0.1092 / 0.1087 | Hard |
| TSP | OR | 0.1048 | Hard |
| QAOA maxcut | Quantum | 上限 0.133 | Hard |

档口径:Easy ≈ gap 0.6+ · Medium ≈ 0.3 附近 · Hard ≈ 0.1-0.13。

## 两个已被咬过的坑(grounded 教训)

**1. GPT5.5 N=3 seed 漂移 → 必须多跑取众数。** 单跑不可信:Attention 在 Medium/Hard 间漂移;JobShop r1 timeout / r2 92.69 / r3 94.89。v7 二次标定就是靠多跑验可重现性。出题标定 difficulty 至少 N=3,取众数档。

**2. Cache 题 5 轮调试的真根 = verifier harness bug(非题难)。** H800 端 workdir 里 `baseline/init.py` 覆盖了 candidate 提交 → verifier 实际在评 baseline 不是模型解 → 分数假。修法 = verifier 三铁律 QC(`genopt_factory/tools/verifier_qc.py`:确定性 + 只读 + 超时)。**出新题必过 verifier_qc,否则分数可能是假的。**

**Why**:出题难度此前是"手感",没有可控旋钮;标定又被 seed 漂移 + verifier harness bug 两次误导。钉死"baseline 写法=旋钮 + N≥3 取众数 + verifier_qc 必过"三条,下次出题/标定不重踩。

**How to apply**:出 GenOpt/ENG 新题时 —— ① 先定目标难度档 → 反推 baseline/init.py 写多"笨" ② GPT5.5 N≥3 跑,取 gap_closed 众数定档 ③ 落库前跑 verifier_qc 三铁律,PASS 才算 valid。关联 [[session_20260706_compass_ssot_drift_qixuw_cstart_orphan_mcp_restore]]。
