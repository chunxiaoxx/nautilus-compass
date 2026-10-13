---
name: orgfuel-ORGG-5f6cf57ecdf6cc5b-703e36f8e4
description: "判读档判例 DUTY_SYSTEM_OPTIMIZATION_20261010 · B 层 · 明天开局执行(daemo"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5f6cf57ecdf6cc5b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 DUTY_SYSTEM_OPTIMIZATION_20261010 · B 层 · 明天开局执行(daemon 稳定后,约 10 分钟)
## B 层 · 明天开局执行(daemon 稳定后,约 10 分钟)

- **B1 watchdog 恢复**:`powershell Enable-ScheduledTask -TaskName 'compass-watchdog'`(+ verdict-evidence 同)——今晚为断循环临时禁用;
- **B2 daemon_start.sh 进程管理统一**(python3.13 幽灵根治):进程匹配改 `python3*` 通配+PID 文件双写;
- **B3 rerank 重开评估**:隧道 keepalive 已重启→remote 实测 3 连通→双开关重开(验收方案 RERANK_ACCEPTANCE_V1 在档);
- **B4 终检正日 18 项**。
