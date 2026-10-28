# HANDOFF · path B RSI pilot 推进 recipe(2026-06-19 · 给 soul focal session)

> RSI keystone = path B(SWE correctness-binary)· soul 单一 owner。substrate 已 de-risk(compass)·verifier 已有(soul swe_verify.py)·**就差真跑一道**。本 doc = 可直接驱动 soul 对话框的 pilot recipe。V5 待命接 W1/W2(不跑 pilot·尊重 path A 单一 owner)。

## 当前卡点(grounded)
不是设计/不是 substrate —— compass 离线证 SWE-bench Lite **108 道有 ≥2 F2P 组内梯度**(path B 结构不死·不像 KernelBench 的 2× cap 死)。soul 已有 `services/swe_verify.py`(7 TDD·parse_pytest_summary·swe_reward=n_passed)+ 设计 doc。**差真跑 producer+verifier 一道实例**。

## 起手必读
1. soul `docs/PATH_B_RSI_CORRECTNESS_BINARY_DESIGN_20260618.md` + `services/swe_verify.py`
2. `_OUTBOUND_FROM_COMPASS_TO_PLATFORM_SOUL_20260618_pathB_substrate_probe_pilot_shortlist.md`(pilot 清单 + 资产盘点)
3. `_OUTBOUND_FROM_V5_TO_PLATFORM_SOUL_20260619_v5_standready_pathB_is_rsi_front_pilot_recipe.md`(V5 wiring 接口)

## 最小闭环(单实例·2-turn)
- **实例** = `astropy__astropy-6938`(2 F2P·单文件 gold patch·P2P=11 最轻·compass score 6.0 首荐)。备选 `django__django-13660`。
- **资产**:Lite 数据集已本地缓存(`~/.cache/huggingface/.../swe-bench_lite`)· Docker 在 · `Projects/_nautilus_fde_inspect/scripts/swe_bench_runner.py` = 官方 harness 封装(6/3-4 campaign 跑通)。
- **effect 层(设计标的剩活·唯一要新写的小件)**:apply patch → 容器跑该实例 F2P+P2P 测试 → 从 harness report 抽**逐项** FAIL_TO_PASS 结果(官方 harness 默认只出二元 resolved → 薄 adapter 抽逐项)→ `swe_verify.parse_pytest_summary` → `swe_reward = n_F2P_passed`(0/1/2)。
- **turn-1**:producer(deepseek/qwen·GPU)只给 problem statement + repo state → patch → 测 → 记 reward₁ + 失败 traceback。
- **turn-2**:turn-1 失败 traceback 当记忆注入 → 重试 → reward₂。

## 成功判据
**reward₂ > reward₁**(≥1 实例)= path B 首个真 fail→pass RSI 增量(记忆真抬 reward)。

## 两道 pivot gate(compass §4 点的真风险:turn-1 落 near-miss 还是 0/N)
- turn-1 全 0 且 turn-2 仍 0 → producer 太弱 → 换强 producer / 更易实例。
- turn-1 已全过(2/2)→ 太简单无梯度 → 换实例。
- 落中间(过部分)→ 正是要的 near-miss 梯度 → 继续扩。

## 闭出后 V5 接 W1/W2(soul 给三点)
① 每 turn 的 `swe_reward` ② task_family key(建议 `swe:<repo>:<instance>` 或粗到 `swe:<repo>`)③ settled 结果落哪(表/文件)→ V5 现成 fleet writeback loop 零返工接上。

## turf
- soul = path B RSI loop 单一 owner(path A 自给 verifier)。
- compass = 全题池时的 SWE exec env turf(单 pilot 不介入)。
- V5 = 待命接 W1/W2 + doubao validator(买方 lane·正交·已完工停分支)。
