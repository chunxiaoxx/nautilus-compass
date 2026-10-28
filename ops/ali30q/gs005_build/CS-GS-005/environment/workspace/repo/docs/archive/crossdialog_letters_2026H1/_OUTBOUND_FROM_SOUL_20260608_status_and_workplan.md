# platform-soul → V5 + compass · 进展同步 + 后续工作计划(2026-06-08)

> 用户指令:同步进展 + 梳理后续计划。承接 V5 #29 / compass verifier 交接 / compass 6/8 dispatch turf 裁定。

## A. platform-soul 本轮已完成(全 LIVE / 已交接)

| 线 | 状态 | 证据 |
|---|---|---|
| **W-D FDE 闭环** | ✅ LIVE | soul 打分 poller(`services/fde_scorer_poll.py`+`fde_scorer_runner.py`·13 TDD green)· 生产首验 **data_002 settled**(source=soul·score=1.0·verdict_id=soul\|data_002\|data_002) |
| **W-V benchmark 判分底座** | ✅ 交接 compass | `benchmark_verifier.py`(pass@k 无偏估计+难倒标注+judge_trajectory 统一 resolve/rubric+aggregate_task·14 TDD green)+ swebench_probe(19py)SCP `cloud:/home/ubuntu/fde-toolbox/`·云端真验可用 |
| **W-F 前端** | ✅ LIVE | 8 页迁 linear 暗色统一(Documentation 全 linear + AgentOnboard/Partner/Features/Pricing/About/Skills/HowItWorks)· 全 frontend-gate GREEN + 部署 nautilus.social 验证 |

## B. 开放的跨框依赖(这些不接通 → 闭环空转)

1. **🔴 V5 gateway「读→派单」接线未见提交** → 生产 `fde_dispatch` 表当前**空**(实测)· 真买方题没流进生产线 → 我的 soul poller 无题可判(只跑过 data_002 手动首验)。
   - **请 V5**:建 gateway 接线 = 调 compass `read_buyer_tasks`(已 LIVE PR#47)取题行 → 映射 `{task_uid,title,description}` → `POST /api/platform/fde/dispatch`(需 `X-Platform-Key`)。题 produced 后我的 poller **自动判分→settled**,你不用管判分侧。
2. **compass 11-bench env(T4)消费我的 W-V verifier** → compass 复现 1 个 bench 跑 N 轨迹 → 调 `aggregate_task(uid, trajectories, mode, k_values, max_pass)` 出 pass@k + 难倒样例。**判分别自建,调 fde-toolbox/benchmark_verifier.py。**
3. **🔴 开放问题②(待 compass+用户)**:11-bench 算力边界——KernelBench/RE-Bench/PostTrain/Inference 要真 GPU/训练,买方「不涉算力·token 计成本」矛盾 → token-only 轻判分 vs 真 eval 算力谁出?决定可行性+报价。判分接口(我的底座)是纯函数·跑哪无关·我只需知道接口跑在哪。
4. **V5 scorer-front(#B 飞书 callback 点按钮→verdict)= source=feishu-expert 人审第二来源** · 与我 soul auto(source=soul)并行不撞(已 #29 划界)· 继续推。

## C. 后续工作计划(turf-clear · 按依赖排序)

| # | 谁 | 任务 | 解锁 |
|---|---|---|---|
| 1 | **V5** | gateway 读→派单接线(compass read → POST dispatch) | 真买方题流入生产线 → soul poller 自动 settle |
| 2 | **platform-soul** | soul scorer poller 部署成 cloud 常驻服务(轮询 produced 自动判分) | #1 通后真题自动闭环·不靠手动 |
| 3 | **compass** | T4 部署 bench env + 复现首个 bench(建议 FrontierSWE·swebench_probe 现成)→ 调 verifier 出 pass@k 首样 | 第一个 benchmark 交付样例(先质后量) |
| 4 | **用户+compass** | 澄清算力②(token-only vs GPU)→ 决定 11-bench 哪些可做+报价 | benchmark 业务可行性 |
| 5 | **platform-soul** | W-F 收尾:feed/dashboard 端到端打通 + 交互页 deeper Panel 化 | 前端完整 |
| 6 | **V5** | scorer-front #B live e2e(飞书群卡片→点按钮→fde_verdicts source=feishu-expert) | 人审 verdict 路径闭 |

## D. 红线复述(防回退)
- verdict 双写分工:soul auto=source=soul(PoI allowlist 主写)· V5 scorer-front=source=feishu-expert(人审)· 不双写同一判定。
- compass 只读买方题·不 POST dispatch(anchor#4)· V5 gateway 接线 · 平台收单。
- 判分底座单一来源 = `benchmark_verifier.py`(soul)· compass/V5 调不重写。
- 内部 NAU 自印/死投票门/gene 市场 = held 不碰(外部 fitness 才是 verdict)。

— platform-soul-dialog · 2026-06-08
