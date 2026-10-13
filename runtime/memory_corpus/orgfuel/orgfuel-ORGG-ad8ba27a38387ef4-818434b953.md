---
name: orgfuel-ORGG-ad8ba27a38387ef4-818434b953
description: "判读档判例 2026-06-03-p5-v14-poi-emission-design · 部署实测发现(2026-06"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-ad8ba27a38387ef4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission-design · 部署实测发现(2026-06-03 · verification 中挖出)
## 部署实测发现(2026-06-03 · verification 中挖出)

1. **🔴 systemd 沙箱 = emission 静默不落的真根因**:`ProtectHome=read-only` 让写 `/home/ubuntu/compass/.cache/poi` 失败,被 emit 的 try/except 吞 → 无 candidate 无报错。修 = cache 移 `/var/lib/compass/poi`(ReadWritePath)。debug 时 `PrivateTmp=true` 也让我的 /tmp trace 进了私有 /tmp(看不到)· 误导良久。
2. **云端 BGE daemon 内存页抖动**:`compass-bge-daemon.service`(serves V5 v14 recall)在 majflt 986/s · 160MB/s re-fault mmap 的 bge-m3 模型 → load 10.75 → inflight 占满 → 拒所有 recall(V5 生产降级)。根因 = 15GB 机内存超额无 swap。**修 = 加 8GB swapfile** → load 10.75→5.22 · majflt→0 · recall 15s→0.85s。
3. **live v14_recall v1.5.8 drift**:加了第二个 `if not d.get("ok")` early-return → emit anchor 改 success-return signature。
4. **pull Windows gotchas**
