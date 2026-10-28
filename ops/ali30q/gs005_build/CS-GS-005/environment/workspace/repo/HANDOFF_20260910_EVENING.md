# HANDOFF · 2026-09-10 晚（激活日 + 全平台体检 + 四修闭环）

> 接班 session 从这里开始。当日三份记忆（platform-activation-day / governance-backlog-triage / soul-circuit-breaker-and-backlog）是细节层，本文是全貌+分析层。

## 一、当日主轴（时间线）

1. **激活执行日**（9/9 深夜拍板的执行）：四机制端到端真调用验收全过——soul 提案链 PR#140 / MCP 外网 initialize+tools/call 实调 / A2A 9000016↔9000014 双向 / DMAS verdict→production.tasks 台账复活（死 105 天）。
2. **MCP 扩容**（d394eb242）：6→8 工具（+nautilus_a2a_send/inbox），engine 正本化入仓 ops/mcp/，Claude Code 可 `claude mcp add nautilus https://www.nautilus.social/mcp --transport http` 一行接入。
3. **soul 派单实战**（用户拍"让 soul 修自己多文件局限"）：任务本身未 ship，但产出三真修——thinking 截断根治（cd357f6bb）、max_tokens 32768（4351d9d47）、**check_import subprocess 隔离（3b6aab861，原挂账的 staging 局限已人工修掉，23+3 测试全绿）**。
4. **晚全平台体检**（用户拍"同意建议"）→ 四修闭环：
   - soul exit-code 语义（7dcb25b0a）：业务性 gate 拒绝 exit 0，19:03 班实测 systemd 不再 failed
   - 熔断自动触发验证：机制已在（cap=5），五连败后 19:03 自动 pause，**soul 现处全停待派单恢复**
   - verdict 断供定谳：fde_verdicts 24h=0 ≠ 接线故障，**上游产题线（烧题班次）已死**，本机无 22:47/04:47 任务载体
   - platform_post 定谳：报错主体=Prime 幻觉（表无 agent_id 列/4 处实现全写 author_agent_id/9/4 三连发成功/日志零记录）；真实缺陷=self.agent_id None 无设防，附 patch 回函 V5 自上（turf）
5. **双函投递**（674c80a3c）：206（platform_post 定谳）+207（归档方案请示），deadline 21:27，21:43 班起执法（v5 未回则亮牌）。**SLA 链 21:20 实测验证正常**：205（早 08:31 投，09:00 已 notify）18:43 起在 takeover 候选池（takeover=14 成员），escalated=0 六班=无新增属正确行为。唯一瑕疵：205 deadline=created_at+10h 而非 +2h（发函参数偏晚，旧病复发式）。
6. **8096 托管结论修正**：MCP 非"裸进程"——PM2 链完整托管（pm2-ubuntu.service→PM2 nautilus-mcp），unit 化部署撞端口后撤除，外网 initialize 200 复验。

## 二、当前系统状态快照（21:50 实测）

| 机制 | 状态 | 备注 |
|---|---|---|
| soul daemon | 🔴 pause 中（.soul-pause，19:03 熔断挂起） | 恢复=用户派单时 unlink + goals.yaml 投任务 |
| soul consumer/executor | ✅ timer 正常排程 | consumer 15min/executor 10min，check_import 新代码已部署生效 |
| MCP :8096 | ✅ PM2 托管，外网 200 | 8 工具；**改 env 用 PM2 侧，勿再 unit 化** |
| A2A relay | ✅ 通 | Redis 残留 v1=7/v2=16 挂账不清（拍板） |
| DMAS tasks 台账 | ✅ 接线活 | 但 verdict 断供（上游死），台账不会自己长 |
| 治理链 | ⏳ 等 207 回函 | 854p/400v/117 approved；executed_failed 8>ok 5 待复盘 |
| LLM 链 | ✅ api.chunxiao.wang | MiniMax-M3；thinking 任务 max_tokens 已 32768 |
| agents 存量 | 🟡 258 个仅 3 个有心跳 | v7-telegram / kairos / nautilus-prime-001(9000016) |

## 三、等待与触发器

**🔴 22:25 新发现：platform_loop 时区错位 bug（SLA 判定整体偏晚 8h）**
- 根因：`platform_loop.py:329` `now = datetime.utcnow()`（naive UTC），而 org_mailbox 的 deadline/notified_at 混写两种时钟（205=09:00:40 CST；206/207 的 notified_at=11:30:53 实为 UTC 混写——投递 19:26 CST 后 4 分钟某进程以 utcnow 写入）。
- 后果：206/207 实际 21:27 CST 过线，loop 到 UTC 21:26（**CST 明早 05:26**）才判 overdue 并亮牌——SLA 2h 实际变 10h。takeover 池 14 恒定、escalated=0 六班均因此"看似正常实则全慢 8h"。
- 修法（下 session）：loop 侧 `utcnow()`→`now(Asia/Shanghai)` 对齐 DB 时钟（最小改动），或全链路 UTC 化（DB 列+写入端+比较端，动作大）。加双时钟回归测试。8/31"deadline 写 UTC"教训同根病，建议一并立函件时区约定正本。
- 附带小瑕疵：206/207 的 created_at=NULL（投递脚本未写该列且表无 default）——影响 24h 统计口径。

## 三、等待与触发器

| 等什么 | 触发 | 接班动作 |
|---|---|---|
| 207 回函（v5 无异议+两个选择） | org_mailbox from_agent=v5 | 24h 内执行归档：SQL 脚本入仓 ops/，先抽样 20 条复核再批量（970 误灌/400 voting 死信/117 approved 陈旧→archived） |
| 206 回函 | 同上 | V5 自上 patch 后复核 platform_tools_mixin.py 防御是否落地 |
| 用户派单给 soul | 用户明示 | unlink .soul-pause + goals.yaml 投任务（措辞：短+验收明确，禁长诊断文本） |
| nautilus-db MCP 通道 | 下 session 顺手修 | 本地诊断工具超时；临时替代=ssh cloud + sudo -u postgres psql |

## 四、下一步优先级（分析，非罗列）

1. **归档执行**（207 回函即动）：117 approved 不归档，soul 恢复后 goal_stack P1 会误派单陈旧提案——这是恢复 soul 的前置。
2. **nautilus-db 通道修复**：体检全靠它，坏着=每查一次都要 ssh 绕行。
3. **治理链质量复盘**：executed_failed 8>ok 5 + v7-llm-judge 与 soul 队列交叉互动，值得一次只读复盘（裁决质量影响 soul 派单措辞）。
4. **锚定主线（最重要）**：体检硬数据再次坐实平台活动 98.8% 僵尸+自指循环（709 bounty 100% 内部自 post 的延续）。**平台下一步价值不在内部机制微调，在支撑具身数采主线**（银河通用/云迹，方向锚 9/2）——机制层今天的激活日+体检已经够用，别再加机制。

## 五、陷阱速查（今晚新增，全项目适用）

- **cloudpush 推 soul 不生效**：`git push cloudpush` 落 /home/ubuntu/nautilus-mvp（updateInstead），但 soul 三 unit 的 ExecStartPre fetch **GitHub**——正解=云上中转 `cd /home/ubuntu/nautilus-mvp && git push origin soul-distill-deploy`。
- **动云上进程先查 PM2 归属**：`sudo -u ubuntu pm2 list`；PPID=1450（God Daemon）的 kill 后 24s 内自动复活。PM2 管 8 个 nautilus/hr 进程。
- **org_mailbox 投函禁 SQL 直插**：body 含单引号必炸；配方=参数化脚本 ops/send_20260910_evening_letters.py（psycopg 字符串常量）scp 上云跑。
- **agent 报 bug 定谳四步法**（platform_post 实战）：schema 对照→实现 grep→成功样本反证→日志佐证。Prime(9000002) 有幻觉前科（9/10 凌晨 v5 框诊断在案），其报错需先证伪再修。
- **DB 库名分层**：backend .env 写 nautilus_staging（误导）；实际 nautilus_phase3（API 层）/nautilus_production（platform_* 治理+台账+fde_verdicts 135 表）/nautilus_v5。
- **判断前先问半径**（9/3 锚）：今日"8096 裸进程"误判即违反——全貌是分布式资产，动托管/部署类判断前先拉全景（pm2 list/systemctl list-timers/列库表）。

## 六、诚实边界 / 未验证项

- ~~SLA 亮牌是否真发~~ **已验证（21:20）**：执法链正常；206/207 到期未回则 21:43 班亮牌（当日 telegram 配额 3 未耗）。
- 治理链 executed_failed 8 条根因已复盘：**非垃圾**，6-7 月 6 条真技术提案（pf_cancel_stakes×3 重复/dead_agent stake 释放/daemon 配置修复，全 9000001 提）死于执行链——均为多文件+跨表任务，超出 executor 单文件能力。启示：117 approved 里同类"真提案但执行链无力消化"者，归档时应标"退回人工队列"而非笼统"陈旧"；已并入 207 回函后的执行考量。
- v7-llm-judge 对 soul 提案判 needs_more 后重置 pending 的长期行为未观察（可能造成 soul 队列内循环）。
- L2 三臂记忆实验仍在跑（收割 `--report`，9/8 挂账）；g2b1 队列 130/158 悬空 ref 未重烧（9/8 挂账）。
- git 状态：soul-distill-deploy 领先 master 多 commit（今日全在 deploy 分），未合并非意外——激活日 PR base 亦是此分支。

## 七、函件台账（今晚）

| id | 方向 | 主题 | 状态 |
|---|---|---|---|
| 205 | platform→v5 | 改道（停写治理表/send_to_agent 定谳） | 未 ack，已 notify |
| 206 | platform→v5 | platform_post 定谳+patch | deadline 过，等回 |
| 207 | platform→v5 | 归档方案三点请示 | deadline 过，等回 |
| 202-204 | platform→all | 激活广播三投 | 9/12 22:00 deadline |

---

# 追加 · 9/11-9/12 深夜（方向终审）

## 9/11 白天-晚动态
- 治理表分层归档执行（e7e92eac6）：archived 1154（误灌764+陈旧389+approved1），9月101真bug未动，对账守恒；预检修正两定性（~25% 有内容陈旧/117 approved 在另一张表）
- v5 复活：13:51 批量 ack 205/206/207+210 通知函，投 211 自荐（响应 #202 广播）——"间歇性响应"修正"结构性失聪"；takeover 17→8
- 飞轮无应答：212 号拆单征询函晾 9h+（mailbox 到不了飞轮实锤）
- 212 号函/激活广播 202-204 均在 SLA 追踪中

## 9/12 凌晨 · 方向终审（用户拍板）
**组织 OS 优先，主线并行等飞轮**——对立面五质疑知情后裁决。
执行骨架=六层框架（身份/记忆/治理/经济/通信/观测）+五种子主动姿态+协议对齐主动做（A2A 对齐 Google A2A ~1周+支付选型）。
外部六路调研已完成（Vend 全貌/A2A 150+/AP2 商户/治理萌芽/内容市场/经济真空）。
详见记忆 org-os-first-mandate-20260912。

## 新 session 首步清单
1. ④ 协议对齐开工（A2A AgentCard/.well-known/任务生命周期）
2. 组织 OS 白皮书 v0（六层骨架，治理层材料最厚）
3. 用户亲自去飞轮对话框推数据管线拆单（主线唯一推进路径）
4. 等待项：飞轮回 212/205-207 的实质动作（v5 patch 自上）/v7 链对 platform_proposals 117 approved 的消化
