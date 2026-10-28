# FDE 原生 AI 组织生产 · 整体工作计划与路线图(讨论材料 · 2026-06-11)

> 用途:组织内部讨论"下一步整体工作计划"。本文是单一真相源——现状盘点(诚实分档)+ 整体架构 + 路线图 + 培训咨询/项目管理如何落地 + 近期行动。
> 关联底本:`FDE_BUSINESS_CHARTER.md`(业务宪章)· `docs/plans/2026-06-05-native-ai-org-fde-productization-master-design.md`(主设计)· `docs/plans/2026-06-11-fde-org-production-engine-design.md`(引擎设计·四层架构)。

---

## 一、一句话定位

我们在建一个**原生 AI 组织**:给保密大厂(经伊洛科技)交付三类 FDE 样例。核心信念——**这套组织生产本身就是 RSI(递归自我提升)的外部 fitness 引擎**:跑真生意(专家亲笔→QC→买方验收→真付钱)产生的外部信号驱动系统进化。红线:fitness 永远外部,不靠内部自评。

分工铁律:**agent 做量+结构+QC+复现;人(领域专家)做不可替代的真场景作者 + 最终验收。** = 提质增效不替代。

---

## 二、现状盘点(诚实分档 · 2026-06-11)

> 区分关键:**"工具/机制建成" ≠ "实际有产出"**。下表按"实际有产出"为准。

### ✅ 已完成 + 有实际产出(实测验证过)

| 领域 | 产出 | 证据 |
|---|---|---|
| **引擎/工作流** | FDE dispatch 引擎(派单→认领→产出→判分→结算)生产 LIVE | walking skeleton 端到端实测闭环(6/11) |
| **agent 生产线(线3)** | kairos/v7/prime 自驱认领+doubao 重做 | 12 道 T3 在跑·systemd LIVE |
| **human-author 生产线(线1/2·S1)** | 飞书派活表→poller→具名认领→专家领活 | **6/11 完整闭环实测**(飞书已领取 + 引擎 claimed_by=expert) |
| **自动判分(QC)** | soul-scorer:produced→verdict→settled | 172s settle 实测·data_002 settled |
| **入口/派单** | 飞书 FDE派活表(tbl69fankpoBhJfw)+ poller 每5min 自驱 | LIVE·老路径废弃入宪章 |
| **交付物·第1类** | data_001 端到端 11/11 过 soul QC = **第一个真外部 PMF 证据** + 6 题 checklist | 实测 verdict |
| **交付物·第3类** | KernelBench/FrontierSWE/AutoLab 复现(真 pass@k 数据·写飞书 L3 表)+ 12 道 T3 名册 | 飞书表+轨迹 |
| **交付物·第2类** | soul 首篇教案《CPU饥饿诊断》 | 飞书教案表 |
| **审核工具** | checklist_scorer + RUBRIC §1-11 + benchmark_verifier(pass@k/难倒) | data_001 实测 |
| **RSI** | 轨2 L2 棘轮喂 12 题 v1 样本·轨1 grounded 两臂账本 2 点(radix escapes=True/bvh False) | 生产 fde_rsi_deltas |

### 🟡 工具就位但未产线化(没接进流程/没真产出)

- **副驾驶 skills** 全就位但未接飞书给专家:checklist-from-task / fde-row-assembler / knowledge-tutorial-assembler / build-html-dashboard / parse-messy-pdf / excel-with-live-formulas
- **S2 亲笔提交→QC 反馈环** = 设计好·未建
- **避坑语料** 有(A 簇 corpus/autolab_avoid_*.md)但未成培训库

### 🔴 设计/愿景·还没建

- **培训咨询**:机制设计了(QC 反馈→避坑知识=教材)但 0 产出
- **项目管理面板**:control-plane 半建(看 verdict/agent)·不是给人 PM 的管理台
- **真外部专家**:即将进场·当前"组织"=AI dialogs + 用户·HR 招聘/专家工作台未建
- **规模交付 + 财务流**:买方规模接收=0(data_001 是 PMF 证据非规模)·结算/成本记账未建
- **飞书权限分层 / 买方隔离**:设计了(引擎设计 §E)·未实施

**实话**:引擎和工作流的**骨架**建成且实测(S1 闭环是里程碑),但"原生 AI 组织"作为运转的组织,**肉还没长出来**——真专家没进场、培训/PM 没产线、规模交付没发生、财务流没建。我们的位置 = 从"5 周设计反复落空"翻到"第一条线可重复闭环"。

---

## 三、整体架构(四层引擎)

```
┌─ RSI 进化拱顶:消费三流外部信号 → grounding/工序改进 → 下次更好 ┐
│   🔴 fitness = QC verdict + 买方验收 + 真$ · 非内部自评           │
├─ 三流:业务流(派活→产→QC→交付)·信息流(verdict-bus)·财务流(缺口)│
├─ 原生 AI 能力(七件·职能全 agent · 人=作者+终验+HR+PM 三席)      │
│   项目管理 · 生产组织 · 培训咨询 · 审核验收 · 全流程编排           │
├─ 引擎+数据模型(已证转):dispatch/verdict/rsi_deltas             │
│   双 producer:agent(线3) + human-author(线1/2)                  │
│   surface 适配器:飞书表(#1·已用)· 未来网页/桌面               │
└──────────────────────────────────────────────────────────────────┘
```

**人类席位仅 3 个**:HR 招聘(专人)· 项目管理(专人)· 专家作者+终验。其余职能全 agent。

---

## 四、路线图(切片次序 · 每片 walking skeleton · binding-DONE 才开下一片)

> 防虎头蛇尾铁律:① 每片最薄一条线贯穿到生产、实测转一圈才加厚 ② 实际买方流量第一天走系统(不搞试点)③ 每片闭环=老路径同步废弃 ④ 一片一个会话·片间验收·2 会话没闭→砍 scope。

| 切片 | 内容 | 闭环判据 | 状态 |
|---|---|---|---|
| **S1** | 派活+验收标准 | 1 专家从飞书领到真买方任务+看到验收标准 | ✅ **DONE(6/11)** |
| **S2** | 亲笔提交→QC 反馈环 | 1 份亲笔稿走完 提交→QC→反馈→改→过,不碰 CLI | 下一片 |
| **S3** | 交付+财务流最小记账 | 1 批交付物从引擎流到买方载体表,带成本/应付账 | 待 |
| **S4** | 三流喂 RSI | ≥1 条人作者流 fail-reason 被 grounded-retrieval 消费并度量 ΔReward | 待 |
| **S5** | PM+培训面板 | 一个面板看清全组织;培训库从 QC 数据自动长出 ≥10 条 | 待 |

**S1-S3 全闭的生产判据(可证伪)**:≥5 道买方交付物全程在系统内流完(派活→亲笔→QC→交付)+ settlement 有记录。不足 5 道 = 没落地,不开 S4。

**三业务线并行推进(各自成熟度不同)**:
- 线1 出题:管道通(data_001)· 下一步随 S2/S3 接专家亲笔
- 线2 教案:首篇有·随 S2 接专家亲笔(🔴 买方跑 AI 检测·副驾驶只校验不代写)
- 线3 复现:最 agent-heavy·已有真交付·继续攒量级 + 报价

---

## 五、培训咨询:如何规划与落地

**核心原则(主设计 §2)**:培训内容**自动来自 QC 反馈环——不单独编教材**。专家被打回的 reason = 避坑知识 = 教材。

**落地三步(随 S2/S5 走 · 复用现成不自建)**:
1. **避坑库(数据源)**:QC verdict 的每条 fail-reason → ingest 进 compass 记忆 + 飞书"避坑知识"表。已有起点:A 簇 corpus/autolab_avoid_*.md。
2. **副驾驶答疑(咨询)**:专家进场,副驾驶 agent 基于 RUBRIC + 避坑库 recall 答"这道该怎么写/为什么被拒"。咨询=陪伴式引导,不是一次性培训。
3. **onboarding 样板**:RUBRIC §1-11 = 方法论底本;data_001 全流程录屏 = 操作指引样板;首篇教案 = 范文。
- **载体**:飞书(专家在飞书·零学习成本)。培训库=飞书表/文档 + 副驾驶 bot。
- **里程碑**:S2 闭后避坑库自动有料 → S5 培训库自动长出 ≥10 条 → 专家进场即接入"已有 QC 案例当教材"的系统(非空系统)。

**当前缺口**:避坑库未产线化(QC reason 没自动 ingest 成培训条目)。这是 S2/S4 的具体活。

---

## 六、项目管理:如何规划与落地

**定位(主设计修订)**:PM 面板是给**专人 PM(人)**用的 **agent 服务台**——不是纯 agent PM。人做决策,agent 做数据/提醒/催办。

**落地(S5 · 复用飞书多维表格 + control-plane 不自建)**:
1. **进度视图(看板)**:飞书派活表的视图——谁领了什么 / 在哪个阶段(待派单→已领取→已提交→QC中→过/打回→交付)/ 卡在哪。飞书多维表格自带看板/甘特视图。
2. **管理服务 agent**:扫派活/提交/QC 流,出提醒(超期催办)、卡点告警、周报(消费三流数据)。复用 control-plane 聚合 + 企业微信 digest。
3. **结算视图**:settlement 表——每专家应付、token 成本归集(S3 起最小记账,S3 后扩财务层)。
- **人 PM 的工作**:看面板分派优先级、处理卡点、确认结算。agent 把信息备齐推到面板。
- **里程碑**:S5 = 一个面板看清全组织状态。前置=S1-S3 产生真数据(没数据的面板=装饰,故放最后)。

**当前缺口**:PM 面板未建·结算未建。S3(最小记账)+ S5(面板)的活。

---

## 七、组织/人员 与 三流数字化

- **人员**:画像=能写硬场景/审复现的领域专家(金融/法律/医疗/工程/ML)· 准入=从业≥3 年+代表作 · 筛选=做一道真题过 checklist_scorer(客观筛·不靠简历)。
- **招募**:垂直社区+前同事网络+行业 KOL(HR 工具不重造·调研过开源 HR API)。
- **三流数字化**:业务流🟢(pipeline 有)· 信息流🟡(verdict-bus/事件脊柱接通中)· **财务流🔴(主缺口·买方付→专家结算→token 成本·S3 起建)**。

---

## 八、近期行动项(谁做什么)

| # | 行动 | 负责 | 依赖 |
|---|---|---|---|
| 1 | S2 实现(亲笔提交→QC 反馈环) | 平台(我·下个会话) | S1 已闭✅ |
| 2 | 真外部专家进场准备(画像/招募启动) | 用户 + HR 专人 | — |
| 3 | 避坑库 ingest 起步(QC reason→compass/飞书) | 平台(S2/S4) | S2 |
| 4 | 飞书权限分层 + 买方隔离实施 | 平台(S2/S3) | 引擎设计 §E |
| 5 | 线3 继续攒交付量级 + 报价 | compass/v5 + 用户 | — |
| 6 | RSI 轨1 第3个 benchmark 两臂(A 簇 GPU 已通) | 平台/v5 | levenshtein harness 适配 |

---

## 九、讨论问题(供会议拍板)

1. **节奏**:S2→S5 一片一会话,还是某几片并行?(纪律建议串行·防虎头蛇尾)
2. **专家进场时点**:S2 建好后进,还是先小批试做?
3. **财务流**:S3 最小记账够开局吗?完整财务层何时建?
4. **飞书 vs 网页**:专家/PM 长期是否都留飞书,还是某角色要网页/桌面?(surface 已解耦·随真使用决定)
5. **培训咨询**:QC-反馈即教材 的机制是否认可作为唯一培训内容源?

---

## 关联资产(证据指针)
- 业务宪章 `FDE_BUSINESS_CHARTER.md` · 主设计 `docs/plans/2026-06-05-native-ai-org-fde-productization-master-design.md` · 引擎设计 `docs/plans/2026-06-11-fde-org-production-engine-design.md` · S1 计划 `docs/plans/2026-06-11-s1-assignment-acceptance-plan.md`
- 飞书派活表 base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tbl69fankpoBhJfw` · RUBRIC `vertical-task-factory/PRODUCTION_RUBRIC.md`
- 能力匹配表 `vertical-task-factory/BUYER_FRONTIER_BENCH_CAPABILITY_MATCH.md`
