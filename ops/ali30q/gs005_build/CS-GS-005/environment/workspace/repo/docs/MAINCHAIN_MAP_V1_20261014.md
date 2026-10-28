# 组织主链贯通图 V1(2026-10-14 · 四步方案③)

> **用途**:全部活资产挂主链节点,一页看清"什么在链上/什么死了/新想法该接哪"。新立项先在此图找节点,答不出"强化哪个节点"=登记不立项。配套:LIVENESS_RUNBOOK_V1(8 锚巡检)/SESSION_RETRO_AND_SYSTEMIZATION(死因四型)。
> **活性时戳**:✅=2026-10-14 实测;🟡=回执级;🔴=断。刷新纪律:ship 后顺手改行,每周全量复测。

## 主链(一横):触客 → 提测 → 判读 → 榜单 → 复算 → 付费

| 节点 | 实物与坐标 | 消费方 | 状态 |
|---|---|---|---|
| **触客·嵌入** | GitHub Action `chunxiaoxx/nautilus-judge-action@main`(self-test CI ✅) | 外部 harness 作者(CI 一键) | ✅ |
| **触客·榜单页** | bench.nautilus.social(正本已入仓 conf-sync 分支) | 榜单访客 | ✅ 双 CI 锚 |
| **触客·GitHub** | Wave1 11 仓(三触毕)/Wave3 16 仓(10/14 发,2 关 14 候) | indie harness 作者 | 🟡 观察窗 10/21 |
| **触客·邮件** | Wave2 七家(Gmail 留痕)/Dev.to 官宣帖(断链已修) | B2B 团队 | 🟡 PlanB 10/20 |
| **提测·表单** | www.nautilus.social/submit/(13223B,含 CI 段) | 无 CI 用户 | ✅(SPA 兜底断面已修) |
| **提测·API** | POST /api/platform/org/assay/submissions(is_smoke 标记) | Action/集成方 | ✅ 免认证=候拍项 |
| **判读·判据** | L3_HARNESS_BOARD_ROUND1(sha16 b81eca84)/criteria 披露页/CASEBOOK_V1 | 判分公信 | ✅ |
| **判读·产能** | compass 判读(首考窗 JD-20261013-001)/assay CLI | 全组织 | 🟡 首考候交付 |
| **判读·查询** | judge_status(9890,10/14 平台代修 502) | 外部查卡/Action fallback | ✅ 真卡接入候 compass |
| **榜单·读数** | bench.nautilus.social(1 判读:mini-swe 双臂)/corpus_stats | 外部+全框 | ✅ 榜填充=先行指标 |
| **复算·样例** | org.nautilus.social 判读卡+L2 样例(sha 67144de4) | 质疑者/复算请求 | ✅ 断链已修 |
| **付费** | pricing.html($199 L2/$99 复核)/收款三步(候用户)/fuel 结算 timer | 付费客户 | ⏸ 候用户操作 |

## 支撑面(纵向基建,全框共用)

| 资产 | 坐标 | 状态 |
|---|---|---|
| 组织函箱 | org_mailbox(acks 纪律)/send_letter/HTTP API 读 | ✅ compass 读函回路🔴待修 |
| 生产 DB | nautilus_production(65 表)/平台 362 端点 | ✅ |
| nginx 正本 | sites-enabled 两 conf+bench index(**已并 master 9596b15a1,10/14 三线合一**) | ✅ |
| 部署管线 | push+restart+curl 三验/四步 runbook | ✅ |
| 记忆体系 | memory/MEMORY.md+session_NODE+compass daemon(9876) | ✅ |
| 本机任务栈 | 13 任务 SYSTEM 化(10/14,弹窗根除)/18001 推理网关(v5 域) | ✅ |
| 活性巡检 | LIVENESS_RUNBOOK_V1(8 锚,周全量) | ✅ 机制位 |

## 退役/冻结区(明确死,勿复用勿重建)

FDE 线(v5 框 10/14 宣告退役;fde vhost/janitor/ecc-scanner 去留候拍)/垂域 5 timer(9/2)/square 论坛/vc_daily 日报(999h 堵)/老平台 13 trigger/driving 舱/44 项施工单(拒建)/org 驾驶舱页(0 访问,档案标待退役)。

## 使用规则

1. **新想法**:在此图找节点→有节点=接线(先查该节点死活);无节点=登记候拍,不直接造
2. **修死点**:先查死点台账(LIVENESS_RUNBOOK §三),同族问题走五类强制位
3. **口径**:对外资产(触客/披露)链接一律指组织静态站,**禁 commit 锚**
4. **三类产出防死位**:动作留痕即完成/资产三件套(正本+入口+巡检)/机制进强制位

—— platform · 2026-10-14 · 下次全量复测:2026-10-21(Wave3 观察窗止同日)
