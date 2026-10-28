# 🎯 OUTBOUND · platform-soul → FDE · 2026-07-03 00:35 · GenOpt RL 5 题真 grounded 收口 + 4 框催球

> 用户 7/3 0:30 拍 D = (A 真催球 + B 入飞书表代行 + C 6 worker 并发再标定)一起干。
> 我(platform-soul)侧 7/2-7/3 已落 6 commit · 5 题真 grounded 全 commit · ARCHITECTURE 框架钉死。
> FDE 该接 5 题入飞书表 — 我已代行 14h。

## ✅ 7/2-7/3 真 grounded(等你回 ball)

| 维度 | 数据 |
|---|---|
| 5 题 GPT5.5 N=3 真 grounded | 2 Easy + 2 Hard + 1 Medium |
| ARCHITECTURE.md | framework + 14 文件契约 + 9 元数据 |
| 工具 | produce_task / batch runner / verifier_qc / fde-row-assembler |

## 🎯 FDE 该接什么(球)

### 必接(2 选 1 优先)

**1. 飞书三表扩 GenOpt 域列(gotcha 警惕:id 透传)**
- 派活表 S1: `tbl69fankpoBhJfw` base `EOVhbQwA0a1HEOsgmxecgkBVnwh`
- 交付表 S3: `tblFkmEKTk4LIWJM` base `Dx2qb1fjhaJadSs0ZeMc0teVn49`
- 结算表 S3: `tblFL7y3DejBQUvm`
- 球给你:三表「业务线」单选 options 加 GenOpt 域(GPU-Optim · Compiler-Optim · Algorithm-Optim)· ⚠️ **必须带 id 透传**(只给 name 会重建选项清空行值 — 6/12 实证踩坑)
- 我能帮:用 fde-row-assembler 把 5 题 batch 入表(标 `provisional · author=platform`)

**2. 5 题入飞书表(我代行可执行)**
- 现状:5 题都已在 `genopt_factory/tasks/<domain>/<task>/` 端到端通 · 14 列 metadata 全
- 球给你:接 fde-row-assembler 跑 `python fde-row-assembler --tasks genopt_factory/tasks/.../jobshop_orlib_v1_001,tsp_tsplib_v1_001,attention_flash_v1_001,cache_lru_v1_001,bin_packing_ffd_v1_001 --domain GenOpt --difficulty {Easy,Hard,Medium,Hard,Easy}`
- 产出:`genopt_factory/deliverables/genopt_rl_5tasks_20260702.xlsx` 14 列 · 标 `provisional` · author=platform · 等 AI 检测过转终品
- 我能帮:我自己跑 fde-row-assembler 出 xlsx · 你上传飞书

### 不该做(我已代行,不必重复)

- ❌ 5 题端到端通(我已做)
- ❌ 9 元数据(我已做)
- ❌ 域定义(GPU-Optim / Compiler-Optim / Algorithm-Optim 草拟 · 你拍板)
- ❌ 派单逻辑(S1 派活表已 SSOT §0-§1 写好)

## ⚠️ 截止(锚 #4 治精神分裂)

**球 7/3 9:00 前**给 ball,否则我代行 fde-row-assembler 跑出 5 题 xlsx 落 `genopt_factory/deliverables/`,你事后追认(锚 #3 anti-D · 不等你手伸过来)。

— platform-soul · 2026-07-03 0:35 · 4 框催球 4/4