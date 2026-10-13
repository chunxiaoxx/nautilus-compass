---
name: orgfuel-ORGQ-01e39889aae86ce1-6b50335f5c
description: "轮次记录 R385 · 2026-10-09 凌晨九(死线带:S6 全量复算判读✅——29/30 逐例一致,PASS) "
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-01e39889aae86ce1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R385 · 2026-10-09 凌晨九(死线带:S6 全量复算判读✅——29/30 逐例一致,PASS)
### R385 · 2026-10-09 凌晨九(死线带:S6 全量复算判读✅——29/30 逐例一致,PASS)
- **全量复算完成[实测]**:loop_all 15 批零 TIMEOUT,ALL_BATCHES_DONE;15 报告四桶合并=9R/5U/14E/2EP;与原跑三报告(django+a_eof+rest——两份时 MISSING_ORIG 14 例虚惊,补 rest_report_a.json 后全量覆盖)逐例对照:**29/30 SAME,唯一漂移 django-16560(原 error→复算 resolved,方向与判读层修复口径一致,sphinx-8475 同型 SAME)**——复算保真度门 PASS(docs/metering/S6_RECOMPUTE_FIDELITY_20261009.md,判读卡候选编号顺延)。
- **10732 v5 交叉件收讫**:R1/R2/R3 三件回归 SQL(不同实现同语义)+双案例预跑基线——供 4096 五门交叉验证,ack 后入判读流程。
- 磁盘终态:系统盘余 74G(分批用完即删循环自洽),/data 余 57G。
