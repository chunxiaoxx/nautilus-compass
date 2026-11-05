# 安全报告独立验证卡 · v14_recall 未认证跨项目读 + ingest_obs 路径逃逸

- 日期:2026-11-05(R442 事件轮)
- 报告人:Nagizaaz Shaik <nagizaazs@gmail.com>(直发 Gmail,11-05 06:59 -0500)
- 前置:compass#66(11-04 用户已处置 closed,R428 定谳)——本件为其后续:报告人按 SECURITY.md 私下补发细节,内容超出 #66 原报(新增洞定位+修复建议)
- 报告人声明:仅源码审查,未对任何活服务发请求;愿 coordinated disclosure
- 本卡性质:compass 域独立源码验证(未发任何请求到活服务,未部署任何变更,未外发任何回函)

## 洞 1(主):`/v1/v14/recall` 无认证 · 跨项目记忆披露

**验证:属实**(`compass_http_v09.py:1509-1524`)

- `def v14_recall(q, top_k, scope, project, agent_id, x_tenant_id=Header(None, alias="X-Tenant-ID"))` — 签名内**无** `Depends(auth_user)`
- 对照:全文件 12 处 `Depends(auth_user)` 覆盖 /v1/observations、/v1/recall、/v1/profile、/v1/audit_log 等;2026-08-30 修复(记忆:security-v09-xuserid-impersonation)补了 drift_check/ingest_obs,唯独漏掉 `/v1/v14/recall`
- tenant 完全取自客户端可伪造的 `X-Tenant-ID` header(`agent_type = x_tenant_id or "unknown"`)
- `scope=user` 触发跨项目 UNION 扫描(全 ~/.claude/projects,37k+ 目录),召回结果(含其他项目记忆)直接返回调用方
- **失败场景**:未认证调用方 `GET /v1/v14/recall?q=...&scope=user` + 任意 X-Tenant-ID → 读到不属于自己的项目记忆

## 洞 2(次):`/v1/v14/ingest_obs` project 路径逃逸 · 任意目录写/跨租户记忆投毒

**验证:属实**(`compass_http_v09.py:1612, 1639-1642`)

- 该端点 2026-08-30 已补 Bearer JWT 必检(line 1600-1610,洞 2 认证前提需先注册)
- `signup` 开放注册(line 551,任意 email 即拿 JWT,无邀请制)→ 认证前提可满足
- `project = (body or {}).get("project") or _V14_DEFAULT_PROJECT` 后直接 `out_dir = home / ".claude" / "projects" / project / "memory"`,**无任何清洗**
- **失败场景**:`project="../../../../tmp/x"` → mkdir+写 session_*.md 逃出记忆根;或跨租户目录投毒记忆
- 修复建议(报告人):project 白名单 `^[A-Za-z0-9._-]+$`,拒绝含 `/` 或 `..` 的值

## 影响面评估(待用户确认后修复)

- 主洞严重度:高(机密性——跨项目记忆披露;前提=服务在公网可达;2026-08-30 修复记录自述该服务曾在公网 443 暴露)
- 修复风险(必须用户拍板,值守轮不自行部署):
  1. 给 v14_recall 加 `Depends(auth_user)` 会**打断现有消费者**——scope=user 的 v14 recall 是 v5/各框 loop 在用的(X-Tenant-ID 无 JWT 方式)。需要先盘点消费者再定切换方式(如服务端 token / 过渡期双读)
  2. scope 绑定认证身份后,现网"以 header 声明租户"的语义全部失效
  3. 次洞修复(project 白名单)低风险,可先行
- 部署面:cloud 生产(43.160.239.61)是否仍在跑此服务、公网暴露态=待独立核验(本轮未探活生产主机,避免误触发)

## 纪律与下一步(候用户)

- 🔴 不外发:对报告人的任何回函(致谢/coordinated disclosure 时间线/修复承诺)必须先过用户审稿(外发硬闸,10/31 定谳)
- 修复三选项候拍板:
  - A. 先修次洞(白名单,低风险)+ 主洞加 auth 并同步升级消费者(v5 各框带 JWT 调 v14)——完整修复,需协调 v5
  - B. 先修次洞 + 主洞临时缓解(如 v14_recall 仅内网绑定/移除 scope=user 路径)——快速降险
  - C. 全部留档,由用户主导协调(coordinated disclosure 90 天窗口自 11-05 起算)
- 无论 A/B/C:建议给报告人致谢回函(draft 候审),并按惯例记 SECURITY 台账
