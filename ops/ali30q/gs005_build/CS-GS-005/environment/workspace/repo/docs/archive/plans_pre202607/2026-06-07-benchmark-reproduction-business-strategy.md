# 基准测试复现业务 · 战略 doc(跨框同步 + 买方匹配 + 落地路径)

> 2026-06-07 · platform-soul-dialog · 回应用户"现在核心任务"
> 用户定位:founder = AI/ML 核心专家;交付 = 给买方的 benchmark 样例。
> **关键纪律(anchor #5)**:我们不是从零 —— 已有 SWE-bench-lite 子集 + probe harness + soul RUBRIC 打分 + compass benchmark-reproduce。本 doc 盘清后再规划,不重造。

---

## 0. 买方到底要什么(从对话记录提炼 · 不外推)

| 维度 | 买方原话 | 含义 |
|---|---|---|
| 造题 vs 复现 | **"复现就可以"** | 不要新题 · 复现现成 benchmark |
| 交付物 | "复现出来的**数据/轨迹**,根据不同 Bench" | = 可执行环境 + 验证器 + 模型解题轨迹 |
| 质量标准 | **pass@k 通过测试 · "难倒模型是标准"** | doubao 2.0 跑5次正确≤3次的难题 = 目标样例 |
| 算力 | 不涉及算力 · **Token 消耗计入成本**,从报价体现 | 我方跑模型,token 成本进报价 |
| coding 类现状 | 采买 swe-bench-pro + terminal-bench-2.0 成品 · **"3月提的,需求应该已经结束"** | ⚠️ **coding 需求可能已关 · 别死磕** |
| 仍要的 | **"11 类基准测试这些都要"** · 1看样例复现质量 2看成品量级 | 重点 = 11 类(非仅 coding)· 看质 + 看量 |

**两条买方验收**:① 样例复现质量(难倒模型程度)② 成品量级(能产多少)。

---

## 1. 我们手里真有什么(资产盘点 · 三框)

| 资产 | 在哪 | 对买方价值 |
|---|---|---|
| **SWE-bench-lite 核心子集** | `phase3/agent-engine/benchmarks/swebench_lite_core_subset.json` | 复现样例骨架(单文件/≥2 hunk 筛过) |
| **swebench_probe harness** | `phase3/agent-engine/benchmarks/swebench_probe/` | 可执行环境 + 跑模型 + 判分 |
| **paradigm-B 探针设计 + cloud runbook** | `docs/plans/2026-06-03-paradigm-b-*` | mini-swe-agent + 官方 harness + 子集筛选流程 |
| **benchmark-as-soul-fitness 设计** | `docs/plans/2026-06-03-benchmark-as-soul-fitness-design.md` | pass@k + escape-noise 统计装置 |
| **soul RUBRIC / checklist_scorer** | checklist-from-task skill + soul harness | **自动判分器 = 买方要的"验证器"** |
| **compass SWE-bench + LongMemEval** | compass `BENCHMARKS_REPRODUCE.md` + `paper/SPEC_LONGMEMEVAL_BENCHMARK.md` | compass 在跑 benchmark + 记忆类基准 spec |
| **FDE verdict-bus + pass@k 概念** | 平台 `fde_verdicts` + handoff 多处 | 复现后 pass@k 通过测试的记录基座 |

**结论**:买方要的"验证器 + 可执行环境 + pass@k + 难倒模型样例"= 我们 SWE-bench probe + soul 判分 + compass benchmark 已有的组合。**差的不是能力,是聚焦 + 量产 + 升级到买方指定的 bench。**

---

## 2. 诚实的差距 / 张力(别建错东西 · anchor #6)

1. **lite vs pro**:我们子集是 SWE-bench-**lite**;买方 coding 提的是 swe-bench-**pro** + terminal-bench-**2.0**(更新更难)。harness 可迁移,但要升级到 pro/terminal-bench 的环境。**且 coding 需求"可能已结束"——先确认,别死磕 coding。**
2. **"复现" vs "用我们系统当标的"**:买方明确"复现就可以"。用户的"标的=我们 compass/平台/soul/agents 系统"是**差异化/二期**(从真实 AI-infra 工程挖新题),**不是 v1 买的东西**。v1 = 复现现成 bench;别一上来就做"从我们 dev 记录造新题",会跑偏买方需求。
3. **11 类是什么 · 待确认**:买方"11 类基准测试都要" —— 需确认这 11 类的清单(是 SWE/terminal/memory/math/agentic/... ?)。这决定复现哪些 bench。**第一个待你/买方澄清的关键信息。**
4. **量级 = 成本**:买方"看成品量级" + "token 计成本"。复现是算力/token 密集 —— 量产需要 cloud 跑批 + token 预算。报价模型要算清。

---

## 3. 差异化:用户的"标的=我们系统"洞察(对的,但是二期)

用户说"我是 AI/ML 专家,测试标的=我们 compass/平台/soul/agents"——**这个洞察对,且是我们独有的护城河**:
- 我们的真实开发史(今天就修了 apiClient mixed-content+token-key 的微妙 bug · 有 commit + 验证器 + pass/fail)= 一堆**真实、难、可验证的 AI-系统工程问题**,天然是 SWE-bench-式语料(真 issue + 真修复 + 可执行验证)。
- 但买方现在买的是**复现现成 bench**。所以:**v1 复现交付(吃现成需求)· v2 用我们 dev 史造 frontier 新题(差异化,难倒模型样例的独家来源)**。
- = 和 FDE 买方题模型同构(专家+真场景+agent 提质)· 也和"benchmark = soul fitness"同构(我们自己的难任务既是商品又是 RSI 燃料)。

---

## 4. 落地流水线(复现一个 bench 的最小可交付 · v1)

```
选 1 个买方要的 bench(待确认 11 类清单 → 先挑我们最近的:SWE-bench 或 LongMemEval)
 → ① 复现可执行环境(probe harness + 官方 grader)
 → ② 跑模型 N 次(doubao/MiniMax/...·token 计成本)
 → ③ pass@k 统计 + 标"难倒模型"案例(pass ≤ 3/5)
 → ④ 交付包 = 验证器 + 环境 + 解题轨迹 + pass@k 报告 + 难倒样例
 → ⑤ soul RUBRIC 二次质检样例质量(复用 FDE 打分)
```

**这正好复用我在闭的 FDE 最后一环**(soul scorer→verdict):benchmark 的 pass@k 判分 = FDE 的 verdict-bus 同一套打分/验证基座。**闭 FDE = 把 benchmark 业务的验证器底座建好。两者收敛,不是两件事。**

---

## 5. 跨框 turf(谁干哪段)

| 段 | 谁 | 现状 |
|---|---|---|
| benchmark 选型 + 环境复现 | **compass**(已在跑 SWE-bench/LongMemEval) + 平台 agent-engine(probe harness) | 已有装置 |
| 跑模型产轨迹 | **agent 框**(V5 producer + 多模型) | producer 已活 |
| pass@k 判分 / 验证器 | **soul**(我·RUBRIC + verdict-bus) | 我在闭 FDE 最后一环 = 同底座 |
| 报价 / 量级 / 买方对接 | **用户**(founder=AI/ML 专家) | 你 own |

---

## 6. 下一步(我的建议)

**不在本 marathon session build**(R3 严重超 + 这是跨框大初始化)。建议:
1. **你/买方澄清**:① 11 类基准清单 ② coding(swe-bench-pro/terminal-bench)是否真已关 ③ v1 先复现哪 1 个(建议从 compass 已在跑的 SWE-bench 或 LongMemEval 起,最快出样例)
2. **fresh 专门 session**:brainstorming→writing-plans,基于本 doc 把"复现 1 个 bench 出首个交付样例"拆成可执行步骤(复用 swebench_probe + soul 判分)
3. **我同步在闭的 FDE 最后一环**(soul scorer→verdict)= benchmark 验证器底座,两者一起推

**首个里程碑建议**:挑 1 个 bench,产出**1 个完整交付样例**(验证器+环境+轨迹+pass@k+难倒案例),给买方看"复现质量" —— 比铺 11 类更能验证我们接得住。先质后量。

---

---

## 7. 甲方点名的 11 个 benchmark(2026-06-07 · 紧急)

MLS-Bench · Frontier-Eng · ResearchGym · PostTrainBench · InferenceBench · FrontierSWE · MLRC-Bench · RE-Bench · KernelBench · EXP-Bench · AutoLab

**共性**:全是**前沿 AI 研发工程 agentic benchmark**(评 agent 做真实 ML 研究:训练/kernel/推理优化/实验/post-training/科研复现)。不是普通 coding,是"AI 做 AI 研发"。

**我们的匹配度**:
- 🟢 **FrontierSWE / RE-Bench**(SWE/研发工程风)= 我们 `swebench_probe`(110 题子集 + evolve/decomp/budget)harness 最直接迁移 → **最快出首个样例**
- 🟡 KernelBench / InferenceBench / PostTrainBench = 需真 GPU/训练/推理执行环境
- 🟡 ResearchGym / MLRC-Bench / EXP-Bench / AutoLab / Frontier-Eng = 各自独立 repo + env,逐个搭

### 🔴 必须先向甲方澄清的一件事(决定可行性 + 报价)
甲方说"**不涉及算力,token 计成本**" —— 但 **KernelBench/RE-Bench/PostTrain/Inference 这类要真 GPU/训练/推理执行**,不是纯 LLM token。矛盾点:
- 若"复现"= 跑 LLM agent 产代码 + 用 benchmark 自带 grader 判分(轻执行)→ token-only 成立。
- 若要真训练/真 kernel 跑分 → 需 eval 算力,谁出?**这必须问清,否则报价/可行性算错。**

### 怎么做(buyer 自己的标准:先质后量)
**不要 11 个一起上。** 甲方"1看样例复现质量 2看量级" → **先产 1 个完整高质量样例**(选 FrontierSWE,我们 harness 现成)→ 证明复现质量 → 再扩。
1 个样例交付包 = 可执行环境 + 验证器 + 模型解题轨迹 + pass@k 报告 + 难倒模型案例(pass≤3/5)+ soul RUBRIC 质检。

---

## 8. 四框分工(这 11 个 benchmark)

| 段 | 谁 own | 凭现有 |
|---|---|---|
| 选 benchmark + 复现可执行环境 | **compass**(在跑 SWE-bench/LongMemEval)+ 平台 agent-engine(swebench_probe) | 🟢 已有 |
| 跑 agent 产解题轨迹(多模型·token 计成本) | **agent 框 V5**(producer 已活) | 🟢 |
| pass@k 判分 / 验证器 / 难倒样例标注 | **soul(我)**(RUBRIC + verdict-bus·正在闭的 FDE 同底座) | 🟢 |
| 报价 / 量级 / 甲方对接 / 选题 / 质量终审 | **用户**(founder = AI/ML 专家) | 你 own |
| 飞书对接(若要) | **V5/V7**(飞书 gateway·见 Q3) | ⚠️ 未建 |

---

## 9. Q3:现在能在平台网页操作吗?还是飞书机器人?(诚实)

**都不是"操作入口"问题 —— benchmark 复现是 cloud 工程流水线,不是点网页按钮 / 跟飞书聊。** 真活 = 搭 env + 跑 agent+grader + 收 pass@k,在 cloud 上跑(compass/agent-engine harness)。

- **平台网页**:`/control` 可**监控/派单/看 verdict**,但**跑 benchmark 本身是 harness 任务**,不是网页操作。要做"网页上点一下跑一个 benchmark"= 得新建,非 v1。
- **飞书机器人**:**平台后端无飞书端点**(实测:有 telegram/wechat/commerce-bot webhook,无 feishu)。飞书 gateway 是 V5/V7 turf,**还没建/部署** → 所以你找不到回调配置地址(它不存在)。要用飞书做**任务入口**,需 V5/V7 先建飞书适配器+webhook 端点,再去飞书开放平台配回调 URL → **协调 agent 框**。
- **但 v1 不用等飞书/网页**:出首个样例的路径 = 直接跑 harness(compass/agent-engine 在 cloud),不依赖飞书/网页入口。飞书/网页是后续"任务入口+监控"的事,别卡在这。

---

## 10. 给用户的即时行动(尽快出首样)
1. **向甲方澄清算力**(§7 红线):token-only 还是要真 GPU/训练 eval?决定报价+可行性。
2. **选 FrontierSWE 起手**(我们 swebench_probe 现成·最快)→ fresh session 产 1 个完整样例。
3. **飞书别等**:不是 v1 路径;要的话另起跟 agent 框(V5/V7)建飞书 gateway。
4. **四框就位**:compass 跑环境 · V5 产轨迹 · 我(soul)判分+验证器 · 你选题+终审+报价。

> 关联:`session_20260605_data001`(FDE 买方题首闭)· paradigm-B probe(`docs/plans/2026-06-03-*` · `swebench_probe`/110题子集)· `2026-06-03-benchmark-as-soul-fitness-design.md` · 本 session handoff `HANDOFF_20260607_session_frontend_fde_crossdialog.md`
