# 复算预注册判据档 · 三道落带题(CS-507/511/513)

> 依据报数纪律(2026-09-15)/判分证据分层(2026-10-03)。复算者=compass 框(非该三题实现者)。
> 开工时间:2026-10-27 14:3x。判据只许更严,开跑后不得回改。

## 对象与来源
- 被复算物:v5 仓 `codesense/items/CS-507`、`CS-511`、`CS-513`(worktree codesense-a-fix,HEAD 77bf98f8)
- 复算环境:隔离副本(`/tmp/cs_recompute_20261027/`),`.venv-judge` 符号链接共用(含 14:23 修复的 astropy)
- 原因:产线框(v5 侧)14:28 仍在提交,按双写互踩纪律不在其工作区内跑判分

## 判据(全过=RECOMPUTE-PASS,任一不过=该项 FAIL 并留证)
- R1 红线:题目录含 `pytest.ini`(testpaths=tests)与 `task.toml`(ut_index 含 gating 标记)
- R2 坑版态:workspace 原样跑 ut_runner(--runs 3)→ gating UT 至少 1 条挂 且 score<1.0;坑版即满分=题目无效
- R3 金标态:solution 文件换入后 ut_runner(--runs 3)→ score==1.0 且三次全一致(deterministic);否则 GOLD-FAIL
- R4 ut_index 抽核:task.toml 声明的 gating UT 名在 tests/ 实文件中存在(裸名匹配)
- R5 防泄漏:`LEAK_SCAN_PASS` 标记在
- R6 读数核对:终表落带读数 vs `_s5/qwen*result.json` 原始分,按机械二值化(score==1.0→1,否则→0)比对;以 raw 为准,不一致照实记
- 每条结论标注 [实测]/[推断]/[不可验];不可验处给 upgrade_path

## 已知局限(诚实披露)
- 本会话开工前已读终表(非盲复算)。缓解:R2/R3 为结构性判据(不依赖读数),R6 用机械二值化规则,不做主观"吻合"判断。
- qwen 侧重跑不做(判据档不授权预算);R6 仅核已有 raw 产物与终表的一致性。模型侧复跑属 [不可验],upgrade_path=另批预算重发 run。

## 输出
`ops/ali30q/RECOMPUTE_CS507_511_513_20261027.md`(逐题逐判据+证据坐标)
