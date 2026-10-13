---
name: orgfuel-ORGG-6ae433e41465532c-f5c4eb3375
description: "判读档判例 2026-06-20-compass-serving-semantic-recall · Task 3: r"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-6ae433e41465532c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-20-compass-serving-semantic-recall · Task 3: recall handler 接语义排序(保留关键词降级 + 所有过滤)
## Task 3: recall handler 接语义排序(保留关键词降级 + 所有过滤)

**Files:**
- Modify: `compass_http_v09.py:521-556`（`recall` handler）
- Test: `tests/test_recall_semantic.py`(新建)

**关键不变量**:`drift` / `cross_agent` / `agent_id` 过滤行为不变;daemon 返 None 时**完全回退到现有关键词打分**(行为零回归);返回结构(`hits` 字段)不变。

**Step 1: 写失败测试**

```python
import compass_http_v09 as srv
# 用现有测试 DB fixture（若无·建最小 sqlite 注入两条 obs：含 "alpha"/"beta"）。
# 注入 _daemon_score 返已知分·验 hits 顺序按 cosine·且 daemon=None 时回退关键词。

def test_recall_uses_daemon_scores(monkeypatch, seed_two_obs):  # seed_two_obs: fixture
    monkeypatch.setattr(srv, "_daemon_score", lambda q, c: [0.2, 0.95])  # 第2条更相关
    res = srv.recall(q="anything", top_k=2, cross_agent=True, user_id="u
