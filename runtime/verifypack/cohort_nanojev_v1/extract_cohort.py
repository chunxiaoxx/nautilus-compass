# -*- coding: utf-8 -*-
"""735 cohort 切片提取:NanoJev web/side_by_side_results.json → v0.3 §E frames。

方案=runtime/cohort_735_recon_20260924.md:6 episodes(2 局×3 系统),
注入 episode_id+t,position 格子运动不变量,collision 走 aggregate。
输出:frames.json(§E from 路径)+ manifest(三元组指纹)。
"""
import hashlib
import json
import subprocess
from pathlib import Path

SRC = Path("C:/Users/chunx/AppData/Local/Temp/nanojev-t3")
OUT = Path(__file__).parent


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    data = json.loads((SRC / "web/side_by_side_results.json").read_text(encoding="utf-8"))
    frames = []
    agg = []
    for ex in data["examples"]:
        game = ex["game"]  # e.g. maze / snake
        for sysm in ex["systems"]:
            ep_id = f"{game}-{sysm['id']}"
            raw = sysm["frames"]
            for t, fr in enumerate(raw):
                # maze: position 单点;snake: body 多节,取蛇头 body[0]
                # (贪食蛇蛇头每步恰动 1 格,格子不变量同样成立——manifest 披露)
                pos = fr.get("position") or fr["body"][0]
                frames.append({
                    "episode_id": ep_id, "t": t,
                    "x": pos[0], "y": pos[1],
                    "score": fr.get("score", 0),
                    "collision": 1 if fr.get("collision") else 0,
                    "done": 1 if fr.get("done") else 0,
                })
            agg.append({
                "episode_id": ep_id, "frames": len(raw),
                "collisions": sum(1 for f in raw if f.get("collision")),
                "final_score": raw[-1].get("score") if raw else None,
            })

    # §E from: payload/frames.json#frames
    (OUT / "frames.json").write_text(
        json.dumps({"frames": frames}, ensure_ascii=False),
        encoding="utf-8", newline="\n")

    # snake 位置语义验证:maze 网格单点;snake 若 position 恒单点(食物模型)
    # 则同样适用格子不变量——逐 episode 记录 max 单步位移供 manifest 披露
    step_max = {}
    by_ep = {}
    for f in frames:
        by_ep.setdefault(f["episode_id"], []).append(f)
    for ep, fs in by_ep.items():
        m = max((max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))
                 for a, b in zip(fs, fs[1:])), default=0)
        step_max[ep] = m

    commit = subprocess.run(
        ["git", "-C", str(SRC), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()

    manifest = {
        "cohort": "nanojev-genesis-v1",
        "spec": "VerifyPack v0.3 §E(episode check kind)",
        "episodes": len(by_ep),
        "total_frames": len(frames),
        "per_episode": agg,
        "max_step_displacement": step_max,
        "subject": {  # 三元组(沿 #635 §R 改脑即新主体)
            "repo": "TianyuCodings/NanoJev",
            "commit": commit,
            "source_manifest_sha256": sha256(SRC / "SOURCE_MANIFEST.json"),
            "frames_source_sha256": sha256(SRC / "web/side_by_side_results.json"),
        },
        "byte_convention": "LF, autocrlf=false clone",
        "extraction": "scripts: extract_cohort.py(本目录);maze position[x,y]→x/y;snake body[0](蛇头)→x/y(贪食蛇蛇头每步恰动1格,不变量同构);"
                      "collision bool→1/0;注入 episode_id/t",
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")
    print(f"episodes={len(by_ep)} frames={len(frames)}")
    print("max_step_displacement:", step_max)
    print("subject:", manifest["subject"])


if __name__ == "__main__":
    main()
