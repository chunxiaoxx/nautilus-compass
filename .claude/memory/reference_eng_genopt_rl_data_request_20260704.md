---
name: reference_eng_genopt_rl_data_request_20260704
description: 7/4 用户发用户原话"必须紧紧围绕着 eng 基准测试需求文档" = 真买方 Frontier-Eng Generative Optimization RL 需求文档已落档 · 真 5 大类目 1000 题量 · 真 N=3 连续分数 + frontier_eval 9 .txt · 真 scoring _score=min(100,100*target/makespan) · 真难度分布 Easy200/Medium400/Hard400/Rejected 0 · 真子样例命名 <domain>/<sub-domain>/<task_id>/ 7 必备文件
metadata:
  node_type: reference
  type: reference
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# 📐 Generative Optimization RL 数据需求文档 · eng 基准测试核心 anchor(2026-07-04)

> 7/4 用户原话"必须紧紧围绕着 eng 基准测试需求文档来开展样例生产任务"。canonical PDF 落在 `C:\Users\chunx\Downloads\Generative Optimization RL数据需求文档 _ Generative Optimization RL Data Request.pdf`。**所有样例生产 = 绕此 PDF 转**。变更走此文件,不另起炉灶。

## 🎯 用户核心约束(verbatim)

> "**必须紧紧围绕着 eng 基准测试需求文档**来开展样例生产任务"

→ 所有样例生产任务 · **schema/file/scoring/difficulty/distribution · 全部按此文档口径**。任何"补样例"先核对本文 §类目/§难度/§评分公式 · **不达 = 退回**。

## 1. 范式 3 大差异(钉死)

| 维度 | 传统 benchmark | **generative optimization(本需求)** |
|---|---|---|
| 分数 | pass/fail 二元 / rubrics 打分 | **连续分数(0-100)** |
| Verifier | 静态测试或 rubric | **真实 verifier/simulator**(物理引擎/专业求解器/领域软件) |
| 起点 | 从零开始 | **从可运行次优 baseline 出发**(MVP-再优化) |

## 2. 单条数据定义与文件命名(钉死)

```
<domain>/<sub-domain>/<task_id>/
├── Task.md           # 题面 + 告知如何验证当前分数
├── README.md         # 背景/环境依赖/目录结构/运行方式
├── baseline/
│   └── init.py       # Starting Point · 可运行次优解(模型优化起点)
├── verification/
│   ├── evaluate.py   # Verifier 主程序(只读,模型不可改)
│   ├── reference.py  # 强参考解(可选 · 对照评分上限)
│   └── 其他 reference 文件
├── data/             # 可优化参数 + benchmark 实例
├── requirements.txt  # 依赖清单(与 Docker 内一致)
├── Dockerfile        # 镜像构建
└── frontier_eval/    # 评测元数据(9 个 .txt)
    ├── eval_command.txt
    ├── eval_cwd.txt
    ├── candidate_destination.txt
    ├── initial_program.txt
    ├── agent_files.txt
    ├── readonly_files.txt
    ├── artifact_files.txt
    ├── constraints.txt
    └── copy_files.txt
```

## 3. 评分方式(钉死)

```python
# 3.1 归一化连续分数(0-100,越高越好)
def _score(target, makespan):
    if target is None or makespan is None or makespan <= 0:
        return None
    return min(100.0, 100.0 * float(target) / float(makespan))
# target = optimum(已知)else upper_bound · 100 表示达到目标

# 3.2 可行性门控 valid(0/1)
valid = 1.0 if instances > 0 and baseline_failures == 0 else 0.0
combined_score = score_best_avg_baseline if valid > 0.0 else 0.0
# 关键:不可行的高分 = 0 分

# 3.3 确定性:verifier 只读 + 确定性可复现
# 评测结果只依赖:candidate + 固定 data + 固定随机种子
```

## 4. N+gap_closed(钉死)

- N = **3**(允许模型最多修改 3 次代码)
- `gap_closed = (模型过程中最高分 - 起始分数) / 100`
- **要求提供 GPT-5.5 trajectory 作为难度参考依据**

## 5. 真 5 大一级类目 + 量级(钉死 · 1000 题总目标)

| 一级类目 | 二级类目(团队可扩) | 量级 |
|---|---|---|
| **Computing and Quantum Information** | QuantumComputing · ElectronicDesignAutomation · ComputerSystems · KernelEngineering · Cryptographic | **200** |
| **Operations Research and Decision Science** | JobShop · PyPortfolioOpt · InventoryOptimization | **200** |
| **Robotics and Control** | Robotics · EnergyStorage · PowerSystems · SustainableDataCenterControl · AdditiveManufacturing | **200** |
| **Optics and Communication Systems** | Optics · CommunicationEngineering · WirelessChannelSimulation | **200** |
| **Physical Sciences and Engineering Design** | Aerodynamics · Astrodynamics · StructuralOptimization · ReactionOptimisation · MolecularMechanics · ParticlePhysics · SingleCellAnalysis · EngDesign | **200** |
| **总计** | | **1000** |

## 6. 难度分布(钉死)

| 难度 | gap_closed | 附加条件 | 量级 |
|---|---|---|---|
| **Easy** | 0.6+ | 最高分 < 95(避免过易) | **200** |
| **Medium** | 0.3-0.6 | - | **400** |
| **Hard** | 0.1-0.3 | - | **400** |
| **Rejected** | < 0.1 | - | 不计 |

## 7. 交付形式(钉死)

- 所有文件 `zip 或 tar.gz`
- 配套 Excel/csv:列 = `task_id, Prompt, Domain, Sub-domain, directory`

## 8. 单题端到端运行逻辑(钉死)

```
Prompt(Task.md) ──┐
Starting point ──┼──→ Seed program(current ← baseline/init.py)
Verifier + config ┘
                          ↓
                ┌── Optimization loop(k=1..N=3)
                ↓
       ① Propose(LLM edits candidate)
                ↓
       ② Execute(run eval_command)
                ↓
       ③ Verify(feasible? + score)
                ↓
       ④ Record(metrics.json)
                ↓
       k<N? yes→loop back · no→Final judgment
                          ↓
                best valid combined_score
```

## 9. 我们真产对照(7/4 已 ship)

| 已 ship | 域 | 合规 | 备注 |
|---|---|---|---|
| JobShop/jobshop_orlib_v1_001 | OR/JobShop | ✅ | gap_closed 0.6843 Easy |
| TSP/tsp_tsplib_v1_001 | ⚠️ OR/未列 | 待校验 | 二级类目无 TSP,可迁到 InventoryOptimization 或 QuantumComputing-Network |
| Attention/attention_flash_v1_001 | Computing/KernelEngineering | ✅ | Hard 0.2293 |
| Cache/cache_lru_v1_001 | Computing/ComputerSystems | ✅ | Hard 0.1087 |
| BinPack/bin_packing_ffd_v1_001 | OR/InventoryOptimization | ✅ | Easy 0.6667 |
| Quantum/qaoa_maxcut_v1_001 | Computing/QuantumComputing | ✅ | 7 instances gap 上限 0.133 Hard |
| Robotics/pathplan_astar_v1_001 | Robotics/Robotics | ✅ | partial commit 04cf6a7ce |

**域覆盖偏差**:Optics + Physical Sciences 仍 0 题 = 真缺口(欠 400+400=800 题量级)
**Easy/Medium/Hard 实际分布**:Easy 2 · Hard 4 · Medium 1 · 不达目标分布
**总完成度**:7 真题 / 1000 题目标 = **0.7%** · 距离真目标 99.3% 缺口

## 10. 与 anchor #1/#3 关系

- anchor #1 平台是 agent first · 本需求文档 9 个 .txt + Task.md = 强化 agent 自治(seed/baseline/verifier 三件,人类专家可设计 = 我方样例工具链)
- anchor #3 反 D 维护陷阱 · 1000 题 = 巨型 D 风险 → 必须切片 + 每 Phase 验证真 grounded
- anchor #5 不重造 · 现有 7 题 schema 100% 合规 = 复用为模板

## 关联

- 真 PDF:`C:\Users\chunx\Downloads\Generative Optimization RL数据需求文档 _ Generative Optimization RL Data Request.pdf`
- 业务宪章:`FDE_BUSINESS_CHARTER.md` §1.3(本需求文档 = 第 3 类 Generative Optimization 类目,与原"12 类基准复现"区别:本需求是 generative optimization 范式,不是 binary pass/fail)
- 真 handoff:`HANDOFF_20260704_FINAL.md`
- 真 session:[[session_20260704_compass_user_says_all_implement]]
- 真 ship:7 题 grounded(SSOT 7/3 已 ship + 7/4 agent_id 真拿)
- 缺口:Optics/Physical Sciences 域 · Easy/Medium/Hard/Rejected 实际 vs 目标分布

---
*真落档时间:2026-07-04 06:30 PDT · 用户原话锚死 · 1000 题总目标 · 5 域各 200 · Easy 200 / Medium 400 / Hard 400*
