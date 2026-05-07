#!/usr/bin/env python3
"""Anchor auto-generator · 从用户 prompt 历史 + memory 推 anchors.

Problem: nautilus-compass 当前 anchors.json 是手写 25+35 条 · 普通用户没 ML 经验写不来.
Solution: 扫 ~/.claude/projects/<proj>/ 的 history.jsonl 提取真实 prompt
          + 简单 heuristic 抽 task pattern · 输出候选 anchors.

Usage:
  python anchor_generator.py --history ~/.claude/projects/C--Users-chunx/history.jsonl \
                             --memory ~/.claude/projects/C--Users-chunx/memory \
                             --output anchors_auto.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

# 正向 task pattern: 验证/查证/grep/cross-check/对照宪法
POSITIVE_PATTERNS = [
    (r"先\s*(?:跑|看|查|grep|read|cat|ls)", "verification-first"),
    (r"(?:对照|检查|cross.?check)", "cross-check"),
    (r"(?:验证|verify|确认)", "verify"),
    (r"(?:实测|跑.*?测试|run.*?test)", "real-test"),
    (r"(?:不要|别).*?(?:猜|编|假设)", "no-guess"),
    (r"(?:修.*?根因|root.*?cause)", "root-cause"),
    (r"(?:三\s*Yes|真客户|能收钱)", "three-yes"),
    (r"(?:简洁|简单).*?(?:>|优先|over).*?(?:复杂|巧妙)", "simple-over-clever"),
    (r"(?:看错了|改方向|重新读)", "honest-correction"),
]

# 反向 task pattern: 编/猜/凭印象/谄媚
NEGATIVE_PATTERNS = [
    (r"假装.*?(?:讨论|说定|商量过)", "fake-prior"),
    (r"(?:我猜|应该是|大概是).*?(?:反正|不查)", "guess-and-skip"),
    (r"(?:你都对|你说得对|宝贝)", "sycophancy"),
    (r"(?:看到|看着).*?(?:就是|就当|应该)", "false-confidence"),
    (r"(?:跳过|skip).*?(?:验证|测试|verify)", "skip-verify"),
    (r"(?:硬编码|hardcode).*?(?:key|password|token)", "hardcode-secret"),
    (r"(?:rm.*?-rf|taskkill.*?/F|--force)", "destructive"),
    (r"(?:重写|rewrite).*?(?:v\d+|version)", "rewrite-loop"),
    (r"代码.*?(?:不|没).*?(?:测试|跑)", "no-test"),
    (r"(?:复制|copy).*?(?:不(?:读|看)|不懂)", "copy-without-understand"),
]


def extract_user_prompts(history_path: Path, max_prompts: int = 2000) -> list[str]:
    """从 Claude Code session jsonl 或 history.jsonl 提取真用户 prompts.

    Schema (Claude Code session jsonl):
      {"type":"user","message":{"role":"user","content":"<prompt>"}}
    """
    prompts = []
    paths = []
    if history_path.is_dir():
        # 整个 project dir: 所有 session jsonl
        paths = sorted(history_path.glob("*.jsonl"))
    elif history_path.exists():
        paths = [history_path]
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    # Claude Code session jsonl
                    if rec.get("type") == "user":
                        msg = rec.get("message", {})
                        if isinstance(msg, dict) and msg.get("role") == "user":
                            content = msg.get("content")
                            if isinstance(content, str):
                                prompts.append(content)
                            elif isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        prompts.append(item.get("text", ""))
                    # ~/.claude/history.jsonl (CLI display log)
                    elif rec.get("display") and len(rec["display"]) > 5:
                        prompts.append(rec["display"])
                    if len(prompts) >= max_prompts:
                        return prompts
        except Exception:
            continue
    return prompts


def is_system_injected(text: str) -> bool:
    head = (text or "")[:300].lower()
    markers = ("<task-notification>", "<system-reminder>", "[monitor event")
    return any(m in head for m in markers)


def classify_prompt(text: str) -> tuple[list[str], list[str]]:
    """Return (positive_tags, negative_tags) matched."""
    pos_tags = [tag for pat, tag in POSITIVE_PATTERNS if re.search(pat, text)]
    neg_tags = [tag for pat, tag in NEGATIVE_PATTERNS if re.search(pat, text)]
    return pos_tags, neg_tags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", type=Path, required=False,
                    help="Claude Code history.jsonl")
    ap.add_argument("--memory", type=Path, required=False,
                    help="Project memory dir (read .md descriptions)")
    ap.add_argument("--output", type=Path, default=Path("anchors_auto.json"))
    ap.add_argument("--per-class", type=int, default=25)
    args = ap.parse_args()

    print(f"=== Anchor Auto-Generator v0.1 ===")
    pos_candidates = []
    neg_candidates = []

    # 1. From history.jsonl: real user prompts
    if args.history:
        prompts = extract_user_prompts(args.history)
        print(f"history prompts: {len(prompts)}")
        for p in prompts:
            if is_system_injected(p):
                continue
            if len(p) < 8 or len(p) > 200:
                continue
            pos_tags, neg_tags = classify_prompt(p)
            if pos_tags and not neg_tags:
                pos_candidates.append(p[:120])
            elif neg_tags and not pos_tags:
                neg_candidates.append(p[:120])

    # 2. From memory dir: extract description fields (mostly aligned content)
    if args.memory and args.memory.exists():
        for f in args.memory.glob("*.md"):
            try:
                txt = f.read_text(encoding="utf-8")
            except Exception:
                continue
            m = re.search(r"^description:\s*(.+)$", txt[:1000], re.MULTILINE)
            if m:
                pos_candidates.append(m.group(1).strip()[:120])

    print(f"\npositive candidates: {len(pos_candidates)}")
    print(f"negative candidates: {len(neg_candidates)}")

    # Dedupe + truncate to per-class
    seen_pos, seen_neg = set(), set()
    pos_uniq = []
    for c in pos_candidates:
        h = c[:50]
        if h not in seen_pos:
            seen_pos.add(h); pos_uniq.append(c)
        if len(pos_uniq) >= args.per_class:
            break
    neg_uniq = []
    for c in neg_candidates:
        h = c[:50]
        if h not in seen_neg:
            seen_neg.add(h); neg_uniq.append(c)
        if len(neg_uniq) >= args.per_class:
            break

    out = {
        "comment": (
            f"Auto-generated by anchor_generator.py · "
            f"{len(pos_uniq)} pos + {len(neg_uniq)} neg · "
            "review and edit before use!"
        ),
        "positive_anchors": pos_uniq,
        "negative_anchors": neg_uniq,
    }
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {args.output} · {len(pos_uniq)} pos + {len(neg_uniq)} neg")
    print(f"⚠️ AUTO-GENERATED · review + edit before using as anchors.json")

    # Sanity quality hint
    if len(pos_uniq) < 10 or len(neg_uniq) < 10:
        print(f"\n⚠️ candidates 太少 · 可能因为 history 太短 · 建议手写补充至 25+")


if __name__ == "__main__":
    main()
