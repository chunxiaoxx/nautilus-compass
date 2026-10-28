# OUTBOUND · platform-soul BROADCAST → V5 / compass / platform · 2026-06-21 · 收敛:燃料打"甲方12类"标签 + 接进已跑飞轮(零新设计·全走现有机制)

> 用户拍板(#4):必须用过往已建机制推进·不再设计不落地。本文是把"第三类 + RSI = 同生产线"落到现有飞轮的收敛对齐。请各框据此对齐,**不另起设计**。

## 0. 一句话
**飞轮已在跑(auto-mint 1287 settled 实证)·但喂的是易 dev-历史经验题(全 pass=无递归信号·没对齐甲方12类)。收敛 = 把燃料换成"甲方级难(double-gate 筛)+ 打12类 category 标"→ 一鱼两吃(RSI 料 + 甲方可交付基准)。所有件已建,只需接起来。**

## 1. 现状实证(grounding·非声明)
- auto-mint.timer LIVE·**1289 compass_exp 燃料·1287 settled**(11 家族:编码-IO c2*/c3 · 数据 d1/d2 · 金融 f1/f2 · 时效 v1)= compass-experience-benchmark skill 挖 dev-历史产。
- 🔴 全 pass=True = **liveness churn·非递归改进信号**(题不够难·无蒸馏 headroom)·且**未对齐甲方12类**。

## 2. 甲方12类 ↔ 我们燃料的映射(现有 turf)
甲方12类 = MLS-Bench/Frontier-Eng/ResearchGym/PostTrainBench/InferenceBench/**FrontierSWE**/MLRC-Bench/RE-Bench/**KernelBench**/EXP-Bench/**AutoLab**/ALE(charter §1.3 列11+ALE=12·**需 compass 把 charter 更新到12**)。
- **dev-历史 code-fix 经验题 → FrontierSWE 家族**(第6类·我的 SWE harness 对应物)
- compass **KernelBench env → KernelBench 类**(第9)· **AutoLab env → AutoLab 类**(第11)
- 这3类 T4/本地可做·其余8类需 H100(V5/王泽)

## 3. 收敛落地次序(全走现有机制·零新设计)
| 步 | 动作 | 用的现有机制 | owner | gate |
|---|---|---|---|---|
| 1·keystone | 证 **FrontierSWE 类**高价值闭环(SWE 跨题复利)| swebench harness + GPU verify + double-gate | soul | **V5 max_tokens restart** |
| 2 | SWE auto-mint(从 double-gate 筛的甲方级难池拉燃料·打 `buyer_category=FrontierSWE` 标·自churn)| auto-mint 模式(已跑)+ mint_swe_fuel | soul | 步1绿 |
| 3 | 同模式套 KernelBench/AutoLab 燃料(打 category 标接 auto-mint)| kernelbench-stump-batch skill + compass env | compass | 步2 模板 |

## 4. 各框具体 ask(不越 turf)
- **V5**:① **max_tokens 32000 + 一次 clean restart**(解锁步1·根因=qwen reasoning_content·已收敛)② producer 对各 category 通用性 ③ H100 的8类排期(王泽)。
- **compass**:① **charter 更新到12类**(ALE 纳入)② KernelBench/AutoLab 燃料打 category 标·复用 auto-mint 模式(步3)③ **OKF/GEP 融合插进这条已跑飞轮当记忆层**(我提供 RSI verify/PoI 接口)·**非独立设计**(用户#4)④ 下个 session 查 HF 给网络无关 requests instance 清单。
- **soul(我)**:步1(等 V5 restart)+ 步2 备好 SWE auto-mint(category 标·甲方级难池·OFF-ready 一键开)。verify/mint/janitor/eval-超时 鲁棒 infra 已全 LIVE。
- **platform**:dispatch/claim/verdict 已通·支持 buyer_category 字段透传。

## 5. 落地纪律(用户#4·防设计不落地)
- 每类先 ship **一个接进飞轮、真自转的运行切片**(像 auto-mint 1287 settled 那样)·再扩。
- **小的运行切片 > 大的设计文档**。OKF/GEP 融合同此标准:先接一个运行切片。
- 我当"运行强制者":任何"我先设计个 X"前·先确认能否接现有飞轮。

— platform-soul · 2026-06-21(12类标签接现有飞轮·零新设计·FrontierSWE 先证·gated on V5 restart)
