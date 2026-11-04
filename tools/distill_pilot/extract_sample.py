#!/usr/bin/env python3
"""D1 正文抽取:按 sample_manifest.json 抽 50 会话的 user/assistant 正文。

输出 extracted/<session_id>.txt(带角色/行号/时间戳标记)+ extraction_stats.json。
工具输出/tool_use/tool_result/image/thinking 全部跳过;原始 jsonl 只读。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def iter_text(content: object) -> list[str]:
    if isinstance(content, str):
        return [content] if content else []
    out: list[str] = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    out.append(text)
    return out


def extract_file(path: Path, out_path: Path) -> dict:
    n_user = n_asst = 0
    extracted_bytes = 0
    with path.open("r", encoding="utf-8", errors="replace") as src, \
            out_path.open("w", encoding="utf-8") as dst:
        for lineno, line in enumerate(src, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg_type = obj.get("type")
            if msg_type not in ("user", "assistant"):
                continue
            texts = iter_text((obj.get("message") or {}).get("content"))
            if not texts:
                continue
            joined = "\n".join(texts)
            ts = obj.get("timestamp", "")
            role = "u" if msg_type == "user" else "a"
            header = f"=== {role} #{lineno} {ts} ==="
            block = f"{header}\n{joined}\n"
            dst.write(block)
            extracted_bytes += len(block.encode("utf-8"))
            if msg_type == "user":
                n_user += 1
            else:
                n_asst += 1
    return {
        "session_id": path.stem,
        "source_bytes": path.stat().st_size,
        "extracted_bytes": extracted_bytes,
        "ratio": round(extracted_bytes / path.stat().st_size, 4) if path.stat().st_size else 0.0,
        "n_user_msg": n_user,
        "n_asst_msg": n_asst,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True, help="产物目录(与 manifest 同目录)")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    out_dir = Path(args.out).expanduser()
    extracted_dir = out_dir / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for group, entries in manifest["groups"].items():
        for entry in entries:
            src = Path(entry["path"])
            if not src.exists():
                print(f"warn: missing {src}", file=sys.stderr)
                continue
            stat = extract_file(src, extracted_dir / f"{src.stem}.txt")
            stat["group"] = group
            results.append(stat)

    stats = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_sessions": len(results),
        "total_source_bytes": sum(r["source_bytes"] for r in results),
        "total_extracted_bytes": sum(r["extracted_bytes"] for r in results),
        "sessions": results,
    }
    stats_path = out_dir / "extraction_stats.json"
    stats_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    overall = stats["total_extracted_bytes"] / max(1, stats["total_source_bytes"])
    print(
        f"extracted {len(results)} sessions, "
        f"{stats['total_source_bytes']:,}B -> {stats['total_extracted_bytes']:,}B "
        f"(overall ratio {overall:.4f})\nstats -> {stats_path}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
