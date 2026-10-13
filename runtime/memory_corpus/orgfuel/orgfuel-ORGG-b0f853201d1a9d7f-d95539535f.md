---
name: orgfuel-ORGG-b0f853201d1a9d7f-d95539535f
description: "判读档判例 2026-06-20-compass-serving-semantic-recall · Task 1: d"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-b0f853201d1a9d7f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-20-compass-serving-semantic-recall · Task 1: daemon 新增 `score` action(bge-m3 query↔候选 cosine)
## Task 1: daemon 新增 `score` action(bge-m3 query↔候选 cosine)

**Files:**
- Modify: `daemon.py`(请求分发处加 `score` 分支 + 一个 `_handle_score` 函数·复用已载 `embedder`)
- Test: `tests/test_daemon_score.py`(新建)

**Contract:**
```
请求:  {"action":"score","query":"<str>","candidates":["<text>", ...]}
响应:  {"ok":true,"scores":[<float cosine>, ...]}   # 顺序对齐 candidates
         {"ok":false,"error":"..."}                  # 候选空/embedder 未载等
```

**Step 1: 写失败测试**

```python
# tests/test_daemon_score.py
import json, daemon  # daemon 模块可 import(顶层无副作用执行)

class _FakeEmbedder:
    # 确定性假向量:按文本是否含 "alpha" 给正交方向,避免真载 bge-m3
    def encode(self, text):
        return [1.0, 0.0] if "alpha" in text else [0.0, 1.0]
