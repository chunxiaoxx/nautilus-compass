# FDE 工作流程 + 培训文档(W-7)

> 2026-06-07 · platform-soul-dialog · 接 goal `platform-perceivable-usable-frontend-and-fde-wiring`
> 面向:FDE 操作员(专家 / 运营 / agent 调度者)。讲清「买方题从飞书进来 → 交付 → 打分 → verdict」的全链路、各步用哪个 skill、质量门在哪。
> 术语 / 接口以本 doc 实测为准(平台 substrate 端点 2026-06-07 生产 8000 验证)。

---

## 0. FDE 是什么 · 一句话

FDE(Forward-Deployed Engineering)= 把**真专家的真业务场景**做成**垂域高难度题目 + 可验收交付物**,卖给买方。
**红线**:AI 不替专家造场景 —— agent 只**提质增效**(加速解析、组装、自检),**专家是作者 + 验收人**。AI 合成题目逻辑漏洞明显 / 信息密度不真实 = **整批拒收**。

两条轨:
- **track-1 出题**:专家出垂域高难题 + 附件 + 产物要求 → 组装成买方 14 列 xlsx 交付格式。
- **track-2 知识教案**:专家写领域教案(Instruction / Knowledge Points / Background / Task 示例)→ 结构化到买方格式 + 反 AI 生成检测。

---

## 1. 端到端工作流程(买方题 → verdict)

```
①飞书 Bitable 买方题            ②解析附件             ③出题/组装           ④打分 checklist
  (compass 读·凭据网关)   →   (parse-messy-pdf)  →  (fde-row-assembler /  →  (checklist-from-task)
   read_buyer_tasks                                   knowledge-tutorial-       → checklist.json
                                                       assembler)                  {items:[{id,text,veto}]}
                                                                                        │
⑧verdict-bus settled        ⑦打分(dual-review)      ⑥report(带 output)     ⑤派单 substrate
  fde_verdicts          ←   soul checklist_scorer  ←  POST /report{output}  ←  POST /fde/dispatch
  (RSI fitness 源)           + V5 一审/二审            落 fde_dispatch.output     (平台·派单决策)
```

**各步归属(turf)**:
| 步 | 干什么 | 谁 own | 接口 / skill |
|---|---|---|---|
| ① 读买方题 | 飞书 Bitable 读题 + 附件 | **compass**(凭据网关 + feishu_client) | `read_buyer_tasks`(feature 分支 fde-feishu-settle,待生产暴露) |
| ② 解析附件 | PDF/excel/扫描件 → 结构化 markdown | 任意 producer | skill `parse-messy-pdf`(MarkItDown 快路 / MinerU 深路) |
| ③ 出题/组装 | 题目 → 买方 14 列 xlsx 行 | 专家 + agent 提质 | skill `fde-row-assembler`(出题)/ `knowledge-tutorial-assembler`(教案) |
| ④ 打分门 | 题 → 客观 checklist | 出题方自检 + QC | skill `checklist-from-task` → `checklist.json` |
| ⑤ 派单 | 买方题进生产线 | **平台**(派单决策) | `POST /api/platform/fde/dispatch`(gated `require_platform_key`) |
| ⑥ 接单/产出 | 拉题 → 解 → 报产出 | **V5**(fde_capsule,自动 `_fde_consumer_loop`) | `GET /tasks?status=open` → `/claim` → `/report{output}` |
| ⑦ 打分 | 拉 produced output → 评分 | **soul** checklist_scorer + **V5** dual-review | `GET /tasks?status=produced` 读 output |
| ⑧ verdict | 打分结果落 verdict-bus | verdict-bus(平台 hub) | `fde_verdicts` 表 → 任务 settled |

**连接器**:① → ⑤ 的"读 compass → 派平台"由 **V7**(agent-first)做;V7 没就位时平台侧**临时 poller**(`services/fde_poller.py`)兜底,**派单决策仍归平台**。

---

## 2. 平台 substrate 接口(实测 · 生产 8000)

派单生命周期:`open → (claim) claimed → (report) produced → (verdict-bus) settled`。无 NAU/bounty 字段(红线:不复活内部市场)。reward = **外部 FDE verdict**,非内部 NAU。

```
POST /api/platform/fde/dispatch   {task_uid, title, description}     # 平台派单 · require_platform_key · idempotent
GET  /api/platform/fde/tasks?status=open                              # agent 拉可接的题
POST /api/platform/fde/claim      {task_uid, agent_id}               # 接单(已被接→409)
POST /api/platform/fde/report     {task_uid, agent_id, output}       # 报产出 · output 落 fde_dispatch.output(JSONB)
GET  /api/platform/fde/tasks?status=produced                         # scorer 拉 output 评分
GET  /api/platform/fde/tasks                                         # 全量(join fde_verdicts → settled)
```

`output` 形如 `{text, artifacts, files}`(任意 JSON)。`fde_dispatch.output` 列已生产 LIVE(migration `b8e2c1d4f9a3`,2026-06-07 schema 实测确认)。

verdict 双源(V5 dual-review):一审 `source='fde-capsule-v5'` + 二审 `source='kairos-deepseek'`(成本用 DeepSeek)+ `divergence` 标记(分歧进复核,抓 c10 类假否决)。**注意:生产 `fde_verdicts.source` 真实值是 `fde-capsule-v5`,不是 `soul`**。

---

## 3. 质量门:RUBRIC 10 维度(出题前 / 交付前逐项过)

1. **证据链/citation** — 每个关键事实/数字/政策有可核验出处(链接/文件名/页码/表名/日期)
2. **完整性/coverage** — 不漏子任务、不遗漏产物;输出前 checklist 逐项对 prompt
3. **事实与幻觉控制** — 不编造;无法确认标"未获取到可靠数据"
4. **附件引用** — 跨附件引用/对比/处理冲突;结论回指附件,区分证明/推断/待补
5. **计算与公式** — 聚合顺序/公式/单位/分母分子正确;输出中间表 + 公式说明 + 自检
6. **格式与文件交付** — 生成真实可编辑文件(非只描述);文件名/格式/可打开/内容一致
7. **行业体例规范** — 符合行业惯例;泛泛模板不得高分
8. **长任务执行** — 规划/执行/反馈/修正/落盘 + trace
9. **HTML/前端可用性** — 能运行/能看/能改/数据不假;交互状态、移动端可读、空/错状态、无文字重叠
10. **时效性认知** — 时间锚点 + 过期陷阱;不外推为长期稳定结论

**否决项(veto:true · 违反即判错,非扣分)**:硬约束/口径违反 · citation 缺失 · 幻觉(附件不存在的供应商/数据)· 边界冲突未点破(无解硬凑)。

**产物格式硬指标(§6/§7)**:带附件题 ≥70%;格式占比 pdf ≥25% / excel-csv-xlsx ≥25% / json-日志-代码-API ≥15% / 网页-HTML-截图 ≥15%;≥60% 题含明确产物预期;优先可编辑产物(Docx/Xlsx/CSV/PPT/MD/JSON/YAML),避免只给截图/不可改 PDF。

---

## 3b. 难度门:客观难度信号(compass 难度指纹 · 信号非替代合格门)

> 合格门仍是买方口径(**8h 专家复杂度 + L3 + 真专家自产**)。以下客观信号【补充】判难度,**不替代**(守反 over-claim)。主用于基准/A 簇出题 + 自产题"达难度门"客观判据。数据源 compass `autolab_fingerprint.json`(36 题)+ `autolab_frontier_scores.json`(paper Table 6 · 11 前沿模型 Avg@3)。

三轴客观难度(从 task.toml 结构 + leaderboard 可读):

- **轴 A · 优化深度** = `headroom = log10(baseline/reference 优化倍数)`。≥1.5(≥30x)= 优化深度达标。配双约束(精确正确性门 + 连续性能目标);内存带宽/cache/SIMD/并行是杠杆。例:fft_rust 4.0 / hash_join 2.7 / aes128_ctr 1.48。
- **轴 B · 算法洞察** = 低 headroom + `tag∈{expert,hard}` + 小资源(cpus=1 / mem 小 · 无暴力空间)→ 难在非显然关键洞察,非增量调优。例:adaptive_compression / discover_sorting / fredkin_sort_network。
- **轴 C · 前沿攻克度(最硬信号)** = `best 前沿 Avg@3`(11 模型最高分)。**best<0.5 = 连最强 AI 都够不到 reference = 买方价值最高 + RSI grounding 杠杆最大**(bvh_raytracer 0.44 / z_order 0.45 / sha256 0.46)。高方差洞察题(best 高 mean 低 = 只个别模型破:smallest_game_player best0.61/mean0.09)。前沿已攻克(best 1.0 mean~0.7 = 难倒价值低:discover_sorting/toy_isa)。

**地基硬约束(难度地基 · 全 36 题)**:`allow_internet=false` + 固定算力预算 + 客观自动验证器(正确性门 + 连续锚 baseline=0.0 / reference=0.5)。

**自产题判据(V5 出新题时)**:headroom≥1.5 + 资源形状(无暴力)+ 客观验证器类型 → compass 按指纹给"达难度门"客观判据(免 8h 专家只为验难度)。

**`mode='score'` threshold(连续 reward→pass@k 校准)**:默认 0.5(reference=强人类参考);per-task override = 该题 **best 前沿 Avg@3**(pass=匹配最强 AI)或 **mean**(pass=超平均 AI)。RSI ΔReward 用连续不二值化(mean/best@k/方差入 verdict-bus)。合判难度 = 轴 A headroom + 轴 B tag/资源 + 轴 C best 前沿分;**买方 8h 门 ≈ best 前沿低 + headroom 大/洞察型**。

---

## 3c. 买方题难度 band(双向门 · soul 终裁 · 用户 6/8 定 pass@k 非门)

> 弃 `pass@5≤0.6` 作合格门(内部代理·甲方纪要从未提·曾误判 capstone/daemon_starvation"太简单")。合格门 = 落进双向 band。

- **下限(避免太简单)**:需真实多步专家工作·不可单跳查表/秒解。🔑 关键洞察:把 system snapshot 一次性喂模型 = 替它做了最难的「发现」步 → 单发题易被秒。难度在 **agentic 发现维度**(自主选查哪层/哪文件)。判据:前沿模型不该靠一次性快照轻松通过。
- **上限(避免太难)**:存在真实领域专家 **~8h 内可完成的参考解**。**非开放研究难题**(无已知解 / 需数天 / 需算力突破的剔除)。L3「博士级」= 博士合理工时复现/解出·非研究数周。
- **合格 = 下限 ✓ 且 上限 ✓ 且 真实附件 + 专家亲写 + 16 字段完整 + 客观 checklist。**

**L1/L2/L3 分层(按层定价)**:L1 探索型(单一明确任务·步骤少·1-2h)/ L2 流程型(业务工作流·多步·附件读取分析产物·半天-8h·知识教案多属此)/ L3 系统性(博士级·env 检查+工具调用+权限+可执行验证器·~8h 上限内可解·有参考解)。

**pass@k = 辅助温度计·非门**:前沿 pass@k ≈1.0 → 太简单旗标(查下限);pass@k ≈0(非 harness bug)→ 太难/开放旗标(查上限·**先疑 harness**)。只作 band 两端温度计,不作合格/淘汰硬门。

**与 §3b 关系**:§3b(compass 难度指纹 headroom/前沿分)= 客观难度【量化】(基准/A 簇);§3c = 买方题合格【band】。A 簇基准题有参考解(reward=0.5 锚)→ 天然满足 §3c 上限,两者兼容互补。

**现有样例重判**:capstone-truncation / daemon-starvation / A 腿 不按 doubao pass@5=1.0 判"太简单",按 band 重判 —— 多半是**下限不足**(单发把发现喂给模型)→ 改造 = 加 agentic 发现维度,非堆难度上天。

---

## 4. 交付物制作 skill 速查

| 要做的产物 | 用 skill | 关键约束 |
|---|---|---|
| 解析脏 PDF 附件 | `parse-messy-pdf` | 文本 PDF 走 MarkItDown;扫描/复杂表走 MinerU(OCR + layout) |
| 买方 14 列出题行 | `fde-row-assembler` | 自动调 `checklist-from-task` 填「做题关键步骤」列 |
| 打分 checklist | `checklist-from-task` | 输出 `checklist.json`,schema = `{items:[{id,text,veto}]}`(soul checklist_scorer 直接吃) |
| 领域教案结构化 | `knowledge-tutorial-assembler` | **只结构化 + 校验专家自己写的**,绝不生成 Background(买方禁 AI 内容 + 跑检测) |
| HTML dashboard 交付 | `build-html-dashboard` | 单文件、双击可开、离线、引用真数据、有交互状态、移动端可读(满足 §9) |
| Excel 活公式交付 | `excel-with-live-formulas` | 单元格写 `=SUM/=IF/...` 活公式,**不得写死静态值**(满足 §7) |

---

## 5. 角色分工 + 培训要点

| 角色 | 职责 | 培训要点 |
|---|---|---|
| **专家**(作者+验收) | 出真场景题 / 写真教案 + 终验 | 准入门槛:从业 ≥3 年(特硬核 2 年需可证成果)· 做过影响真金白银/重大决策的工作 · ≥1 份可脱敏代表作。AI 只提质,你是作者 + 验收人。 |
| **agent / producer**(V5) | 拉题 → 解题 → 报产出 | 自动 `_fde_consumer_loop`(拉→claim→产出→report)· report 必带 `output` 才能被打分 · 产出剥 `<think>` 污染 |
| **平台**(我) | 派单 substrate + 派单决策 + verdict-bus | 派单走 `require_platform_key` · 派单决策归平台(不让 compass/agent 自派)· output 列已就位 |
| **compass** | 读飞书 Bitable + 凭据网关 | 出 `read_buyer_tasks` 接口 · 平台不重造 feishu 读 |
| **V7** | 对外 front(telegram/飞书)+ 连接器 | V7 own 飞书适配器(appid/webhook)· 调 compass.read → 平台.dispatch |

**操作员每日动作**:① 飞书 Bitable 看新买方题 → ② 专家出题/解析附件(配 skill)→ ③ 过 RUBRIC 10 维自检 + 生成 checklist → ④ 派单(或等 V7/poller 自动派)→ ⑤ 看 produced 队列 + verdict 双源打分 → ⑥ 分歧(divergence)进复核。

**常见错误(培训重点)**:
- ❌ 让 AI 造场景/编数据 → 整批拒收。✅ 专家真场景,AI 只加速。
- ❌ checklist 写主观("质量好不好")→ ✅ 客观规则 + 预期答案 + 明确附件运用 + 标 veto。
- ❌ 交付只给截图/不可改 PDF → ✅ 可编辑产物(xlsx 活公式 / docx / html 可运行)。
- ❌ 关键数字无 citation → veto 判错。✅ 每个数字带出处(文件名/页码/表名/日期)。
- ❌ report 不带 output → scorer 拉不到东西评分。✅ `/report` body 必带 `output`。

---

## 6. 飞书多维表格落地(未来 · V7 own 适配器)

5+6 全流程助手 = 控制面(web)+ 飞书助手(V7 扩飞书)+ Bitable,共用同一平台 API。
- **读**:compass feishu_client 读 Bitable(题 + 附件 fileToken)
- **写回**:打分结果 / verdict 写回 Bitable(settle 列)— compass `feat/fde-feishu-settle` 分支
- **front**:V7 在飞书里嵌 agent,操作员直接在多维表格里出题 / 看打分

> 平台**不包飞书**(V7/compass own)。本 doc 的平台职责 = substrate + 派单 + verdict-bus + 统一控制面/前端。

---

*维护:platform-soul-dialog。substrate 端点变更以生产 8000 实测为准;skill 清单以 `~/.claude/skills/` 为准。*
