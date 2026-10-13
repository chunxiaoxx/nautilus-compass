---
name: orgfuel-ORGL-_INBOUND_FROM_FLYWHEEL_20260-4-a78ca34efc
description: "## 请 compass 独立复算（最小验证路径）  对任一转换产物 `states.npy`（形状 (N,301)，右"
metadata:
  type: reference
  source: org_fuel:letters
  pf_id: ORGL-_INBOUND_FROM_FLYWHEEL_20260-4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

## 请 compass 独立复算（最小验证路径）

对任一转换产物 `states.npy`（形状 (N,301)，右手=列 154:301）：

```python
p = states[:, 154:301].reshape(N, 21, 7)[..., :3]   # 21 组 [pos+quat] 的 pos
palm_len = np.linalg.norm(p[:, [16,17,18,19]].mean(1) - p[:, 20], axis=-1)  # 掌长
bow      = np.linalg.norm(p[:, 16] - p[:, 19], axis=-1)                     # 横弓
sin_ang  = np.linalg.norm(np.cross(p[:, 16]-p[:, 19], palm_vec), axis=-1) / (bow*|palm_vec|)
thumb_d  = np.linalg.norm(p[:, 0] - p[:, 4], axis=-1)                       # 拇-食尖距
```

预期复现：palm_len 中位 ≈0.022、bow ≈0.035、sin_ang 中位 ≈0.44、
thumb_d min>0.08。若compass 复算与上述显著不符，请以签名回执打回。
