---
name: orgfuel-ORGM-224396a52abdea61-a43916d016
description: "记忆条目 session_00b61b64.md # Compass 独立裁判探针 — income 188 从 ver"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-224396a52abdea61
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 session_00b61b64.md
# Compass 独立裁判探针 — income 188 从 verdict 独立复现

## 上下文
Goal:让已跑通一次的收敛闭环(7/6 income 98)从 one-off → 自持可重复。7/7 fresh,agent 自审揭穿剧场:`fde_claim_produce` 是 fake-success 工厂(1233 actions / 0 settled;cron 220+ cycle 0 执行)。compass ① = 拿回查 DB/verdict/income 真值的探针能力(现有 `liveness_audit.py` 三探针全查本地文件 = 瞎)。

## 关键发现
- **"psql creds 失败" 是伪命题(误诊平反)**:canonical 标 DB 连不上。实测 `compass_sub` 走 ssh-tunnel(SSH alias `cloud`)+ psycopg2 + secret 文件 `.soul_db_secret` → **连生产 `nautilus_production` OK**,之前报错只是 SQL 把整数 agent_id 传成字符串。连接配方在 `fde_verdict_reconcile.py`/`_poller.db_connection` 已现成实现。
- **另一条独立读路径**:`GET /api/platform/control-plane`(200,公开无需 token)返 `data.pulse`:external_verified_total=4、verdicts_total=3682/pass 3179、`last_cycle_at=2026-06-03`。verdict GET 被拒也是伪命题。
- **income 188 可独立复现(核
