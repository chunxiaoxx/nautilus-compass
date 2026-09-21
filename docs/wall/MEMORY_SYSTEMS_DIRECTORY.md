# 认证轨·记忆系统目录 v0(2026-09-21 立版)

> 定位:买方尽调的菜单——每个记忆系统一行,分数是**谁报的**一目了然。
> 分级纪律:厂商自报(哪怕经由第三方评测汇总)= `self-reported / UNVERIFIABLE`;
> 经 Assay 独立复算过门的声明才标 `assayed`。**本目录首版全部 UNVERIFIABLE 起步,
> 包括我们自己。**

## 数据源与诚实分级

主表数字来源:**MemTensor/OmniMemEval**(生产者自建统一评测,15 后端×6 用户
记忆基准;answer=gpt-4.1-mini/judge=gpt-4o-mini 全披露)。我们对它做过 **Tier-1
复算**(README 十数 10/10 对上源表+基线均值精确复算+两小发现,回执
GENESIS_MEMTENSOR_OMNIMEMEVAL.md)——**验的是其自洽性与溯源,不是评测本身的
正确性**(那需要 Tier-2 全重跑)。故下表所有分数的正确分级是:
**「经 Assay Tier-1 溯源核验的厂商自报」**,仍非独立复算值。

## 目录(v0 · 2026-09-21)

| 系统 | LoCoMo | LongMemEval | HaluMem | Assay 验证状态 |
|---|---:|---:|---:|---|
| MemOS(MemTensor) | 88.83 | 89.20 | 80.91 | 🔹 assayed-tier1(README↔源表 10/10+均值复算;LongMemEval 加权口径缺口在案) |
| EverOS | 82.75 | 80.40 | 88.66 | ⚪ self-reported/UNVERIFIABLE |
| Cognee | 83.48 | 51.80 | 72.60 | ⚪ self-reported/UNVERIFIABLE |
| Hindsight | 81.99 | 72.20 | 83.99 | ⚪ self-reported/UNVERIFIABLE |
| Mem0 | 77.68 | 56.00 | 73.64 | ⚪ self-reported/UNVERIFIABLE |
| Letta | 77.12 | 77.67 | 85.43 | ⚪ self-reported/UNVERIFIABLE |
| Supermemory | 73.53 | 66.07 | 52.61 | ⚪ self-reported/UNVERIFIABLE |
| mem9 | 73.64 | 78.00 | 72.80 | ⚪ self-reported/UNVERIFIABLE |
| MemMachine | 73.90 | 63.60 | 47.02 | ⚪ self-reported/UNVERIFIABLE |
| MemoryLake | 72.49 | – | – | ⚪ self-reported/UNVERIFIABLE |
| Viking | 69.33 | 61.07 | 77.39 | ⚪ self-reported/UNVERIFIABLE |
| Zep / Graphiti | 63.83 | 79.80 | 81.71 | ⚪ self-reported/UNVERIFIABLE |
| Memori | 41.34 | 20.80 | 49.38 | ⚪ self-reported/UNVERIFIABLE |
| NanoJev(TianyuCodings) | – | – | – | 🔹 **assayed×3**(六声明 AGREE+校准全重放 1.99e-08+权重级重放四锚全 exact)——轨迹域,非对话记忆榜 |
| NautilusMem(我们) | LME-V2 web 40.0 / ent 38.4 | ← LME-V2 | – | ⚪ self-reported/UNVERIFIABLE(**同尺自报,照登**) |

升级通道:任何厂商提交可复算材料(公开 artifacts+判据锚)→ 免费复算 → 过门
升 `assayed`,回执挂墙。UNVERIFIABLE 不是差评,是**还没验**——本目录的默认态。

## 边界

- 表内分数互相可比性受制于 OmniMemEval 的统一 harness(其自披露口径);
  不同榜单/口径的分数禁止混读。
- judge=gpt-4o-mini 的 LLM-as-judge 依赖是方法固有局限(生产者已自披露)。
- 本目录不构成采购建议;买方尽调走 SKU-A(L1 算术/L2 轨迹/L3 全栈)。
