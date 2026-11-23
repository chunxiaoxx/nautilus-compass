#!/usr/bin/env python3
"""D1 正文抽取:按 sample_manifest.json 抽 50 会话的 user/assistant 正文。

输出 extracted/<session_id>.txt(带角色/行号/时间戳标记)+ extraction_stats.json。
默认抽取正文。显式选择工具证据时，附带有界调用和返回记录及原文位置。
image/thinking 块跳过，原始 jsonl 只读。
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from publish_to_memory import atomic_write


def iter_text(content: object) -> list[str]:
    if isinstance(content, str):
        return [content] if content else []
    out: list[str] = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if isinstance(text, str) and text:
                    out.append(text)
    return out


def set_excerpt(record: dict, text: str, limit: int) -> None:
    """Keep source head/tail separately so omitted content stays explicit."""
    if len(text) <= limit:
        record.update(text_head=text, text_tail="")
    else:
        head = (limit + 1) // 2
        tail = limit // 2
        record.update(text_head=text[:head], text_tail=text[-tail:] if tail else "")
    record["omitted_text_chars"] = record["text_chars"] - len(record["text_head"]) - len(record["text_tail"])


def tool_record(obj: dict, block: dict, line: int, index: int,
                line_sha: str, excerpt_chars: int) -> dict:
    kind = block["type"]
    record = {
        "kind": kind, "source_line": line, "source_block": index,
        "source_line_sha256": line_sha, "message_uuid": obj.get("uuid"),
        "timestamp": obj.get("timestamp", ""),
        "tool_use_id": block.get("id" if kind == "tool_use" else "tool_use_id"),
    }
    if kind == "tool_use":
        record["tool_name"] = block.get("name")
        text = json.dumps(block.get("input"), ensure_ascii=False, sort_keys=True)
        record["text_encoding"] = "canonical_json_input"
    else:
        text = "\n".join(iter_text(block.get("content")))
        record["text_encoding"] = "text_blocks_joined_with_newline"
        record["source_assistant_uuid"] = obj.get("sourceToolAssistantUUID")
        flag = block.get("is_error")
        record["reported_is_error"] = flag if isinstance(flag, bool) else None
        metadata = obj.get("toolUseResult")
        if isinstance(metadata, dict):
            record["reported_exit_codes"] = {
                key: metadata[key]
                for key in ("exit_code", "exitCode", "return_code", "returncode")
                if type(metadata.get(key)) is int
            }
    record["text_chars"] = len(text)
    record["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    set_excerpt(record, text, excerpt_chars)
    return record


def link_tool_results(records: list[dict], calls: dict) -> None:
    for record in records:
        if record["kind"] != "tool_result":
            continue
        identifier = record["tool_use_id"]
        matches = calls.get(identifier, []) if isinstance(identifier, str) else []
        parent = record["source_assistant_uuid"]
        if isinstance(parent, str) and parent:
            matches = [call for call in matches if call["message_uuid"] == parent]
        record["call_match"] = {
            "status": "matched" if len(matches) == 1 else "ambiguous" if matches else "unmatched",
            "candidate_count": len(matches), "candidates": matches[:4],
        }
        if len(matches) == 1:
            record["tool_name"] = matches[0]["tool_name"]


def extract_file(path: Path, out_path: Path, *, include_tool_evidence: bool = False,
                 tool_record_limit: int = 96, tool_excerpt_chars: int = 2048,
                 tool_budget_chars: int = 65536) -> dict:
    if path.resolve() == out_path.resolve():
        raise ValueError("Extraction output must differ from the original session")
    if any(type(value) is not int or value < 0
           for value in (tool_record_limit, tool_excerpt_chars, tool_budget_chars)):
        raise ValueError("Tool evidence limits must be nonnegative integers")
    n_user = n_asst = 0
    entries = []
    first_records = []
    head_limit = (tool_record_limit + 1) // 2
    tail_records = deque(maxlen=tool_record_limit // 2)
    calls = defaultdict(list)
    tool_count = 0
    source_hash = hashlib.sha256()
    with path.open("rb") as src:
        before = os.fstat(src.fileno())
        for lineno, raw_line in enumerate(src, 1):
            source_hash.update(raw_line)
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            msg_type = obj.get("type")
            if msg_type not in ("user", "assistant"):
                continue
            message = obj.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if include_tool_evidence and isinstance(content, list):
                for index, block in enumerate(content):
                    if not isinstance(block, dict) or block.get("type") not in ("tool_use", "tool_result"):
                        continue
                    record = tool_record(obj, block, lineno, index,
                                         hashlib.sha256(raw_line).hexdigest(), tool_excerpt_chars)
                    tool_count += 1
                    if record["kind"] == "tool_use" and isinstance(record["tool_use_id"], str):
                        calls[record["tool_use_id"]].append({
                            key: record[key] for key in
                            ("source_line", "source_block", "message_uuid", "tool_name")
                        })
                    if len(first_records) < head_limit:
                        first_records.append(record)
                    else:
                        tail_records.append(record)
            texts = iter_text(content)
            if not texts:
                continue
            joined = "\n".join(texts)
            ts = obj.get("timestamp", "")
            role = "u" if msg_type == "user" else "a"
            header = f"=== {role} #{lineno} {ts} ==="
            provenance = ""
            if obj.get("isApiErrorMessage"):
                provenance = ("[来源类别: chat_api_error。仅证明会话接口报错，"
                              "没有被评测服务端点的绑定证据。]\n")
            block = f"{header}\n{provenance}{joined}\n"
            entries.append((lineno, -1, block))
            if msg_type == "user":
                n_user += 1
            else:
                n_asst += 1
        after = os.fstat(src.fileno())
    current = path.stat()
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
    if identity(before) != identity(after) or identity(after) != identity(current):
        raise RuntimeError("Source session changed during extraction")
    if before.st_ctime_ns != current.st_ctime_ns:
        # File-provider metadata can change while bytes and mtime stay stable.
        # Rebind the bytes instead of treating a metadata-only update as content.
        if hashlib.sha256(path.read_bytes()).hexdigest() != source_hash.hexdigest():
            raise RuntimeError("Source session changed during extraction")
    metadata = None
    if include_tool_evidence:
        records = first_records + list(tail_records)
        link_tool_results(records, calls)
        excerpt_total = sum(len(r["text_head"]) + len(r["text_tail"]) for r in records)
        if excerpt_total > tool_budget_chars:
            per_record = tool_budget_chars // max(1, len(records))
            for record in records:
                set_excerpt(record, record["text_head"] + record["text_tail"], per_record)
        metadata = {
            "schema": "distill-tool-evidence/1", "source_sha256": source_hash.hexdigest(),
            "source_record_types": ["user", "assistant"],
            "tool_records_seen": tool_count, "tool_records_emitted": len(records),
            "tool_records_omitted": tool_count - len(records),
            "truncated_records": sum(r["omitted_text_chars"] > 0 for r in records),
            "excerpt_chars": sum(len(r["text_head"]) + len(r["text_tail"]) for r in records),
            "limits": {"records": tool_record_limit, "per_record_chars": tool_excerpt_chars,
                       "total_excerpt_chars": tool_budget_chars},
            "scope": "历史调用与返回记录。调用条目只证明请求，is_error保留来源值。"
                     "按原文行号及时间核对状态，截断或省略部分需召回原文。",
        }
        entries.insert(0, (0, -1, "=== source_evidence #0 ===\n" + json.dumps(metadata, ensure_ascii=False) + "\n"))
        for record in records:
            header = f"=== {record['kind']} #{record['source_line']} {record['timestamp']} ==="
            entries.append((record["source_line"], record["source_block"],
                            header + "\n" + json.dumps(record, ensure_ascii=False) + "\n"))
    payload = "".join(block for _, _, block in sorted(entries)).encode("utf-8")
    atomic_write(out_path, payload)
    result = {
        "session_id": path.stem,
        "source_bytes": before.st_size,
        "extracted_bytes": len(payload),
        "ratio": round(len(payload) / before.st_size, 4) if before.st_size else 0.0,
        "n_user_msg": n_user,
        "n_asst_msg": n_asst,
    }
    if metadata is not None:
        result["tool_evidence"] = metadata
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True, help="产物目录(与 manifest 同目录)")
    parser.add_argument("--include-tool-evidence", action="store_true")
    parser.add_argument("--tool-record-limit", type=int, default=96)
    parser.add_argument("--tool-excerpt-chars", type=int, default=2048)
    parser.add_argument("--tool-budget-chars", type=int, default=65536)
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
            stat = extract_file(src, extracted_dir / f"{src.stem}.txt",
                                include_tool_evidence=args.include_tool_evidence,
                                tool_record_limit=args.tool_record_limit,
                                tool_excerpt_chars=args.tool_excerpt_chars,
                                tool_budget_chars=args.tool_budget_chars)
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
