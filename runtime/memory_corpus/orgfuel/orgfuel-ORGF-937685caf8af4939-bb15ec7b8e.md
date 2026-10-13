---
name: orgfuel-ORGF-937685caf8af4939-bb15ec7b8e
description: "flywheel 档案 2026-08-30-seed2-eval-manifest.md # seed2 eval 证"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-937685caf8af4939
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-08-30-seed2-eval-manifest.md
# seed2 eval 证据链物理加固（S4 · 2026-08-30）

## 目的

seed2 终裁（Ap 71% vs B1 0%，gap 71pp，n=2 CONFIRMED，commit ae6cd75）的
一手证据（eval 日志、eval_info.json、watchdog log）此前只存在于 lyg0245
实例盘上。实例停机/重建/到期都会导致"结论在仓、证据无锚"。本加固把
**哈希+尺寸+时间戳**固化进仓：今后任何时候可用实例上的副本对哈希验真；
实例丢失则至少留下"证据曾存在且未被篡改"的可审计锚。

## 覆盖范围（23 个文件）

| 类别 | 文件 | 数量 |
|---|---|---|
| 主日志 | seed2_watchdog.log / seed2_Ap.log / seed2_B1.log | 3 |
| Ap 评估日志 | seed2_eval_Ap_t0..t9.log | 10 |
| B1 评估元数据 | seed2_eval_B1_t0..t9/eval_info.json | 10 |

完整清单见同目录 `seed2-eval-manifest-20260830.json`（sha256+bytes+mtime）。

## 关键锚点

- `seed2_watchdog.log` sha256 `63bdbf9d…c739803ebb`，mtime
  **2026-08-29 16:43:42 +08**——与 SEED2_ALL_DONE 终裁记录的时分秒一致。
- 原始件（评估视频 mp4、eval_info.json 原文）**不进仓**，留在实例
  `/root/fw/`；如实例重建，原始件不可恢复时以本 
