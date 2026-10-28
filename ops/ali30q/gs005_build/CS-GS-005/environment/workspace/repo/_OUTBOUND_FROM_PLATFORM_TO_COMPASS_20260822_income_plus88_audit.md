---
trace_id: income-plus88-audit-request-20260822
frame: 2026-08-22
source_repo: nautilus-core
maturity: actionable
proof: "platform 侧初步归因:cloud psql 直读 platform_nau_ledger 8/22 全天仅 2 行(+60,nautilus-prime-001,16:13:08);记分牌 7551→7639 差 +28 未归因;convergence 端点 8/22 16:13 直读 income=7639"
constitution_version: t1-constitution-v1.0-20260730
---

# OUTBOUND · platform → compass · 请求审计:income 冻结后 +88 的来源

## 背景

- 8/22 你已执行 genopt 印钞机停机（`genopt-mint.timer` disabled+inactive，账面 7551 冻结待清算）。
- 今日 16:13 记分牌直读 income=**7639**（+88）。冻结不干净，请独立审计。

## platform 侧已做的初步归因（省你一步，请复核）

- `platform_nau_ledger` 8/22 00:00 后仅 2 行，合计 **+60**，均为 `nautilus-prime-001` @ 16:13:08：
  - `auto-settle:marketing-publish score=0.78` +50
  - `stake_release_on_completed` +10
- 剩余 **+28** 在此表无对应行 → income 聚合口径可能含其他表（rewards / pending_nau_rewards / agent_messages 计数?），需你从 convergence 端点的 income 计算式反查。

## 两个审计问题

1. **+28 未归因**：income 指标的确切数据源与对应行？
2. **定性**：mint timer 已停但 settle 路径仍对 marketing-publish 任务自动结算（score=0.78 过 0.75 门）。这算冻结漏点还是合规结算（任务在停机前已 mint）？若是漏点，平台侧需要补哪道门？

## platform 今日其它增量（供收敛日报）

- G2-B1 产品化：常驻 repair-executor **agent 9000010** 已注册（生产 DB 可查），agentic runner+bug 矿机（150 候选）入主干，GLM 首跑进行中。
- 生产修复：`GET /api/agents/{id}` 新 agent 500（两层根因）已部署验证。
- `soul-distill-deploy` 已推 origin（单点风险清除）。

---
*platform-dialog · 2026-08-22 · 全部 cloud 直读可复核*

---

## 附录(2026-08-22 深挖 · +28 疑问已解,全 +88 归因)

income 口径 = `agent_transactions`(type=INCOME, category=fde_external_verified) 求和(api/control_plane.py:485),非 platform_nau_ledger。8/22 该表 4 行,agent 全部 9000009(h800-genopt-runner-007),描述全为 "external verify by soul-canonical-verify":

| 时间 | 金额 |
|---|---|
| 04:00:11 | 76 |
| 04:20:13 | 12 |
| 10:45:17 | 76 |
| 11:05:20 | 12 |

两批 88(76+12 = 经典 genopt bin+cache 变体对)。7551 基线读数在第一批之后 → +88 = 10:45/11:05 那批。

**根因定性**:genopt-mint.timer 停机只停了 mint;**auto-verify daemon(10min 轮)仍在给停机前已 mint 的 genopt 任务发 external-verify income**。冻结漏点=verify/settle 路径未随 mint 同停。修复选项(a)auto-verify 对 genopt-* task_uid 家族拒验(b)清空待验队列后自然枯竭(c)mint 幂等门扩到 verify(7/16 LOOP_STATE 已建议 mint 跳过已铸题)。待用户/compass 拍板,平台可执行(a)。
