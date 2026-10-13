---
name: orgfuel-ORGG-4347b3235a638d4b-fdb14e7ef6
description: "判读档判例 P2_JUDGE_TRAINING_PREREG_20260930 · 数据(已冻结) ## 数据(已冻结)"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-4347b3235a638d4b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 P2_JUDGE_TRAINING_PREREG_20260930 · 数据(已冻结)
## 数据(已冻结)

- 源:runtime/verdict_corpus/train_set_v0.jsonl(labelled 1454)
- 切分:tools/corpus_split.py · seed=20260930 · 80/10/10 · **qid 分组切分**
  (d12/d14 同题不同 run 必须同折,防 test 泄漏;leak-check 跨折=0 PASS)
- 分布:train 1162(pass 610/fail 546/U 6)· dev 143(71/72/0)· test 149(78/70/1)
- **已知短板**:U(insufficient_evidence)全库仅 7 条,dev 零 U——U 态为
  探索性指标,不设门槛如实报;扩充路径=v5 errata 活水(gold tier)+歧义题专项标注
- tier:现库全部 gold 级(官方规则/双层复算/人工审计/独立盲评);tier 加权
  留接口,bronze/silver 样本到达后启用
