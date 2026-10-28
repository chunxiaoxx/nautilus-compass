# 存量拔草台账 V1(2026-10-14 · 四步方案④)

> 判据:消费方(在用?)+主链位(挂靠?)+活性实测。四档:✅活 / 🧊冻结档案(留数据停运行时)/ 🔴候拔(证据齐候拍)/ 已拔。
> 配套:MAINCHAIN_MAP_V1(资产挂链)/ARCHITECTURE.md(全景)。刷新:每月一次,或退役事件发生时。

## 已拔(本日 ✅)

| 项 | 证据 | 动作 |
|---|---|---|
| 本机 8 死任务(gwfix×4/r81/r83/r81_resume/compass-watchdog) | next 全空;last 10/5-10/6 一次性修复时代;compass-watchdog 9/11 停 | 8/8 schtasks 删除(10/14) |
| 失效 MCP×3(gmail/blockchain/nautilus-compass) | 连接失败重连循环 | ~/.claude.json 停配(备份 .bak-20261014-mcp) |
| 旧 happy 守护(PID 23844) | 10/6 起双份守护重复 | 已杀,省 1.6GB |

## ✅ 活(实测热,勿动)

DB 20 表近 7 天有写入:agent_tool_calls(17.6万写)/platform_agents/skill_registry/platform_audit/agent_messages/org_mailbox(4724 封)/conversation_memory/ledger×3/bounties/stakes/**assay_submissions(16 条=主链提测在用)**/proposals。timer 30 个全 active(核心:platform-loop/capability-settle/order-lifecycle/fuel-settle/soul 系/compass 系/v5-cron-tick)。

## 🧊 冻结档案(数据留,不进运行时决策)

| 项 | 量 | 依据 |
|---|---|---|
| atoms/vec_atoms 表 | 462 行 | 记忆实验产物,30 天零 analyze |
| platform_proposal_votes | 455 行 | 提案投票史,保留审计 |
| platform_agent_lineage | 145 行 | 血统档案 |
| fde_verdicts | 3663 行 | 判分范式档案(9/2 冻结口径) |
| LOOP_STATE_SSOT 历史增量 | — | 双版本并存+考古注(10/14 合并) |

## 🔴 候拔(证据齐,候用户拍)

| # | 项 | 证据 | 拔法/风险 |
|---|---|---|---|
| 1 | ~~fde-janitor.timer~~ | **已拔 10/14(用户拍)**:stop+disable,list-timers 零残留,unit 文件保留 | — |
| 2 | ~~ecc-fde-scanner.timer~~ | **已拔 10/14(用户拍)**:同上处置 | — |
| 3 | fde.nautilus.social vhost+/start 教材面 | FDE 退役;/start 或有历史学员;主链判读卡已迁 org 站 | 拍板后 301 归档或保留静态 |
| 4 | org 驾驶舱页 | 档案 9/3 标"0 访问待退役";判读卡/L2 样例已由 org 域静态承载(保留 org 域本身) | 仅下线驾驶舱页;org 静态站保留 |
| 5 | workbuddy 对外 MCP | 8/29 首调后 0 复调(档案) | 下线或挂着(成本≈0,列观察) |
| 6 | nautilus-pipeline.timer 内容待考 | 30 timer 之一,职能未核 | 先查 unit 内容再定,不盲拔 |
| 7 | crm.chunxiao.wang / hr-chunxiao / x-chunxiao / zenmind-web-intl 四 vhost | 个人/他框域,平台不判死活 | 移交各域自查,平台不拔 |
| 8 | DB 历史层(conversations/users/oauth_*/simulation/academic/multimodal,4-5月) | 档案标历史 | 冷备导出后可 DROP(单独拍,涉数据不可逆) |

## 原则回顾(防复活)

- 拔=删运行时(timer/进程/端点),数据一律留档不删
- 复活判据:主链图出现新节点需要它,否则登记不重建
- 每月对账:候拔未拍项滚动复核(下次 11/14)

—— platform · 2026-10-14 · 本日拔 8 任务+3 MCP+1 重复守护;候拍 8 项
