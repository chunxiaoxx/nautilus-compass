---
name: orgfuel-ORGM-compass-daemon-pylibs-ro-0cb904525a
description: "--- name: compass-daemon-pylibs-rootcause-20260830 descripti"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-compass-daemon-pylibs-ro
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: compass-daemon-pylibs-rootcause-20260830
description: compass daemon 1322 次 recall 失败根因=启动脚本注入 PYTHONPATH=C:\pylibs 旧库快照;HUD 丢失/报错同源;修=移除注入改用 site-packages
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-08-29T18:05:29.081Z
---

# compass daemon 长期报错根因 · PYTHONPATH=C:\pylibs(2026-08-30 修复)

**现象**:HUD COMPASS 丢失不稳定 + "compass 一直报错" + `daemon.log` 累计 **1322 次** `conn handler fail: Could not import module 'PreTrainedModel'`,每次请求触发 BGE 加载→秒挂。

**根因链**:
1. `daemon_start.ps1` / `daemon_start.sh` 启动命令注入 `PYTHONPATH=C:\pylibs`(2026-08-23 的"torch 短路径防 WinError 206"修复)
2. `C:\pylibs` 是 2026-07 时代的整套旧库快照(旧 transformers/st/torch),**优先于 site-packages**
3. 旧 transformers 的 lazy import 炸(`import_utils.py` `_LazyModule.__ge
