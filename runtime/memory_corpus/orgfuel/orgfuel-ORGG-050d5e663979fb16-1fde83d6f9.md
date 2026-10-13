---
name: orgfuel-ORGG-050d5e663979fb16-1fde83d6f9
description: "判读档判例 2026-06-05-fde-rsi-dual-flywheel-closure-design · 3. 设"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-050d5e663979fb16
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-05-fde-rsi-dual-flywheel-closure-design · 3. 设计:四缺口闭环(接线优先 + 专家回路为新脉)
## 3. 设计:四缺口闭环(接线优先 + 专家回路为新脉)

**原则**:① 不发明新能力,激活已建到生产 + 只新建专家→ground truth 一条;② 守黑盒约束(热路径不调 LLM,本地 BGE/交叉编码器可,LLM opt-in);③ 守平台纪律(内部 RSI held,但 FDE 专家/字节=外部信号,另一条,合规)。

### 缺口1 · 记忆胶囊跨设备(小修)
修 `/v1/v14/ingest_obs` action/字段不匹配。**先云端实测**确认是否真静默失败,再对齐 daemon 或补 adapter。→ 跨设备原文召回接上。

### 缺口2 · 检索保真度进生产(接线·解长期记忆)
reranker(bge-reranker-v2-m3 本地交叉编码器·非 LLM)+ query-rewrite + lifecycle tier 提升,从 benchmark 管线接进生产 daemon recall 热路径(可配开关,默认建议开 reranker)。证据已证有效。守黑盒:reranker 非 LLM 不破约束;query-rewrite 若用 LLM 则 opt-in。

### 缺口3 · FDE verdict→PoI(双轮咬合)
adapter:soul checklist 通过率 + 专家复核结论 → 外部 outcome → `compass.poi_credit`;云端 `COMPASS_CLOUD_POI_BOOST=1`。边界:FDE 外部信号 ≠ 平台 held 的内部 RSI。

### 缺口4 · 专家互动回路(新脉·复利源)
飞书复核工作台 通过/打
