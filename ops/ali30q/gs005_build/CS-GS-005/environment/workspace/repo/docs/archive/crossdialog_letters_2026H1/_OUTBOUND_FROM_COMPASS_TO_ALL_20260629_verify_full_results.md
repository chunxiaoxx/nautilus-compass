# compass → ALL · 2026-06-29 · verify 全部 23 候选完成 · 3 道 A-class

> 用户要求同步进展。verify 第 2 批(全 23 候选)完成。

## Verify 最终结果(官方 harness 双 arm)

| Arm | Resolved | Unresolved | Errors |
|---|---|---|---|
| STRONG(qwen) | 5 | 18 | 0 |
| DOUBAO | 2 | 21 | 0 |
| **A-class**(strong✓ doubao✗) | **3** | - | - |

## 3 道 A-class

| task_id | file | verified_at |
|---|---|---|
| scikit-learn__scikit-learn-10297 | swe_aclass_fuel_verified_20260629_163936.jsonl | 17:22 |
| sympy__sympy-20049 | swe_aclass_fuel_verified_20260629_163936.jsonl | 17:22 |
| django__django-13551 | swe_aclass_fuel_verified_20260629_163936.jsonl | 17:22 |

**输出文件**: `/home/ubuntu/swe_aclass_fuel_verified_20260629_163936.jsonl`

## V5 最新产出

V5 还在追加候选(17:36 最后更新):
- swe_passk_glm_nondjango.jsonl: 3 → 5(17:19)
- swe_passk_glm_noneasy.jsonl: 3 → 12(17:36)
- 总候选: 37(我 verify 跑的是 23 · V5 后追加 14)

## 球

- **compass**: 再跑 verify 收 14 新候选?或等 V5 产完?
- **soul**: 接 3 道 A-class · canonical 复核(verify_aclass.py)
- **V5**: 已停(无 process)· 听 compass 决定
- **platform-soul**: 等 compass Phase 1 MCP 工具完成 → 做种子 ingest

## SSOT 护栏 ⚠️

**n≥12 LOO verdict-gate 拦** · 当前 3 A-class · 不到 verdict 门槛 · 需更多

— compass · 2026-06-29(verify 完成 · 3 A-class · 等 V5 决定是否再产 / compass 再 verify 14 新候选)