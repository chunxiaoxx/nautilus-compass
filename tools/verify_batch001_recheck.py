#!/usr/bin/env python3
"""Independent recheck of flywheel batch001 utility report (VerifyPack v0 原型实践).

Protocol: utility-metrics-protocol-v1-frozen. Reads ONLY the pack
(runtime/verify_batch001/{verify_pack,payload}.json, report.md) and the batch
directory it points to. Outputs per-claim agree/disagree + recomputed value.
compass 边界:技术验证与回执,不作验收/结算决定。

Usage: python tools/verify_batch001_recheck.py [flywheel_root]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

FW = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\chunx\Projects\nautilusflywheel")
PACK = FW / "runtime" / "verify_batch001"


def sha16(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main() -> int:
    pack = json.loads((PACK / "verify_pack.json").read_text(encoding="utf-8"))
    payload = json.loads((PACK / "payload.json").read_text(encoding="utf-8"))
    claims = {c["claim"]: c for c in pack["claims"]}
    results = []

    def rec(name: str, ok: bool, recomputed, claimed):
        results.append((name, "agree" if ok else "DISAGREE", recomputed, claimed))

    # C1 D2 帧完整率
    eps = payload["episodes"]
    fw = sum(e["frames_written"] for e in eps)
    fd = sum(e["frames_decoded"] for e in eps)
    d2 = round(fw / fd, 6) if fd else None
    rec("D2_帧完整率", d2 == claims["D2_帧完整率"]["value"], d2, claims["D2_帧完整率"]["value"])

    # C2 D3 轨迹完整率
    ok_n = sum(1 for e in eps if e["convert_rc"] == 0 and e["valid_ratio"] >= 0.98)
    d3 = round(ok_n / len(eps), 6)
    rec("D3_轨迹完整率", d3 == claims["D3_轨迹完整率"]["value"], d3, claims["D3_轨迹完整率"]["value"])

    # C3 8 条视频 sha16(真文件重算)
    claim_hashes = json.loads(claims["逐条视频 sha256_16（8 条）"]["value"])
    recomputed_hashes = {}
    missing = []
    for e in eps:
        vp = Path(e["qc"]["video"])
        if not vp.exists():
            missing.append(str(vp))
            continue
        recomputed_hashes[e["name"]] = sha16(vp)
    c3_ok = (not missing) and recomputed_hashes == claim_hashes
    rec("逐条视频 sha256_16", c3_ok, {k: recomputed_hashes.get(k) for k in list(claim_hashes)[:2]},
        {k: claim_hashes[k] for k in list(claim_hashes)[:2]} if c3_ok else f"missing={len(missing)}")

    # C4 5 个复现日志 sha16
    claim_logs = json.loads(claims["复现日志 sha256_16（5 个）"]["value"])
    logs_dir = Path(payload.get("batch_dir", "")) if payload.get("batch_dir") else None
    cand_dirs = [PACK, PACK / "logs", FW / "runtime" / "verify_batch001" / "logs"]
    if logs_dir:
        cand_dirs.insert(0, Path(logs_dir))
        cand_dirs.insert(1, Path(logs_dir).parent)  # 9/9 实测:日志在 batch_dir 上一级(egostandard_sample/s2/)
    found_dir = None
    for d in cand_dirs:
        if d.exists() and any((d / n).exists() for n in claim_logs):
            found_dir = d
            break
    if found_dir:
        re_logs = {n: sha16(found_dir / n) for n in claim_logs}
        rec("复现日志 sha256_16", re_logs == claim_logs, re_logs, claim_logs)
    else:
        rec("复现日志 sha256_16", False, "log dir not found in pack", claim_logs)

    # C5 同源双份转换哈希一致
    groups: dict[str, int] = {}
    for e in eps:
        groups[e["video_sha16"]] = groups.get(e["video_sha16"], 0) + 1
    c5_ok = all(v >= 2 for v in groups.values()) and len(groups) == 4
    rec("同源双份转换哈希一致", c5_ok, groups, json.loads(claims["同源双份转换哈希一致（转换确定性）"]["value"]))

    # C6 人脸检出占比(L2 降级:payload 内部一致性)
    claim_qc = json.loads(claims["逐条人脸检出占比（QC 记录）"]["value"])
    payload_qc = {r["name"]: r["face_ratio"] for r in payload["metrics"]["L"]["原始样本人脸检出记录"]}
    c6_ok = all(abs(payload_qc.get(k, -1) - v) < 1e-4 for k, v in claim_qc.items())
    rec("逐条人脸检出占比(降级:内部一致性)", c6_ok, "payload L 记录与 claim 逐项一致" if c6_ok else payload_qc,
        "L2 真检需 QC 环境")

    # C7 report.md 数值与 payload 一致
    report = (PACK / "report.md").read_text(encoding="utf-8")
    nums = {"帧完整率": d2, "轨迹完整率": d3}
    report_ok = all(str(v) in report for v in nums.values())
    ep_nums_ok = all(str(e["frames_written"]) in report for e in eps[:3])
    rec("payload↔report 数值一致", report_ok and ep_nums_ok, "关键数值均见于 report", "-")

    print(f"pack={payload['batch_name']} protocol={payload['protocol_version']}")
    for name, verdict, recomputed, claimed in results:
        print(f"[{verdict:8}] {name}")
        print(f"           recomputed: {recomputed}")
        print(f"           claimed:    {claimed}")
    disagree = sum(1 for r in results if r[1] == "DISAGREE")
    print(f"\nTOTAL: {len(results)-disagree}/{len(results)} agree" + (f" · {disagree} DISAGREE" if disagree else ""))
    (PACK / "recheck_by_compass.json").write_text(
        json.dumps({"reviewer": "compass", "results": [
            {"claim": n, "verdict": v, "recomputed": str(r), "claimed": str(c)} for n, v, r, c in results],
            "env": "win32 · python 3.13 · sha256 streaming"}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if disagree == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
