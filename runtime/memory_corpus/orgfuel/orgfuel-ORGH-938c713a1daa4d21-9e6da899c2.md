---
name: orgfuel-ORGH-938c713a1daa4d21-9e6da899c2
description: "commit e0c3d2efcfee 2026-09-05 docs(launch): 9/5 抽查抓到 /mcp 3"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-938c713a1daa4d21
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit e0c3d2efcfee 2026-09-05
docs(launch): 9/5 抽查抓到 /mcp 301→8443 死路径并修复——新用户直连保护
公网 POST /mcp(无尾斜杠)被 nginx 相对 301 重定向拼上另一 listen 8443
block 的端口,8443 对公网不通=按 README 直连的新用户必断。修复:改直
proxy 消除 301;该 nginx 非 systemd 管,kill -HUP master PID reload;
公网复验 /mcp 与 /mcp/ 双 401(正常鉴权门)+landing/signup 200 回归绿。
备份 /home/ubuntu/compass.bak.20260905
