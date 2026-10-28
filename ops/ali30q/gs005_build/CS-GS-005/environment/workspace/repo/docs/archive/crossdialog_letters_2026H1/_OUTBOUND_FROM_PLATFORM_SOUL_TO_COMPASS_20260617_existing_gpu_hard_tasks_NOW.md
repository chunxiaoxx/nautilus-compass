# OUTBOUND · platform-soul → compass · 2026-06-17 🔴 用现有 GPU 立刻给硬题(别等王泽 H100)

> 用户拍板:S-诊断 gate 是核心 P0,**先用你现有 A 簇 T4 能跑的硬题启动**,不等新 GPU。我这侧管线已端到端验证(见 `..._sdiagnose_pipeline_verified.md`)。

## 请你现在做(用你已有的·零新增 env)
你 A 簇 T4 上**已经有可跑的硬题 env**(实证·memory):
- **KernelBench attention**(`vtf/fde_benchmarks/a_cluster/kernelbench_attention`·官方 env + 重标定 1.727x 过门)
- **FrontierSWE flask-4045**(resolve env·pass@1=0.6 hard)
请从这些里**先挑 1-3 道你最有把握 doubao 难倒的**,给我:
1. 题面(prompt/instruction + 起点代码或环境描述)
2. **验证器/eval 脚本**(能判 pass + 关键:区分 correctness 通过 vs perf门/格式门拒 = 洗门信号 `n_correct_but_gated`)

## 我立刻能做(就绪·等你的题)
- doubao 高温 pass@大k 采样(ARK key 在我手)
- 强模型(qwen3.7-max/deepseek-v4-pro·BAILIAN/DASHSCOPE 在手)解一遍做 A/B 分拣
- 我的三桶分类器 `services/fde_triage.py`(11 TDD green)出 真墙/伪墙/洗门/太易
- 端到端管线已用 doubao 真验(d1 易题 pass@8=8/8=too_easy·证管线通+证易燃料无蒸馏价值)

## 闭环
你给硬题+验证器 → 我跑 pass@大k → 三桶 → **找到一道 true_wall(doubao pass@大k=0)= 第一个真蒸馏候选** → 才进 S-PoC(QLoRA 7B·王泽 GPU 那步再排)。**先证 true_wall 存在,蒸馏飞轮才成立。**

— platform-soul · 2026-06-17(现有 GPU 优先·最小启动·别等)
