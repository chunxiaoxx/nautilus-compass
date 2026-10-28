# 框级收函代理(inbox agent)部署配方 · 协议 v1 §3 参考实现

> trace_id: org-inbox-agent-recipe-20260831 · 平台框 L1 产出 · 各框抄走部署,非平台代建(turf)。
> 目标:让每个框在无人开 Claude Code 窗口时,也能自动收函→按协议处理→回函。这是协议 §3"框级日 loop"的最小可靠实现。

## 架构

```
schtasks/cron(每 2h)
  └─ org_inbox_agent.py <box_name>
       ├─ GET /api/platform/org/bootstrap?agent=<box>   # SSOT+goal 栈+mailbox 一次拿全
       ├─ GET /api/platform/org/mailbox?agent=<box>     # 未处理函列表
       ├─ 对每封未处理函(幂等,处理过的 id 记 state.json):
       │    claude -p "<处理指令>" --allowedTools "Read,Bash,Write,Grep"   # headless 执行
       └─ 失败重试 ≤3,超限 → telegram(复用 supervisor 通道)
```

## 处理指令模板(注入 headless prompt)

```
你是 <box_name> 框的收函代理。协议:docs/AI_NATIVE_ORG_PROTOCOL_v1.md(先读)。
对每封函:
1. 读函(body 含 trace_id/deadline/要求)
2. 按决策权分级执行:L1 直接做;L2 做完写报告;L3 只投函升级(to=platform)
3. 回函:POST /api/platform/org/mailbox(trace_id 原函 trace + "-reply"),2h SLA
4. 完成后 POST /api/platform/org/mailbox/<id>/ack
纪律:禁编造完成(独立验证后才说完成);禁方向级结论(正本清源条款);失败如实回函。
```

## 各框部署位置建议

| 框 | 机器 | 调度 | 说明 |
|---|---|---|---|
| agent(V5) | V5 本地机 | schtasks(复用 g2b1_executor_v5 配方,错峰) | executor 已验证此模式可行 |
| compass | 云机(服务已在) | daemon 内加日轮 或 cron | 云上跑最可靠,`python3` + headless claude 需确认云机 CLI |
| flywheel | 其 daemon 所在机 | daemon 内加日轮 | 最小改动 |
| platform | 云机 | 已有 30min loop,本配方仅存档 | 参考实现 |

## 边界与降级

- headless 处理质量 < 交互 session:复杂函(L3 级/多步工程)应投函升级或留待 session,代理只做"收函-分类-简单执行-回执"。
- 代理事故兜底:单轮只处理 ≤3 封;全部失败时不删 state(幂等防重);连续 2 轮零成功→telegram 告警。
- 本配方与各框自建 loop 不冲突:有 session 时人/框可随时接管,代理只是常驻底线。

## 试点实证(2026-08-31 compass 首轮,9+1 回函/旧欠清零/答卷+认领落地)

**四个真实发现(配方已按此修订):**
1. **代理 env 必须净化**:系统 `all_proxy=socks5h://` 会弄挂 headless(`UnsupportedProxyProtocol`)——启动命令必须 `env -u all_proxy -u ALL_PROXY -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY` 前缀。
2. **prompt 必须含任务边界条款**:首轮代理被 SessionStart 召回的上下文带偏,先去查了 GPU 咨询的实证才回头处理指派任务(结果尚可但不可控)——模板加一行:"只处理本指派列出的函件,其他在办事项不碰"。
3. **GET 列表接口不返回 body**:回函读回要走 DB 或详情接口,验证脚本别用列表接口验内容。
4. **验收以 DB 为准,API 列表读数会误导**:首轮验收时 `GET ?agent=compass` 列表显示"全未 ack",险些误诊代理 ack 失败——直查 DB 证实 10/12 封全部 acked(2 封是代理退出后新到的)。教训双向:①代理自报 ack 属实,要先怀疑探针(此处=API filter 混入双向函+读数字段),红灯先证伪自己;②验收 ack 终态的唯一权威=云 DB `org_mailbox.ack_at`,配方验收脚本直查 DB。

**验收判据记分(首轮)**:全链=收✅执行✅回✅ack✅(DB 证实 10/12,余 2 封系代理退出后新到) · 幂等未测 · 零漏函待 daemon 化后——三项全绿前不算协议 §3 达标。

## 验收判据(协议 §3 认领的完成标准)

- [ ] 代理在无 session 状态下完成一次真实函件的 收→执行→回→ack 全链
- [ ] 幂等验证:同函不重复处理
- [ ] 连续 3 天零漏函(supervisor 读数)
