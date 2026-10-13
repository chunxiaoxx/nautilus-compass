---
name: orgfuel-ORGQ-c78048808e952e87-75defbcc7c
description: "轮次记录 R517 · 2026-10-11 晨(主件轮:RERANK 双加固重开✅[实测 3/3 连通]+instal"
metadata:
  type: reference
  source: org_fuel:queue_r3
  pf_id: ORGQ-c78048808e952e87
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R517 · 2026-10-11 晨(主件轮:RERANK 双加固重开✅[实测 3/3 连通]+install.sh 假注册修正——发布面两 bug 全修)
### R517 · 2026-10-11 晨(主件轮:RERANK 双加固重开✅[实测 3/3 连通]+install.sh 假注册修正——发布面两 bug 全修)
- **主件=rerank 重开完成**:双开关 ON+隧道 keepalive 重启→**remote 3/3 连通[实测]**(首包 19.8s 隧道重连,稳态 181/166ms)→daemon 重启带开关→V1 实测通过(nginx query 2ms 常速)。
- **install.sh 假注册修正**:v1.0 第 4 步只 echo 不写入→真写 settings.json(幂等 JSON 安全写入)。
- daemon 幽灵进程根因拔除(python3.13.exe 命名错位);hook 探活快退+timeout 120s。
- 四项修复状态:①install.sh ✅ ②daemon 幽灵 ✅ ③hook 挂 ✅ ④PyPI 环境雷(文档候 3.3.1)。
