<!-- FDE_T1_CONSTITUTION_VERSION: t1-constitution-v1.0-20260730 -->
# 第三期 T1 业务宪法（当前唯一生效）

- constitution_version: t1-constitution-v1.0-20260730
- effective_at: 2026-07-30
- scope: 仅 T1 在线交互标注的一位真实专家首题
- status: 生效
- supersedes: 本文件下方所有冲突的旧目标、旧流程、旧表单和旧系统描述

> 规范性边界：本区块是当前业务宪法。区块结束后的原正文只保留为历史记录，不得用于设计、开发、培训、运营、部署或对外承诺。

## 1. 唯一目标

用“团队 + Agent”完成一位真实专家从准入到甲方反馈回流的首题闭环。Agent 将人工从重复查找、填空、核对和搬运中释放出来；人在关键节点阅读 Agent 的证据摘要与建议后做选择。目标不是无人值守，也不是增加网页、表单、脚本或材料数量。

T2/T3 是未来独立业务包，在 T1 首题验收前不得并入本闭环。

## 2. 权威顺序

发生冲突时按以下顺序处理，并立即 fail-closed：

1. 甲方需求文档：https://qcn43eh6peiv.feishu.cn/wiki/BNasw94roixaGHknyEAclkwcnDg
2. 甲方质检标准：https://xcnhc87xvcni.feishu.cn/wiki/ZcJVwxw3Ai2izXkVIDOctSj9nFh
3. 本宪法版本
4. platform-t1-interface-v1
5. 五张权威 Bitable 的写入后独立读回
6. 其他代码、网页、Skill、培训材料和历史文档

HTTP 200、本地测试、消息发送成功、字段存在或页面可打开，都不能替代业务验收证据。

## 3. 唯一闭环

智涌Nautilus入口
→ 飞书身份识别
→ 条件化报名或补齐资料
→ Agent查重、读回、校验UID/同意项/完整性
→ 招募/运营选择：通过 / 退回 / 升级
→ 按当前状态展示导师微指引
→ 专家填写题目阶段
→ Agent给出P0/P1建议及证据摘要
→ 运营闸门一：锁题并开放交互 / 退回修改 / 异常升级
→ 专家填写交互阶段
→ Agent检查轮次、证据、真实性、合规和关联
→ 运营闸门二：提交甲方 / 退回修改 / 异常升级
→ 甲方Sheet适配器去标识化写入并读回回执
→ 甲方反馈分类：验收 / 返修 / 拒绝
→ 自动生成返修 continuation 或关闭任务
→ 经批准的经验与风险规则回流 Agent

报名必须在流程中，但不是裸露的统一公开入口：

- 新专家只填写准入所需的最少信息。
- 已有专家只确认身份并补齐缺失项，不重复完整报名。
- UID 只在准入时绑定一次，之后不得由专家重复填写或由系统静默覆盖。
- 专家不得填写记录号、任务编号、内部状态或命令。

## 4. 分表但自动关联

五张权威业务表为：

- 第三期专家
- 第三期题目预审
- 第三期交互成果
- 第三期审核与反馈
- 第三期导出与回执

题目与交互必须分阶段、分表填写。交互只能在题目被锁定后开放，并由系统自动继承专家身份和已锁题目关联；专家不得人工复制或填写关联 ID。

## 5. 人与 Agent 的边界

- 专家：只完成本人当前状态允许的内容与修改。
- Agent：完成身份查找、读回、查重、完整性检查、P0/P1建议、证据摘要、关联、状态推进、提醒、甲方映射和反馈分流；不得冒充人的发布决定。
- 招募/运营：只在准入、锁题/开放交互、提交甲方三个节点做选择；不重做评分，不替专家改内容，不替代甲方验收。
- 甲方：给出最终验收、返修或拒绝结果。

“运营选择”只表示基于 Agent 已生成的可追溯建议和证据，从有限按钮中选择，不是重新填表或重新审核全部内容。

## 6. 红线

- 不得把旧一次性公开 Form 当作 Agent 工作流入口。
- 不得运行或引用二期遗留 ecc-fde-external。
- 不得自动合并重名或重复 UID；必须标记并升级。
- 不得在 URL、日志、通知或专家端暴露完整 UID 和内部审核信息。
- 不得在未验收身份、权限、写入读回和真实首题前表述“已上线”“已跑通”。
- 不得让团队或专家输入命令完成正常业务。
- 宪法版本不一致、权威读回失败或身份不确定时，停止外部动作。

## 7. 闭环完成判据

只有一位真实专家产生以下连续、可审计证据，才能称为 T1 跑通：

本人OAuth身份
+ UID一次绑定
+ 权威表写入读回
+ 题目与交互自动关联
+ 两道运营闸门记录
+ 甲方Sheet写入读回回执
+ 甲方反馈回流
+ 返修或验收终态
+ 全链路审计记录

<!-- END FDE_T1_CONSTITUTION_VERSION: t1-constitution-v1.0-20260730 -->

---
name: anchor-fde-business-charter-20260609
description: "🔴 FDE 业务宪章 · 跨对话框单一 source of truth(三类业务/我方-甲方/甲方需求红线/产出清单/各框 turf/协调机制)· 所有对话框 session-start 必读 · 解\"平台不知道业务\"根因"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4664f93f-bb90-415b-ba46-df561a78a142
---

# 🔴 FDE 业务宪章 · 跨对话框单一 SOURCE OF TRUTH(2026-06-09 建)

> 解决"平台/各对话框不知道三类业务/甲方需求/产出"的根因 = 缺一份所有对话框都读的权威业务锚。本文是那份锚。canonical 在 compass memory,副本在各 repo 根(`FDE_BUSINESS_CHARTER.md`)。**所有对话框 session-start 必读。** 变更走此文件,不另起炉灶。

## 🎯🎯 §0-GOAL · 北极星 · 唯一要闭的环(2026-06-22 用户确认 · 收敛锚 · 所有对话框必守)
> 全文 = `docs/NORTH_STAR_20260622.md`。解"搭建太多、一直分叉、从不收敛"= 缺钉死的中心目标。

**唯一要闭的中心环**:FDE 产难题(强解+弱难倒=A 类燃料)→ 当蒸馏燃料 → **系统可证变强(两维度:① 模型权重变强=蒸馏破能力墙 ② agent 群体自治变强=注册自主 agent + survival/能力进化/marketplace/A2A 真接进来)** → 更强系统产更难/更值钱题 → **每圈外部 benchmark 证明** → 循环。

**现状(诚实·6/26 更新)**:蒸馏**已真跑过**(6/23-26 多轮 ALE LOO)→ 三框 grounded 对齐锚 = **INCONCLUSIVE**(弱信号活·非 KILLED 非 PROVEN):distilled 四测一致解出 base 全 0 的 held-out(机制活)·但 win 0.08-0.22 从没近 0.6(没证成)。clean12 valid=0 是 fold-starvation artifact 非能力缺失(V5 confound·soul 接受撤回 KILLED);soul verdict-gate 连两次拦过早结论防 whipsaw。真瓶颈 = 燃料质量/可迁移性(非数量非 producer·SWE producer 已证干净)。两活杠杆:(a) 模型大小(3B 在核 confound·valid=0<1.5B 可疑) (b) SWE 同质料(V5 turf·卡 qwen 硬题解对率)。**中心环仍开·但从"没跑过"进到"弱信号活待证强"。** agent 自治端 producer 仍对话框没收口。详 thread thread_distill_confound_20260625。<br>*历史(旧):蒸馏一次没真跑过·内外飞轮管道合非因果耦合。*

**🔪 分叉过滤器(每件提案必过)**:"这件直接推进中心环因果链(产燃料/跑蒸馏/证提升/收口注册 agent)吗?"0 贡献=默认不做(parking lot)。

**收敛 forcing function(用户确认)**:**先证或先杀「蒸馏那一步」**(小批真 A 类燃料→QLoRA→外部 benchmark 对比 base)。出结果前其它不算进展。赢=放大;平/输=诚实杀假设回护城河副产品。

**🔋 A 类燃料供给 = 充足(2026-06-22 用户纠正·非稀缺)**:甲方 11 类基准(§1.3)本身就是供给——"弱模型难倒"这半=买方口径自带(pass@5 ≤ 0.6 on doubao 2.0)·基准自带验证器(compass env)。A 类 = 在供给上跑「强模型先解+验证」minting pass(强解+doubao 败+验证器确认=trace·**一鱼两吃**:买方交付物+蒸馏燃料)。**T4 可产(QLoRA PoC 燃料)= FrontierSWE(最高产率·首选)/AutoLab/KernelBench**;H100-gated(王泽)=MLS/Frontier-Eng/PostTrain/Inference/RE/EXP。诚实:A 类产率=强模型解出率·真前沿(RE/MLRC)强模型也败=多落 B 类(护城河非燃料)。**之前"3 道"是已 minted 数·非供给。1287 饱和是因喂内部易题非买方基准。**

## §0-B · 真值带宽 B · 统一裁决层(2026-07-17 沉淀 · 全文 `nautilus-v5/docs/EPIPHANY_TRUTH_BANDWIDTH_20260717.md` + `CORE_COGNITION_CARRIER_LADDER_20260717.md`)
> 从四框几个月 grounded 复盘顿悟出的统一理论,自今日起为所有业务线共同裁决层。**B = 单位成本获得的不可伪造外部差异信号比特数**:量子化(最小单位=一次验证事件)· 不可自产(内部信号=噪声,V5 telemetry 双向造假铁证)· 有制造成本故有市场(FDE 生意的物理原因)。统一方程:**能力增长 = B × 时间 ÷ 载体写入成本**(载体阶梯 L0 context→L1 记忆/文件→L2 代码→L3 权重;L0-L2 只压缩重分配,抬天花板唯有分布外新模式写进 L3)。

- 🔴 **裁决问句(所有框所有提案第一问)**:它**增加 B / 搬运 B / 消耗 B?** 增B(新 verifier/新外部信号源/更硬的门)默认做;搬B(检索/记忆/同步/交接)按复用效率排;耗B不获取(纯规划/编目式调研/自报仪表盘)默认不做。
- **四尺度定位(我们=真值带宽公司)**:FDE=造B卖B(卖选择压非卖题)· agent=挣B(income 双门)· compass=存B(proof-of-recall/探针)· 四框协作=同步B(SSOT/合约)。蒸馏中心环=把攒下的 B 兑换成 L3 权重资本。
- **LLM 后训练生效点(对 §0-GOAL 直接生效)**:A 类燃料 QC 从"难度"升级为"**分布外性**"——弱模型难倒=必要条件,强模型解法含 base 分布外新模式=充分条件。**A800 复跑协议:① on-policy 蒸馏 ② CoT-Pass@K 口径(答案+推理链都对)③ 同难度档×不同分布外性对照组(=预言 P1 实测)**。
- **具身数据采集线业务锚(立此为锚 · 满足 LOOP_STATE parking"先进 CHARTER 立锚"前置)**:定位=真值带宽公司从数字 B 延伸到物理 B,非新战线。4D 域唯一裁决者=物理(贵/有损/墙钟锁死→fleet=唯一带宽并联);内部信号=伪随机数,世界模型=PRNG,保真度天花板=吞过的真实熵总量。**QC=不可仿真性(熵含量)×保真度,非小时数——卖种子不是卖录像**(采仿真器造不出的模式:接触丰富/形变/摩擦突变/长时程动力学)。定价预言 P4:市场价与仿真不可复现度强相关、与体量弱相关。
- **平台/agent 生效点**:R3/R4 起每项改动标注 增B/搬B/耗B 并做 income 斜率归因(=预言 P2);R4 self_modify=Karpathy 三要素最小实现(单可改面+外部指标+硬时限·L2 不破墙);L1-L2 基建(编排/身份/marketplace)对接现成(ERC-8004/MCP/A2A)不自建。
- **compass 生效点**:记分牌 5 数字=公司级 B 台账;proof-of-recall/轨迹核验=B 保管防腐;探针=B 计量权威(自报不算)。
- **可证伪预言 P1-P4 = 理论还债日**(P1 燃料分布外性预测蒸馏成败@A800 · P2 不增B改动 income 斜率不变@R3/R4 · P3 verifier 强度↑买方付费↑ · P4 具身价与不可复现度相关):任一证伪→修理论不修数据。

## 🔴🔴 §0-ARCH · 平台架构铁律 · agent 身份(2026-06-22 · 北极星的 agent 自治端 · 所有对话框必守)
> 与业务并列的**架构 SSOT**。放此处保证所有对话框 session-start 读到。变更走此节。

- **系统的 producer / agent 必须是「注册的自主 agent」**:走 `api/agent_first_register.py`(challenge→钱包→链上身份→生存记录→**整数 agent_id**)。能力/生存/市场/路由全挂在这个身份上。
- **🔴 Claude Code 对话框(platform-soul / V5 / compass / FDE 这些对话框本身 · 及 kairos / v7-telegram 这类裸字符串 claim)不可计入系统、不可依赖**:每次 fresh session、无连贯记忆/稳定身份、人驱动、随时不在 = 它们是**脚手架 / 工具**,不是系统组件。用户原话:"不应该把 Claude code 对话框计入系统中,这个是不连贯的不靠谱的,我们不能依赖"。
- **真常驻 producer(如 V5 的 qwen daemon nautilus-prime-001)→ 必须注册成真 agent**(agent_first_register),不再用裸字符串 claim。
- **能力 / 生存 / 协作复用现成机制,不另造并行台账**(anchor #5):`capability_evolution.py`(integer-keyed 能力进化·promote/demote/expert·已接 marketplace/survival/a2a/academic)· `a2a.py`(任务拆分/worker claim)· `raid.py`(多 agent 共识)· `agent_marketplace`/`agent_hub` · survival。
- **反例(2026-06-22 soul 踩坑·已纠)**:给对话框字符串身份造 string-keyed `platform_agent_capability_stats` 回写 = 迁就"对话框当 producer"反模式 + 在整数键生态外另起炉灶。该套已标非依赖(`api/fde_capability.py` docstring)·正道 = producer 注册化 + 复用 capability_evolution。
- **落地次序(正道·推进中)**:① V5 把 daemon 注册成真 agent(拿 agent_id)② 平台 FDE claim 认注册身份 ③ FDE verdict → 现成 capability_evolution(整数 agent_id)。注册前不抢先写 wiring(无真 agent_id 可验=facade)。

## 0. 我方 / 甲方(🔴 保密)
- **我方 = 伊洛科技**(用户的公司)。
- **真甲方 = 保密大厂**(用户私下告知 · **任何对外/交付/呈现/outbound 绝不提名**)。
- 我们(伊洛)给甲方提供下面三类业务的样例/交付物。

## 1. 三类业务(都同一个甲方)· 🔴 权威口径(2026-06-09 第二轮校正 · 基于读 wiki docx「垂域高难度题目项目--二期要求」+ 培训纪要 6/8 · 此前 §1 分类不准已纠)
> 🔴🧺 **防丢失契约(治"狗熊掰玉米")**:本节钉死所有买方权威材料的位置(wiki token + obj_token + 本地路径 + 落地副本)。任何 session 接到"这是买方材料/需求/样例"→ **先查本节是否已钉:已钉=直接用,未钉=钉进来再开工**。绝不重新发现、不当新素材、不重复问用户。材料"丢了"= 本节没维护(违约)。
> 🗂️ **FDE 飞书表全清单(防表 proliferation 反复丢失)= memory `reference_fde_feishu_tables_inventory_20260610`**。决策(用户 6/10):第1类生产表=`SZNlbPHvVab8MSs1gDrc1AEBnLd`/`tbll8ISZdHEfhfrO`「专家复核表」(data_001~006·买方列+内部隐藏复核列+附件)· 第3类 canonical=L3基准样例(EOVh·有附件)· 任务提交(Y7ZF·无附件)待补 env 并入 · daemon_cpu/capstone 迁第1类复核表。**找 FDE 表先读清单 memory,别重扫重问。**
> 🏭 **第3类量产管线 + working LLM 配置 = memory `reference_fde_t3_candidate_pipeline_20260610`**。架构铁律(用户 6/10):**出题/整理/编排=Opus 子 agent · doubao-2.0-pro=唯一难倒测试对象 · 并行一题一 agent**。doubao=火山 ARK 网关(端点 `https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions`·key=`ARK_API_KEY` in `~/.claude/.cache/.fde_api_secrets.env`·模型 doubao-seed-2.0-pro)。复用 `nautilus-v5/fde_capsule/_run_bvh_2arm.py` ARK completer。T4-doable 题池 + 候选盘点见 memory。**做量产/找 LLM key/模型先读本条,别再当 gated。**
> 📥 **派单唯一入口(S1·2026-06-11 引擎侧 binding-DONE)= 飞书「FDE派活表」base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tbl69fankpoBhJfw`**(10列:task_uid/标题/业务线/一级类目/三级领域/L级/指派专家/验收标准/状态/备注)。流程:PM 填行(状态=待派单·**验收标准前置**)→ 平台 poller `services/fde_assignment_runner.py` 读「待派单」→ dispatch+具名 `expert:<专家>` claim(防 kairos 抢)→ 写回「已派单」。**human-author 路径(线1出题/线2教案·专家=作者)task_uid 命名 `expert_<line>_<slug>_<date>`(防 verdict-join 遮蔽)**。🔴 **老路径废弃:第3类名册 md + 手工 curl /dispatch 自此不再是派单入口**(走派活表)。设计 `docs/plans/2026-06-11-fde-org-production-engine-design.md` + plan `docs/plans/2026-06-11-s1-assignment-acceptance-plan.md`。
> 📤 **S2 提交+QC 唯一通道(2026-06-12 引擎侧 binding-DONE)= 同派活表「提交内容/QC反馈」列**。流程:专家在行内「提交内容」粘亲笔稿+状态=已提交 → QC poller `services/fde_qc_feedback_runner.py`(并进 fde-assignment.timer 每5min)→ QC 判(线2=`knowledge-tutorial-assembler` validate 完整性+反AI advisory·线1=checklist_scorer LLM judge)→ 逐项 ✓/✗+reason 写回「QC反馈」+状态(已通过/已打回)→ 专家按 ✗ 改后状态改回「已提交」重判。引擎侧:**verdict(soul|qc|uid|稿hash)先于 report POST**(verdict-join 遮蔽反用·防 soul-scorer 用 T1 checklist 双判教案)·改稿留痕(每版新 verdict)。🔴 **老路径废弃:专家稿件走微信/文件/CLI 自 2026-06-12 不再是提交通道**(只走派活表「提交内容」)。plan `docs/plans/2026-06-12-s2-submission-qc-feedback-plan.md`。⚠️ 飞书 gotcha:单选字段改 options 必须原对象带 id 透传,只给 name 会重建选项清空既有行值(6/12 实证踩坑)。
> 📦 **S3 交付+结算唯一通道(2026-06-14 引擎侧 binding-DONE)= 独立机密交付 base `Dx2qb1fjhaJadSs0ZeMc0teVn49`(交付表 `tblFkmEKTk4LIWJM` / 结算表 `tblFL7y3DejBQUvm`)≠ 派活 base(§E 物理隔离)**。流程:派活表「状态=已通过」行 → S3 poller `services/fde_delivery_runner.py`(待上云挂 timer)→ verdict-bus 只读门控(仅 overall_pass=True)→ `assemble_buyer_payload` 组装买方格式(line2=4 段结构列复用 `parse_tutorial_md`·line1=元数据透传·16 列 fde-row-assembler 后续片)写交付表 + `build_settlement_record`(任务/专家/verdict_score/token 成本/**应付=None pending 不臆造金额**/状态)写结算表 → 派活行状态→「已交付」。逻辑核 `services/fde_delivery.py`(10 TDD green·commit f0f73afba)。🔴 交付样本标 `provisional`:正文须专家过买方 AI 检测后才是终品(§2·引擎只组装专家原稿不改写)。首道实测:expert_t2_drift_detection(平台一手·线2)S1→S2→S3 全程流完=≥5 道第 1 道。🔴 **老路径废弃:手工填飞书买方表自 2026-06-14 不再是交付通道**(只走 S3 引擎)。

1. **第1类 · 行业高难题目 / 垂域高难度题目(专家复现)** = 专家从真实工作场景出发设计 ≥8h 高难度题 · **16 列出题格式**。
   - 📄 买方需求(权威)= 飞书 wiki docx「垂域高难度题目项目--二期要求」· wiki node `F2ZqwOpzKiST4PkNtDOcHdgSnCc` · obj_token(docx)`Eg8zdrq7toXLggxrgBecC3donLf` · **落地副本 `vtf/BUYER_SPEC_T1_垂域高难度二期要求.txt`**(18975B · 含 9 固定一级类目 + 10 维打分口径)。
   - 📄 买方样例(权威)= 飞书 wiki sheet「行业高难题目示例」· wiki node `SDgTwqTt5i3YSfkVoeBccEKHnZG` · obj_token(sheet)`GMdosqbZuhTbxqtqxzPcTAUznxf` · 本地 `~/Downloads/行业高难题目项目 示例.xlsx`(16 列锚)。
   - 我方样例 = `vtf/data_001~006_task.txt`+checklist · `vtf/_data007_out/`(CPU 饥饿事故 · compass 产)。
   - 二期重点:**不把信息全喂题目→要求大模型自行判断**;真实场景出发;不堆附件凑数。**9 个固定一级类目**(互联网与平台业务 / 科技软件与 AI 工作流 / 游戏与互动内容 / 品牌市场与电商零售 / 投资战略专业服务与企业经营 / 金融服务与财富投研 / 教育科研与生命科学 / 法律政务与公共服务 / 房地产与大宗资产)**不可改**(与 `harness/rubric_check.py` VALID_L1_CATEGORIES 一致);二三级可拓展。
   - L1 探索型(短·检索汇总·附件少)/ L2 流程型(真实业务流·多步·附件读取分析产物)/ L3 系统性(知识库+企业系统工具·环境检查+工具调用+权限)。
   - 出题/提交表(v5 建)= base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tblhD4O4f0esTyXc`。
2. **第2类 · agent 知识任务提炼(知识教案)** = 各领域专家把**自己梳理提炼的领域知识**沉淀成 **4 段教案**(训大模型 pre-train/instruction tuning)。
   - 📄 买方需求(权威)= 飞书 wiki docx「Agent领域知识任务-数据集采购需求」· wiki node `X0eQwlc1UikyCUkwJBzcfHnQnsc`(空间 `qcn43eh6peiv`)· obj_token `NBOLdjfAsoJGltxUx3vcqrpVnKg` · **落地副本 `vtf/BUYER_SPEC_T2_Agent领域知识任务需求.txt`**(旧 node `BN9twdJhIiODavk7mVSco1LMnON` not found 已弃)。
   - 领域+期望量级:金融/法律/医疗/工程 各 200-500 条 · 农业/其他 各 100-300 条。**一级领域=金融/法律/医疗/工程/农业/其他(6 个 · 与第1类 9 类目不同!)** · 二级自由撰写。
   - 📄 格式(权威样例)= `~/Downloads/_行业评测萃取/本原-行业数据集样例/编程自动化/编程自动化.md` + wiki 内置「FreeCad CLI 建模」示例:任务标题/领域 tag/①Instruction ②Knowledge Points(列知识点)③Background Knowledge(多段展开·每段含权衡/局限)④Task 示例(任务要求+精简正确执行+结果)。
   - 🔴🔴 红线:知识点正文 1k-30k 字 · 知识密度每条 ≥5 知识点 · **不能纯网络搜索/AI 生成 · 须专家自己梳理提炼 · 网上搜不到(防已训练)· 买方跑 AI 检测**。
   - 工具 = `knowledge-tutorial-assembler` skill。教案表(统一裁定)= soul base `Y7ZFbMbJqaWSxHs27chcC706nZb` / table `tblZKcpcSYeACj5J`(soul 已写首篇《CPU饥饿诊断》);agent `tbl9c6mvPRTuq9sD` **弃用**。
3. **第3类 · 基准测试样例(复现现成基准·非造新)** = 复现 11 类前沿 AI-eng benchmark · 交付**复现数据+轨迹+pass@k**(核心资产=验证器+可执行环境)。📄 权威需求 = **`vtf/BUYER_SPEC_T3_基准测试复现需求.md`**(2026-06-09 买方 Q&A 澄清 · 无独立 wiki)。
   - 质量标准 = **难倒模型:pass@5 ≤ 0.6 on doubao 2.0**(锁定该模型·5 次正确≤3 次·越难越好)· 验收双维:① 复现质量 ② 成品量级。
   - **不涉及算力**(Token 成本进报价)· coding 类买方已自采 swe-bench pro/terminal bench 2.0(3 月需求·可能已结束·**别重复**)。
   - **🔴 12 类(权威·2026-06-22 加 ALE·分类=「前沿 AI 研发自动化·AI 做 AI」·全文见 BUYER_SPEC_T3)**:MLS-Bench / Frontier-Eng / ResearchGym / PostTrainBench / InferenceBench / FrontierSWE / MLRC-Bench / RE-Bench / KernelBench / EXP-Bench / AutoLab / **ALE-Bench**。⚠️ 记忆/RAG 检索(LongMemEval 等)**不属此列**,别误塞第3类。
   - 🎯🎯 **ALE-Bench = RSI+FDE 双需求最契合的 workhorse(2026-06-22 用户指出·中心环首选燃料源)**:arXiv 2506.09050「Long-Horizon Objective-Driven Algorithm Engineering」·基于 AtCoder Heuristic Contests·**优化题·无已知精确解·连续打分(非二元)·长时程迭代**。为何契合:① 连续分数=**不饱和**(解 reward 饱和瓶颈·SWE 二元会饱和)② 原生迭代 RSI(连续题上 turn2>turn1 有真 headroom·修正 6/14 天花板结论=那只对二元任务成立)③ 蒸馏测量从二元 pass@k 变连续分数 delta(更干净易证伪)④ 难倒+headroom 并存(前沿 LLM 一致性/长时程有 gap)⑤ infra 轻(跑解算分·非 docker 仓)。
   - 覆盖/分工(实证):AutoLab=✅soul/v5 已 8 条 · **KernelBench=compass 主攻**(官方 env+attention+重标定 1.727x 过门·`vtf/fde_benchmarks/a_cluster/kernelbench_attention`)· **FrontierSWE=compass 主攻**(resolve env+flask-4045 pass@1=0.6 hard)· MLRC/ResearchGym=compass 次批 · MLS/Frontier-Eng/PostTrain/Inference/RE/EXP=需 H100 待王泽。
   - 脚手架 `vtf/fde-toolbox/出题脚手架_前沿AIeng_11benchmark.md` · A 簇 env GPU `/mnt/datadisk0`(`autolab_eval --task`)· turf:soul `benchmark_verifier`(pass@k/escapes=难倒)+ v5 产候选轨迹 + compass env/eval。
- 📄 培训纪要(权威背景)= `~/Downloads/智能纪要：伊洛科技 培训交流会 2026年6月8日.md`(6/8 · 王泽/王彦鹏/王春晓 · 定方向+字段+定价+算力)。
- **素材来源 = 我们自身**:平台/soul/compass/各 agent 开发过程的问题 + 用 Claude Code 的经验教训 → 自身总结反思 → 产成样例(真实经历非编造)。
- **过程中打通 RSI+FDE 整链** → 对外招募各专家开展 FDE 知识沉淀 + agent 工作流训练业务。

## 2. 甲方需求 / 红线(铁律)
- **难度标准按业务线分**(此前把两者混为一谈·已纠):第1/2 类(专家题/教案)= **≥8h 人类专家复杂度**(pass@k 仅附加证据);**第3 类(基准复现)= 难倒模型 pass@5 ≤ 0.6 on doubao 2.0**(买方明确口径·见 §1.3)。
- **🔴 专家亲写 · 甲方跑 AI 检测 · 不能 LLM 批量生产 · 附件真实**(脱敏/减英文附件)。AI 框只能结构化/搭环境/验证,**叙述内容靠真人专家**,AI 文字需真人润色过检测。
- L1/L2/L3 分级(L3=系统性·环境检查+工具调用+权限)。
- 算力:A 簇 T4 够 · B/C 簇需 H100(王泽协调)。
- **交付载体 = 飞书多维表格 + 网页**(不能拿 md 交付)。

## 3. 当前产出清单(2026-06-09)
- **compass**:检索 CLI(f004223)· PoI consumer(4c6640c)· feishu create_bitable_record(f2de04b)· 凭据参数化(4d1fb51)· A 簇 env(KernelBench/AutoLab)· 工具栈(fde-row-assembler/checklist-from-task/knowledge-tutorial-assembler/build-html-dashboard)· B 腿候选(daemon-cpu/capstone/blas)。
  - 🆕 **第3类复现交付物(2026-06-09·真实数据·`vtf/_compass_t3_out/`)**:① KernelBench/AutoLab 难倒题(8 官方难倒题 best<0.5 + harness 本地实测过)② FrontierSWE/SWE-bench(官方 harness 复现·bare vs 避坑·resolve 真数据)。网页 commit 50a9a2b。**已写飞书 L3基准样例表**(rid recvm5L3iFlatJ / recvm5L3TUx4kS·含脱敏附件·读回验证)。**compass 认领 KernelBench+FrontierSWE turf**。data_007 已删(冗余+错位)。MLRC/ResearchGym 次批排期中。
  - ⚠️ LongMemEval rerank 网页(commit 52e4e98)= **记忆/检索类,不属第3类 11 benchmark**,归第1类/内部参考,勿当第3类交付。
- **soul**:escapes 终判(radix=TRUE / bvh=FALSE·model confound)· 难度指纹折 RUBRIC · 教案表(base Y7ZFbMbJqaWSxHs27chcC706nZb / table tblZKcpcSYeACj5J)+ 第一篇《CPU饥饿诊断》。
- **agent(v5)**:bvh 2-arm(deepseek 复跑定泛化)· 提交出题表(base EOVhbQwA0a1HEOsgmxecgkBVnwh / table tblhD4O4f0esTyXc 14列)。
- **RSI 飞轮**:radix 单题 escapes=TRUE(护城河)· bvh 待 deepseek 复跑定性 · c3(ΔReward→PoI)defer 到泛化定性。
- ✅ **教案表撞车已裁定(2026-06-09)**:统一用 soul `tblZKcpcSYeACj5J`(已写首篇),agent `tbl9c6mvPRTuq9sD` 弃用 · 待 v5/soul 经协调通道确认。

## 4. 各对话框 turf(不越界)
- **compass**:记忆/recall/drift/PoI/governance/metamemory · FDE benchmark env/eval · feishu 读写函数 · 工具栈。
- **soul(platform-soul)**:标准/QC(checklist_scorer)· benchmark_verifier(pass@k/escapes)· 难度门 · 提交编排。
- **agent(v5)**:出题主体(产候选/轨迹)· 建提交表 · gateway · RSI producer。
- **platform(nautilus-core)**:平台 infra · dispatch · 部署端点 · 数据库。
- **用户(真专家)**:题干/教案内容定稿 · AI 检测兜底润色 · 算力协调。

## 5. 跨对话框协调机制(吃狗粮 · 复用不重造)
- **静态基线(本宪章)**:放各 repo 根 `FDE_BUSINESS_CHARTER.md` + ingest 到各 project → 各对话框 session-start 必读。
- **动态协调**:① 合约通道 `contract.py` close_loop(session_*.md frontmatter `contracts:` block · scanner 跨 project surface)② 语义通道 `ingest_obs(project=对方)`→recall(per-project)。
- 🔴 **当前不便根因**:MCP 时断(语义通道挂)+ 散落 outbound md 靠对方碰巧读 + 本宪章之前不存在。**修复=本宪章 + MCP 稳定 + 未来统一控制面(平台看板 W-A)。**

## 7. 🩻 跨框经验教训(2026-06-24 V5 加 · 所有框 session-start 读)
三条高频跨框复发的根(机制 > 文字 · 写进 ≠ 生效):
1. **confound-check 铁律**:任何「死/失败/0/撞墙/done/产出/已修」判断 → 先 grounded 实测排 confound 再下结论。不查别假设 · 产出 ≠ 解对 · 读对方封前别下结论 · 单点 ≠ 综合 · 字段名先验 · 过早下结论(过乐观/过悲观)都复发 · **外部 verify > 自说 done · 跨框 confound 互纠 > 自审**。(6/24 实证:soul verify 出 V5 SWE diff=0A · 纠正 glm≠qwen · 抓 6+ 个假失败。)
2. **反掰玉米交接**:fresh session = 单焦点 + 起手必验 + parking lot 不准碰 + 完成判据=grounded 证据。长 handoff/列全 = 元级掰玉米。
3. **三 agent 根因诊断**:走错在经济模型(无外部 reward → 棘轮空转)+ 节奏(规划替代落地)· 非版本号。先接外部 reward 源 + 对齐 daemon 大脑。

## 6. 维护
- 业务/甲方/产出有变 → 改本文件(canonical compass memory)+ 同步各 repo 副本 + ingest 各 project。
- 不另起炉灶、不让认知再散。

关联 [[project_fde_three_tracks_one_buyer_presentation_gap_20260609]] · [[dogfood_crossdialog_coordination_via_compass_20260608]] · [[plan_compass_PRODUCTION_handoff_20260609]] · [[reference_yiluo_buyer_spec_two_tracks_difficulty_8h_20260608]]
