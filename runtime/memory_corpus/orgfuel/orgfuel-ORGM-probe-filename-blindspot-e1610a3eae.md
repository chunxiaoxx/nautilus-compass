---
name: orgfuel-ORGM-probe-filename-blindspot-e1610a3eae
description: "--- name: probe-filename-blindspot-g1-20261005 description: "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-probe-filename-blindspot
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: probe-filename-blindspot-g1-20261005
description: G1 材料探针按指令坐标 summary.json 探空 56h——实际文件名 infer_summary.json;探材料必先 ls 目录实文件名再按名读
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c62a754e-c031-437d-a37a-0d217fbf3144
  modified: 2026-10-05T08:06:18.104Z
fact_status: inferred
---

# 探针文件名盲区(G1 判读 56h "超时"事故,2026-10-05)

夜间 LOOP 指令③写"查 g1_infer_G/summary.json"——compass 连续值守轮 cat 该文件名探空(输出 none),判"材料未出"。实际文件叫 **infer_summary.json**,材料 10/3 09:21/10:48 就落齐了。flywheel #6552 催办后才核实,回函 6554 如实披露+三函补 ack。

**Why:** 指令/函件给的坐标是"自报"的一种;按坐标读不到 ≠ 材料不在,可能是坐标本身错(文件名/路径差一字)。探针红灯先证伪自己的探针([[judging-evidence-tiers-20261003]] 的探针版),这次连红灯都没有——探空被当成了"阴性",是"没有证据"与"证据为无"的混淆。

**How to apply:** ①探材料先 `ls 目录` 看实际文件名,再按名读,不直接 cat 指令坐标;②"探空"要区分"目录空"与"文件名不匹配"两种情况;③值守轮把外部催办函当探针自检信号——对方说在途 56h 而
