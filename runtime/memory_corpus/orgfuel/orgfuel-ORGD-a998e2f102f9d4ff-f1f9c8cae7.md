---
name: orgfuel-ORGD-a998e2f102f9d4ff-f1f9c8cae7
description: "[## 结论:**6/7 agree · 1 agree-with-caveat(协议缺陷项,非数据问题)**] | #"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-a998e2f102f9d4ff
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 结论:**6/7 agree · 1 agree-with-caveat(协议缺陷项,非数据问题)**] | # | claim | 复算 | 裁定 |
|---|---|---|---|
| 1 | D2_帧完整率 = 1.0 | sum(190×8)/sum(190×8) = **1.0** | ✅ agree |
| 2 | D3_轨迹完整率 = 1.0 | 8/8(convert_rc=0 且 valid_ratio≥0.98) = **1.0** | ✅ agree |
| 3 | 8 条视频 sha256_16 | 对 `egostandard_sample\s2\out\...\videos\` 真文件重算,8/8 逐字节一致 | ✅ agree |
| 4 | 5 个复现日志 sha256_16 | worker1-4.log **4/4 一致**;`resource_log.csv` 重算 `e7a5989e0d1d153f` ≠ 声称 `1f9ce5cd319db717` | ⚠️ **agree-with-caveat**(见下) |
| 5 | 同源双份转换哈希一致 | 4 组各 ×2,分组计数与声称全同 | ✅ agree |
| 6 | 人脸检出占比(L2) | 降级核对:payload L 记录与 claim 逐项一致(8/8) | ✅ agree(降级口径已声明) |
| 7 | payload↔report 数值一致 | 关键数值均见于 report.md | ✅ agree |
