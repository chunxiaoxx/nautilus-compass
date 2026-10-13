---
name: orgfuel-ORGH-ea1928b30bcb0bfe-217bf89a9e
description: "commit 25a568a9006c 2026-06-08 feat(fde): cnt_c3 PoI consume"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ea1928b30bcb0bfe
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 25a568a9006c 2026-06-08
feat(fde): cnt_c3 PoI consumer for soul rsi_delta feed (pre-built · wire on deploy)
按 soul PoI 消费契约 spec 预建 consumer:读 escapes_only ΔReward feed 行 → PoI credit。
三条硬规则:credit∝delta_reward(>0·过 escapes 门)· delta_id 幂等去重(DB-backed·
survives restart)· 归因 producer_model+grounding_source.policy(赢的策略·外部选择压力
指向'什么产法')· escapes_noise=False 永不 credit(防御自滤)。复用 poi_credit_store.
upsert_credit 中央账本·不重造。6 TDD(真 sqlite 全链·soul spec 真数据 0.0734)。fetch
为 wire-time(端点 G-cloud 部署后启用)·credit 逻辑端点无关已验。与 c3 defer 一致:代码
预建 un-gated·wire live gated。
