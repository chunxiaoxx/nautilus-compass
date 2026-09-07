# P-0003 · watchdog 日志每日汇总卡

- 日期：2026-09-07
- 来源：跑批监控节奏约定（早间 8 点汇总检查）+ cron-durability-lesson 记忆（跨夜监控必须 durable cron）
- 级别：L2（新增定时任务+接飞书发送链路）
- 状态：draft

## 问题
watchdog 每 10min 记 free/DONE/FAIL 到日志，但要人 ssh tail 才知道；异常（worker 全退/盘逼近/FAIL 新增）不会主动找人。

## 方案
每日 08:00 durable cron 跑汇总脚本：解析 watchdog.log 近 24h → DONE 进度/增速、free 趋势、FAIL 增量、worker 存活 → 正常发简报、异常（worker 全退/free<15G/新 FAIL）走现成 _send 脚本经 cloud 中继推飞书 p2p。

## 验证
连续两天 08:00 收到卡片，内容与 ssh 实查一致（独立验证：抽查一天数字对账）；人为停一个 worker 验证异常告警触发。

## 预期收益
每天省 1 次 ssh 巡检（≈10 分钟）；异常响应从"人找问题"变"问题找人"（分钟级 vs 小时级）。

## 风险与红线
cron 必须 durable（非 session-scoped，9/1 断档教训）；飞书推送每天仅 1 条+异常加发，防打扰；脚本只读+经 cloud 中继白名单通道。
