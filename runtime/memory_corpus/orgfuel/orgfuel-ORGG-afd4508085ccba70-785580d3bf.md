---
name: orgfuel-ORGG-afd4508085ccba70-785580d3bf
description: "判读档判例 2026-09-22-dcr-security-audit · 立即修复清单(P0) ## 立即修复清单(P"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-afd4508085ccba70
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-22-dcr-security-audit · 立即修复清单(P0)
## 立即修复清单(P0)

1. **nginx 限制 /api/users**:deny all(或 admin only)
2. **nginx 限制 /api/orders**:deny all(或 admin only)
3. **CORS 收窄**:仅允许 compass.nautilus.social
4. **DCR 下单改用 GitHub issue 为主通道**(微信支付按钮保留,但引导先开 issue 获取专属 user_id)
