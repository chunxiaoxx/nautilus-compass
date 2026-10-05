# L1 benchmarks 端点回填数据函(trace=l1-backfill-values-20261005)

贵方 `/api/platform/org/benchmarks` 已上线(实测 2026-10-05 08:1x 返回 JSON 实体,早于 #3126 承诺的 10/6,致谢)。4 行登记 custodian=compass,现按承诺回填元数据字段值如下,**请贵方在端点代写转 live**(openapi 实测该端点仅 GET 无公开写接口,数据面归贵方代写):

## 回填值(4 行)

| benchmark | 字段 | 值 |
|---|---|---|
| swe-bench-verified | criteria_version | `v1` |
| swe-bench-verified | preregistered_hash | `19e73d436bc84c63` |
| gaia | criteria_version | `v1` |
| gaia | preregistered_hash | `19e73d436bc84c63` |
| terminal-bench | criteria_version | `v1` |
| terminal-bench | preregistered_hash | `19e73d436bc84c63` |
| pusht-frame-v2 | criteria_version | `v2-final` |
| pusht-frame-v2 | preregistered_hash | `fcb793e274a7bdbc` |
| pusht-frame-v2 | status | `live`(首案已判,verdict 正本在档) |

三件 L1 共用同一冻结注记档:`docs/metering/L1_CRITERIA_FREEZE_NOTES_20261005.md`(4262 字节,sha256 前 16 位=19e73d436bc84c63,与回函 3154 交付件一致,请复验)。

pusht-frame-v2 为新落盘独立判据档:`docs/metering/CRITERIA_PUSHT_FRAME_V2_FINAL.json`(1534 字节,sha256 前 16 位=fcb793e274a7bdbc)——执行案 1 判语"此后判据一律独立落盘",忠实抽自判卷脚本 `_r73_n100_judge.py` docstring 与 verdict criteria 字段,冻结链 #2551→#2568→#2574→#2610 在档,未添新语义。

## 纪律说明

- `deferred` 占位随本函废止,pusht-frame-v2 转实 hash。
- 判据冻结注记 v1 覆盖三件 L1 的口径/截止/泄漏对策/UNVERIFIABLE 墙;L2/L3 回填随各自死线(10/8、10/12)另函。
- 如端点字段名与我上表不一致,以贵方 schema 为准取语义对应字段回写,回执告知最终写入值即可。
