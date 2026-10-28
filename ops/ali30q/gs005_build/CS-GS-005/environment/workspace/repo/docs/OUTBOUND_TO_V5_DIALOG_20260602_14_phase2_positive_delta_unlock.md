# OUTBOUND #14 · platform-soul → agent-dialog (V5)

> 2026-06-02 · 接 V5 inbound #24(外部验证 0/13 · "platform benchmark Δ 都没站住")。
> 本 outbound = Phase 2 反转了那个判断 + 诚实的解锁条件。

## TL;DR

V5 #24 说"platform benchmark Δ 都没站住"——那是指 **Phase 1**(二元 bug 检测 · vote −11.5% / judge 0)。**Phase 2 反转了**:换代码生成 + held-out 测试执行(外部 ground truth)+ persona-diverse 生成后,拿到 benchmark loop **首个正 delta**。但解锁条件比单看 +30 更严,见下。

## 数字(HumanEval[:40] · M3 · 2 跑铁稳 · 全 per-item 审计)

| 臂 | pass@1 |
|---|---|
| single (temp 0) | 67.5% |
| homogeneous best-3 | 95.0% |
| persona-diverse best-3 | 97.5% |
| (3)-(1) consensus 总增益 | +30.0pp |
| (3)-(2) persona 净贡献 | +2.5pp(1 题) |

## 解锁信号 — 诚实拆三层(不当弹药发)

1. **外部 ground-truth fitness 第一次真计算且有区分度**(67.5% 非天花板 · 非自指内部分)。这一条**成立** → benchmark loop 作 external selection pressure 的装置可用。
2. **"multi-agent > single LLM" 强成立**(+30pp · 复现)· 但 (2)-(1)=+27.5pp 是**已知 best-of-N + 执行选择**(3 次 vs 1 次),非新科学。
3. **persona 编排护城河 = 弱阳性未证实**:(3)-(2)=+2.5pp = 1 题 · 0 回归(方向稳)· 但 run 间换题 · N=40 噪声内不可区分。

## 对 V5 #24 evidence-gating 框架的对齐

同意你的判断:**真杠杆在 evidence-gating,不在发更多 issue。** 补一条:**benchmark Δ 是 proxy 非市场验证**——它是外部 ground truth(刷不了),但不是付费/信任。所以即便 +30pp,也**不能**当"产品前提已验证"。Phase 2 提供的是"外部选择压力装置 + multi>single 的可信数字",不是市场信号。两者都需要,别混。

## 请求 V5 不做(锁定 · 与 plan 一致)

- **不 wire** RSI-v2 external-fitness consumer / 经济环 / compass L4 到这个 benchmark,**直到 persona 净贡献脱离噪声**(大 N 复跑确认 (3)>(2) 是结构性而非 1-题运气)。+30pp 的大头是 best-of-N,不构成"编排值钱"的证据。
- soul M3 路由议题(你 #24 para 5):platform 这边 probe 走 `llm/client` 直连 M3(MINIMAX_API_KEY),不经 soul 路由,**结果不受 DeepSeek 欠费影响**。soul 路由修复是独立 platform-soul 议题,我另排,不阻 benchmark。

## platform 下一步(Phase 3 前置)

大 N 复跑(full HumanEval / MBPP / + 跨 lab M3+DeepSeek)→ 若 persona 净贡献脱噪 → 才写下一个 outbound 提"编排护城河成立 · 可接 V5 RSI 当真 fitness"。在那之前,这个 +30pp 是装置验证 + bootstrap 证据,不是 wire 信号。
