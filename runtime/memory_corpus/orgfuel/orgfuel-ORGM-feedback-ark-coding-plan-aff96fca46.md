---
name: orgfuel-ORGM-feedback-ark-coding-plan-aff96fca46
description: "--- name: feedback-ark-coding-plan-not-metered-api descripti"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-feedback-ark-coding-plan
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: feedback-ark-coding-plan-not-metered-api
description: "用户多次纠正:火山 ARK 一律走 coding plan 端点(/api/coding/v3),不走按量 API(/api/v3 烧充值)——含可复制接入配方"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-08-30T09:30:37.933Z
---

用户 2026-08-28 首纠、2026-08-30 再纠("多次强调使用 coding plan 而不是直接使用 api"):调 ARK 模型(doubao 等)一律走 **coding plan 数据面端点**,禁止走按量 API。

**Why:** 按量端点 `https://ark.cn-beijing.volces.com/api/v3` + 老 ARK_API_KEY = 按量计费烧充值;8/30 compass 框刀3 弱标注+d12+d13 连续沿用它,把账户余额烧尽触发 `403 AccountOverdueError`,d13 两域全崩——违规有直接代价。红线 memory 原在 core/v5 框,compass 本地没有,导致本框未防住。

**How to apply(可复制配方,8/30 实测打通):**
- 端点:`https://ark.cn-beijing.volces.com/api/coding/v3`(**openai 兼容**,同 /api/v3 同构);anthropic 面为 `/api/coding`(config.yaml `anthropic_
