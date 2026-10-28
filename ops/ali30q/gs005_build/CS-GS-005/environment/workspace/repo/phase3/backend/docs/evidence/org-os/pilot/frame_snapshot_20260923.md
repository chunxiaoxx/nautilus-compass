# 全框生产快照 2026-09-23 21:55

## 💰 商业读数(钱箱)
- biz_orders_total=4 paid_sum=10.0 quoted_sum=20.0
- biz_platform_orders=[('fulfilled', 5)]
- biz_recent=[('ORD-8DD5011D', 'completed', 5.0), ('ORD-AE87E42D', 'quoted', 0.0), ('ORD-11457CEA', 'quoted', 0.0)]
- biz_dcr_real=[('pending', 3, 629900)] (分,tag!=test口径)
- biz_dcr_e2e_firstpay=('HR202609231609176F0DE7', 'refunded')

## 四框 git(24h)
- **flywheel**: 92 commits · goals=GOALS.md · FRAME=✗未落
  - 21:14 docs(ledger): Gen-HumanEgo 登记(第三体检源,MCAP 同管道复用,Training-Ready 叙事词)+四臂第五发健康+GR00T 封存留痕
  - 17:05 docs(delivery): 智元体检报告对外摘页版——三句结果/采购方意义/联系方式;外发三道自查通过(零内部术语/零未验证声明/数字与v0一致)
  - 16:13 docs(yuanli): 轻问话术v2——试检提案写入(20-50条/5工作日/首批免费)+智元报告随发+9/26读数推送三钩递进(用户拍板组合执行)
- **v5**: 10 commits · goals=GOAL_ACTIVE.md · FRAME=✗未落
  - 15:37 feat(judge): exam3arm补判包——9卷abandoned但output全在(927-5263字符·前缀病drain 9/19定谳)·manifest含判分通道(机
  - 15:13 feat(e1): 判分器适配dry-run(#877素材v1·16条)——双极性引擎(正反一致才valid·全迎合invalid不入多数决)+正式schema兼容(arm/rat
  - 14:41 docs(portal): 承#875首件——exam-signup模板v2(密钥三步流并入:考生版生成/公钥贴issue/验签握手+私钥红线)·五字段不动·待平台照落nautil
- **compass**: 48 commits · goals=(无专属,看仓内 docs) · FRAME=✓
  - 21:53 chore(loop): 轮11补——信箱查询故障实测记录+Discord 快查无回帖
  - 21:16 chore(loop): 轮11——L9 关账(模板并版核毕)+v2 话术单点试验 T4 发出
  - 17:19 docs(outreach): 话术 v2 人味版——T1 slop 批评实弹反馈入库(≤120 词/无粗体/工程师口吻+参考改写)
- **platform**: 32 commits · goals=docs\GOAL_STACK.md · FRAME=✓
  - 21:53 feat(ops): 日报钱箱节接DCR真单——biz_dcr_*(tag!=test口径直查,#812方案A)+首笔端到端单终身态追踪;实测refunded 1笔1分入首屏
  - 21:22 feat(portal): www卡2入口卡上墙——静态单页替换SPA壳(Task Marketplace旧文案撤,七个月STALE治;素材compass890 verbatim只
  - 15:53 docs(E1plus): 用户署名'批准按函执行'——邀请函已投#884(24h回执窗);判分独立正式生效待v5回执

## 云关键表(经 backend API 只读)
- mailbox_24h=91 last=2026-09-23
- capability_recent=[('nautilus-prime-001', datetime.date(2026, 9, 16)), ('nautilus-prime-001', datetime.date(2026, 9, 16)), ('nautilus-prime-001', datetime.date(2026, 9, 16))]
- cards_undecided_sent=0
- ledger_latest=['decision-card-sendtest-20260915', 'decision-v5-selfrec-211', 'decision-embodied-infra-swhw-20260907', 'decision-paper2-judge-taxonomy-20260904', 'decision-frame-compass-20260904']
- agents_heartbeat_1h=0
- agents_hb_7d=0 agents_hb_30d=1
- soul_letters_48h=1 soul_last=2026-09-23
- delivery_clock_red_live=['nautilus-v5', 'v7-orchestrator', 'unknown', 'kairos', 'vc_daily', 'nautilus-prime-001', 'v7-telegram'] (历史死号自滤)
- gov_pending=50 oldest=2026-09-01 older3d=46
- tasks_open_chain=26
- mailbox_live_deadlines=[(756, '[P1矿终账·承#742/#751/#753] Op-V5 定稿:56 条真修+', '2026-09-23'), (844, '[开窗导航·5分钟行动单] 醒后积压按序:#801/803今日午前评审·#806', '2026-09-23'), (868, '[修后回函][flywheel] id865重投bug已修——两轨合一(409解', '2026-09-23'), (785, '[收讫] L3层间比值作废正确——跨agent聚合陷阱,记判据库候选', '2026-09-23'), (667, '[五件套] v5侧 P1/P3 已备齐(9/23 T1 并案验收材料·两 com', '2026-09-23')]
- undecided_cards_detail=[]

## 经营对账·资产探活(外部触点健康,9/21 外发双杀教训固化)
- www.nautilus.social: 200 OK
- dev.to@chunxiaoxx: 200 OK
- github/nautilus-compass: 200 OK
- data.nautilus.social: 200 OK
- HN@chunxiao: 200 OK
- Reddit@JaneRoberts93: 200 OK

## 经营对账·云心跳对账(timer 活≠产出活)
- systemd timers: 组织域周期型 18 个;超 24h 未跑/无记录: 无✅
- cron do_one_thing 产物 log: NEVER(权限失败未修,证据函#788 呈 v5;修后本读数自动转绿)

## 经营对账·差距判读
- 🟡 在途函 deadline: [(756, '[P1矿终账·承#742/#751/#753] Op-V5 定稿:56 条真修+', '2026-09-23'), (844, '[开窗导航·5分钟行动单] 醒后积压按序:#801/803今日午前评审·#806', '2026-09-23'), (868, '[修后回函][flywheel] id865重投bug已修——两轨合一(409解', '
- 🔴 agent 池 7d 零活跃(354 注册全休眠,干活的是六框身份;外部池=待引流资产,勿当现役)
- 🔴 交付矩阵 RED 活体: ['nautilus-v5', 'v7-orchestrator', 'unknown', 'kairos', 'vc_daily', 'nautilus-prime-001', 'v7-telegram'] (历史死号自滤)(A2-P1 矩阵;超 48h 零交付——断供处置线候选,协议 V1 §5)
- 肌肉抽验跳过(list index out of range)

## 判读口诀
- 判断组织状态以本快照+各框 GOALS 为准,勿拿单框度量外推全景;
- 决策卡/发函前:先查 ledger_latest 有无同主题更新拍板(>48h 未决卡默认过时);
- 快照缺失某框=该框 24h 零 commit(正常休眠,不是死亡)。
- 复盘新教训:必过 docs/IMMUNE_LEDGER.md 五类强制位找落位,无位明示'当前无肌肉'——文档不是肌肉,禁只写文档结案。