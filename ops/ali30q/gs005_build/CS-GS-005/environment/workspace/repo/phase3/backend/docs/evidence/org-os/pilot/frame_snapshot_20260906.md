# 全框生产快照 2026-09-06 09:07

## 四框 git(24h)
- **flywheel**: 17 commits · goals=GOALS.md · FRAME=✗未落
  - 21:53 docs(s9): 投递 compass 复核函——手部位姿两条数据级发现(拇指自由度冻结/掌形系统性压扁)含独立复算最小路径与预期读数;QC掌形保真度判据候选提请讨论;诚实标注n
  - 21:48 feat(s9): 映射层④ ego2libero.py v0 实现并跑通——301维→LIBERO 7维纯几何映射(state=掌心pos3+掌系轴角3+开度1,action=d
  - 21:34 feat(s9): 映射层③点序考证完成——21组=拇指链{0,1,2,3}+四指平行链(食{4,8,12,16}/中{5,9,13,17}/无名{6,10,14,18}/小{7,
- **v5**: 13 commits · goals=GOAL_ACTIVE.md · FRAME=✗未落
  - 08:33 ship: customer landing page (markdown + html) - 280 bounties - 4616 NAU - customer_void st
  - 05:11 fix(v5): _resolve_portable 跨平台路径 + repo 别名查找
  - 23:17 docs(vendingbench): 首版报告——3 seed 有效数据(43臂 day21 启动售90件)+结构级驳回机制修复史+长跑结构从税变命的首版答案
- **compass**: 10 commits · goals=(无专属,看仓内 docs) · FRAME=✓
  - 20:17 docs: 发布物料一致性收口——对打嵌入披露补齐+CHANGELOG 追平 3.1.x
  - 19:26 fix(marketing): 19页路演版源文件重建(此前只有产物源md丢失)+版式升级v4+launch_plan补官方榜应答
  - 19:02 feat(marketing): 深讲版 PPT v4——35页压缩重构+市场价值页+两图重做
- **platform**: 6 commits · goals=docs\GOAL_STACK.md · FRAME=✓
  - 20:41 fix(backend): GET /api/agents 500 根因——get_agents_list_cached 返回形状漂移
  - 18:02 evidence: g2b1 k3 配方午后战果 13 件——8 实修 7 过(87.5%),4 fixture_broken 免费剔除
  - 18:02 mailbox: 催办 170-172 回函(三框零回函超SLA)+V5 cmd 改动知会——deadline 20:00 动态算

## 云关键表(经 backend API 只读)
- mailbox_24h=2 last=2026-09-05
- capability_recent=[('nautilus-prime-001', datetime.date(2026, 9, 3)), ('nautilus-prime-001', datetime.date(2026, 9, 3)), ('nautilus-prime-001', datetime.date(2026, 9, 3))]
- cards_undecided_sent=3
- ledger_latest=['decision-paper2-judge-taxonomy-20260904', 'decision-frame-compass-20260904', 'decision-gangqu-gov-perspective-20260903', 'decision-dispatch-commercial-terms-20260903', 'decision-quote-v02-reprice-20260903']
- agents_heartbeat_1h=0

## 判读口诀
- 判断组织状态以本快照+各框 GOALS 为准,勿拿单框度量外推全景;
- 决策卡/发函前:先查 ledger_latest 有无同主题更新拍板(>48h 未决卡默认过时);
- 快照缺失某框=该框 24h 零 commit(正常休眠,不是死亡)。