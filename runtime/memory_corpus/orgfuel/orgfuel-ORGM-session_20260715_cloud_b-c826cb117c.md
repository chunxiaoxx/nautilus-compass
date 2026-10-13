---
name: orgfuel-ORGM-session_20260715_cloud_b-c826cb117c
description: "--- name: session_20260715_cloud_box_health_audit descriptio"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-session_20260715_cloud_b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: session_20260715_cloud_box_health_audit
description: 2026-07-15 cloud box 健康审计:certbot 自动续期已死(pyOpenSSL/cryptography 版本冲突)Aug 17 证书到期前必修;ufw 关 4 周;BGE daemon 饿死 DB
metadata: 
  node_type: memory
  source_session: 2026-07-15 compass 继续探索 box 健康
  forget_at: 2026-08-18T00:00:00Z
  type: project
  originSessionId: e4544c1e-7207-4060-8121-a054066dcec8
---

# cloud(43.160.239.61)box 健康审计 · 2026-07-15

compass 修完 backend 502 后继续探索,SSH 坐实(非自报)以下:

## certbot 续期(纠正:HTTPS 其实不危险 · 证伪自己第3次)
- ⚠️ 前一版本条目说"certbot 已死 Aug17 HTTPS 必挂"= **过头结论,已纠**。深挖后真相:
  - **坏的只有 apt `/usr/bin/certbot`**:它用 pyOpenSSL 21.0.0(dist-packages)+ cryptography 48.0.0(有人 pip 装进 ~/.local shadow 了系统版),pyOpenSSL21 引用的 `X509_V_FLAG_NOTIFY_POLICY` 在 crypto48 已删(实测 hasattr=False)→ apt certbot 连 import 都崩。**别动 ~/.local 的 cryp
