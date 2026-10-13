---
name: orgfuel-ORGQ-R238-324d68adf8
description: "### R238 · 2026-10-06 07:2x-07:4x(r80 判读主轮:材料到→机判→出读数 20min "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R238
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R238 · 2026-10-06 07:2x-07:4x(r80 判读主轮:材料到→机判→出读数 20min 闭环)
- **probe(07:31)**:#9965 v5 r80 材料坐标到(nautilus-v5@5c2cb21c jsonl,sha16=cfd7d21b2bb534d4)·CI 折叠·A100 GPU 空
- **材料拉取验签 [实测]**:gh api 拉 522KB,sha16 逐位一致;ack 9965 起判(24h SLA 07:24 起算)
- **机判 v1 红灯→自证伪**:全 U=我字段名猜错(transcript 列实为 trajectory list;finished/errors 原子字段不在导出)+同源门比对口径错(source=产线标识 v5-selfline 非 operator dict);列名实读修正
- **机判 v2 [实测]**:判定源=库 convert_submit 产物(verifier),判读侧独立复核=轨迹末条角色实态↔判定——**25/25 复核零分歧:pass 6/fail 19(unfinished 全列)**;四门(形态/同源前缀口径/实态轮替)过,G4=SKIP(panel 侧)披露;抽检 3/3(seed 20261006);披露三则(双层转义降层解析/fpp 列全 NULL/零方差不适用)
- **读数函 9968**→platform(承 4908:逐单清单上仓 r80_verdicts.json;出分触发结算;errata 建议 19 fail=execution/unfinished/measured);SLA 20min 闭环
- M1:+1(挂账多日的 r80 25 单判读闭环=判分机构履约件;负样本照交=数据飞轮供料)
