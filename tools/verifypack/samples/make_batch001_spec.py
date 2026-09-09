#!/usr/bin/env python3
"""batch001 v0 包 → VerifyPack v0.2 build spec 生成器(DoD 端到端第一步)。

读 flywheel v0 包(runtime/verify_batch001),把 7 条自然语言指引的 claims
翻译成 v0.2 结构化 check,产出 build spec JSON。一次性迁移样例:此后数据方
应直接产出 v0.2 spec(或用本文件作翻译参照)。

Usage: python tools/verifypack/samples/make_batch001_spec.py [--out SPEC.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

FW_PACK = Path(r"C:\Users\chunx\Projects\nautilusflywheel\runtime\verify_batch001")
LOGS_DIR = Path(r"C:\Users\chunx\egodata\egostandard_sample\s2")


def main() -> int:
    v0 = json.loads((FW_PACK / "verify_pack.json").read_text(encoding="utf-8"))
    payload = json.loads((FW_PACK / "payload.json").read_text(encoding="utf-8"))
    claims = {c["claim"]: c for c in v0["claims"]}
    eps = payload["episodes"]

    # inputs:8 条源视频(qc.video 绝对路径)+ 5 个复现日志(batch_dir 上一级)
    inputs: list[dict] = []
    for e in eps:
        vp = Path(e["qc"]["video"])
        inputs.append({"name": f"video_{e['name']}", "path": str(vp.parent),
                       "files": [vp.name]})
    inputs.append({"name": "logs", "path": str(LOGS_DIR),
                   "files": sorted(payload["repro_log_hashes"].keys())})

    frames_needles = [{"value": str(e["frames_written"])} for e in eps[:3]]
    d2 = claims["D2_帧完整率"]["value"]
    d3 = claims["D3_轨迹完整率"]["value"]

    pack = {
        "pack": "verify_batch001",
        "protocol_version": "verifypack-0.2",
        "generated_at": v0["generated_at"],
        "requested_by": v0["requested_by"],
        "upstream_protocol": payload.get("protocol_version"),
        "inputs": inputs,
        "claims": [
            {"id": "D2_frame_integrity", "statement": "D2 帧完整率",
             "level": "L1", "value": d2,
             "checks": {"primary": {
                 "kind": "aggregate", "from": "payload/payload.json#episodes",
                 "num": "sum(frames_written)", "den": "sum(frames_decoded)",
                 "op": "ratio_eq"}}},
            {"id": "D3_track_integrity", "statement": "D3 轨迹完整率",
             "level": "L1", "value": d3,
             "checks": {"primary": {
                 "kind": "aggregate", "from": "payload/payload.json#episodes",
                 "filter": [{"field": "convert_rc", "op": "==", "value": 0},
                            {"field": "valid_ratio", "op": ">=", "value": 0.98}],
                 "num": "count()", "den": "count()", "op": "ratio_eq"}}},
            {"id": "video_hashes_8", "statement": "逐条视频 sha256_16(8 条)",
             "level": "L1",
             "value": json.loads(claims["逐条视频 sha256_16（8 条）"]["value"]),
             "checks": {"primary": {
                 "kind": "file_hash_map", "algo": "sha256_16",
                 "from": "payload/payload.json#episodes",
                 "key": "name", "path": "qc.video"}}},
            {"id": "repro_log_hashes_5", "statement": "复现日志 sha256_16(5 个)",
             "level": "L1",
             "value": json.loads(claims["复现日志 sha256_16（5 个）"]["value"]),
             "checks": {"primary": {
                 "kind": "file_hash_map", "algo": "sha256_16",
                 "names_from": "claim", "dir_decl": "logs"}}},
            {"id": "dup_conversion_determinism", "statement": "同源双份转换哈希一致(转换确定性)",
             "level": "L1",
             "value": json.loads(claims["同源双份转换哈希一致（转换确定性）"]["value"]),
             "checks": {"primary": {
                 "kind": "group_count", "from": "payload/payload.json#episodes",
                 "by": "video_sha16", "min_group": 2, "expect_groups": 4}}},
            {"id": "face_ratio_l2", "statement": "逐条人脸检出占比(QC 记录)",
             "level": "L2",
             "value": json.loads(claims["逐条人脸检出占比（QC 记录）"]["value"]),
             "checks": {
                 "primary": {"kind": "script", "repro": "repro/qc_face_ratio.py",
                             "requires_env": "qc"},
                 "fallback": {"kind": "json_map_equal",
                              "file": "payload/payload.json",
                              "path": "metrics.L.原始样本人脸检出记录",
                              "map_by": "name", "field": "face_ratio"}}},
            {"id": "report_payload_consistency", "statement": "payload 与 report.md 数值一致",
             "level": "L1", "value": "report.md",
             "checks": {"primary": {
                 "kind": "text_contains", "file": "report.md",
                 "needles": [{"claim": "D2_frame_integrity"},
                             {"claim": "D3_track_integrity"}, *frames_needles]}}},
        ],
    }
    spec_doc = {
        "pack": pack,
        "files": {
            "payload/payload.json": str(FW_PACK / "payload.json"),
            "report.md": str(FW_PACK / "report.md"),
        },
    }
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv \
        else Path("docs/verifypack/samples/batch001_spec.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec_doc, ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="\n")
    print(f"[OK] spec: {out} · claims {len(pack['claims'])} · inputs {len(inputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
