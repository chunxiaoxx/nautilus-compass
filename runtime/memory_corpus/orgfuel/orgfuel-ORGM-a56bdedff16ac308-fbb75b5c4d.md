---
name: orgfuel-ORGM-a56bdedff16ac308-fbb75b5c4d
description: "记忆条目 compass-daemon-pylibs-rootcause-20260830.md # compass d"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-a56bdedff16ac308
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 compass-daemon-pylibs-rootcause-20260830.md
# compass daemon 长期报错根因 · PYTHONPATH=C:\pylibs(2026-08-30 修复)

**现象**:HUD COMPASS 丢失不稳定 + "compass 一直报错" + `daemon.log` 累计 **1322 次** `conn handler fail: Could not import module 'PreTrainedModel'`,每次请求触发 BGE 加载→秒挂。

**根因链**:
1. `daemon_start.ps1` / `daemon_start.sh` 启动命令注入 `PYTHONPATH=C:\pylibs`(2026-08-23 的"torch 短路径防 WinError 206"修复)
2. `C:\pylibs` 是 2026-07 时代的整套旧库快照(旧 transformers/st/torch),**优先于 site-packages**
3. 旧 transformers 的 lazy import 炸(`import_utils.py` `_LazyModule.__getattr__` 兜底,cause 被 daemon except 吃掉只见表面文本)
4. → daemon 永远加载不出 BGE → 所有 recall/drift/HUD 失败;HUD wrapper 每次冷启动连不上 → "HUD 总是丢失"

**修复**(2026-08-30):两个启动脚本移除 pylibs 注入。前提已成立:Store Python site-packages 现有 torch 2.11.0+cpu + transformers 5.16.1 + sentence-transformer
