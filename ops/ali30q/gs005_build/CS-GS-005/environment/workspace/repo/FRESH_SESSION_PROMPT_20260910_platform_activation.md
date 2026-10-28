# FRESH SESSION PROMPT · 2026-09-10 · 平台激活执行日(platform 框)

> 昨夜(9/9 深夜)用户已拍板,今天执行。**不要重新讨论方向,直接开工。**
> 详细锚点已入 memory:`platform-activation-mandate-20260909` / `t15-vloop-theory-status-20260909` / `feedback-liveness-vs-capability`(compass recall 可查)。

## 用户拍板(9/9 深夜,逐字口径,今日最高优先)

1. **"不加表只激活"** —— 不建机制活性表,直接激活机制
2. **"DMAS 任务/结算层救"** —— 老 tasks 表复活,接回烧题流水线
3. **"应该回归平台激活平台"** —— 平台是主业,理论线让位
4. 纠正:探活 ≠ 能力实测。**每个机制的验收 = 一次端到端真调用**,不是 HTTP 200 / timer active

## 四机制卡点地图(9/9 23:30-23:50 实测,勿重探,直接用)

| 机制 | 状态 | 卡点 | 验收标准 |
|---|---|---|---|
| soul | 两条 timer disabled+dead | 无 API 写 platform_proposals 队列(5/28 契约 Option B ~30 LOC 未建) | 投一条真提案走完 提案→gate→draft PR→回写 |
| MCP | 8096 端口活(裸 python `mcp/mcp_server.py`,8/31 起)但 `/mcp/` 404(外网+本机) | nginx 路由(server{88-98}→8096/mcp/)与 server 实际路径不匹配 | MCP initialize 握手 200 + tools/list 返回工具清单 |
| A2A | `.well-known/agent.json` 200;`/api/a2a/relay/messages` 404 | 消息中继端点未部署或路径漂移(后端源码 grep a2a 定位) | 两 agent(如 9000010↔9000014)真发一条消息并收到 |
| DMAS 双轨 | 老 production.tasks 表死 105 天(最后 2026-05-27);新 org 台账活(platform-loop run#54、#131 CLOSED、capability-settle/order-lifecycle 30min) | 烧题流水线在本地 evidence(426 份),不进云端任务/结算层 | g2b1 烧一题 → tasks 表出现该任务 → capability-settle 记账读到 |

## 今日执行顺序(每步完成并验证后才进下一步)

1. **soul**:读 `phase3/soul/` 与云端 soul_consumer 现状 → 补写入端点(Option B)→ `systemctl enable --now nautilus-soul.timer nautilus-soul-executor.timer` → 投真提案端到端验
2. **MCP**:云端读 8096 server 源码定位真实路由 → 对齐 nginx 或升级 streamable HTTP → 真握手+tools/list 验
3. **A2A relay**:后端源码定位端点 → 缺则补 → 两 agent 互发真消息
4. **DMAS 接线**(工程量最大):executor 烧题落账时同步写 tasks + capability-settle 记账;先设计(幂等/去重/映射)再动手

## 纪律提醒

- 云上变更走仓→云部署,**禁 VM 直改**(ops/DEPLOY_DISCIPLINE.md);soul timer enable 属云上 systemd 变更,先在函/plan 里写明再动
- soul 消费者当年验证过 gate 会拒( NEVER auto-merge),激活后第一周盯 draft PR 产出,防空转
- 同日理论线待办(低优先,别抢主线):T15 入账理论总账(标"假设"+反证条件+长度对照设计);U2 预测函降格发(论文仓+V5)
- V5 批量 ack 清单 9/9 12:00 已过期未交——今天可按已批 A/B 协议走 telegram 升级提醒(日限额 2 条内),发前向用户确认

## 现场状态快照(9/9 深夜)

- 分支 soul-distill-deploy;fmB 已定谳(强门 FAIL 4/8,统计 bug 已修);executor evidence 426 份,下一班 22:47 换 04:47
- 新 commit(a92e9e904 等)未推云,push 重试脚本在 `C:\Users\chunx\AppData\Local\Temp\claude\retry_push_v3_20260908.sh`
- 平台活体体检=每月固定动作(9/9 对用户承诺),下次挂 10/9 月报
