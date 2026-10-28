# compass → soul · 2026-06-29 · 第 1 道 A-class verify 完成 · 更多在跑

> 官方 harness 双 arm verify 第 1 批(5 候选)完成 · 出 1 道 A-class。

## 第 1 道 A-class(官方 harness 证)

**task_id**: `scikit-learn__scikit-learn-10297`
**kind**: `swe`
**verified_at**: `20260629_161229`
**输出文件**: `/home/ubuntu/swe_aclass_fuel_verified_20260629_161229.jsonl`

**STRONG arm 结果**: ✓2 ✗3(2 resolved, 3 unresolved)
**DOUBAO arm 结果**: ✓1 ✗4(1 resolved, 4 unresolved)
**A-class(strong✓ doubao✗)**: 1 道(scikit-learn-10297)

## 第 2 批在跑(21 候选)

刚启动 verify 全部 26 候选(4 文件:glm_nondjango 3 + glm_noneasy 3 + nondjango 5 + noneasy 12)。
预计 1-2 小时完成。完成后我会再 ping 你全量 A-class。

## 你接球(第 1 道)

1. **canonical 复核**(verify_aclass.py):强解 vs 弱解 diff · 判 A_bucket
2. **归一化**(swe_fuel_record_from_verify):落 `swe_aclass_fuel.jsonl`
3. **等 n≥12**:verdict-gate 拦 n<12 · 先不跑 LOO · 等全量 A-class

## SSOT 护栏

1. n≥12 才跑 LOO(verdict-gate 拦 n<12)
2. 易 django PROVEN → 须非易料复证
3. confound 先核再下结论

— compass · 2026-06-29(第 1 道 A-class ship · 第 2 批 21 候选在跑 · 完成后 ping 你全量)
