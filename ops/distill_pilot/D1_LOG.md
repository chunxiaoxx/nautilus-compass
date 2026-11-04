# D1 执行台账(2026-11-04)· 供非实现者复算

判据正本: `docs/soul/SESSION_DISTILL_PILOT_20261104.md`(预注册判据 J1-J6 未动)

## 交付件

| 件 | 坐标 | 验证 |
|---|---|---|
| 选样扫描器 | `tools/distill_pilot/scan_bucket.py` | 实跑 2 次(B 组补 mid5-20MB 档后定型) |
| 正文抽取器 | `tools/distill_pilot/extract_sample.py` | 46 会话实抽 |
| 锚点核验器 | `tools/distill_pilot/anchor_check.py` | selftest PASS(3 真+2 假=3/5,期望值精确命中) |

## 实测读数 [实测]

- 扫描: **1811 个 jsonl**(2026-11-01 治理时 1639,3 天 +172)
- 选样: A 近 30 天活跃 20 / B 高价值 16(handoff-linked 3 + big>20MB 4 + mid5-20MB 9)/ C 值守负对照 10(**10/10 全中"LOOP 轮指令"签名**)
- **偏差 1**: 总数 46≠50(B 组 5-20MB 档用尽仍差 4;不降档凑数,判据不依赖 N)
- 抽取: **314,854,974B → 6,972,100B,总抽取比 2.21%**(立项档预估 1-3% 区间内)
- handoff 映射仅 3 条: 多数 handoff-*.md 的 originSessionId 是 Windows 期 UUID,对不上本桶 Mac 期 stem——已知边界,非 bug

## 产物坐标(复算入口)

- 全量统计: `bucket_stats.json` · 选样清单: `sample_manifest.json`
- 抽取正文: `extracted/<session_id>.txt`(46 件,带角色/行号/时间戳标记)
- 抽取统计: `extraction_stats.json`

## 复算命令

```bash
python3 tools/distill_pilot/scan_bucket.py --bucket ~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass --memory-dir ~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory --out runtime/scratch_distill_pilot_20261104
python3 tools/distill_pilot/extract_sample.py --manifest runtime/scratch_distill_pilot_20261104/sample_manifest.json --out runtime/scratch_distill_pilot_20261104
python3 tools/distill_pilot/anchor_check.py --selftest --source runtime/scratch_distill_pilot_20261104/extracted/<任一>.txt
```

## D2 待办(下一动作)

本地模型服务(llama-server + Qwen3 量化)→ 压缩臂跑 A/B 组 → 参考臂 10 会话 → D3 盲评出数。6.97MB 正文 ≈ 2-3M token,本地臂一晚可磨完 [推断]。
