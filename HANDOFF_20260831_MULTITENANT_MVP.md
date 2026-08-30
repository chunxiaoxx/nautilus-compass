# HANDOFF · 多租户 MVP 六件 · 新 session 开工件(2026-08-30 深夜立)

> 用户拍板路径 B:8/31 用户交话术版提审;本文件 = 6 件 MVP 的开工清单,新 session 直接照做。
> 设计依据:`docs/plans/2026-08-30-multi-tenant-memory-design.md` · 任务总账:`docs/plans/2026-08-30-multitenant-roadmap-tasks.md`
> trace_id: compass-multitenant-mvp-20260831

## 完成判据(五步旅程端到端 + 四探针四绿)

```
1. 落地页 Get started → /signup 可注册
2. 注册即得身份 + 专属记忆空间(u_<id>_memory)
3. 控制页一键创建/撤销 agent token(scope 只限本人空间)
4. MCP 客户端连 https://compass.nautilus.social/mcp/ + Bearer token 可用
5. 注册后四探针自动跑:跨用户读DENY/跨用户写DENY/同用户跨设备同空间/撤销即生效
```

## 六件(顺序执行,每件验收判据)

| # | 件 | 实操要点 | 判据 |
|---|---|---|---|
| 1 | 用户模型上 8097 | 8770 的 users/agents/observations 表结构(SQLite)搬到 mcp_http_server.py 的存储层;不搬代码搬模型 | 建表+读写 smoke |
| 2 | signup+login API | 参照 8770 `/v1/auth/signup\|login`(JWT 签发);补统一失败文案(防枚举)+限流 | signup→login→JWT→recall 本人空间 |
| 3 | token 自助 API | create/list/revoke;**服务端强制 scope=本人 project,不信任客户端传值**;复用 /etc/compass/tokens.json 或新表(二选一,写明) | 四步 e2e(创建→用→撤→DENY) |
| 4 | /signup + 控制页 | 落地 landing/ 同款风格,单页+几十行 JS 即可;nginx 加 location(静态) | 旅程 1-3 步可点可跑 |
| 5 | agent.json 已改真(✅8/30 深夜完成) | capabilities 全指 /mcp/·auth=邀请制 bearer·npm 死链已删;**MVP 完成后把 acquisition 从"邀请制"改为"自助"** | 卡片与实物一致 |
| 6 | 四探针自动化 | signup 成功后自动跑,结果落控制页;后续进 cron 常态回归(T7) | 无人值守四绿报告 |

## 关键地形(已验证的事实,别重查)

- 8097 = `mcp_http_server.py`(compass-mcp-http.service),公网经 nginx `/mcp/`;鉴权 = `/etc/compass/tokens.json`(HTTP 版有 mtime 热加载)。
- 9877 TCP = `mcp_server.py`(compass-mcp-tcp.service),**改 tokens 必须重启服务**(无热加载,T8 未做)。
- 8770 = `compass.service`,WorkingDirectory=/home/ubuntu/compass;**该目录与 repo 已分叉,退役(9/15)前禁止同步/重部署**。
- 8770 参考实现:signup/login(JWT)、oauth/authorize+token(603/630 行)、users/agents/observations 三表——只抄设计。
- JWT_SECRET = 环境变量 NAUTILUS_JWT_SECRET(unit 注入),勿落代码。
- 落地页源 = `landing/index.html`(nginx 静态根 = /home/ubuntu/nautilus-compass/landing)。

## 纪律

- 每件完成即 commit(只 add 具体文件)+ 公网实测验证,不说"应该可以"。
- 动 nginx 前备份(sudo cp),nginx -t 过了再 reload。
- 买方名/内部代号不进任何对外页面;数字只用已定案口径。
- GPU/d13 主线在并行跑,与本 MVP 无资源冲突,勿跨界动 GPU 机。
