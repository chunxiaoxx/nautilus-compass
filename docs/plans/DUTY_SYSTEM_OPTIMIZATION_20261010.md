# 值守系统优化方案 v0(2026-10-10 深夜 · 源自 daemon 事故+LOOP 首夜复盘)

> 三层:今晚立即执行 / 明天开局执行 / 机制设计候评估。每条标注来源教训。

## A 层 · 立即执行(不依赖 daemon)

- **A1 发函前置检查清单**(教训:agent 框 400 发后才知):发组织信箱前查白名单台账(五框坐标 memory)——已入五框坐标 memory 补录 ✓
- **A2 跨框投件惯例认知刷新**:_INBOUND 模式是五框一年惯例非新发明——已入 memory ✓
- **A3 数学自洽检查**(勘误 9):PRECOR 发布 checklist 增"逐行 agreement×n 与 flips 整除互验" ✓(已入 LOOP_RETRO)

## B 层 · 明天开局执行(daemon 稳定后,约 10 分钟)

- **B1 watchdog 恢复**:`powershell Enable-ScheduledTask -TaskName 'compass-watchdog'`(+ verdict-evidence 同)——今晚为断循环临时禁用;
- **B2 daemon_start.sh 进程管理统一**(python3.13 幽灵根治):进程匹配改 `python3*` 通配+PID 文件双写;
- **B3 rerank 重开评估**:隧道 keepalive 已重启→remote 实测 3 连通→双开关重开(验收方案 RERANK_ACCEPTANCE_V1 在档);
- **B4 终检正日 18 项**。

## C 层 · 机制设计(候评估,不急)

- **C1 真·定时唤醒**:评估 ScheduleWakeup/CronCreate 让"值守"名副其实(LOOP 首夜 62 轮全靠用户消息推动的差距);若启用,须配"无事件静默"规则防打扰;
- **C2 轮次预算**:LOOP 模式每 25 轮强制中复盘+建议开新会话(长会话稀释教训);
- **C3 审计岗载体重设计**:独立只读线保留,输出改"值守轮附载审计段"(替代信箱自函错配);
- **C4 hook timeout 永久化**:settings.json UserPromptSubmit timeout=120s(已改 ✓,防再挂)。

## 自查一句

本档自身遵守卡帕西规范:一页纸/分层/可执行/每条有来源教训。

—— compass · 值守优化方案 v0 · 2026-10-10 深夜
