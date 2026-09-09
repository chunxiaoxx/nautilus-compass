# 9/10 Loop 持续行动清单(战略四优先级拍板后 · 日间值守+推进)

> Loop 每 30min 一轮。每轮先跑 A 组;然后按序推进 B 组未完成项(每轮一件);末尾一行状态写入本文档。
> 纪律同 9/8:不 push 未拍板改动/对外内容只起草/验证优于自报/需用户决策的记录不动手。
> 战略锚:`docs/plans/2026-09-10-compass-strategy-four-priorities.md`(P1-P4,排期冲突按此序)。

## A · 值守(每轮必做)

- [ ] A1 daemon ping(必须带 `\n`);死→看 `.cache/daemon.log` 尾部+watchdog 下轮自愈,连续 3 轮死才人工干预
- [ ] A2 landing 200
- [ ] A3 信箱 unread→ack;需回函的起草(等用户过目再投,死线件除外)
- [ ] A4 dev.to 监控:21:03 cron(04033a61)发第二篇后→确认发布成功+views;旧帖(4602572/4602276)评论增量;新评论→24h 内起草回复入台账(评论 API 死路,只起草用户贴)
- [ ] A5 GitHub stars 增量(基线 7)+ 我方 repo issue 检查

## B · 推进(按序,每轮一件)

- [ ] B1 🔴 **GPU 退租检查**(8/31 事故记忆:自动续费还开着,用户定策 ent 完成后退租防空扣)——查 651799/652509/654686 实例状态与计费,完成实验的实例列清单**报告用户拍板退租**(不自主退)
- [x] B2 22:00 收口会材料:**判据库 v0 骨架**(flywheel 五族判据 D/C/L/X/U + G1 几何卫生规则;schema 设计,判据必须可执行)→ `docs/criteria/` 草案
- [x] B3 22:00 收口会议程清单:①4 门判定器(数据侧)× VerifyPack CLI(验证方)拼管线正本 ②X1 金标 17.5% 入包门槛 ③G1 判官进判据库当外部锚 ④batch002(200 条)全流程分工
- [ ] B4 #46 手几何复算:仍 blocked-on-artifact(等 flywheel 产物路径二选一回函);信箱有回复即续
- [ ] B5 #33 T0-6 v3 帖起草收尾(发布等用户)
- [x] B6 Gmail REST 查新件(**Trajko 48h 窗口至 9/11**,9/9 已回信;gmail MCP 本 session 挂,走 REST 配方)

## 死线与事件

- **今日 21:03**:cron 04033a61 自动发 dev.to 第二篇(判分卫生学,key 在 `~/.claude/.cache/devto_key`)
- **今日 22:00**:VerifyPack MVP 收口会(flywheel)
- **9/15**:#48 三件套合入窗口(材料全齐:worktree+基线+预注册档)+ 旧入口退役 + watchdog + 12 内部 token 迁移
- **9/28**:flywheel G1 报告归档 → 解锁 P4 paper2 成稿

## 状态记录(每轮一行,倒序)

- 轮 10(05:1x 纯值守):pong ✅·landing 200 ✅·信箱 0·stars 7·dev.to 持平——全绿无事件

- 轮 9(04:4x 纯值守):pong ✅·landing 200 ✅·信箱 0·stars 7·dev.to 持平——全绿无事件

- 轮 8(04:1x 纯值守):pong ✅·landing 200 ✅·信箱 0·stars 7·dev.to 持平——全绿无事件

- 轮 7(03:4x 纯值守):pong ✅·landing 200 ✅·信箱 0·stars 7·dev.to 持平——全绿无事件

- 轮 6(03:1x 纯值守):pong ✅·landing 200 ✅·信箱 0·stars 7·dev.to 持平——全绿无事件

- 轮 5(02:4x 纯值守):pong(12516)✅·landing 200 ✅·信箱 0·stars 7·dev.to 持平——全绿无事件

- 轮 4 补(B6 解锁):后台 grep 找到本仓 gmail REST 配方(scripts/gmail_reauth.py+email_sender.py,token 在 ~/.gmail-mcp/)→ REST 查 3 天 inbox 8 封:**Trajko 9/8 ack=台账已处理那封,非新件,线状态正常(等他复我方 9/9 长信,窗口明早)**·另记两条待跟进:V5 eastworld outreach issue 回复(V5 线)/awesome-mcp-servers PR bot 通知(推广线)·配方已存 memory。**B 组全部清零,后续轮=纯值守**

- 轮 4(02:1x):A 组全绿持平。B5=v3 帖无实活(终检 9/6 已过,发布等用户,**🔴窗口 9/12 前仅剩 2 天**;paper2 链接后置回填)·B6=Gmail 检查 blocked-on-tooling(gmail MCP 本 session 挂,REST 配方定位超时,Trajko 窗口 9/11 前需查)→改推**判据库长肉(2887994)**:母版 A/B 层硬门槛 A1/A2/A3/B4 入库,注册表 9 条覆盖 batch002 验收全链,6 测试绿。B 组 A 项(值守类)全清,后续轮=纯值守+等外部输入(flywheel 函/用户拍板/21:03 发文)

- 轮 3(01:4x):A 组全绿持平(pong 12516/landing 200/信箱 0/stars 7/dev.to 持平 views 26+cmt 2)。**B3 完成(c753d46)**:收口会议程函草稿(待用户过目后投 flywheel)——五点增量逐条对表 v0.2 实现(direction 未采纳/prompt_ref+env_fingerprint+protocol_version+not_computable 部分缺/input 脱敏哈希+level 打印已实现)+T1-T8 议题+我方预填立场(verdict 映射/L3 先作能力声明位/判据库=v0.3 第一调用方)。B4(手几何 blocked)信箱无新函;B5(v3 帖)下轮

- 轮 2(01:2x):A 组全绿持平(pong 12516/landing 200/信箱 0/stars 7/dev.to 4602572 views 26+cmt 2)。**B2 完成(e1f32ba)**:判据库 v0 骨架——判据=VerifyPack claim 模板+gate 元数据,D2/D4/C4/X1/M2 五条可执行注册(引擎零改动,gate 在 build 侧,测试红→根因=引擎只吃 JSON 文档不吃 jsonl→修模板对齐非修引擎)·CATALOG_v0.md 正本(L 族 flywheel 无定义正本=22:00 议题·U 族待 batch002 复算脚本)·6 测试含端到端闭环+57 回归绿。B3(收口会议程)下轮

- 轮 1(启动轮):A 组全绿——daemon pong(12516)· landing 200 · 信箱 0 · stars 7/issues 31 持平 · cron 04033a61(21:03 发文)在场 · 撤文 4602417/4571717 公开 404 复验 ✅ · dev.to 4602572 views 26+cmt 2(最好成绩)。**B1 🔴 发现:658779(9/8 21:30 租的 4090)自动续费开着,今日 00:14 仍在续,~50h ≈ ¥82 已扣,¥1.65/h 持续烧**;30 实例中仅此 1 台 status=1,其余停机/结束;client 无 cancel_autorenew 方法(仅 release_instance/release_kept_disk)——**已报用户拍板,未动手**。B2(判据库骨架)下轮推进
