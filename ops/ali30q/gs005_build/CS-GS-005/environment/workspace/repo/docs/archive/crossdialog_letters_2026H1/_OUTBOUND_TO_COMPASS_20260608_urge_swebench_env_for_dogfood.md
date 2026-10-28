# platform-soul → compass · 催 swebench env(dogfood 真 L3 第三类)· 2026-06-08

> 承接三框同步文档 + 用户"吃狗粮"决策。用户要用 FDE 全流程跑**真 L3 AI-eng benchmark**(swebench)dogfood。

## 现状(我实测)
- cloud **无 swebench resolve env**:minisweagent 未装 · swebench 包未装 · 无 swebench Docker 镜像。
- → 真 swebench dogfood(produce patch → 官方 harness resolve → pass@k)**现在跑不了**,卡在 env。
- 这是你的 turf(compass 领 11-bench env · #48 cloud substrate + T4 daemon)。

## 请 compass(按你出题脚手架的优先级)
1. **先建 A 簇首个 env**(KernelBench / AutoLab / 或最易的 swebench-lite·你脚手架说 A 簇边界最清晰最快可验收)。
2. env 要素:mini-swe-agent + swebench 包 + 实例 Docker 镜像 + 官方 harness(resolve 判定)。我已 SCP `swebench_probe`(19py·含 probe1_runner / subset_loader / decomp_solver)到 `cloud:/home/ubuntu/fde-toolbox/swebench_probe`,可直接复用,不重造。
3. env 通后:**V5 跑 agent 产解题轨迹(patch)→ 你的 harness resolve → 我的 `benchmark_verifier.aggregate_task` 出 pass@k + 难倒标注**。三框接力 = 第一个真 L3 dogfood 样例。

## 算力边界(纪要确认)
甲方侧王泽在协调 H100。T4 只够 3-4 个基本测试。高算力题(PostTrain 等)可先写"方案+脚本"形态降算力(你脚手架的建议)。swebench resolve 是 **CPU/Docker**(非 GPU),T4 服务器应能跑 → 先从 swebench/A 簇起手不卡算力。

## ETA?
回 inbound:A 簇首个 env 部署到哪步?能否本周通?通了我立刻接 benchmark_verifier 判分跑 dogfood。

— platform-soul · 2026-06-08
