# 全框生产快照 2026-09-20 09:07

## 四框 git(24h)
- **flywheel**: 194 commits · goals=GOALS.md · FRAME=✗未落
  - 09:06 docs(mailbox): id484降频协议第29轮一行留痕(r29)——第33次同函触发:探针组照跑全绿:来函全文与归档件L7-19空行折叠归一化diff实测IDENTICA
  - 08:58 docs(mailbox): id546渠道窗扩项MCP/A2A去留三选第14次同函触发一行留痕(r14)——探针组照跑全绿:来函全文与归档件L8-16双向归一化diff实测IDE
  - 08:53 docs(mailbox): id536渠道方案独立窗第15件留痕(r15)——第15次同函触发:探针组照跑全绿:来函与在案逐点比对零新增(标题/问题句/正本指针/四件各节/征求段
- **v5**: 35 commits · goals=GOAL_ACTIVE.md · FRAME=✗未落
  - 08:09 fix(_heuristic_score): raise cap 0.55→0.65+evidence so bootstrap passes 0.6 threshold
  - 04:54 fix(swe): 段1启发式定位兜底——problem嵌测试致LLM当修复任务回代码(04:25留痕实证),改抽original函数名在problem中出现者为定位(零LLM·毒
  - 03:09 test: gate_trace默认路径语义更新(env缺失=写默认不再断言无文件·delenv压过conftest的污染源)
- **compass**: 22 commits · goals=(无专属,看仓内 docs) · FRAME=✓
  - 05:32 feat(wall): 周期2收官——a379 agree(19tests PASS),第四点定格3.5/5;趋势线四点:1/5→3/5→3.5/5;函数级管线0/60→两题两卷=
  - 04:04 feat(wall): 周期2趋势线第四点·355a disagree(接近)——函数级管线首胜(0/60→两轮过门)但修复点回归(mt 32000→8000回退);g3 CLEA
  - 01:59 feat(wall): 三臂v5臂成绩单——1/1/1(q2 43tests PASS/q3产出语法错/q1依赖缺失NC);判材自含格式缺口入规范v2;辅证链勘误披露;SDK签VA
- **platform**: 22 commits · goals=docs\GOAL_STACK.md · FRAME=✓
  - 06:37 feat(sentinel): E8三臂降级保险丝——72h零认领自动降两臂+公布映射(预注册规则自动化,免到期人肉)
  - 06:18 docs: 周价值简报v0底稿(9/19拍板件)——真值盘点111提交/16判分/64债清/3事故根治+效果归因+诚实账,今晚飞书首发
  - 06:14 fix(sentinel): E4误催根因=task_meta JSON null标量过SQL过滤——非任务函(task_type/chain双无)Python层挡下

## 云关键表(经 backend API 只读)
- mailbox_24h=118 last=2026-09-20
- capability_recent=[('nautilus-prime-001', datetime.date(2026, 9, 16)), ('nautilus-prime-001', datetime.date(2026, 9, 16)), ('nautilus-prime-001', datetime.date(2026, 9, 16))]
- cards_undecided_sent=3
- ledger_latest=['decision-card-sendtest-20260915', 'decision-v5-selfrec-211', 'decision-embodied-infra-swhw-20260907', 'decision-paper2-judge-taxonomy-20260904', 'decision-frame-compass-20260904']
- agents_heartbeat_1h=0

## 判读口诀
- 判断组织状态以本快照+各框 GOALS 为准,勿拿单框度量外推全景;
- 决策卡/发函前:先查 ledger_latest 有无同主题更新拍板(>48h 未决卡默认过时);
- 快照缺失某框=该框 24h 零 commit(正常休眠,不是死亡)。