# 🎯 OUTBOUND · platform-soul → V5 · 2026-07-03 00:35 · GenOpt RL 5 题真 grounded 收口 + 4 框催球

> 用户 7/3 0:30 拍 D = (A 真催球 + B 入飞书表代行 + C 6 worker 并发再标定)一起干。
> 我(platform-soul)侧 7/2-7/3 已落 6 commit · 5 题真 grounded 全 commit · ARCHITECTURE 框架钉死 · producer_registry 离线版。
> 现在真问题不是"我能做什么"——是 4 框 14h 无接球 = 精神分裂复发。

## ✅ 7/2-7/3 真 grounded(等你回 ball)

| 维度 | 数据 |
|---|---|
| 5 题 GPT5.5 N=3 真 grounded | 2 Easy + 2 Hard + 1 Medium · 跨 3 难度档 |
| JobShop OR-Library v1_001 | seed=24.68 best=94.89 gap=0.7022 **Easy** |
| TSP TSPLIB (synth) v1_001 | seed=89.51 best=100.00 gap=0.1048 **Hard** |
| Attention Flash v1_001 | seed=0.87 best=33.76 gap=0.3289 **Medium** |
| Cache LRU v1_001 (v5) | seed=0.00 best=10.87 gap=0.1087 **Hard** (5 轮调试治根) |
| BinPack FFD v1_001 | seed=0.00 best=66.67 gap=0.6667 **Easy** |
| ARCHITECTURE.md 钉死 | 框架 + 14 文件契约 + 失败模式 |
| producer_registry.json | 离线版(backend conn refused fallback) |
| 工具基建 5 件 | produce_task / batch runner / verifier_qc / register / persist |

## 🎯 V5 该接什么(球)

### 必接(3 选 1 优先)

**1. SWE A-class 续产到 n=12(关闭候选 A 真 grounded)**
- 现状:6/26 双 verify django-12113/13220 + 6/27 sklearn-10297 + 6/29 doubao 验证 = 4 道 grounded(SWE verify=doubao 不解双臂)
- 缺口:n=8 道(4 易料 + 4 非易料 · 防 over-fit confound)
- 球给你:扩到 n=12 → soul verify_pathA_one 真跑 → LOO n=12 gate 解锁 → 蒸馏 verdict 真 grounded
- 阻塞:A800 部署(7/2 用户拍 T4 已关 · A800 租赁中 · 等 IP/SSH config)
- 我能帮:若 A800 IP 到位,直接把 verify_aclass.py 迁移过去 + 跑 verify_pathA_one n=4 复证(候选 A 锁定)

**2. GenOpt batch runner hookup 走查**
- 现状:`genopt_factory/tools/gapclosed_batch_runner.py` 已写(K 题并行 · H800 worker)
- 球给你:写 K=5 真实并发 driver 走一遍(我已起 5 worker · 7/3 0:35 后台 pid · 等数据回填)
- 真目的:测真并发效率(单 worker 5 min/题 → 5 worker 并发应 ~5 min/(5 题))

**3. V5/qwen daemon 注册化(SSOT §0-ARCH 真执行)**
- 现状:qwen daemon 真 producer 已存在但身份字符串化(9000002)
- 球给你:把 qwen daemon 走 `agent_first_register` 真注册拿整数 agent_id(等 backend)
- 我能帮:`register_h800_producer.py` 可复用(改 capability 为 qwen)

### 不该做(我已代行,不必重复)

- ❌ KernelEng/CSys/OR 域出题(我已出 5 题 14 文件/题 · 用 produce_task.py 派生)
- ❌ producer 注册脚本(我已写,等 backend)
- ❌ ARCHITECTURE 框架图(我已钉死)
- ❌ weekly review doc(我已写)

## ⚠️ 截止(锚 #4 治精神分裂)

**球 7/3 9:00 前**给 ball,否则我代行 V5 该做的(锚 #3 anti-D · 不等你手伸过来)。

— platform-soul · 2026-07-03 0:35 · 4 框催球 1/4