# core factory 资产清单 · 喂给 v5 flywheel-design(不重写 v5 plans)· 7/3 17:25 修正版

> 🔴 **本档 = 给 v5 flywheel 6 plans 用的资产清单**。v5 写 design 不重写,本 dialog 只补"跨 dialog 通用资产"那一段。
> 引用:`nautilus-v5/docs/plans/2026-07-02-genopt-flywheel-design.md` / `genopt-flywheel-implementation.md` / `genopt-flywheel-v2-design.md` / `genopt-flywheel-v2-implementation.md` / `2026-07-02-genopt-10-real-tasks-plan.md`
> 🔴 **修正 7/3 17:25**:第 7 题 Robotics:pathplan_astar 已在 core partial ship(`04cf6a7c GenOpt RL 第 7 题 Robotics:pathplan_astar_v1_001 框架完成 (partial)`)· **不重做** · 本档补全第 7 题状态 + 删"v5 注册 producer 等于 0 个"的旧假设(v5 已注册 9000010-9000014 共 5 个)

## 📍 工厂资产(platform-soul 框 7/2 落)

### 数据资产 · 4 域 × 多题模板(7/3 修正 = 5 域含 Robotics partial)
| 域 | 路径 | 真状态 |
|---|---|---|
| **OR(运筹)** | `genopt_factory/tasks/operations_research_and_decision_science/` | JobShop (orlib_v1_001 Easy 0.6843) · TSP (tsplib_v1_001 Hard 0.1048) |
| **KernelEng(系统内核)** | `genopt_factory/tasks/kernel_engineering_and_systems/` | Attention (attention_flash_v1_001 Hard 0.2293) |
| **ComputerSys(计算机系统)** | `genopt_factory/tasks/computer_systems/` | Cache (cache_lru_v1_001 Hard 0.1092) |
| **Quantum(量子信息)** | `genopt_factory/tasks/quantum_information/` | QAOA (qaoa_maxcut_v1_001 Hard 上限 0.133 · 7/3 第 6 题端到端通) |
| **Robotics(机器人)** | (pathplan_astar partial ship · commit `04cf6a7c`) | **第 7 题 框架完成(partial)· 实际 trajectory 待跑 · 不重做** |

> **共 6 题真 grounded + 1 题 partial** + ALE-Bench ahc001 6/30 在 T4 上真跑通(compass 自 turf)· 距离 1000 题远 · v5 flywheel 真扩 = 走 `produce_task.py` 工厂批量

### 工具栈(不重写,v5 自取)
- `genopt_factory/tools/produce_task.py` = 工厂(题目生成)· 新题模板复用
- `genopt_factory/tools/gapclosed_batch_runner.py` = K 题并行 runner
- `genopt_factory/tools/verifier_qc.py` = 三铁律 QC(确定性+只读+超时)
- `genopt_factory/tools/fetch_orlib_jssp.py` / `fetch_tsplib.py` / `fetch_tsplib_synth.py` / `fetch_attention_synth.py` / `fetch_cache_synth.py` = 5 个真实例数据获取器
- `genopt_factory/tools/register_h800_producer.py` = H800 harness 注册拿 agent_id(走 `/api/agent-first/{challenge,register}` · capabilities=["code"])
- `genopt_factory/tools/persist_trajectory_verdict.py` = trajectory → fde_verdicts INSERT(producer_agent_id binding)

### 推理栈(已通)
- **GPU**:H800 PCIe 80GB(`ssh -p 34467 root@connect.westc.seetacloud.com` · 公钥 Windows `~/.ssh/h800_ed25519`)
- **LLM**:GPT-5.5 via qixuw 代理(`base_url=https://v2.qixuw.com/v1` · `model=gpt-5.5` · chat.completions + `extra_body={"reasoning_effort":"low"}` · 150-300s/round)· ⚠️ 本机 b2xwto5km/b0urzez29 三轮 502/close 全断 ⇒ **真工作路径走 H800** · Minimax M3 备援
- **stack**:torch2.7+trl/peft 全 · 数据盘 250G

### 评分口径
- **连续分数** = `min(100, 100 * optimum / makespan)`(来自 Frontier-Eng 官方)
- **可行性门** = `valid = 1.0 if instances > 0 and baseline_failures == 0 else 0.0`
- **gap_closed** = (best_score - seed_score) / 100
- **难度分桶**:Easy (gap≥0.6 + 最高分<95) / Medium (0.3-0.6) / Hard (0.1-0.3) / Rejected (<0.1)
- **N=3** rounds 修改代码上限
- **doubao 难倒辅助**:pass@5 ≤ 0.6 on doubao 2.0(SSOT 已有 doubao=火山 ARK 端点)

### Producer 注册化(SSOT §0-ARCH 红线)
- H800 端 Python 进程 = 真 producer · 必须走 `api/agent_first_register` 拿整数 agent_id · 不能以裸字符串 "harness" 跑数
- 7/2 已写完 `register_h800_producer.py` + `persist_trajectory_verdict.py` · dry-run 通 · **等 backend 通就执行**

## 🎯 v5 flywheel 6 plans 我建议如何复用(不重写)

| v5 plan | 我建议如何用 factory 资产 |
|---|---|
| `genopt-flywheel-design.md` | 补"数据来源"段:本档 4 域 × 6 题真 grounded · 不重写其他段 |
| `genopt-flywheel-implementation.md` | 补"producer 实现"段:走 `produce_task.py + register_h800_producer.py` + persist · 不重写其他段 |
| `genopt-flywheel-v2-design.md` | 同上 v2 增强 · 我建议 v2 路线:走 mode='score' 连续 reward(不 retrofit pass@k)· soul 已 APPROVE |
| `genopt-flywheel-v2-implementation.md` | 补第 7 题选题清单(等用户拍哪域) |
| `2026-07-02-genopt-10-real-tasks-plan.md` | **10 题 = 我(本框)已产 6 题 + v5 飞书 v2 #2-#10 模板上 4 题** = 双 dialog 各产 5 题 = 10 题真 grounded |

## ⚠️ 不撞的边界(防重复造轮子)

| 谁做 | 不做 | 做 |
|---|---|---|
| **v5(本 dialog = platform 代行)** | ❌ 不重写 flywheel design · ❌ 不重写 implementation | ✅ 出题 ship 飞书 buyer 表 · ✅ 跨 agent 协同 SOP |
| **platform-soul(本 dialog)** | ❌ 不重写 v5 已 ship 的 JS-SP · ❌ 不动 v5 flywheel design | ✅ OR 域(JSSP/TSP/VRP/CFLP)raw 数据 · ✅ H800 运维 · ✅ factory 资产 · ✅ verifier QC · ✅ producer 注册 |
| **compass** | ❌ 不动 OR 域(platform turf) | ✅ KernelEng + ComputerSys 域 · ✅ Attention/Cache 模板(原属 platform 7/2 写,7/3 转 compass) |
| **soul-verify** | ❌ 不出题 | ✅ mode='score' 难度分桶 · ✅ verdict-gate n≥12 守门 · ✅ canonical verify |

## 关联
- core SSOT `nautilus-core/LOOP_STATE_SSOT.md` 7/3 14:00 后
- v5 7/3 02:08 真 ship 飞书 record_id=recvojPszE0XoJ
- sync evidence `nautilus-compass/vtf/_inbound_from_core_sync_20260703.md`
- 6 plans `nautilus-v5/docs/plans/2026-07-02-genopt-*.md`