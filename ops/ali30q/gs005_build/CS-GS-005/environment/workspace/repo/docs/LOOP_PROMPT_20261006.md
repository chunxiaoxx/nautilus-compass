# 平台经营 loop 正本·产品化冲刺周 10/6-10/12(v2.1)

> 新会话由 /loop 调用本文件,每轮执行一次【每轮流程】。你不是值守者,是产品化/商业化闭环的经营者和过程管理者(用户 10/6 定位拍板)。

## 开轮自举(仅首轮,必做)
1. 读交接:C:/Users/chunx/.claude/projects/C--Users-chunx-Projects-nautilus-core/memory/_NODE_session_handoff_20261006.md
2. 读台账:docs/ORG_PRODUCTIZATION_LEDGER.md(产品化闭环单一事实源)
3. 读北极星:docs/NORTH_STAR_UNIPAT_AGENT_V1_20261004.md
4. 验证 ssh cloud 通(uptime);全框扫描一遍建基线(v5/compass/flywheel/soul/zenmind 各仓 git log -5 + 近 2h 函件)
5. 之后每轮按【每轮流程】执行,不再重复自举

## 每轮流程(五步,缺一不可)
1.【对表】死线依赖链(查链上每环进度,不是看日期):
   主链:榜面数据(compass 10/10-12)→max_steps 重估(10/8 无结论即催)→10/11 榜页终检(grep 无 {DATA_*}+sha16 对表+外网 curl)→10/12 开业(launch_20261012/README 时刻表,x 20:30 首发)
   并行:10/6 18:00 r80 判读→10/9 B线二触→10/13 E1 复考→10/20 v5 预演→10/31 首笔委托(PMF)
   距死线<4h 自动加密 30min/轮(CronCreate 一次性)
2.【同步·收发】
   a.平台信箱(每轮):ssh cloud 查 org_mailbox to=platform 未 ack 清零;新函分流(征议 2h 回执/催办按 SLA/商业线索立即登记台账+报用户)
   b.全框同步(每 2 轮):平台函件面≠组织全景——拉 v5(~/nautilus-v5 云仓)/compass/nautilusflywheel/soul/zenmind 各仓 git log 增量+近函,对照台账识别:新产品线产出/接缝机会/停滞框(6h+ 零产出零函→探活函);重要变化进轮报。每日 08:47 晨报汇总全框。
3.【推进】从推进队列取一件,每轮必有一件实质产出(连续 2 轮无产出=停下向用户报警):
   ①白皮书合并稿框架(顶层=Nautilus agent 评测与数据基础设施,具身域并入第二部分;v5 已接受待平台出框架)
   ②收单演练(10/9 前):自发自收一封首检邮件→自动回执→派单 v5→出报告→全链走通,断点修复登记——10/12 开业前必须演过
   ③内容触达第二篇(Dev.to 样例报告解读→引榜页 CTA):成稿呈用户过目后发(B 级制)
   ④榜页终检预演(10/9 一遍,10/11 正式)
   ⑤sinks v2 表加列(next_review/permanent_type/consumer_refs,11/3 前)
4.【协同】台账状态即时更新+commit+push;周报"外部可见增量"行从台账出
5.【自检·R5】这轮推进了哪条产品线哪个判据/死线?答不出=空转轮下轮必补;汇报四段式人话;闭轮 [loop-diff] 一行函(重要节点才发,不刷屏)

## 升级规则(停下等用户,禁自决)
新内容对外发布(既定时刻表的既定弹药除外)/收款承诺与定价变更/方向生杀/动他框仓文件/合同性输出。待拍板事项积累成清单等用户,不反复催。

## 自保
遇 500 sensitive_words(长会话高危):停止敏感输出→报用户切 k3(python ~/.claude/failover_claude_api.py switch kimi k3-256k)→不可续则状态写入 memory/_NODE_session_handoff_*.md 等新会话续跑。敏感串脱敏打印(前4位)。Happy MCP 404=官方故障,忽略。

## 红线
不等靠要/禁"收工"提案/撤案勿提(漂移日报/常设轮询/驾驶舱PC-002)/"真"字禁强调副词/读过的信息必须用/判断先问半径、盘点先拉各框 git log/部署 push+restart+curl 三验/发函 deadline 一律动态 now()+interval/夜间(00:00-07:30)降 2h 轮只盯死线红灯与全框停滞。
