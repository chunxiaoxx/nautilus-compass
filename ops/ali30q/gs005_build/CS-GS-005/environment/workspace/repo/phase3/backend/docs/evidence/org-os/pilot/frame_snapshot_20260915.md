# 全框生产快照 2026-09-15 09:07

## 四框 git(24h)
- **flywheel**: 35 commits · goals=GOALS.md · FRAME=✗未落
  - 08:16 docs(loop): 08:1x 轮——Calibra调研落档+转换body17/32(head21达标),B线双200,平台面静默
  - 07:54 docs(research): Calibra调研——机器人数据集体检新工具(冻结帧/抖动/重复/标定漂/损坏五检+核心集选择);对表六道闸:三项缺口补闸②,核心集接闸⑤,误报未测
  - 07:20 docs(loop): 06-07轮——head线达标(补批9/9零失败,21 DONE)+body补批conv4起跑(10小帧),body主批11/25,B线双200
- **v5**: 12 commits · goals=GOAL_ACTIVE.md · FRAME=✗未落
  - 00:50 feat(rsi): c 方案无罪释放——chat 口历史首次真工具发射(kernel-chat n_tools=1 succ)
  - 00:43 fix(rsi): ticket_gen --post 换行转义终修(chr(10) 直写)
  - 00:42 feat(rsi): watchdog 循环死检测(治休眠假活)+ticket_gen 直连投递模式
- **compass**: 16 commits · goals=(无专属,看仓内 docs) · FRAME=✓
  - 00:38 docs(license+charter): 用户双拍板落地——LICENSE A4 验证服务独立口径(A2 托管上限仅指记忆功能)·CLAUDE.md 报数纪律(预注册判据档+非
  - 00:00 docs(marketing): 验证价值 playbook+商业化路径——免费复算入口已开(#166 官方回复)·四路径排会话·第一付费 SKU=发布前独立审计($99-299 
  - 23:27 docs(soul): 提案过质量门(v7-llm-judge approved)——评审摘要入档+护栏2采纳'占位句改空白'建议;draft PR 落点待平台回写
- **platform**: 21 commits · goals=docs\GOAL_STACK.md · FRAME=✓
  - 00:43 ops(mailbox): 贾维斯v0征求V5意见函——callback加im.message形状分发,9/5纪律先问后做
  - 00:42 docs(t15): 判读首轮——假设两轴化(启动/方向),mt v3 入账+判据冻结段(周节奏 1/52)
  - 00:12 fix(llm): thinking-only 自适应重试——2x max_tokens 一发,治 soul fw-tpl 32k 爆思考(正本+副本 verbatim 同步)

## 云关键表(经 backend API 只读)
- mailbox_24h=26 last=2026-09-15
- capability_recent=[('nautilus-prime-001', datetime.date(2026, 9, 3)), ('nautilus-prime-001', datetime.date(2026, 9, 3)), ('nautilus-prime-001', datetime.date(2026, 9, 3))]
- cards_undecided_sent=3
- ledger_latest=['decision-card-sendtest-20260915', 'decision-v5-selfrec-211', 'decision-embodied-infra-swhw-20260907', 'decision-paper2-judge-taxonomy-20260904', 'decision-frame-compass-20260904']
- agents_heartbeat_1h=0

## 判读口诀
- 判断组织状态以本快照+各框 GOALS 为准,勿拿单框度量外推全景;
- 决策卡/发函前:先查 ledger_latest 有无同主题更新拍板(>48h 未决卡默认过时);
- 快照缺失某框=该框 24h 零 commit(正常休眠,不是死亡)。