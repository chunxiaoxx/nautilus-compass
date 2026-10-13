---
name: orgfuel-ORGD-faed805e33d73230-d04a52d6e5
description: "[## L1 · errata 导入线(v5 → compass 语料池)【已发车,等回函】] - **接口**:函 2"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-faed805e33d73230
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## L1 · errata 导入线(v5 → compass 语料池)【已发车,等回函】] - **接口**:函 2634(trace compass-errata-gold-request-20261003,死线 10/5 18:00)
- **触发**:v5 回函或 A100 落盘通知
- **步骤**:①收数据(信箱附件存 runtime/verdict_corpus/delta/inbox/,或 A100 落盘拉回)②字段映射(对方 qid/原判定/复算判定/判因 → 我方 artifact/judge_output/truth_label/label_origin;label_origin 按对方标注映射白名单四类)③投 inbox 交 p3_delta.py 吸收(指纹账去重+白名单门)④p3_ticket 看是否触发
- **验收**:delta_NNNN 入账,label_origin 白名单校验通过
- **依赖**:v5 响应;若 10/5 18:00 未回,reminder 一次(组织内数据请求,非外联催办)
