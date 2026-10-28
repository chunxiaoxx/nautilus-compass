# 全框生产快照 2026-09-19 09:07

## 四框 git(24h)
- **flywheel**: 38 commits · goals=GOALS.md · FRAME=✗未落
  - 08:42 docs(mailbox): id285 day0_smoke同函二十次值守复核REJECT维持(跨日第十六轮·本轮独立复算非沿用)——判据1实采样例不存在:docs/eviden
  - 08:10 docs(mailbox): id285 day0_smoke同函十九次值守复核REJECT维持(跨日第十五轮·本轮独立复算非沿用)——判据1实采样例不存在:docs/eviden
  - 07:44 docs(mailbox): id285 day0_smoke同函十八次值守复核REJECT维持(跨日第十四轮·本轮独立复算非沿用)——判据1实采样例不存在:docs/eviden
- **v5**: 10 commits · goals=GOAL_ACTIVE.md · FRAME=✗未落
  - 00:41 data(exam): 三臂题面×9变体——compass抽3题(q1 v5仓/q2 core/q3 compass仓)×3臂reserved
  - 22:20 feat(exam): 门反馈轨迹采集旁路——SFT/DPO燃料管道(错误即燃料落地件)
  - 22:16 docs(exam): 三臂实验设计——同题多agent能力图谱+跨谱系对照+SFT燃料(组织融合首验)
- **compass**: 9 commits · goals=(无专属,看仓内 docs) · FRAME=✓
  - 00:42 feat(protocol): §5b 验证者责任与挑战权——'承诺效力为零'的回应:误判=墙OVERTURNED同规格+退款+承担挑战成本+track record清零;挑战权属
  - 00:40 feat(protocol): Assay Protocol v0 公开+独立验签 CLI——协议一页(判据注册棘轮j=(m,τ,D)/验证包/三态回执/墙纪律/验证者纪律I3盲判
  - 00:35 feat(wall): 重考周期1终版——37a1补交卷16tests PASS,NC改判agree,终版agree3/disagree2/0,趋势线1/5→3/5(坏卷零上交);
- **platform**: 7 commits · goals=docs\GOAL_STACK.md · FRAME=✓
  - 18:32 fix(worker): _post_mail 409容错=幂等成功(审计trace重复不再崩整轮)
  - 18:03 fix(worker): v0.2——prompt走stdin防截断(442实证headless没取到函)+禁MCP明示+fail不ack防假清零;死信箱清零实为假象已识破
  - 16:32 fix(worker): 处理毕ack原函——防同函重复拉取重复执行(重复headless浪费+审计trace虽幂等)

## 云关键表(经 backend API 只读)
- mailbox_24h=82 last=2026-09-19
- capability_recent=[('nautilus-prime-001', datetime.date(2026, 9, 16)), ('nautilus-prime-001', datetime.date(2026, 9, 16)), ('nautilus-prime-001', datetime.date(2026, 9, 16))]
- cards_undecided_sent=3
- ledger_latest=['decision-card-sendtest-20260915', 'decision-v5-selfrec-211', 'decision-embodied-infra-swhw-20260907', 'decision-paper2-judge-taxonomy-20260904', 'decision-frame-compass-20260904']
- agents_heartbeat_1h=0

## 判读口诀
- 判断组织状态以本快照+各框 GOALS 为准,勿拿单框度量外推全景;
- 决策卡/发函前:先查 ledger_latest 有无同主题更新拍板(>48h 未决卡默认过时);
- 快照缺失某框=该框 24h 零 commit(正常休眠,不是死亡)。