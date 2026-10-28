# 全框生产快照 2026-09-05 09:07

## 四框 git(24h)
- **flywheel**: 32 commits · goals=GOALS.md · FRAME=✗未落
  - 01:59 feat(s9): Open100K 外购池三线接入全闭环——body(190帧)/头视(496帧,换样后过,首样2/2 segfault 诚实记录为个例)/EgoPro(268帧
  - 01:51 feat(s9): 系统页能力清单新增 H5 采集员侧 v0 行——本地冒烟 PASS（登录门控 307/三页路由实测响应），试点 3-5 人待设备+签约；诚实标注本地冒烟≠部署
  - 01:19 feat(s9): Open100K 外购池接入实证——EgoStandard-body 样本（8.9MB/6.3s）bucket 匿名下载→mcap2lerobot rc=0（1
- **v5**: 12 commits · goals=GOAL_ACTIVE.md · FRAME=✗未落
  - 00:34 feat(swebench): B组双脑并行评测——b_group_v2(cloud/local 双模式·即判·断点续跑·空文件轮询修复)+b_group_final(统一收编兜底
  - 20:40 feat(eval): 500题 worker 改队列模式——mkdir 原子领任务+.done 防重,3路并发不绑 stride,死批清掉自动重领
  - 20:25 feat(eval): 补跑废批次脚本——扫 preds patch<8 的批清掉重解+判分(新 key 到位后恢复全速用)
- **compass**: 70 commits · goals=(无专属,看仓内 docs) · FRAME=✓
  - 09:07 docs(paper2): 操作单标题补完整副题+作者字段说明(tex 带机构/表单只填人名)
  - 09:02 docs(paper2): 逐字段提交操作单(照抄即提交)——八字段值+上传单文件说明+ID 回填四处;gitignore 补 docs/papers/*.aux
  - 08:53 docs(marketing): tools/list 收敛执行记录入档——17→8 上线+admin 假设纠偏教训(分 token 类型实测视角)
- **platform**: 14 commits · goals=docs\GOAL_STACK.md · FRAME=✓
  - 08:58 chore: 卫生战役第二批——363 未跟踪归类落地(A+B+C 共 357 项入库+D/E 五规则入 gitignore)
  - 00:42 chore: 卫生战役——摘 5.4 万项死代码备份跟踪+_gitignore 修冲突标记补规则
  - 00:18 mailbox: 收 flywheel 9/5 进展同步函(注册确认+承运方案接口投影请求)

## 云关键表(经 backend API 只读)
- mailbox_24h=10 last=2026-09-05
- capability_recent=[('nautilus-prime-001', datetime.date(2026, 9, 3)), ('nautilus-prime-001', datetime.date(2026, 9, 3)), ('nautilus-prime-001', datetime.date(2026, 9, 3))]
- cards_undecided_sent=3
- ledger_latest=['decision-paper2-judge-taxonomy-20260904', 'decision-frame-compass-20260904', 'decision-gangqu-gov-perspective-20260903', 'decision-dispatch-commercial-terms-20260903', 'decision-quote-v02-reprice-20260903']
- agents_heartbeat_1h=0

## 判读口诀
- 判断组织状态以本快照+各框 GOALS 为准,勿拿单框度量外推全景;
- 决策卡/发函前:先查 ledger_latest 有无同主题更新拍板(>48h 未决卡默认过时);
- 快照缺失某框=该框 24h 零 commit(正常休眠,不是死亡)。