# -*- coding: utf-8 -*-
"""效用结算证据包管线 — 每批交付自动出具可独立复算的验证包。

用法:python ops/evidence_pack.py <batch> <readback_report.json> [criteria_version]
  例:python ops/evidence_pack.py sim50-001 /path/m1_readback_sim50.json v0.3

流程:读回报告 → payload(47 集读数+坏帧披露)→ claims(4 条,判据 v0.3 口径)
→ compass 仓 VerifyPack build+verify(subprocess)→ 包路径+回执摘要。
依赖:compass 仓本地存在(默认 C:/Users/chunx/Projects/nautilus-compass,
云 /home/ubuntu/nautilus-compass;可用 COMPASS_REPO 覆盖)。
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

COMPASS_REPO = os.environ.get(
    "COMPASS_REPO",
    r"C:\Users\chunx\Projects\nautilus-compass"
    if sys.platform == "win32" else "/home/ubuntu/nautilus-compass")

CLAIMS = [
    {"id": "C1_frame_integrity", "statement": "C1 帧完整率:written/decoded==1.0(转换零丢失)",
     "level": "L1", "value": 1.0,
     "checks": {"primary": {"kind": "aggregate", "from": "payload/payload.json#episodes",
                            "num": "sum(frames_written)", "den": "sum(frames_decoded)", "op": "ratio_eq"}}},
    {"id": "C2_parquet_integrity", "statement": "C2 数据表行数=写入帧数(真读回)",
     "level": "L1", "value": 1.0,
     "checks": {"primary": {"kind": "aggregate", "from": "payload/payload.json#episodes",
                            "num": "sum(parquet_rows)", "den": "sum(frames_written)", "op": "ratio_eq"}}},
    {"id": "C3_valid_floor", "statement": "C3 逐集有效帧率>=0.9 硬门槛(判据 v0.3)",
     "level": "L1", "value": 1.0,
     "checks": {"primary": {"kind": "aggregate", "from": "payload/payload.json#episodes",
                            "filter": [{"field": "valid_ratio", "op": ">=", "value": 0.9}],
                            "num": "count()", "den": "count()", "op": "ratio_eq"}}},
]


def make(batch: str, report_path: str, criteria_version: str = "v0.3") -> Path:
    src = Path(report_path)
    if not src.is_file():
        raise SystemExit(f"report not found: {src}")
    rows = json.loads(src.read_text(encoding="utf-8"))["rows"]
    episodes = [{"name": r["uuid"], "frames_state": r["frames_state"],
                 "frames_decoded": r["frames_decoded"], "frames_written": r["frames_written"],
                 "parquet_rows": r["parquet_rows"], "valid_ratio": r["valid_ratio"],
                 "dual_mp4": r["dual_mp4"]} for r in rows]
    payload = {"batch": batch, "criteria_version": criteria_version,
               "episodes_total": len(episodes),
               "frames_written_sum": sum(e["frames_written"] for e in episodes),
               "frames_decoded_sum": sum(e["frames_decoded"] for e in episodes),
               "parquet_rows_sum": sum(e["parquet_rows"] for e in episodes),
               "valid_min": min(e["valid_ratio"] for e in episodes),
               "valid_full_count": sum(1 for e in episodes if e["valid_ratio"] == 1.0),
               "bad_frame_episodes": [{"name": e["name"], "valid_ratio": round(e["valid_ratio"], 4)}
                                      for e in episodes if e["valid_ratio"] < 1.0],
               "episodes": episodes}

    out = Path(os.environ.get("EVIDENCE_OUT", f"docs/evidence/packs/{batch}"))
    (out / "payload").mkdir(parents=True, exist_ok=True)
    (out / "payload" / "payload.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (out / "payload" / "readback_raw.json").write_text(
        src.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    h = hashlib.sha256(src.read_bytes()).hexdigest()[:16]
    claims = CLAIMS + [{"id": "C4_report_hash", "statement": "C4 验证报告原件哈希(执行方读数正本)",
                        "level": "L1", "value": h,
                        "checks": {"primary": {"kind": "file_hash", "algo": "sha256_16",
                                               "file": "payload/readback_raw.json", "expect": h}}}]
    spec = {"pack": {"pack": f"utility_settlement_{batch}", "protocol_version": "verifypack-0.2",
                     "requested_by": "guoshu-commercial",
                     "upstream_protocol": f"m1-chain-criteria-{criteria_version}-frozen",
                     "inputs": [], "claims": claims},
            "files": {"payload/payload.json": str((out / "payload" / "payload.json").resolve()),
                      "payload/readback_raw.json": str((out / "payload" / "readback_raw.json").resolve())}}
    spec_path = out / "spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    r = subprocess.run([sys.executable, "-m", "tools.verifypack", "build",
                        "--spec", str(spec_path), "--out", str(out / "pack")],
                       cwd=COMPASS_REPO, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:] or r.stdout[-2000:], file=sys.stderr)
        raise SystemExit(f"verifypack build failed (rc={r.returncode})")
    print(r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-200:])
    v = subprocess.run([sys.executable, "-m", "tools.verifypack", "verify", str(out / "pack")],
                       cwd=COMPASS_REPO, capture_output=True, text=True)
    if v.returncode != 0:
        print(v.stderr[-2000:] or v.stdout[-2000:], file=sys.stderr)
        raise SystemExit(f"verifypack verify failed (rc={v.returncode})")
    tail = [line for line in v.stdout.splitlines() if line.strip()]
    print("\n".join(tail[-6:]))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    make(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "v0.3")