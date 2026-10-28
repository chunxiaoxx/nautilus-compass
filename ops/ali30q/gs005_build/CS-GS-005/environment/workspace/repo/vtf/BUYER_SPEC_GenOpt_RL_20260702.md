# Generative Optimization RL 数据需求文档(买方权威 SPEC · 2026-07-02 接单)

> 来源:`~/Downloads/Generative Optimization RL数据需求文档 _ Generative Optimization RL Data Request.pdf`(7 页,中英双语)
> 本文件 = PDF 全部内容的结构化落地副本(含图片页表格,已人工核对补齐)。页面渲染图在 `vtf/_genopt_pdf_pages/page1-7.png`。
> 定位:FDE 第 3 类业务的新大单 —— **Frontier-Eng「generative optimization」范式,总量 1000 题**。与北极星 ALE-Bench 认知同构(连续分数+迭代优化)。

## 1. 背景与目标

真实工程场景:工程师从一个能跑通的**次优方案**出发,借助真实验证/仿真反馈,在预算内持续迭代逼近更优解。Frontier-Eng 称之为 **generative optimization**,与传统 benchmark 三点区别:

1. **分数有连续性**,非 pass/fail 二元判断或 rubrics 打分。
2. **真实 verifier/simulator**:物理引擎、专业求解器、领域软件等真实工具打分。
3. **从可运行次优解 baseline 出发**,非从零开始 —— 模拟工程师先有 MVP 再系统性优化。

买方希望提升:
- **工程优化/迭代能力**:在已有可运行系统上读取 verifier 反馈、定位瓶颈、持续改进代码提升连续分数;
- **行业/领域知识补充**:覆盖计算系统、量子信息、运筹优化、机器人控制、光学通信、能源、物理与工程设计等多学科。

## 2. 单条数据的定义与构成

### 2.1 关键要素

| 要素 | 说明 |
|---|---|
| Question / Prompt | 问题背景、输入输出规范、优化目标、约束、评分标准、运行方式(对应 Task.md / README.md) |
| Optimizable Parameters & Data Asset | 模型优化所需全部参数、benchmark 实例数据、checkpoint、外部数据、业务数据等 |
| Starting Point / Baseline 次优解 | **能跑但明显非最优**的 baseline 代码,作为模型优化起点 |
| Verifier | **只读、确定性**评分脚本,输出连续分数+可行性判定 |
| README | 评测命令、读写权限清单、产物清单、约束声明等元数据(对应 frontier_eval/*.txt) |

### 2.2 目录规范

```
<domain>/<sub-domain>/<task_id>/
├── Task.md                    # 题面:需告诉 agent 如何验证当前分数
├── README.md                  # 任务说明:背景、环境依赖、目录结构、运行方式
├── baseline/
│   └── init.py                # Starting Point:可运行的次优解(优化起点)
├── verification/
│   ├── evaluate.py            # Verifier:评分主程序(只读,不可被模型修改)
│   ├── reference.py           # 强参考解(可选,对照评分上限)
│   └── 其他 reference 文件     # 命名不做要求
├── data/                      # 可优化参数 / benchmark 实例 / data asset
│   └── ...                    # 大文件需给出来源 URL 与校验值
├── requirements.txt           # 依赖清单(与 Docker 内安装一致)
├── Dockerfile                 # 与方式一对应的镜像构建文件
└── frontier_eval/             # 评测元数据(9 个文件,见 2.3)
```

### 2.3 frontier_eval/ 评测元数据(9 文件)

| 文件 | 作用 | e.g. |
|---|---|---|
| eval_command.txt | 评测命令模板,支持 `{python}/{repo_root}/{benchmark}/{candidate}` 占位 | `{python} {repo_root}/benchmarks/JobShop/frontier_eval/evaluate_unified.py --benchmark-dir {benchmark} --candidate {candidate}` |
| eval_cwd.txt | 评测工作目录 | `.` |
| candidate_destination.txt | 模型产出的候选解落地路径 | `baseline/init.py` |
| initial_program.txt | starting point 文件路径 | `baseline/init.py` |
| agent_files.txt | 暴露给模型、允许其读取/修改的文件清单 | Task.md / README.md / baseline/init.py / verification/evaluate.py … |
| readonly_files.txt | 只读、模型不得篡改的文件(题面、verifier、数据) | Task.md / verification / frontier_eval … |
| artifact_files.txt | 评测产物清单 | metrics.json / artifacts.json / eval.stdout.txt / eval.stderr.txt |
| constraints.txt | 自然语言约束:优化目标、允许/禁止的库、需保持的接口契约 | "minimize makespan; pure Python stdlib only; preserve solve_instance output fields" |
| copy_files.txt | 需复制进沙箱的额外文件 | |

## 3. 评分方式(verifier 三铁律)

1. **归一化连续分数(0–100,越高越好)**。对优化目标与当前状态做相对评估并归一化。Frontier-Eng 参考写法:
   ```python
   def _score(target, makespan):
       if target is None or makespan is None or makespan <= 0:
           return None
       return min(100.0, 100.0 * float(target) / float(makespan))
   # target = optimum(已知)else upper_bound;100 表示达到目标
   ```
2. **可行性门控 valid(0/1)**。先判定解是否满足硬约束(可行调度/物理可行/接口契约);任一实例不可行则 valid=0 且 combined_score=0("不可行的高分"一律 0 分):
   ```python
   valid = 1.0 if instances > 0 and baseline_failures == 0 else 0.0
   "combined_score": score_best_avg_baseline if valid > 0.0 else 0.0,
   ```
3. **确定性与隔离**。verifier 必须只读、确定性可复现:评测结果只依赖候选解 + 固定数据 + 固定随机种子。

## 4. 数据分布(5 大一级类目 × 200 题 = 1000 题)

> 二级类目数据团队**可以自主扩充**。

| 一级类目 | 二级类目(可扩充) | 题目量级 |
|---|---|---|
| Computing and Quantum Information | QuantumComputing、ElectronicDesignAutomation、ComputerSystems、KernelEngineering、Cryptographic | 200 |
| Operations Research and Decision Science | JobShop、PyPortfolioOpt、InventoryOptimization | 200 |
| Robotics and Control | Robotics、EnergyStorage、PowerSystems、SustainableDataCenterControl、AdditiveManufacturing | 200 |
| Optics and Communication Systems | Optics、CommunicationEngineering、WirelessChannelSimulation | 200 |
| Physical Sciences and Engineering Design | Aerodynamics、Astrodynamics、StructuralOptimization、ReactionOptimisation、MolecularMechanics、ParticlePhysics、SingleCellAnalysis、EngDesign | 200 |

## 5. 难度分布(GPT5.5 基线 · N=3)

- 以 **GPT5.5 作为基线参考,N=3**(允许模型最多修改 3 次代码)。
- **gap_closed = (模型修改过程中的最高分 − 起始分数) / 100**。
- **要求提供 GPT5.5 轨迹**作为难度参考依据。

| 难度 | gap_closed | 附加条件 | 题目量级 |
|---|---|---|---|
| Easy | 0.6+ | 最高分小于 95(避免题目过于简单) | 200 |
| Medium | 0.3–0.6 | – | 400 |
| Hard | 0.1–0.3 | – | 400 |
| Rejected | <0.1 | – | (拒收) |

> ⚠️ 我方现状:无 GPT5.5 API。策略 = 题目生产与内部难度预标(用代理模型)先行,GPT5.5 轨迹待 API 渠道确认后统一补跑校准。

## 6. 交付形式

- 所有文件以 **zip 或 tar.gz** 交付;
- 配套一个 **Excel 或 csv**,列:`task_id | Prompt | Domain | Sub-domain | directory`。

## 7. 单题端到端运行逻辑(附件图,page3)

```
Prompt(Task.md) + Starting point(baseline/init.py) + Verifier+config(verification/ + frontier_eval/)
        ↓
Seed program: current ← baseline(init.py)
        ↓
Optimization loop —— 最多 N 轮(algorithm.iterations):
  ① Propose  (LLM edits candidate)
  ② Execute  (run eval_command)
  ③ Verify   (feasible? + score)
  ④ Record   (metrics.json)
  k < N ? → no: keep best, k←k+1 回 ①  /  yes(k=N)↓
        ↓
Final judgment: best valid combined_score
```

## 8. 我方生产要点(非买方原文 · 平台侧备注)

- 生产机 = **H800 PCIe 80GB**(`ssh -p 34467 root@connect.westc.seetacloud.com`,AutoDL 容器,Ubuntu 22.04,176 核/1TB RAM,数据盘 `/root/autodl-tmp` 250G,CUDA 12.8,torch 2.7.0+cu128 / transformers 5.12.1 / trl / peft / accelerate 已装)。
- 生产根目录 = `/root/autodl-tmp/genopt/`(tasks/ + runs/ 骨架已建)。
- 一鱼两吃:每条题目既是买方交付物,又是 RSI 蒸馏的连续分数燃料(ALE 同构)。
