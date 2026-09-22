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

---

## 汇率牌格式 v1(2026-09-22 · 承校准货币立项 · C=1−ECE)

> 校准货币定义:C(agent, domain, t) = 1 − ECE_t。做市方只对「此 C 值在 TTL 内
> 经过独立复算」背书,不对分数本身背书。C 不可自报;自家同尺照登。

| 系统 | 域 | C(校准货币) | TTL | 趋势 | 做市方 | 来源 |
|---|---|---|---|---|---|---|
| Jev 1.13.0(hosted) | 闭合确定性任务 | **0.959** | 2026-12-21 | ▬ 新上市 | Assay | 研究#1 ECE 0.041 |
| Jev 1.13.0(hosted) | 对抗压测 | **0.988** | 2026-12-21 | ▬ 新上市 | Assay | 研究#2 ECE 0.012 |
| Jev 1.13.0(hosted) | python 异常预测(jev-trust 首跑) | **0.953** | 2026-12-21 | ▬ 新上市 | Assay | n=120 acc 100% ECE 0.0466(待非实现者复算) |
| Jev 1.13.0(hosted) | 代码 patch 行为判定(jev-trust 域2) | **0.866** | 2026-12-21 | ▼ 较域1 | Assay | n=120 acc 92.5% ECE 0.1343(待非实现者复算) |
| Jev 1.13.0(hosted) | 具身数据 QC 标注(jev-trust 域3) | **0.689** | 2026-12-21 | ▼ 较域2 | Assay | n=120 acc 50%(全 yes 策略:召回 100%/精确 50%)ECE 0.3108(待非实现者复算) |
| Jev 1.13.0(hosted) | 合成邮件分诊(mini) | **0.831**(spam 布尔) | 2026-09-22 | ▼ 单次 | Assay | mini-DCR dry-run ECE 0.169 |
| Jev 1.13.0(hosted) | 合成邮件三分类 | **0.086**(choice) | 2026-09-22 | ▼ 单次 | Assay | mini-DCR choice acc 50%@conf 91% |
| NanoJev 0.6B(local) | 轨迹重放 | **≈1.000** | 2026-12-19 | ▬ 新上市 | Assay | Tier-3 四锚全 exact |
| NanoJev 0.6B(local) | 校准基准重放 | **≈1.000** | 2026-12-19 | ▬ 新上市 | Assay | Tier-2 15 指标 Δ1.99e-08 |
| MemOS(MemTensor) | OmniMemEval 自报 | ⚪ UNVERIFIED | — | — | —(Tier-1 溯源已验,评测本身未复算) | README 溯源 10/10 |
| Mem0 | OmniMemEval 自报 | ⚪ UNVERIFIED | — | — | — | 同 |
| EverOS | OmniMemEval 自报 | ⚪ UNVERIFIED | — | — | — | 同 |
| …其余 12 系统 | | ⚪ UNVERIFIED | — | — | — | 见上方 v0 目录 |
| NautilusMem(自家) | LME-V2 | ⚪ UNVERIFIED | — | — | —(**同尺照登**) | 自报 web 40.0/ent 38.4 |

**读法**:C≥0.80=可信任面值;0.50-0.79=按 C 折扣信任;C<0.50=降级(人工复核);
UNVERIFIED=未验(非差评)。**趋势列**:▲=最新复算高于上次;▬=持平;▼=低于上次。
mini-DCR 的 choice C=0.086 就是活教材:Jev 在邮件三分类域的 0.9 置信当 0.5 用。

**上榜通道**:DCR 订单(免费首 10/付费)→ 独立复算出 C 值 → 挂牌(客户可选匿名
域名,但 C 值与 TTL 公开)。**贬值通道**:§5b 挑战成功 → C 硬着陆 0 + 赔偿。
