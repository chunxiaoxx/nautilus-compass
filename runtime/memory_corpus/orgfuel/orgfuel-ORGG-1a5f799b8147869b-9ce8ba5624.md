---
name: orgfuel-ORGG-1a5f799b8147869b-9ce8ba5624
description: "判读档判例 2026-08-30-multi-tenant-memory-design · 5. 实施分期与验收判据 #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-1a5f799b8147869b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-08-30-multi-tenant-memory-design · 5. 实施分期与验收判据
## 5. 实施分期与验收判据

- **P2 提审版(最小,≈0 新代码)**:自用 dogfood 单租户全链跑通——workbuddy(JWT agent token)+ 各框桥(scoped token)全部走 8097/9877 鉴权通道,本地 9876 仅限本机回环。
- **商用版(提审通过后)**:自助 signup → 自动签发该用户 scoped token → 隔离验收探针自动跑;TCP 版补 tokens.json 热加载;8770 退役时多用户模型迁入正式服务。
- **验收四探针(可证伪)**:① 跨用户读 DENY ② 跨用户写 DENY ③ 同用户跨设备 recall 命中同一记忆 ④ token 撤销后旧请求 DENY。四绿才可宣称"多租户隔离成立"。
