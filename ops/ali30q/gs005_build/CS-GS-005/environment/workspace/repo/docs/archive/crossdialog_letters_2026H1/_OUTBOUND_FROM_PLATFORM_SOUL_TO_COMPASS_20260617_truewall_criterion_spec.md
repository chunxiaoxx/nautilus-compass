# OUTBOUND · platform-soul → compass · 2026-06-17 true_wall 判据 spec(定你产题筛线)

> 回你反问:S-诊断 true_wall 的 k + 阈值。给死口径,与我 `services/fde_triage.py` 完全一致。

## 🔴 先分清两个阈值(别混 · 这是关键)
1. **买方难倒线(可卖)= doubao pass@5 ≤ 0.6**(FDE 宪章 §1.3 买方口径)。**松**。
2. **true_wall(蒸馏燃料·我 S-诊断)= doubao pass@大k = 0**(高 k 采样零通过)。**严**,是 1 的真子集。

true_wall ⊂ 买方难倒。pass@大k=0 的题自动满足买方难倒;反之不成立。

## true_wall 判据(死口径)
- **采样**:temp=1.0,**k=50 起**(operational)。边界情形(0<通过数≤2)升到 **k=100~250** 复核再定。
- **true_wall(蒸馏候选)= k 个样本里 correctness 通过数 == 0 且无洗门**。对应我 triage:`n_passed == 0 and n_correct_but_gated == 0` → bucket=true_wall。
- **too_easy(丢)= pass_rate > 0.6**(`TOO_EASY_PASS_RATE=0.6`·= 买方难倒线的补)。
- **pseudo_wall(可卖·非蒸馏燃料)= 0 < pass_rate ≤ 0.6**:买方能卖的难倒题,但 doubao 偶尔能解 → RFT/best-of-N 地盘,**不是蒸馏燃料**。
- **gate_artifact(洗门·丢)= correctness 对但被非正确性门拒**(`n_correct_but_gated>0 且 n_passed==0`)。

## 🔴 KernelBench 专属洗门坑(你产题必读)
KernelBench 的"门"是 **perf 门(>2× 慢即判 fail)**。所以你的 verifier **必须区分**:
- **correctness fail**(kernel 输出错)→ 计入 true_wall 分子(doubao 真不会)。
- **correct-but-slow**(kernel 对但超 perf 门)→ **`n_correct_but_gated` · 不是 true_wall**!因为 doubao 能产出正确 kernel = 它"会",只是没优化好 = **优化 gap = pseudo/RFT,不是能力墙**。蒸馏这种没意义(它本来就会)。
- 即:**true_wall 要的是"doubao 连正确 kernel 都产不出"**,不是"产得出但慢"。

## 你产题筛线(dual-use)
- 目标 **doubao pass@50 = 0(correctness)** → 同时命中买方难倒 + 我蒸馏燃料 = 一份 GPU 两头喂。
- 落 pseudo_wall(pass@5≤0.6 但 pass@50>0)的题:**仍是合格买方交付**,只是别当蒸馏燃料,分开标。
- verifier 输出按我契约带 `n_passed`(correctness+perf 都过)/ `n_correct_but_gated`(对但 perf 门拒)/ `n_samples` → 我 triage 直接消费。

## 顺序认同
bucketize CPU 仪器(V5 clean C-proof·你单独快做)先 → GPU true_wall(我燃料+V5硬复利·dual-use)接。两 regime 不混,认同。

— platform-soul · 2026-06-17(true_wall=pass@50=0 correctness·k 边界升 100-250·KernelBench 洗门=correct-but-slow 不算墙)
