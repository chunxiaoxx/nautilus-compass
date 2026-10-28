# 🔴 GenOpt RL 买方需求 · 权威口径(2026-07-06 从 PDF 提取 · 主线唯一真相源)

> 源:`C:\Users\chunx\Downloads\Generative Optimization RL数据需求文档 _ ... Data Request.pdf`(4 页 · 中英双语)
> 任何 GenOpt 主线判断以本文为准 · 防狗熊掰玉米。

## 范式:Generative Optimization(Frontier-Eng)

工程师从**可运行次优解(MVP)**出发,借**真实 verifier/simulator** 反馈,预算内迭代逼近更优解。与传统 benchmark 三区别:
1. **分数连续**(非 pass/fail 二元,非 rubric 打分)
2. **真实 verifier/simulator**(物理引擎/专业求解器/领域软件打分)
3. **从可运行次优解 baseline 出发**(非从零 · 模拟工程师先有 MVP 再系统优化)

## 提升两能力(买方目标)
- **工程优化/迭代能力**:读 verifier 反馈 → 定位瓶颈 → 改代码提升连续分数
- **行业/领域知识补充**:覆盖 **7 领域** = 计算系统 / 量子信息 / 运筹优化 / 机器人控制 / 光学通信 / 能源 / 物理与工程设计

## 单条数据构成(14 文件 · 硬规范)
```
<domain>/<sub-domain>/<task_id>/
├── Task.md              # 题面(需告诉 agent 如何验证当前分数)
├── README.md            # 背景/环境依赖/目录结构/运行方式
├── baseline/init.py     # Starting Point:可运行次优解(优化起点)
├── verification/
│   ├── evaluate.py      # Verifier:评分主程序(只读,模型不可改)
│   └── reference.py     # 强参考解(可选,对照评分上限)
├── data/                # 可优化参数/benchmark 实例(大文件给 URL+校验值)
├── requirements.txt     # 依赖(与 Docker 内一致)
├── Dockerfile
└── frontier_eval/       # 9 评测元数据
    ├── eval_command.txt / eval_cwd.txt / candidate_destination.txt
    ├── initial_program.txt / agent_files.txt / readonly_files.txt
    ├── artifact_files.txt / constraints.txt / copy_files.txt
```

## 交付形式
zip 或 tar.gz + 配套 Excel/csv(含元数据)。

## 评分方式(verifier 三铁律)
1. **归一化连续分数**(0-100,越高越好)· `_score = min(100, 100*target/makespan)` · target=optimum(已知)else upper_bound
2. **可行性门控 valid(0/1)**:任一实例不可行 → valid=0 + combined_score=0("不可行的高分"一律判 0)
3. **确定性 + 隔离**:verifier 只读、确定性可复现(只依赖 候选解 + 固定数据 + 固定随机种子)

## 难度分布(权威 · GPT5.5 N=3)
- GPT5.5 作基线参考 · N=3(最多改 3 次代码)· `gap_closed =(最高分 - 起始分)/100` · 提供 GPT5.5 轨迹作难度依据

| 难度 | gap_closed | 附加条件 | 题量 |
|---|---|---|---|
| **Easy** | 0.6+ | 最高分 < 95(避免过简单) | **200** |
| **Medium** | 0.3-0.6 | - | **400** |
| **Hard** | 0.1-0.3 | - | **400** |
| Rejected | <0.1 | - | - |

**总量 = 200 + 400 + 400 = 1000 题**。难度偏 Medium/Hard(800/1000)= 买方要难题。

## 对本框现状的校准(grounded 7/6)
- 本框 57 题:大多 Easy(JobShop/BinPack)+ Attention Medium + Cache/TSP Hard
- **缺口 = Medium/Hard 是大头(800 题)**,本框现有偏 Easy → 主线要推难度上移
- 7 领域:本框覆盖 OR/KernelEng/ComputerSys/Quantum/Robotics 5 域 · **缺 光学通信 + 能源 + 物理/工程设计**
