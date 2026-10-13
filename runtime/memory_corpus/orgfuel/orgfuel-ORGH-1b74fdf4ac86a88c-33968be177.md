---
name: orgfuel-ORGH-1b74fdf4ac86a88c-33968be177
description: "commit 65a5d7ff529f 2026-09-23 fix(bc1+jev-trust): 复算抓出两份成绩单"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-1b74fdf4ac86a88c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 65a5d7ff529f 2026-09-23
fix(bc1+jev-trust): 复算抓出两份成绩单签名断链——重签+披露+0.2.1 发布
非实现者复算验签腿 RED(判分/口径两腿绿):根因=实现者签 V2 时把
pub 文件误作 seed 传 from_hex(pub-as-seed 签名+自验同错路=假
VALID);v1 系改 sha 行未重签。修复:专用密钥(seed 存 .cache 不
入仓,pub=be070105…)重签两份+「签名记录」披露段(事件留档不删)
+披露后二次重签,外部视角直验双 VALID。jev-trust 0.2.1 发布
(KeyPair pub 保留+pub_from_seed 修复,33 测试过,PyPI 独立装版
pub-preserving 实测 0.2.1)。
