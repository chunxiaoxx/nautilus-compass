---
name: orgfuel-ORGG-f5265c087f546e05-dddbbacec0
description: "判读档判例 S6_RECHECK_FIX_20261008 · 实锤①:正本坐标不可寻址 → 已修 ## 实锤①:正本坐"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f5265c087f546e05
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 S6_RECHECK_FIX_20261008 · 实锤①:正本坐标不可寻址 → 已修
## 实锤①:正本坐标不可寻址 → 已修

- **根因 [实测]**:split_train_v1/split_dev_v1/split_test_v1 三件语料正本被 .gitignore 静默挡住**从未 commit**——GitHub 上不存在,云工作树(999b6541 旧版)更无;平台按云侧找自然 5 件不符。这是 compass 侧真实缺陷,复核有价值。
- **修复 [实测]**:三件+anchor_v0+reg100 强制入仓(commit 00d29232,pushed);cloud 侧 fresh clone 只读正本镜像 `/home/ubuntu/compass-registry-mirror` @ **00d2923**,六件逐件存在性验证 OK(在役树不动,daemon.py 本地修改不受影响)。

**正本坐标(可公开寻址)**:
- 仓:`https://github.com/chunxiaoxx/nautilus-compass` @ commit **00d29232**(main HEAD,随主线滚动,复核时以"当时 HEAD"为锚)
- 六件路径(仓根相对):`docs/metering/L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md` / `docs/metering/PRECOR_BC_VERDICT_20261007.md` / `docs/metering/PRECOR_ENACRE1_VERDICT_20261007.md` / `runtime/verdict_corpus/split_train_v1.jsonl` / `runtime/verdict_corpus/split_t
