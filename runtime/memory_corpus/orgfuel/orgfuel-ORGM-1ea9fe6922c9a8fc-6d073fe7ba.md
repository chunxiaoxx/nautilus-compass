---
name: orgfuel-ORGM-1ea9fe6922c9a8fc-6d073fe7ba
description: "记忆条目 feedback-ark-coding-plan-not-metered-api.md 用户 2026-08-"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-1ea9fe6922c9a8fc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 feedback-ark-coding-plan-not-metered-api.md
用户 2026-08-28 首纠、2026-08-30 再纠("多次强调使用 coding plan 而不是直接使用 api"):调 ARK 模型(doubao 等)一律走 **coding plan 数据面端点**,禁止走按量 API。

**Why:** 按量端点 `https://ark.cn-beijing.volces.com/api/v3` + 老 ARK_API_KEY = 按量计费烧充值;8/30 compass 框刀3 弱标注+d12+d13 连续沿用它,把账户余额烧尽触发 `403 AccountOverdueError`,d13 两域全崩——违规有直接代价。红线 memory 原在 core/v5 框,compass 本地没有,导致本框未防住。

**How to apply(可复制配方,8/30 实测打通):**
- 端点:`https://ark.cn-beijing.volces.com/api/coding/v3`(**openai 兼容**,同 /api/v3 同构);anthropic 面为 `/api/coding`(config.yaml `anthropic_base_url`)
- key:本机 `~/.arkcli/.env` 的 `VOLCENGINE_ARK_API_KEY`(36 位 UUID,profile=coding-plan_cn-beijing_personal,有效期至 2026-10-28);⚠️ grep 必须锚定行首 `grep '^VOLCENGINE_ARK_API_KEY='`,否则混入 KEY_UID 行导致 400 Bad Request(8/30 踩坑:错误 key 长度 47)
- 查通道:`ar
