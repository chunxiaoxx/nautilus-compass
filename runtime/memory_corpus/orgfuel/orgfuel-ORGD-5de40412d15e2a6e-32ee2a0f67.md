---
name: orgfuel-ORGD-5de40412d15e2a6e-32ee2a0f67
description: "[## 拓扑实测(Task 0 · 2026-06-20 实测·后续 Task 据此填真值)] | 项 | 实测值 | "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-5de40412d15e2a6e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 拓扑实测(Task 0 · 2026-06-20 实测·后续 Task 据此填真值)] | 项 | 实测值 |
|---|---|
| **serving 机** | `cloud` = `43.160.239.61` · `/home/ubuntu/compass`(**非 git repo**·deploy=scp) · `uvicorn compass_http_v09:app --host 0.0.0.0 --port 8770 --workers 4` · PID 289407 · healthz `version:1.0.0` `users:1` `observations:348` |
| **daemon 机** | T4 = **`43.166.8.20`**(⚠️ ≠ ssh config `t4`=43.163.80.46)· `/home/ubuntu/compass/daemon.py` · PID 674936 · bind `127.0.0.1:9876` · `compass-daemon.service` · 显存 4817/16384 MiB(瘦身后·余量足) |
| **隧道** | `compass-t4-tunnel.service`(cloud 上)· `ssh -N -L 127.0.0.1:9876:127.0.0.1:9876 -L 127.0.0.1:9877:127.0.0.1:9877 -i /home/ubuntu/.ssh/id_ed25519_qb ubuntu@43.166.8.20` · cloud:9876 → T4 daemon:9876 ✅ 实测通(score 请求经隧道返 daemon JSON) |
| **T4 跳板** | 本地无 43.166.8.20 直连;经 `ssh cloud 
