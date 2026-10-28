# 全框生产快照 2026-09-11 11:42

## 四框 git(24h)
- **flywheel**: 27 commits · goals=GOALS.md · FRAME=✗未落
  - 00:17 docs(loop): 00:2x 轮——A线11/50盘21G,B线双200,纯值守
  - 23:17 docs(loop): 23:2x 轮——仲裁器文章吸收沉淀(G1口径锁定),A线10/50,B线双200
  - 22:17 docs(loop): 22:2x 轮——A线9/50盘18G,B线双200,r3产出上墙金标准达成
- **v5**: 8 commits · goals=GOAL_ACTIVE.md · FRAME=✗未落
  - 21:19 feat(vtf): mt v2.1/2.2 分层判据重判定谳——base意图层80%,墙=边界抑制缺失+签名墙(EQ-005 verified)
  - 19:49 chore(vtf): EQ-002 verdict 更新——daemon 重启完成,reason 生产实证待首条 legacy 行
  - 19:46 feat(vtf): mt v2首跑判决——三臂0发射,行动签名墙在最小任务复现(EQ-005立案)
- **compass**: 8 commits · goals=(无专属,看仓内 docs) · FRAME=✓
  - 22:03 docs(marketing): 直邮第二批草稿(Di Wu·LongMemEval 一作判分卫生钩子/Haitao Li·Awesome-LLMs-as-Judges 收录钩子)
  - 21:38 docs(marketing): dev.to v3 主帖发布落地(PUT 200·published_at 13:36:53Z·URL 已记)——当日 GitHub 资产配套(v
  - 21:23 chore(release): v3.2.0 — sealed evidence release (VerifyPack v0.2 + Reproducibility Wall +
- **platform**: 16 commits · goals=docs\GOAL_STACK.md · FRAME=✓
  - 22:56 fix(loop): SLA 执法时钟 utcnow→Asia/Shanghai——与 org_mailbox naive 本地时钟对齐,根治判定整体偏晚 8h
  - 22:19 docs(handoff): platform_loop 时区错位 bug 入账——utcnow vs Asia/Shanghai 混写,SLA 判定整体偏晚 8h,206/207
  - 21:23 docs(handoff): SLA 链实测勘误——205 早经 notify 在 takeover 池,206/207 21:27 到期未过线;executed_failed 8

## 云关键表(经 backend API 只读)
- ssh: connect to host 43.160.239.61 port 24860: Unknown error

## 判读口诀
- 判断组织状态以本快照+各框 GOALS 为准,勿拿单框度量外推全景;
- 决策卡/发函前:先查 ledger_latest 有无同主题更新拍板(>48h 未决卡默认过时);
- 快照缺失某框=该框 24h 零 commit(正常休眠,不是死亡)。