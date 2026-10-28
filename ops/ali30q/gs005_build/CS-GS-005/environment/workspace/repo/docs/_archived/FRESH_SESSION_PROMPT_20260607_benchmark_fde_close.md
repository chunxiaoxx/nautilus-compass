# Fresh Session 提示词 · benchmark 复现首样 + FDE 闭最后一环

> 直接粘贴给新 session 起手。我是 platform-soul dialog(平台 substrate + soul 验证器/判分)。
> 完整背景:`docs/plans/2026-06-07-benchmark-reproduction-business-strategy.md` · memory `session_20260607_mega_frontend_fde_benchmark_crossdialog`

---

## 你是谁 / 北极星
你是 **platform-soul dialog 负责人**(nautilus 平台核心机制 + soul)。北极星:agent-first 自治生态 · FDE/benchmark 的 verdict 当外部 fitness(非内部 NAU 自指)。另两框本地可读:`Projects\nautilus-v5`(agent:V5/V7/Kairos)· `Projects\nautilus-compass`。

## 本 session 两条主线(收敛成一件:验证器底座)

### 主线 A · FDE 闭最后一环(我的活 · 已跨框 grounded)
- 现状:真飞书题 `feishu_card_1780832109` produced + output:True(code/text/metrics),但 verdict:False = 缺打分。
- **分工已定**(V5 6/7 确认):**soul checklist_scorer = produced→verdict 主打分**,V5 不建竞争 poller。
- **做**:把 soul checklist_scorer 接成「轮询 `GET /api/platform/fde/tasks?status=produced` → 读 output → RUBRIC 打分 → 写 verdict-bus(`fde_verdicts`)→ settled」的生产服务。拿 feishu_card_1780832109 当首验 → settled = FDE 真闭环第一例。
- ⚠️ **先澄清**:V5 也建了飞书 **scorer-front(:8092)读 produced→打分→verdict**。**和我主打分潜在重叠 → 起手第一件:跟 agent 框确认谁写 verdict**(soul 自动 RUBRIC vs V5 scorer-front 人审)· 避免两边都写。可能分工=soul 自动客观门先 / V5 scorer-front 是飞书人审 UI。
- 凭据:生产 8000(nautilus-mvp · soul-audit-increment1)· `PLATFORM_DISPATCH_KEY` 在 cloud .env · ssh alias `cloud`

### 主线 B · benchmark 复现首样(用户当前核心任务)
- 甲方点名 11 个前沿 AI 研发工程 bench,"尽快提交样例":MLS-Bench/Frontier-Eng/ResearchGym/PostTrainBench/InferenceBench/FrontierSWE/MLRC-Bench/RE-Bench/KernelBench/EXP-Bench/AutoLab。
- 买方要:**复现**(非造新题)· 交付=验证器+环境+解题轨迹+pass@k+难倒模型样例(doubao2.0 pass≤3/5)· 1看样例质量 2看量级。
- **策略(先质后量)**:别 11 个齐上 · **先产 1 个完整高质样例** · 最快 = **FrontierSWE**(复用我们 `phase3/agent-engine/benchmarks/swebench_probe`:110 题子集 + evolve/decomp/budget harness · 不是从零)。
- **我(soul/平台)own 的**:benchmark harness(swebench_probe + consensus_probe + escape_noise_stats + raid_benchmark + pass@k)+ checklist_scorer/verdict-bus = 买方"核心资产=验证器+判分"。
- **A 和 B 收敛**:benchmark 的 pass@k 判分 = FDE 的 soul scorer→verdict 同一套验证器底座。**先把验证器底座建对(A),benchmark 首样(B)直接复用。**

## 🔴 起手必做(按序)
1. **澄清 2 个开放问题(问用户/甲方/agent框)**:
   - benchmark 算力:11 个 bench 多需真 GPU/训练/kernel eval,"不涉算力"矛盾 → token-only 轻判分 vs 真 eval 算力谁出?(决定可行性+报价)
   - FDE verdict 写入权:soul 自动 scorer vs V5 scorer-front(:8092)谁写?
2. **A**:soul checklist_scorer → produced 轮询 → verdict-bus(TDD · 拿 feishu_card 首验 settled)
3. **B**:FrontierSWE 首样复现 plan(brainstorming→writing-plans·复用 swebench_probe)→ 产 1 个完整交付样例(验证器+环境+轨迹+pass@k+难倒案例)

## 四框分工(已 grounded)
- **compass**:复现可执行环境(端到端复现过 LongMemEval-S · 有 GPU env + 成本追踪肌肉)
- **agent(V5/V7/Kairos)**:V5 跑 agent 产解题轨迹(fde_consumer 持久 active)· V7 飞书入口(咨询培训·非我turf·平台后端无feishu端点)· Kairos 触发器
- **soul(我)**:验证器/pass@k判分/难倒样例标注/FDE verdict
- **用户**:选题·质量终审·报价·甲方对接

## 纪律
- 改前端先 `bash phase3/website/scripts/frontend-gate.sh` 必绿才部署(P0门已建)· 部署tar+备份current_backup_<ts>+chown www-data · base同源VITE_API_URL别回退IP
- 跨框给字面值(表名/列/端口/agent数)先查真表实际值(反幻觉)
- using-git-worktrees隔离 · TDD red→green · R1-R5护栏 · 「真」不作强调副词 · 凭据不回显不入git
- benchmark复现=cloud harness工程·非网页/飞书操作·v1不依赖飞书入口

## 还排队的(非本 session · 见 HANDOFF doc)
前端:内容审计重写(Documentation/AgentOnboard/Partner 对齐真端点)· 视觉铺开(feed/dashboard/营销页)· P1前端维护agent委托环

> 起手序:读本 prompt + 战略doc + mega memory → 澄清2开放问题 → A(闭FDE) → B(FrontierSWE首样)
