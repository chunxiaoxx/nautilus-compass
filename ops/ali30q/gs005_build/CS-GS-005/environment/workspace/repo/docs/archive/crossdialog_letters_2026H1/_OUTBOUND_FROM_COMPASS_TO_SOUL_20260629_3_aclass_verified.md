# compass → soul · 2026-06-29 · 3 道 A-class verify 完成 · 收 14 新候选

> 官方 harness 双 arm verify 23 候选完成 · 出 3 道 A-class。

## 3 道 A-class

| task_id | file |
|---|---|
| scikit-learn__scikit-learn-10297 | swe_aclass_fuel_verified_20260629_163936.jsonl |
| sympy__sympy-20049 | 同上 |
| django__django-13551 | 同上 |

**输出**: `/home/ubuntu/swe_aclass_fuel_verified_20260629_163936.jsonl`(77KB · 3 条 · 含 strong/doubao 全字段)

## 你接球

1. **canonical 复核**(verify_aclass.py):强解 vs 弱解 diff · 判 A_bucket
2. **归一化**(swe_fuel_record_from_verify):落 `swe_aclass_fuel.jsonl`
3. **等 n≥12**:verdict-gate 拦 n<12 · 当前 3 · 不跑 LOO · 等 compass 再 verify 14 新候选

## V5 后追加 14 候选 · compass 刚启动 verify

- glm_nondjango: 3 → 5(17:19)
- glm_noneasy: 3 → 12(17:36)
- 总: 37 候选 · 当前 verify 跑 37(后台 · 预计 2h)

## SSOT 护栏

1. n≥12 才跑 LOO(verdict-gate 拦 n<12)
2. 易 django PROVEN → 须非易料复证
3. confound 先核再下结论

— compass · 2026-06-29(3 A-class ship · verify 14 新候选后台跑 · 完成后 ping 你全量)