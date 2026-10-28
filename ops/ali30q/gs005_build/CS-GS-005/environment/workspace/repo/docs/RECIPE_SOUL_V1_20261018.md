# 生产配方卡 · soul(2026-10-18 锁版)

> 章程(docs/PRODUCTION_CHARTER_V1_20261018.md)执行件。红线:改动默认拒绝,走变更审批才许动。

## 最佳态锚定
- **时间点:2026-09-23 ~ 09-29**(T1 ¥0.01 端到端 PASS/jury 7/7/tools 工具箱开放/信箱 12h 步0 回执/无熔断)
- 2026-10-18 修复后恢复至该态(等价配置:850 dict 兼容 commit 517c64356)

## 配置快照(锁版)
| 件 | 锁定值 |
|---|---|
| 部署基座 | origin/soul-distill-deploy(ExecStartPre fetch+reset --hard,workspace=/home/ubuntu/nautilus-soul-workspace) |
| 主服务 | nautilus-soul.timer :00/:15/:30/:45(one cycle);consumer/executor 同频 |
| 模型 | k3-256k 主力(9/25 MiniMax 漂移切换后口径) |
| 熔断 | 无 pause(.soul-pause 不存在=正常态);breaker 只断 ship 保回函 |
| PR 门 | draft-PR 永不自动合,人审(10/18 PR#317 已合并出清) |

## 班表
- 主循环 15min/轮:步0 收信→选 goal→ship 或回函
- 信箱积压:旧函不触发回执(12h 步0 回执心跳),消费靠主循环逐轮

## 红线(违反=事故)
1. 改 soul 代码/配置默认拒绝;动前必过用户批
2. 熔断恢复唯一配方=pause+failure-state 双移(9/24 验证,10/18 复用)
3. 判活必查 `journalctl -u nautilus-soul.service`(Finished 轮),**信箱心跳≠活性**
4. 云端基座冻结=事故(10/13-10/18 教训):push 后 15min 内 ExecStartPre 自动生效,超 1 轮未生效即查

## 值守接线
liveness `soul_daemon` 锚(6h 绿轮=0 即红)+`members_active` 锚(72h 实质函)自动盯,红灯函 4h 去重。
