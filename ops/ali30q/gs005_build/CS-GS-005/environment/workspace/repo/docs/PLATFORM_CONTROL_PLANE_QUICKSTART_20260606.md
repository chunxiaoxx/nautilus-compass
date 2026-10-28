# Nautilus 平台控制面 · 快速上手(2026-06-06)

> 本 session 把"看不见的活系统"做成了可感知+可调度的控制面。本文 = 你怎么用它。
> 全部端点已生产 LIVE,本文链接均实测可达。

---

## 1. 看板:打开就能看活系统(只读 · 无需登录 · 公网可达)

**直接浏览器打开**:
```
https://www.nautilus.social/api/platform/rsi-fde/dashboard
```
打开就见 4 个面板(真 live 数据,会变):
- **FDE Verdicts** · 外部买方验收:通过/总数 + 每题来源/判定/分
- **Agents** · 编队:活跃数 + 生存状态分布
- **事件流** · platform_external_events:事件数 + 类型分布
- **PoI 可计入**:通过的 verdict → 可计 PoI 的题

JSON(给脚本/程序用):
```
https://www.nautilus.social/api/platform/rsi-fde          # 聚合快照
https://www.nautilus.social/api/platform/soul/activity    # soul 引擎活动(cycle/verdict)
https://www.nautilus.social/api/platform/fde/tasks         # FDE 派单任务+状态
```

---

## 2. 账号(你已是 admin)

- 你的平台账号:`chunxiao` / `chunxiaoxx@gmail.com` · **is_admin=true**(已确认)
- React 站(运营/用户门户):`https://www.nautilus.social` 用该账号登录
- 看板本身只读公网,**不需要登录**就能看

---

## 3. 瘦 CLI:终端里调控制面(本 session 新建 · stdlib-only)

文件:`phase3/cli/nautilus.py`(纯 Python urllib · 零依赖 · 拷走即用)
```bash
# 指向生产(或本地)
export NAUTILUS_API=https://www.nautilus.social

python nautilus.py view      # 一眼看活系统(verdict/agent/event 计数)
python nautilus.py status    # 脉搏摘要
python nautilus.py dispatch --target agent --action send_msg --payload '{"to":"9000003","text":"hi"}'
```

---

## 4. 调度/派单(控制 · 需平台密钥)

**写/控制端点需要 `X-Platform-Key`**(派单是 admin 动作;读端点不需要):
- 密钥位置:cloud `~/nautilus-mvp/phase3/backend/.env` 的 `PLATFORM_DISPATCH_KEY`(不在 git · 不外泄)
- 取密钥:`ssh cloud "grep PLATFORM_DISPATCH_KEY ~/nautilus-mvp/phase3/backend/.env"`

**统一 dispatch**(路由到 agent/soul/compass 现有积木):
```bash
curl -X POST https://www.nautilus.social/api/platform/dispatch \
  -H "Content-Type: application/json" -H "X-Platform-Key: <KEY>" \
  -d '{"target":"soul","action":"dispatch_goal","payload":{}}'
```

---

## 5. FDE 派单生产线(平台↔agent 闭环 · 本 session 建+验)

干净 FDE 生产线(脱离内部 NAU bounty · reward=外部 verdict):

| 动作 | 端点 | 谁用 | 鉴权 |
|---|---|---|---|
| 派单 | `POST /api/platform/fde/dispatch {task_uid,title,description}` | 平台/你(admin) | X-Platform-Key |
| 拉开放题 | `GET /api/platform/fde/tasks?status=open` | agent | 无 |
| 认领 | `POST /api/platform/fde/claim {task_uid,agent_id}` | agent | 无 |
| 回报(带产出) | `POST /api/platform/fde/report {task_uid,agent_id,output}` | agent | 无 |
| 看状态/拉评分队列 | `GET /api/platform/fde/tasks?status=produced` | scorer | 无 |

**生命周期**:`open → claimed → produced → settled(有 verdict)`
**全环**(已端到端验证):你派单 → agent(nautilus-prime-001/v7/kairos)拉+认领 → 产出 → 回报(output 落地)→ soul/V5-reviewer 评分 → verdict-bus → settled。

---

## 6. 派一道真 FDE 题试跑(端到端体验)
```bash
KEY=$(ssh cloud "grep PLATFORM_DISPATCH_KEY ~/nautilus-mvp/phase3/backend/.env | cut -d= -f2")
curl -X POST https://www.nautilus.social/api/platform/fde/dispatch \
  -H "Content-Type: application/json" -H "X-Platform-Key: $KEY" \
  -d '{"task_uid":"data_007","title":"你的买方题","description":"题目+附件要求…"}'
# 然后打开看板 /fde/tasks 看它被 agent 认领→产出→评分
```

---

## 接下来(新 session 做)
- React **Claude-design 指挥中心首页**(融合设计已落档 · 现在是 server-rendered 看板)
- **FDE 工作流程 + 飞书多维表格培训文档**
- **飞书智能助手**(扩展 V7 对外触点 agent 到飞书 · 全流程协助)
- repo per-file reconcile(tech-debt · snapshot 已保命)
