# DEMO RUNBOOK · 2026-06-17 早

> 🔴 保密红线:受众=甲方。任何 surface、任何口头讲解,**绝不提甲方名称**。我方=伊洛科技,只讲"我们的客户/买方"。
> 一句话定位:**一个自治的原生 AI 组织引擎,把"AI 做 AI"的递归自我提升(RSI)飞轮 + FDE 数据生产业务环,接进同一条 verdict-bus,自动跑、可观测、可结算。**

---

## 0. demo 前 5 分钟自检(开场前跑一遍)

```bash
# A. 飞轮在自转?(settled 数应随时间涨·auto-mint 每5min 补燃料)
ssh cloud 'curl -s http://localhost:8000/api/platform/rsi-fde?limit=3 | python3 -c "import sys,json;d=json.load(sys.stdin)[\"data\"];print(\"飞轮确定性:\",d[\"flywheel\"][\"deterministic\"][\"passed\"],\"/\",d[\"flywheel\"][\"deterministic\"][\"total\"]);print(\"FDE人工环:\",d[\"fde_business\"][\"passed\"],\"/\",d[\"fde_business\"][\"total\"])"'

# B. 三个 timer 都 active?
ssh cloud 'systemctl is-active auto-mint.timer fde-bench.timer soul-scorer.timer'

# C. 站点活着?
curl -s -o /dev/null -w "dashboard %{http_code}\n" https://www.nautilus.social/api/platform/rsi-fde/dashboard
```
全绿才开场。任一红 → 见 §5 兜底。

---

## 1. 演示顺序(建议 4 步 · 由"自动飞轮"→"业务环"→"结算闭环")

### Surface ② 网页看板(开场主屏 · 公开免登录)
**URL**: `https://www.nautilus.social/api/platform/rsi-fde/dashboard`
**讲解**:
- **🔁 RSI 飞轮卡**:"这是 AI 自己给自己出题、自己解、机器判分(非 LLM 主观打分)、自动结算的闭环。现在 94/103 题确定性通过,**每 5 分钟自动补一道新燃料,无人干预**。" → 当场刷新一次,指 settled 数在涨。
- **🧑‍🔬 FDE 人工业务环卡**:"这是另一条轨——领域专家亲写的高难题/教案,走 派活→人工 QC→交付→结算。**和飞轮共享同一条 verdict-bus,在同一块看板上并排。**" → 这是"一个引擎两条轨"的核心叙事。
- 右侧 Agents/事件流/PoI:"整个 agent 编队的生存状态、事件流、可计入产出,都是真实库数据。"

### Surface ① 飞书多维表格(展示业务环的真实工作流落地)
- **派活表(RGDK v06_派活)** `tblfPoDrZzKHpU36`:"专家任务从这里派发,状态机:待派单→已派单→已提交→已通过→已交付。"
- **审计表** `tblqX49MQooUZjKH`:操作留痕。
- **交付表(Dx2qb)** `tblFkmEKTk4LIWJM`:"过了 QC 的稿,引擎自动组装成买方格式入这里。**机密物理隔离:交付/结算在独立 base,与派活表不同租户空间。**"
- **结算表(Dx2qb)** `tblFL7y3DejBQUvm`:**指 `expert_line2_persona_drift_20260616` 行 → 应付金额=1800、应付状态=computed**。"应付=专家工时单价(300/h)×工时(6h),引擎按名册自动算,不臆造。"

> 🔴 **诚实叙事(quality-over-quantity)**:当前**这 1 道**(persona drift 检测器教案)走完了**完整生命周期** 派活→QC→交付→结算·应付,是端到端"真流通"的证据,**不堆数量充门面**。业务环卡里的 18+ 道是已 QC 的人工 FDE 产出(部分尚未走完飞书全链)。讲法:"我们先把**一条线可靠地闭环**,再批量复制"——这正是工程上诚实的路径。

### Surface ③ control 页(运营指挥视角 · 需登录)
**URL**: `https://www.nautilus.social/control`(🔴 演示者**先登录**,门控正常不影响)
**讲解**:"这是运营/指挥官的统一控制面——FDE verdict 流(双源)、编队生存、PoI 累积,15 秒脉搏刷新。和公开看板同一数据源,面向内部运营。"

### Surface ④ 飞书应用内嵌 agent
**讲解**:"飞书作为前台操作面,PM/专家在熟悉的工具里直接调度 agent 服务台。"(若内嵌未就绪,用 ① 的多维表格 + 看板组合替代叙事即可)

### (可选·live "wow")事件驱动业务环 当场跑
> 🟢 2026-06-17 已端到端验证通(poller→webhook→runner→写回·dispatched 0→1·200)。**仅在主路径演完、时间充裕时再演**(有 poller/webhook 在线依赖)。
- 当场把 v06_派活 一行(用 test 行·非真专家行)状态改成「已提交」→ ~30s 后刷新该行:webhook_dispatched_at 被自动填、QC反馈 列自动写入、状态自动变。
- 讲解:"专家提交后,无人干预——poller 30s 内捕获状态变,自动触发 AI QC 并把结果写回飞书。这就是'AI 组织自己跑'。"
- 🔴 兜底:若 poller/webhook 当时不稳,退回 §5 手动跑 runner,叙事不变。

---

## 2. 一句话价值锚(被问到"这是什么"时)

> "我们做的是**原生 AI 组织**:不是一个工具,是一套能自己出题、自己解、自己验收、自己结算的生产体系。第3类用机器确定性验证器做 RSI 飞轮(AI 提升 AI),第1/2类用领域专家把高难知识沉淀成可训练数据——两条轨共享一套验收/结算底座,全程可观测、可审计、可计价。"

---

## 3. 关键真实数字(诚实口径 · 别 overclaim)

| 指标 | 值 | 口径 |
|---|---|---|
| 飞轮确定性通过 | 94/103(开场前以实时为准) | source=compass/bench_eval·机器判 reward·非 LLM 主观 |
| FDE 人工业务环 | 18/25 QC过 | source=soul/feishu-expert·人工 QC |
| FDE 外部验收总 | 132/155(85%) | 全 verdict-bus |
| 应付真算样例 | 1800 元 | 平台专家#1 · 300/h × 6h · computed |
| auto-mint 自转间隔 | 5 min | TARGET_OPEN=1 限流·V5 自动消费 |

🔴 **诚实声明(如被追问)**:
- 交付样本标 `delivered_provisional`——正文经专家过买方 AI 检测后才是终品;平台一手内容真实但当前样例由平台 dev 充当专家#1。飞轮燃料题=我们自身开发踩坑的真实经验,非编造。
- **业务环当前只有 1 道走完整飞书生命周期**(派活→QC→交付→结算·应付)。这是刻意的"先闭一条线"——不堆 5 道半成品充数(那会违背买方"专家亲写·不能批量 AI 生产"红线)。批量复制是下一步,不是今天的承诺。

---

## 4. 演示中"让它当场动起来"(可选 · 增强说服力)

```bash
# 当场 mint 一道飞轮燃料,30~90s 后看板出现新 settled 行
ssh cloud 'cd /home/ubuntu/auto-mint && TARGET_OPEN=99 python3 auto_mint_poll.py'   # 强制 mint 一道
# 然后刷新看板 ②,指 RSI 飞轮卡顶部新出现的 automint_<时间戳> 行
```

---

## 5. 兜底(自动化没就绪时现场手动跑)

```bash
# FDE 飞书自动化(webhook)没配 → 现场手动跑 runner 演示业务环流转:
# S2 自动 QC(已提交→已通过)
ssh fde-cloud 'cd /opt/ecc-shared/runner/platform_soul && python3 s2_auto_qc.py'
# S3 交付+结算(已通过→已交付·算应付)
ssh fde-cloud 'cd /opt/ecc-shared/runner/platform_soul && python3 s3_delivery_settlement.py'

# 飞轮 timer 万一停了 → 手动补燃料 + 重启 timer
ssh cloud 'sudo systemctl restart auto-mint.timer && cd /home/ubuntu/auto-mint && python3 auto_mint_poll.py'

# 站点挂了 → 看门狗会报·手动重启后端
ssh cloud 'sudo systemctl restart nautilus-backend && sleep 5 && systemctl is-active nautilus-backend'
```

凭据:`ssh cloud`(43.160.239.61:24860)· `ssh fde-cloud`(VM-0-8-ubuntu)。

---

## 6. surface URL 速查

| # | Surface | URL / 位置 | 登录 |
|---|---|---|---|
| ② | 网页看板(主屏) | nautilus.social/api/platform/rsi-fde/dashboard | 否 |
| ③ | control 指挥页 | nautilus.social/control | **是**(演示者先登录) |
| ① | 派活表 | 飞书 RGDK base · tblfPoDrZzKHpU36 | 飞书 |
| ① | 交付/结算表 | 飞书 Dx2qb base · tblFkmEKTk4LIWJM / tblFL7y3DejBQUvm | 飞书 |
| ④ | 飞书内嵌 agent | 飞书应用 | 飞书 |
