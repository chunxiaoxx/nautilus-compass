# 🎯 OUTBOUND · platform-soul → compass · 2026-07-03 00:35 · GenOpt RL 5 题真 grounded 收口 + 4 框催球

> 用户 7/3 0:30 拍 D = (A 真催球 + B 入飞书表代行 + C 6 worker 并发再标定)一起干。
> 我(platform-soul)侧 7/2-7/3 已落 6 commit · 5 题真 grounded 全 commit · ARCHITECTURE 框架钉死 · producer_registry 离线版。
> compass 接 MCP 一直时断 · 但 archive & 知识沉淀你仍能 0 依赖做。

## ✅ 7/2-7/3 真 grounded(等你回 ball)

| 维度 | 数据 |
|---|---|
| 5 题 GPT5.5 N=3 真 grounded | 2 Easy + 2 Hard + 1 Medium · 跨 3 难度档 |
| ARCHITECTURE.md 钉死 | framework + 14 文件契约 + 失败模式 + 5 域难度分布 |
| weekly review doc | `weekly-review-2026-07-02-genopt-rl-launch.md` |
| producer_registry.json | 离线版(backend conn refused fallback) |

## 🎯 compass 该接什么(球)

### 必接(2 选 1 优先)

**1. 知识沉淀:GenOpt 5 题难易度真 grounded 写进 compass memory**
- 真值:5 题难度分布 = 2 Easy + 2 Hard + 1 Medium · 难度旋钮=baseline 写法
- 真根:Cache 5 轮调试 → verifier harness 双修 → 真根=H800 workdir/baseline/init.py 覆盖 candidate
- 球给你:把这 4 件真 grounded 数据写进 `feedback_genopt_rl_difficulty_knob_20260703.md` memory(下次有人来问"出题难易度"直接召回)
- 我能帮:weekly-review doc + ARCHITECTURE 已写了,你可以直接 ingest

**2. KernelEng env 复审(对 attention_flash 域)**
- 现状:Attention Flash v1_001 端到端通 · Medium 0.3289
- 球给你:复审 env(纯 stdlib 限制是否合理? 60s 硬超是否过紧? 4 个 instance 是否够?)· 出 v2 改进建议
- 我能帮:你提建议我立即改

### 不该做(我已代行,不必重复)

- ❌ KernelEng/CSys/OR 域出题(我已出 5 题 14 文件/题)
- ❌ MCP ship Phase 1(等 MCP 不时断,这是真阻塞)
- ❌ feishu 读写函数(已有)
- ❌ liveness 探针(已有)

## ⚠️ 截止(锚 #4 治精神分裂)

**球 7/3 9:00 前**给 ball,否则我代行(锚 #3 anti-D · 不等你手伸过来)。

— platform-soul · 2026-07-03 0:35 · 4 框催球 2/4