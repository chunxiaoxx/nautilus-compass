"""Session image surgeon · remove only invalid images from a Claude Code jsonl.

Preserves all text content + valid images + message structure.

Validation per image content block:
  1. base64 decodes cleanly
  2. decoded payload <= 5 MB (Anthropic limit)
  3. magic bytes match a supported format (jpeg/png/gif/webp)
  4. (optional) Pillow can open it · skipped if Pillow not available

Bad image blocks are replaced with a text block:
    {"type": "text", "text": "[image removed by surgeon: <reason>]"}

This keeps the message envelope intact so Claude Code can replay the session.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import sys
from pathlib import Path

MAX_IMG_BYTES = 5 * 1024 * 1024  # Anthropic limit
SUPPORTED_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",  # webp = RIFF...WEBP
}

try:
    from PIL import Image  # type: ignore
    import io
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False


def detect_format(data: bytes) -> str | None:
    for magic, fmt in SUPPORTED_MAGIC.items():
        if data.startswith(magic):
            if fmt == "image/webp" and b"WEBP" not in data[:32]:
                continue
            return fmt
    return None


def validate_image(block: dict) -> tuple[bool, str]:
    """Return (is_valid, reason_if_invalid)."""
    src = block.get("source") or {}
    if src.get("type") != "base64":
        return True, ""  # we only handle base64 images
    b64 = src.get("data") or ""
    if not b64:
        return False, "empty base64"
    try:
        raw = base64.b64decode(b64, validate=False)
    except (binascii.Error, ValueError) as e:
        return False, f"base64 decode error: {e}"
    if len(raw) > MAX_IMG_BYTES:
        return False, f"too large {len(raw)} > {MAX_IMG_BYTES}"
    fmt = detect_format(raw)
    if not fmt:
        return False, f"unsupported magic {raw[:8].hex()}"
    declared = src.get("media_type")
    if declared and declared != fmt:
        return False, f"media_type mismatch declared={declared} actual={fmt}"
    if HAVE_PIL:
        try:
            img = Image.open(io.BytesIO(raw))
            img.verify()
        except Exception as e:
            return False, f"PIL verify failed: {type(e).__name__}: {e}"
    return True, ""


def patch_content_array(content: list, line_no: int, stats: dict) -> list:
    """Recursively patch image blocks · handles tool_result wrappers etc."""
    out = []
    for blk in content:
        if not isinstance(blk, dict):
            out.append(blk)
            continue
        btype = blk.get("type")
        if btype == "image":
            stats["total_images"] += 1
            ok, reason = validate_image(blk)
            if ok:
                stats["valid_images"] += 1
                out.append(blk)
            else:
                stats["bad_images"] += 1
                stats["bad_reasons"].append(f"L{line_no}: {reason}")
                out.append({
                    "type": "text",
                    "text": f"[image removed by surgeon: {reason}]",
                })
        elif btype == "tool_result" and isinstance(blk.get("content"), list):
            # tool_result may contain a nested content array with images inside
            blk["content"] = patch_content_array(blk["content"], line_no, stats)
            out.append(blk)
        else:
            out.append(blk)
    return out


def patch_message(msg: dict, line_no: int, stats: dict) -> dict:
    """Walk the canonical Claude Code message shapes and patch image arrays."""
    # Top-level shape: {"type":"user"|"assistant","message":{"role":...,"content":[...]}}
    inner = msg.get("message")
    if isinstance(inner, dict):
        content = inner.get("content")
        if isinstance(content, list):
            inner["content"] = patch_content_array(content, line_no, stats)
    # Defensive: also patch top-level content if present
    content = msg.get("content")
    if isinstance(content, list):
        msg["content"] = patch_content_array(content, line_no, stats)
    return msg


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("jsonl", type=Path)
    p.add_argument("--out", type=Path, required=True,
                   help="output path · MUST differ from input")
    p.add_argument("--strip-all-images", action="store_true",
                   help="remove every image regardless of validity (last resort)")
    args = p.parse_args()

    if args.out == args.jsonl:
        print("ERROR: --out must differ from input (we never edit in place)")
        return 2

    stats = {
        "lines": 0, "skipped_lines": 0,
        "total_images": 0, "valid_images": 0, "bad_images": 0,
        "bad_reasons": [],
    }

    with args.jsonl.open("r", encoding="utf-8", errors="replace") as fin, \
         args.out.open("w", encoding="utf-8") as fout:
        for line_no, line in enumerate(fin, 1):
            line = line.rstrip("\n")
            if not line:
                fout.write("\n")
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError as e:
                stats["skipped_lines"] += 1
                fout.write(line + "\n")  # preserve unknown · don't break flow
                continue
            if args.strip_all_images:
                # Treat every image as bad
                def _strip_all(content, ln, st):
                    res = []
                    for b in content:
                        if not isinstance(b, dict):
                            res.append(b); continue
                        bt = b.get("type")
                        if bt == "image":
                            st["total_images"] += 1
                            st["bad_images"] += 1
                            res.append({"type":"text","text":"[image stripped by --strip-all-images]"})
                        elif bt == "tool_result" and isinstance(b.get("content"), list):
                            b["content"] = _strip_all(b["content"], ln, st)
                            res.append(b)
                        else:
                            res.append(b)
                    return res
                # patch via _strip_all
                inner = msg.get("message")
                if isinstance(inner, dict) and isinstance(inner.get("content"), list):
                    inner["content"] = _strip_all(inner["content"], line_no, stats)
                if isinstance(msg.get("content"), list):
                    msg["content"] = _strip_all(msg["content"], line_no, stats)
            else:
                msg = patch_message(msg, line_no, stats)
            fout.write(json.dumps(msg, ensure_ascii=False) + "\n")
            stats["lines"] += 1

    print(f"lines processed: {stats['lines']}")
    print(f"lines skipped (parse error): {stats['skipped_lines']}")
    print(f"total image blocks: {stats['total_images']}")
    print(f"  valid kept: {stats['valid_images']}")
    print(f"  bad replaced: {stats['bad_images']}")
    if stats["bad_reasons"]:
        print("first 10 bad reasons:")
        for r in stats["bad_reasons"][:10]:
            print(f"  · {r}")
    print(f"PIL validate: {'on' if HAVE_PIL else 'off (install Pillow for stricter check)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
