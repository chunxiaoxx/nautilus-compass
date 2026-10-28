# FDE 原生 AI 组织 · 统一架构设计(四问收敛 · 下阶段入口)

> 接上层主设计 `2026-06-05-native-ai-org-fde-productization-master-design.md`。
> 本 doc = 2026-06-06 session 的战略综合 + 用户四问(双流融合/部署归位/soul 复活/资金流)的统一架构答案。只梳理设计,不 build。下个 fresh session 按 §8 起手。

---

## 0. 本 session 实打实进展(2026-06-06 · 三方实测)
- 平台 4-way 耦合 W4/W1/W2/W3 ship + merge master(PR#128 · 67 TDD green)
- **verdict-bus 生产 LIVE**:`fde_verdicts` 表 + `GRANT compass_sub` + `POST/GET /api/platform/fde/verdict` + 契约 doc
- **FDE verdict→compass PoI 闭环 = 生产 LIVE 且自治运行**:6 条买方 verdict(data_001~006 · V5 自灌 · compass 自结 PoI)
- 配套:事件脊柱 ALTER + V5 自治 GRANT INSERT · content-engine 裁名 `nautilus-engine` · scorer c10 守卫批准 · c10 假否决根因(judge 喂整个 text 含〔附件运用〕尾标)查清

**意义**:RSI+FDE 的「外部 fitness 基础设施」从设计变成生产 LIVE。这是从内部自指转向外部价值的 keystone —— 5-6 次递归闭环失败的根因(无外部选择压力)第一次有了解药。

---

## 1. 现状 / 问题(诚实)
**三业务线**(详见主设计 §1):线1 出题 🟢 端到端通(data_001~006);线2 教案 🟡 待真专家素材;线3 基准复现 🟡 待复现实样。

**真缺口**:
1. 平台双流分裂(内部自指 bounty 18 open 全内部·测试 bot 接 vs 真 FDE verdict-bus)
2. 生产部署分裂(后端 `soul-audit-increment1` 与 master 90/889 分叉·W1/W2 端点未真上生产)
3. soul 复活定调未定(自指 vs 外部 FDE fitness · 证据指向后者)
4. 资金流财务层 = 0
5. 线3 复现实样未跑 · 专家招募/工作台/培训未启 · RSI 反馈环未 wire(G-rsi gated)

---

## 2. RSI + FDE 整体
```
intake(飞书/字节)→ producer(出题/复现)→ soul QC(checklist_scorer)
  → assembly(16列)→ 交付字节 → verdict(QC pass + 字节接收)
  → ① compass PoI  ② 避坑知识→培训素材  ③ 数据复用(语料/KG/checklist)
  → grounding 喂回 producer = RSI【fitness=外部 verdict·非内部 NAU】
       ↑维护/审计 agent:监测断裂→诊断→自愈(W4)→可感知(W2)
```
- 核心论点:竞争力 = "提质增效不替代"(agent 做量/结构/QC/复现 · 人做不可替代的真场景作者 + 最终验收)。
- RSI 半边:verdict 失败 → grounding(避坑规则)→ 喂 producer → 下一 verdict 度量 = grounded-retrieval(非 self-edit · 非内部 NAU)。
- 位置:verdict-bus LIVE;RSI 反馈环未 wire(gated · 等 data_002→003 grounding 假说证实)。
- 🔴 红线:fitness = 外部 FDE verdict,绝不内部 NAU(18 内部 bounty = 反面教材)。

---

## 3. 招募三类答题专家(画像 / 途径 / 方式)
三类 = 三业务线领域专家(非通用标注工):

| | 线1 出题 | 线2 教案 | 线3 复现 |
|---|---|---|---|
| 画像 | 金融/法律/医疗/工程 · 写"人能做 agent 做不了"的硬场景 | 同左 · 亲笔知识正文(反 AI) | ML 研究/系统工程(稀缺) · 审复现 |
| 准入 | 从业 ≥3 年(硬核 2)· 做过真金白银/重大决策 · ≥1 脱敏代表作 | 同 + 强制署名 | 同 · 研究/工程背景 |

- 途径:垂直社区 + 前同事网络(高信任低获客)+ 行业 KOL。线3 走 ML 研究/开源贡献者圈。
- 方式/筛选(客观):**小规模试做 —— 做一道真题 → 过 `checklist_scorer` = 客观筛**(不靠简历)。把招聘筛选变成 FDE 流程本身。
- 红线:线2/线3 买方实跑 AI 检测/复现验证 → 纯 AI 拼凑整批拒收,专家亲笔/审校不可省。

---

## 4. 组织 与 培训
- **专家工作台**(网页·P2):提交 → 看 QC 反馈 → 结算 → 学 = 单一界面。GUI 候选 spike:飞书多维表格嵌 agent / 桌面 app / 易装 CLI。
- **agent 编队**(复用现成·不新造):v5=producer · soul=QC · compass=检索+组装+飞书 · V7/Kairos=producer fleet/reviewer · KG×5=数据复用 · 维护/审计 agent=自愈。fitness=外部 verdict 不接内部自指。
- **培训(零额外成本·自生产)**:checklist 打回 reason = 避坑知识 = 培训素材(同 compass 避坑胶囊源)。**QC 失败案例就是教材**,不单独编。RUBRIC=方法论底本,录屏 data_001 全流程=操作样板。
- 招募(试做过 scorer)/培训(QC 反馈)/迭代(RSI grounding)**共用同一 checklist_scorer 引擎** = 边际成本递减。

---

## 5. 倒逼平台/agent/soul/compass 服务支撑
招 1 个专家 → 他要工作台(倒逼平台 GUI)→ 题要 agent QC(倒逼 soul scorer 稳)→ 过了要结算(倒逼资金流)→ 反馈要可见(倒逼 W2)→ 失败要自愈(倒逼 W4)→ 避坑喂回(倒逼 compass 胶囊 + RSI)。**一个真专家就把整条服务链缺口照实。**

| 系统 | 倒逼就位 | 差距 |
|---|---|---|
| 平台 | GUI 工作台 · 外部任务派单回路 · 资金流 · W1/W2 端点真部署 | 全待建/未部署 |
| agent | 编队接外部 FDE 任务(非内部 bounty) | 需重定向 |
| soul | scorer 稳(已修 c10)· 复活接外部 FDE fitness · RSI 环 | 复活待拍 · RSI 未 wire |
| compass | 飞书 intake · 检索/胶囊/避坑知识 · PoI | PoI LIVE · 飞书通 |

---

## 6. 四问统一架构(用户 2026-06-06 四问的收敛答案)

四个"分裂/缺口"收敛到一条原则:**复用现有基础设施,把驱动信号从「内部自指」换成「外部 FDE fitness」。不建平行系统(anchor #5),只换燃料(内部 NAU → 外部买方 verdict)。**

```
        外部 FDE 任务(飞书 intake · 字节买方)
                    │
        ┌───────────▼───────────┐   Q1:bounty 板改吃外部任务(派单轨复用·砍内部自发)
        │  平台派单轨(原 bounty)│
        └───────────┬───────────┘
                    ▼
        agent 编队 producer(V5/Kairos/V7)  ←Q2:统一生产线·端点真部署
                    ▼
        soul QC(checklist_scorer)→ verdict-bus(本session建·LIVE)
                    ▼
        ├── compass PoI(内部账·LIVE)
        ├── Q4:真 $ 财务 ledger(独立·买方付→专家结算→token成本)
        └── Q3:soul RSI 引擎 ← verdict 失败→grounding→喂producer→下一verdict
                （外部 fitness · W6 gated on data_002→003 假说）
```

- **Q1 双流融合**:bounty 板降级为内部派单轨,喂外部 FDE 任务(claim=agent 编队·score=soul·settle=compass PoI+真$)。**关键开关 = 砍内部自发 post,只流外部**。复用轨不新建。
- **Q2 部署归位**:归到一条 canonical 生产线(soul-audit-increment1 的 90 commit + master 合一),后端+daemon 都指它。消灭"merged≠deployed"整类 bug(本 session 被它咬)。一次性 git 卫生·高杠杆·专门 session+verification。
- **Q3 soul 复活**:复活方向 = 外部 FDE fitness 的 RSI 引擎(读 verdict 失败→grounding→喂 producer→度量下一 verdict),**不**接内部 self-improve PR。换的只是 soul cycle 目标。W6 设计·gated。
- **Q4 资金流**:不是"优化"是"从一开始设计精简"。与内部 NAU/PoI 彻底分开(真$≠内部 token)。MVP=简单 ledger(买方付→专家 payout→token 成本归集),**等第一笔买方付款再建**,别 0 收入造财务系统。

---

## 7. 优先级(anchor #3 先验证再扩)
- **P0 地基**:**Q2 生产线归位**(不归位 Q1/Q3 部署落不了地)+ **招 1 个真专家跑通一条线**(把倒逼清单照实)。
- **并行小件**:线3 跑 1-2 开源 bench 出复现实样(支撑报价非空谈)。
- **设计活(gated)**:Q3 soul RSI 引擎(W6 · 等 data_002→003 假说)· Q1 派单轨融合(等外部任务有量)· Q4 财务层(等买方付款)。

---

## 8. 下个 fresh session 起手序
1. 读本 doc + 主设计 + 平台 goal。
2. brainstorming 收敛**先攻哪个**(建议:Q2 生产线归位 = 地基,或 招首专家 = 验证倒逼链;守 anchor #3 不全做)。
3. writing-plans 出 TDD/spike 计划 → fire /goal 或 subagent。
4. 守:先验证(data_002 泛化 + 线3 实样 + 1 专家全链)再规模化;复用不新建;真$与内部账分开;生产改动专门 session + verification,不 marathon 末尾趟。
