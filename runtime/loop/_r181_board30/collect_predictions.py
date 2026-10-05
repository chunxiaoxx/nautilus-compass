# -*- coding: utf-8 -*-
"""L3 Round 1 判分前置: 双臂 patch 收集 → swebench predictions.json ×2.

坐标:
  A 臂 nautilus-v5/tools/uni_agent_bridge/e5_workdirs/task_{idx}_{run_id}/trajectory.json (final_patch 字段)
  B 臂 runtime/loop/_r181_board30/board_b/task_{idx}/patch.diff
对齐: tasks.json idx→instance_id (A 臂 idx 从 1 起, B 臂从 0 起).
输出: preds_arm_a.json / preds_arm_b.json (swebench 官方格式).
"""
import json
from pathlib import Path

BOARD = Path(__file__).resolve().parent
V5_WD = Path("C:/Users/chunx/nautilus-v5/tools/uni_agent_bridge/e5_workdirs")

MODEL_A = "l3r1a_v5-harness-4e14a898+ms50_MiniMax-M3"
MODEL_B = "l3r1b_mini-swe-agent-2.4.6+ms50_MiniMax-M3"


def latest_traj(idx: int):
    """A 臂同 idx 多 run_id 目录取最新; 只认 session_id 前缀 l3r1a_
    (e5_workdirs 与 daemon 日批共用目录树, 按 session_id 隔离防抓错批)."""
    for p in sorted(V5_WD.glob(f"task_{idx}_*/trajectory.json"), reverse=True):
        try:
            t = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if str(t.get("session_id", "")).startswith("l3r1a_"):
            return p, t
    return None, None


def collect(tasks):
    out_a, out_b = [], []
    for t in tasks:
        idx0 = t["idx"]
        # A 臂 idx=idx0+1
        tp, traj = latest_traj(idx0 + 1)
        patch_a = ""
        note_a = ""
        if tp is None:
            note_a = "missing_trajectory"
        else:
            patch_a = traj.get("final_patch") or ""
            if not traj.get("env_ready"):
                note_a = "env_bare"
        out_a.append({
            "instance_id": t["instance_id"],
            "model_name_or_path": MODEL_A,
            "model_patch": patch_a,
            "_note": note_a,
        })
        # B 臂
        bp = BOARD / "board_b" / f"task_{idx0}" / "patch.diff"
        patch_b = bp.read_text(encoding="utf-8") if bp.exists() else ""
        rp = BOARD / "board_b" / f"task_{idx0}" / "result.json"
        note_b = ""
        if rp.exists():
            rec = json.loads(rp.read_text(encoding="utf-8"))
            if rec.get("status") != "ok":
                note_b = f"runner_{rec.get('status')}"
        out_b.append({
            "instance_id": t["instance_id"],
            "model_name_or_path": MODEL_B,
            "model_patch": patch_b,
            "_note": note_b,
        })
    return out_a, out_b


def main():
    tasks = json.loads((BOARD / "tasks.json").read_text(encoding="utf-8"))
    out_a, out_b = collect(tasks)
    for name, rows in (("preds_arm_a.json", out_a), ("preds_arm_b.json", out_b)):
        p = BOARD / name
        p.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        nonempty = sum(1 for r in rows if r["model_patch"].strip())
        print(f"{name}: {len(rows)} preds, patch nonempty {nonempty}, "
              f"notes {sum(1 for r in rows if r['_note'])}")
    # instance_id 双臂一致性
    ids_a = [r["instance_id"] for r in out_a]
    ids_b = [r["instance_id"] for r in out_b]
    assert ids_a == ids_b == [t["instance_id"] for t in tasks], "instance_id mismatch"
    print("instance_id alignment OK (30/30)")


if __name__ == "__main__":
    main()
