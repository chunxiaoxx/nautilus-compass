---
name: orgfuel-ORGG-b1ca6b192f888b62-a9f8af78ba
description: "判读档判例 BC1_LAUNCH · 外部基线(2026-09-25/26 发布前预跑) ## 外部基线(2026-09"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-b1ca6b192f888b62
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 BC1_LAUNCH · 外部基线(2026-09-25/26 发布前预跑)
## 外部基线(2026-09-25/26 发布前预跑)

开源记忆产品实测(同一 backbone MiniMax-M3,三臂对拍):

| 臂 | 分 |
|---|---|
| 直连(题面+原始材料全给) | **16/18** |
| 过 mem0 2.2.0(默认配置,写入→检索→作答) | **11/18** |
| 过 mem0 2.2.0(写入关压缩存原文,唯一变量) | **18/18** |

**同题同模型,写入时语义压缩一项就造成 -7 分**;默认臂塌点集中在
DIM3 复发识别(4/4→1/4)。失败解剖:mem0 写入时把结构化日志压缩成叙述句,
丢的恰好是审计要查的机器可检字段(`artifact: null` 这类"无凭证"标记);
关掉压缩(存原文)即恢复满分——给记忆系统用户的第一份免费体检报告。
全工件+逐题翻转表+调参臂因果证据:
[mem0_baseline/BASELINE_REPORT.md](../../runtime/assay_bc1_20260927/mem0_baseline/BASELINE_REPORT.md)
——**你的记忆系统会不会也在这样丢分?来考一次就知道**。
