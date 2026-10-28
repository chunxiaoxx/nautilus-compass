# 全框生产快照 2026-09-18 09:07

## 四框 git(24h)
- **flywheel**: 28 commits · goals=GOALS.md · FRAME=✗未落
  - 08:04 feat(loop): 基线读数+欠训练判定——底座1.515vs微调1.544窄带同分布=1500步仅7%epoch未生效;闭环验证步首次实战抓住训练步问题;steps15000
  - 07:24 fix(loop): 评测LoRA加载真bug排雷——from_pretrained不认纯adapter目录(首评微调读数无效=伪数据险情,不轻信自报拦下);修复=PEFT原生挂载
  - 06:54 docs(loop): RoboCap四启示(设备路线重估/验证叙事同盟/手部标注三基准/GSI生态L1机会)+训练27%@4.92步/s提速
- **v5**: 23 commits · goals=GOAL_ACTIVE.md · FRAME=✗未落
  - 06:48 fix(org): 漏网投函路径补X-API-Key——org_protocol_loop+kairos_rescue(391)
  - 06:46 data(exam): 判卷包judge_pack——5题commits/paths/运行命令/产出全文(389索要)
  - 06:42 feat(rsi): ATTRIBUTION_MAP补pf_claim_bounty——首考期新面孔归因(×5实证)
- **compass**: 20 commits · goals=(无专属,看仓内 docs) · FRAME=✓
  - 07:10 docs(wall): 首考成绩单挂墙——README自家数字段+官网商业章增1/5 agree首考行(难看数字照登纪律产品化);已部署验证
  - 07:09 feat(wall): Assay首考成绩单——agree1/disagree4/0:914b三门全过72passed唯一agree;355a/a379产出自带语法错误(think
  - 06:51 feat(benchmarks): BC1出题生成器v0——TDD 5用例绿(确定性/形状+判据引用白名单/植入违例可判/环节-判据映射/切分不交+manifest);六题型落地(
- **platform**: 18 commits · goals=docs\GOAL_STACK.md · FRAME=✓
  - 09:02 fix(jarvis): @直达指令带task_meta——进哨兵E4超时监控(回执承诺与执法闭环对齐,测试17过)
  - 08:02 docs(examhall): 首考成绩单跨仓留档(全球第一份被审计RSI转录判分:agree1/disagree4,难看数字照出)
  - 06:56 feat(converge): 接口收口两件——哨兵E4b超时自动催办函(消人肉追函)+贾维斯@框直达指令(from=user单入口指挥,测试28过)

## 云关键表(经 backend API 只读)
- mailbox_24h=71 last=2026-09-18
- capability_recent=[('nautilus-prime-001', datetime.date(2026, 9, 16)), ('nautilus-prime-001', datetime.date(2026, 9, 16)), ('nautilus-prime-001', datetime.date(2026, 9, 16))]
- cards_undecided_sent=3
- ledger_latest=['decision-card-sendtest-20260915', 'decision-v5-selfrec-211', 'decision-embodied-infra-swhw-20260907', 'decision-paper2-judge-taxonomy-20260904', 'decision-frame-compass-20260904']
- agents_heartbeat_1h=0

## 判读口诀
- 判断组织状态以本快照+各框 GOALS 为准,勿拿单框度量外推全景;
- 决策卡/发函前:先查 ledger_latest 有无同主题更新拍板(>48h 未决卡默认过时);
- 快照缺失某框=该框 24h 零 commit(正常休眠,不是死亡)。