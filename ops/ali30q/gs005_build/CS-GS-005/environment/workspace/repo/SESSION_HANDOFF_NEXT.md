# 交接文档 · 新 session 起手读这个(2026-08-28 夜 · 平台框超长 session 收尾)

## 起手三步(按序)
1. 读 `LOOP_STATE_SSOT.md`(十二次增量止)+`docs/GOAL_STACK.md`(目标栈 v2 三台阶)
2. 读 `docs/DECISION_LEDGER.md`(决策分级试点进行中,B 级自决要落账)
3. 挂 loop:`/loop 1h` 用 GOAL_STACK 里的标准 prompt(栈项尽则降频)

## 当前等待项(全挂自动/外部,无一是平台可立即推进)
| 项 | 谁解 | 判据 |
|---|---|---|
| V5 executor 恢复排期(停机 8/25 起,让位 DPO) | V5(用户已拍发动机优先,DPO让位升级函已投) | supervisor ZERO→自动转绿 |
| 附件包(国曙 22 人 23 题原始提交,解锁 5 题结算+PII+QC v1/v2) | 用户(在台式机,10 分钟) | 用户提供路径→机器脱敏→qc_gate |
| 三台阶回执(deadline 8/29 22:00) | V5/compass/飞轮 | 仓根回函 |
| P1 实弹(ZERO→真派单) | 用户批(首次实弹=A级) | P0 观察 1-2 个真实 ZERO 事件 |
| 变体生成设计(矿藏破顶 100 题) | 新 session | 设计文档 |

## 已在产自动运转(无需人)
supervisor 30min(含 ZERO→派单 dry-run+死因分类 YIELDED✓)/三曲线自动计量/auto-verify daemon/V5 DPO 夜间流水线/飞轮 GPU 线/compass CHUNK_RECALL

## 新 session 首日清单(按 GOAL_STACK 栈序)
1. 晨报:三曲线+supervisor 夜间报告+V5 回执扫描
2. 变体生成设计(栈内最高优先可动项)
3. 台阶一判据检查(三曲线 7 天窗口从 8/27 晚起算,8/28 是第 1 天)

## 教训速查(本 session 新增)
- 越权红线:他框仓操作只传授权通知,永不代做(memory feedback-turf-v5-repo-20260828)
- NUL 字节不可作 subprocess 参数(ValueError 被 fail-soft 吞成假 UNKNOWN)
- 模型测试绿≠生产 schema 对(FK split-brain 查 pg_get_constraintdef)
- 别反复提收工:节奏由任务+用户意愿定(memory feedback-dont-keep-proposing-wrapup)
- 死因分类:git活跃≠生产活,判据要产量增量

## 关键文件索引
- 路线图:`docs/plans/2026-08-27-rsi-transfer-roadmap.md`(六线全图+摸底+固化度台账)
- 三台阶:`docs/GOAL_STACK.md`(阶段层)
- ZERO→派单设计:`docs/plans/2026-08-27-zero-to-dispatch-design.md`(v1.1 死因分类)
- 决策分级:`docs/DECISION_LEDGER.md`(试点 9/11 判)
- dogfood 设计:`docs/plans/2026-08-25-dogfood-supervision-wiring-design.md`(两票转常设)
- supervisor 产物:云 `phase3/backend/docs/evidence/supervisor/`(report+dispatch_recommendations)
