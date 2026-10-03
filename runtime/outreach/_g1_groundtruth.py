"""判读补深:①双臂全 16 帧明细 ②直接读数据集 ep0 实测 ‖act−state‖(验证零增量推断)。"""
import json
from pathlib import Path

BASE = Path("/root/vdd3/pipe_art")

print("== 双臂全部帧明细 ==")
for arm in "GB":
    rows = [json.loads(l) for l in
            (BASE / f"g1_infer_{arm}" / "infer_compare.jsonl").read_text().splitlines()
            if l.strip()]
    for r in rows:
        print(f"[{arm}] ep={r['ep']} idx={r['idx']} dir={r['dir_consistent']} "
              f"ratio={r['ratio']:.1f} pred={r['pred_head']} act={r['act_head']}")

print("\n== 数据集直接实测 ‖act−state‖(ep0 前 8 帧,双臂数据集)==")
import os
os.environ["G1_DATASET_ROOT"] = "/root/vdd2"
import sys
sys.path.insert(0, "/root/openpi/src")
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

for name in ("g1_gbatch_lerobot_v21", "g1_bbatch_lerobot_v21"):
    try:
        ds = LeRobotDataset(name, root=f"/root/vdd2/{name}",
                            video_backend="pyav", tolerance_s=0.5)
        eps_norms = []
        idxs = list(range(min(8, len(ds))))
        for i in idxs:
            item = ds[i]
            import numpy as np
            a = item["action"].numpy()[:14]
            s = item["observation.state"].numpy()[:14]
            eps_norms.append((i, round(float(np.linalg.norm(a - s)), 6),
                              round(float(np.linalg.norm(a)), 3)))
        print(f"{name}: ‖act−state‖逐帧={eps_norms}")
        print(f"  (‖act‖参考:首帧 {eps_norms[0][2]})")
    except Exception as e:
        print(f"{name}: ERR {type(e).__name__} {str(e)[:120]}")
