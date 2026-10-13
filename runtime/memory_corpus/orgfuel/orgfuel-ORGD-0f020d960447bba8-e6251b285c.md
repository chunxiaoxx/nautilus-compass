---
name: orgfuel-ORGD-0f020d960447bba8-e6251b285c
description: "[## 二 · 八个底层算子(签名 · 代码实物 · 数学形态)] | # | 算子 | 签名 | 代码实物 | 数学形"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-0f020d960447bba8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 二 · 八个底层算子(签名 · 代码实物 · 数学形态)] | # | 算子 | 签名 | 代码实物 | 数学形态 |
|---|---|---|---|---|
| 1 | W 写入 | (doc,meta)→e=E(doc) 落库 | daemon ingest(verbatim+BGE-m3,写侧零 LLM) | **无投影存储**:不经过有损映射 g(doc)→摘要,信息保持(智能后置到读取,由已知查询分布决定投影) |
| 2 | R 召回 | q→top-k | daemon.py:216 `_rrf_fusion`(k=60)+BM25 流 | RRF:score(d)=Σᵢ 1/(k+rankᵢ(d)) |
| 3 | D 漂移 | prompt→r(p)∈ℝ,alert=r<τ ∨ rule_hit | daemon.py:1289 `drift_score=round(pos_cos−neg_cos,4)` | 加权 top-3 双原型 **margin**:s(p)=w̄₊·cos(p,A₊)−w̄₋·cos(p,A₋) |
| 4 | X 沿链 | S→S∪N₁(S) | **插件仓** `~/.claude/plugins/nautilus-compass/daemon.py:1145/1161` `_entry_link_text`/`expand_chain_links`(记忆门三件套,主仓 daemon 无此符号) | 1-hop 邻域扩张,谓词=锚存在(全文级) |
| 5 | B 封印 | dir→(manifest,claims) | tools/verifypack/seal.py | B(P)={hᵢ=SHA256(Pᵢ)}:把字节集映为哈希清单 |
| 6 | V 复算 | (pack,env_caps)→{agree,d
