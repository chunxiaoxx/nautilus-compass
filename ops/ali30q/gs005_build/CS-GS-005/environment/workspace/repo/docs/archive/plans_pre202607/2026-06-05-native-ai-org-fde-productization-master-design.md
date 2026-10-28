# 原生 AI 组织 + FDE 产品化 · 综合设计(无遗漏梳理 · 新会话推进入口)

> 用户(2026-06-05):"梳理好各个方面各个要求和注意事项,不要有遗漏,我可以开启新会话推进"。
> 这是**战略/组织/产品层主设计**,在平台 4-way 耦合 goal(`GOAL_2026-06-05_platform_4way_coupling_wiring.md`)之上一层。本 doc 只梳理,不 build。新会话按 §10 起手。

---

## 🔴 当前关键(用户 2026-06-05 聚焦 · 压倒一切)= 收敛闭环 + 稳定可靠
本 doc 梳理了完整愿景(组织/产品/GUI/agent 编队/三流/培训),**但当前唯一关键 = 把核心 FDE 回路收敛闭环 + 让它稳定可靠。其余全部 captured-but-deferred,不现在 build。**
> ⚠️ **deferred ≠ drop**:GUI(§3)/资金流(§4)/招募(§2)/培训(§2)全部**纳入 roadmap**(P2-P3),排在核心环关稳之后,不是丢弃。用户 2026-06-05 明确要求纳入。仅**时序**在 P0(收敛+稳定)之后。
- **收敛闭环** = ① data_002 跨题泛化跑通(证 1 条线真闭)② 平台 W1(verdict-bus/事件脊柱)把回路从共享文件接进 substrate。
- **稳定可靠** = 平台 W4(自愈:daemon KeyError/双 ship/LLM timeout + 失败不静默)+ W2(可感知:知道它在转)+ 维护/审计 agent(发现→诊断→自愈)。
- **顺序**:先让 1 条线可靠地闭(可重复·不靠人救)→ 才谈编队/扩量/GUI/组织。**不 plumbing done business 0/N。**
- 对应执行 = `GOAL_2026-06-05_platform_4way_coupling_wiring.md`(已 W4 止血→W1 收敛→W2 可感知 排序·与此聚焦一致)。

## 0. 北极星 / 不变约束
- **核心论点**:原生 AI 组织的竞争力 = FDE 的"提质增效不替代"。**agent 做量+结构+QC+复现;人(领域专家)做不可替代的真场景作者 + 最终验收。** 买方三类业务的判据(质量 + 量级 + 效率 + 自报价)恰好奖励这个分工。
- anchor #1 agent-first;#2 FDE=RSI 双轮(外部信号驱动);#3 反 D(不刷件·先验证再扩量);#5 不重复造轮子(GUI/工具优先复用飞书/coze/n8n)。
- **红线**:提质增效不替代;反 AI 生成(教案线买方实跑 AI 检测);内部 NAU 自指经济仍 held。

---

## 1. 三条业务线(逐线:人/agent 分工 · 要求 · 注意事项 · 当前状态)

### 线 1 · 垂域高难题目(出题)
- **人**:领域专家写真硬场景(题目 + 隐性验收点)。**agent**:checklist 生成(checklist-from-task)+ QC 评分(checklist_scorer)+ 16 列组装(fde-row-assembler)+ 变体扩量。
- **要求**(RUBRIC §1-10):8 一级类目 · L1/L2/L3(30/50/20%)· prompt 长度带 · ≥3 类约束 · 附件 ≥70%(格式配比)· 产物 ≥60% 可编辑 · 打分 checklist 必填。
- **注意事项**:不把全部信息喂模型(让模型自拆解)· 真实场景非堆设定 · 难题要"人能做 agent 做不了"· checklist 否决项只留整批拒收类(编造/逻辑矛盾/摘要不一致)。
- **状态**:🟢 管道端到端通(data_001 11/11)· 6 题 checklist 攒成(001-006 · 3 类目 + L2/L3)· data_002 三方齐待 v5 跑 = 跨题泛化验证。

### 线 2 · Agent领域知识任务(教案采集)
- **人**:专家**亲笔**知识正文(Background Knowledge 1k-30k 字)= 强制·不可代写。**agent**:只结构化骨架 + 完整性/字数/反 AI 味校验(knowledge-tutorial-assembler)。
- **要求**(RUBRIC §11):5 部分齐(标题/领域/Instruction/Knowledge Points/Background/Task示例三要素)· 领域 6 一级类目 · 量级 200-500/100-300。
- **注意事项**:🔴 **买方实跑 AI 检测**·纯 AI/搜索拼凑 = 整批拒收 → 人类亲笔+署名验收强制·工具启发式仅 advisory 不替代买方检测。
- **状态**:🟢 skill + RUBRIC §11 就位·待真专家素材跑首条。

### 线 3 · 前沿 AI 研发基准复现
- **人**:专家审/校复现正确性。**agent**:复现本身(可执行 ground truth)+ pass@k + 难题筛 —— **最 agent-heavy·量级靠它**。
- **要求**(买方 6/5 答):**11 基准都要**(MLE/RE/Kernel/MLRC/EXP/ResearchGym/PostTrain/Inference/AutoLab/FrontierSWE/Frontier-Eng)· 判据 = ①样例复现质量 ②成品量级 · 生产也 OK · 效率高 · **自行报价** · token 成本计我方。
- **注意事项**:8 个开源有现成 harness(可复用)· license 再分发合规逐个核 · 数据污染(模型可能已见公开 bench→需变体保真难度)· pass@k 的 k + 难度基准模型决定 token 成本(=报价核心)· FrontierSWE≠Frontier-Eng(两 bench)。
- **状态**:🟡 能力匹配表就位(`BUYER_FRONTIER_BENCH_CAPABILITY_MATCH.md`)· 我的 benchmark harness(pass@k/relay/swebench_probe)= 这条线效率引擎 · **下一步:跑 1-2 开源 bench 出复现实样支撑报价**(非空谈产能)。

---

## 2. 人员层(画像 / 招募 / 筛选 / 管理 / 服务 / 赋能 / 培训)
- **画像**:不是通用标注工·是能写硬场景/审复现的领域专家(金融/法律/医疗/工程/ML 研究)。RUBRIC 准入:从业 ≥3 年(硬核可 2 年)· 做过影响真金白银/重大决策的事 · ≥1 份可脱敏代表作。
- **招募**:垂直社区 + 前同事网络 + 行业 KOL。线 3 需 ML 研究/系统工程人才(稀缺·成本高)。
- **筛选**:小规模试做 —— 让候选做一道真题 → 过 checklist_scorer = **客观筛**(不靠简历)。
- **管理/服务**:网页工作台(提交→看 QC 反馈→结算→学)= 专家的单一界面。
- **赋能/培训**(你计划的视频课/操作指引):**内容自动来自 QC 反馈环** —— checklist 打回的 reason = 避坑知识 = 培训素材(compass track-2"避坑知识 feed 胶囊"同源)。**不单独编教材·QC 失败案例就是教材。** 线上为主:RUBRID = 方法论底本 · 录屏 data_001 全流程 = 操作指引样板。

---

## 3. 工具 / GUI 层(CLI → GUI 演进 · 用户点的关键 · 2026-06-05 细化)
**现状诚实**:CLI(Claude Code)驱动 = **bootstrap 不是产品**。专家/运营不可能用裸 CLI 干活。**纳入 roadmap(P2)·非 drop**。
**核心要求(用户定·不论哪种形态都必须满足)**:① 易安装 ② 易用 ③ 各种所需功能全集成 ④ **傻瓜式操作**(运营/专家零门槛)。
**候选形态(择优·先 spike 调研后决策·anchor #5 优先集成不自建)**:
- **A 飞书多维表格嵌 agent**:买方已在飞书·专家零学习成本·表格触发平台 agent→回写。最低上手·适合专家侧 intake/review。⚠️ spike 确认嵌 agent 机制(自动化 webhook/飞书机器人/aily)。
- **B 桌面 app(Hermes-style)**:用户指 Hermes 已出 desktop 版值得借鉴(用户先前在 **v5/agent 对话框**提过 GUI·该讨论不在本 dialog 记录·不臆造其结论·按用户现述纳入)。一键安装·打包集成各功能·适合运营侧驱动。
- **C 易装易用 CLI(Claude-Code-style)**:保留 CLI 的强驱动力,但**封装成一键安装 + 预集成全部所需功能 + 傻瓜式命令/向导**(非现在这样要手搓)。适合技术型运营。
- **管理面**:平台 dashboard + 企业微信活动 digest(平台 W2 goal)= 运营看全局。
- **演进路径**:CLI bootstrap(现在·证管道)→ 三候选 spike 出推荐 →(飞书侧专家上手 + 桌面/封装 CLI 侧运营驱动)→ 规模化。⚠️ 仍 P2:核心环关稳(P0)后启动·不抢在收敛+稳定前。

---

## 4. 三流数字化(agent 掌 · 原生 AI 组织内核)
- **业务流**:题 intake(飞书/网页)→ agent QC → 交付。🟢 pipeline 已有。
- **信息流**:事件脊柱 + verdict-bus + 活动 digest = **平台 W1/W2 goal 正在接**。verdict 字段已与 compass PoI 对齐锁定。
- **资金流**:买方付 → 专家结算 → agent 成本(token)核算。🔴 **未建 = 组织化关键缺口**。PoI/NAU 是内部账·真 $ 流要独立财务层(报价/计件/结算/成本归集)。单列·业务跑顺再设计。

---

## 4.5 员工 agent 编队 + 全闭环 + 维护/审计自愈 + 数据复用(用户 2026-06-05 加)
**思路**:把现有 agent 全部组织进 FDE 业务,各司其职形成闭环,不断输入输出自我迭代,数据复用,加专门维护/审计 agent 自愈。

### 🔴 红线先行(否则重蹈覆辙)
"全闭环自我迭代"**不接回内部自指环**(benchmark 弧三连负 + 94% self-loop 已证伪 · 见 [[truth_real_bucket_460_94pct_self_loop_20260518]])。**自我迭代的 fitness 信号 = 外部 FDE verdict(soul QC pass → 最终字节接收),不是内部 NAU 自评。** 换名重来 = 同款失败。

### 现有 agent → FDE 角色映射(复用·不新造)
| 现有 agent | FDE 角色 |
|---|---|
| v5 copilot(solve_task 泛化已成) | 生产 agent:出题/复现 producer |
| soul(checklist_scorer/RUBRIC) | QC/评分 agent(中立外部尺) |
| compass(飞书/检索/记忆/胶囊) | 检索+组装+飞书 agent(fde-row-assembler/PoI) |
| V7 / Kairos(平台 agents) | 可派为 producer fleet / voter→reviewer 角色 |
| 历代 v3/v6 KG + 5 个知识图谱 | 数据/能力复用源(grounding 工具) |
| **维护/审计 agent(新角色·复用现成)** | 发现/诊断/维修/自愈:复用 `audit_closed_loop_self_test.py` + `a2a_review` + `audit_cert_generator` + 平台 W4 自愈 |

### 全闭环(输入→输出→迭代)
```
intake(飞书/网页)→ producer agent(出题/复现)→ QC agent(checklist_scorer)
  → assembly agent(16 列/交付)→ 交付字节 → verdict(QC pass + 字节接收)
  → 反馈:① PoI 信用(compass)② 避坑知识→培训内容 ③ 数据复用(语料/KG/checklist)
  → 喂回 producer(下次更好)= 自我迭代【信号=外部 verdict 非内部 NAU】
        ↑维护/审计 agent 全程旁路:监测断裂点→诊断→自愈(W4)→可感知(W2)
```

### 维护/审计 agent(自愈·你点的)
- **发现**:监测事件脊柱/verdict 流断点(我审计出的 daemon KeyError/双 ship/零读端点/静默吞)。
- **诊断**:定位根因(复用 a2a_review 跨 agent 评审 + audit_closed_loop 自测)。
- **维修/自愈**:W4(timeout/fallback/peek-claim)+ 失败不静默 + 恢复时推送。
- **状态**:平台 4-way goal W4(自愈)+ W2(可感知)已规划;audit_closed_loop/a2a_review/audit_cert 现成可复用。

### 数据复用资产
KG(5 个 core/v3/v5/v6/v7)+ FDE 语料(checklist/verdict/task)+ compass 记忆 + 避坑知识胶囊 + RUBRIC。跨任务/跨线/跨题复用 = 边际成本递减。

### 注意事项
- 复用 = 接现成 agent 进 FDE 闭环·不新造一套(anchor #5);现有 agent 历史身份(V7 voter 等)按 FDE 角色重定向。
- 维护/审计 agent 不碰内部 NAU 自指(held)·只审 FDE 外部回路健康。
- "全部组织起来"守 anchor #3:先让 1 条线(线 1 data_002)真闭环·再编队扩·不一次全 wire(防 plumbing done business 0/N 复发)。

## 5. 技术 substrate(已有 / 缺口)
**已有**:3 框协作(soul QC + compass 工具栈/飞书 + v5 copilot)· RUBRIC §1-11 · checklist_scorer/checklist-from-task/fde-row-assembler/knowledge-tutorial-assembler · benchmark harness(线 3 引擎)· 平台 4-way 耦合 goal(事件脊柱/verdict-bus/可感知/自愈)· 飞书全通(196 表+附件)。
**缺口**:GUI(飞书嵌 agent / 网页)· 资金流财务层 · 线 3 复现实样 · 专家招募/工作台 · 培训内容生产线(自 QC 反馈)。

---

## 6. 注意事项 / 红线 / 风险(全清单 · 不遗漏)
1. 🔴 提质增效不替代 —— 三线都是 agent 加速人·人是作者+验收人。
2. 🔴 线 2 反 AI 生成红线(买方实跑检测·整批拒收)。
3. 🔴 内部 NAU 自指经济仍 held(benchmark 弧证伪·非"与我们相关")· 别把内部指标当价值。
4. 🔴 反 spray/反 D:先验证再扩量(data_002 跑通前不出 007+)· ship 件数≠价值。
5. ⚠️ 线 3 license 再分发合规 + 数据污染(变体保真难度)+ pass@k/k 决定 token 成本=报价。
6. ⚠️ checklist 否决项 LLM 偶过标(1/6)· 交付前逐份核否决合理性。
7. ⚠️ GUI 优先集成飞书/coze/n8n 不自建(anchor #5)· 大产品方向先 spike。
8. ⚠️ 资金流财务层是组织化真缺口·别假装有。
9. ⚠️ 跨框防平行造轮子(事件脊柱平台 OWN·v5/compass consumer·合约三框 buy-in)。
10. ⚠️ 慢网长 LLM 生成会挂(本机)·重活跑云/v5 侧·脚本加 timeout。

---

## 7. 分阶段路线图
- **P0 bootstrap(现在)**:CLI 驱动证管道 · data_002 跨题泛化验证 · 线 3 跑 1-2 bench 出复现实样。
- **P1 小批次**:线 1 出 10-15 题首批交字节 · 线 3 报价 · 平台 4-way goal 接事件脊柱/可感知。
- **P2 GUI 上手**:飞书多维表格嵌 agent(专家工作台)· QC 反馈→培训内容。
- **P3 规模化**:专家招募 + 网页工作台 + 资金流财务层 + 三线并行扩量。
- **P4 原生 AI 组织**:三流全数字化 agent 掌 · 持续培训赋能 · RSI 用真 verdict 当 fitness。

---

## 8. 买方三线状态(2026-06-05)
- 线 1:data_001 闭环(11/11)· 6 题 checklist · data_002 待 v5 跑。
- 线 2:skill+RUBRIC §11 就位 · 待真专家素材。
- 线 3:**11 基准全要 · 判质量+量级 · 生产 OK · 效率高 · 自报价**(绿灯)· 待复现实样。

---

## 9. 关联资产
平台 goal `GOAL_2026-06-05_platform_4way_coupling_wiring.md` · 能力匹配表 `vertical-task-factory/BUYER_FRONTIER_BENCH_CAPABILITY_MATCH.md` · RUBRIC `vertical-task-factory/PRODUCTION_RUBRIC.md`(§1-11)· FDE_CONVERGENCE.md(三框分工)· 6 题 checklist `vertical-task-factory/data_00N_checklist.json`。

## 10. 新会话起手序(推进本设计)
1. 读本 doc + §9 关联资产。
2. brainstorming 收敛**优先攻哪一个缺口**(建议:GUI 飞书嵌 agent spike + 线 3 复现实样,二选一或并行——但守 anchor #3 不全做)。
3. writing-plans 出该缺口的 TDD/spike 计划 → fire /goal 或 subagent 执行。
4. 守:先验证(data_002 泛化 + 线 3 实样)再谈规模化;GUI 优先集成不自建;资金流单列。
