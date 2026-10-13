---
name: orgfuel-ORGD-2f4b16ff63b6acaa-8f8a81b8c7
description: "[## M4 · 运营护栏(部分无悔,部分冻结)] - [ ] **T8 TCP 版 tokens.json 热加载**"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-2f4b16ff63b6acaa
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## M4 · 运营护栏(部分无悔,部分冻结)] - [ ] **T8 TCP 版 tokens.json 热加载**(无悔):去 `systemctl restart` 依赖,撤销即时生效。判据:revoke 后旧 token 下一请求即 DENY,无重启。
- [ ] **T9 per-token 限流**(无悔):mcp_server.py 已有 rate-limit 雏形,接正式服务。判据:超限 429 且不伤及他 token。
- [ ] **T10 租户数据导出/删除**(冻结 · 等 P3 首批真实用户):对外商用合规项,提前做=无人消费。解冻:P3 首个外部安装。
