#!/usr/bin/env python3
"""D1 锚点核验器(J1 判据的机械层):摘要中的锚点必须能在源文命中。

锚点类型: 日期/中文日期/路径/URL/长hex(md5,sha)/带标签ID(CS-x,GH-x,#n,函 n)。
用法:
  anchor_check.py --summary 摘要.txt --source 源.txt [--out 结果.json]
  anchor_check.py --selftest --source 源.txt   # 冒烟:3 真+2 假锚点,期望 3/5
输出: 逐锚点判定 + 可回溯率。不做语义判断,语义层归大模型盲评(L2)。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ANCHOR_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("date", re.compile(r"\d{4}-\d{2}-\d{2}")),
    ("date_cn", re.compile(r"\d{1,2}月\d{1,2}[日号]")),
    ("url", re.compile(r"https?://[^\s\"'\)\]\}>,，。；、：）]+")),
    ("hex32", re.compile(r"\b[0-9a-f]{32,64}\b")),
    ("tag_id", re.compile(r"\b(?:CS|GH|PR|UT|RFC)-?\d{1,5}\b|#\d{3,6}\b|函\s?\d{4,6}")),
    ("path", re.compile(r"(?:[\w.@+-]+/){1,}[\w.@+-]+")),
]
PATH_MIN_LEN = 6
CJK_RE = re.compile(r"[一-鿿]")
SUMMARY_BODY_MARK = "# 总纪要"
TRAILING_PUNCT = "`'\".,;:：，。；、)]）】》"


def date_variants(value: str) -> list[str]:
    """中文日期/斜杠日期生成可等价匹配的变体(测源文原样存在其一即算命中)。"""
    cn = re.match(r"(\d{1,2})月(\d{1,2})", value)
    if cn:
        m, d = int(cn.group(1)), int(cn.group(2))
        return [value, f"{m:02d}-{d:02d}", f"{m}/{d:02d}", f"{m:d}/{d:d}",
                f"{m:02d}/{d:02d}", f"2026-{m:02d}-{d:02d}", f"2025-{m:02d}-{d:02d}"]
    return [value]


def strip_preamble(summary_text: str) -> str:
    """去掉蒸馏器落盘的元信息行(源文件名/生成时间),不依赖模型是否写标题。"""
    lines = [
        line for line in summary_text.splitlines()
        if not line.startswith(("- 源:", "- 生成:", "# 蒸馏纪要"))
    ]
    return "\n".join(lines)


def collect_anchors(text: str) -> list[dict]:
    """按 pattern 顺序收集锚点,去重叠(先到先得),path 加最短长度过滤。"""
    spans: list[tuple[int, int, str, str]] = []
    for name, pattern in ANCHOR_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0)
            if name == "path" and len(value) < PATH_MIN_LEN:
                continue
            spans.append((match.start(), match.end(), name, value))
    spans.sort()
    picked: list[dict] = []
    last_end = -1
    for start, end, name, value in spans:
        if start < last_end:
            continue  # 与已选锚点重叠,先到先得
        value = value.rstrip(TRAILING_PUNCT)  # 模型复述常粘尾标点(反引号/引号/全角括号)
        if len(value) < 4:
            continue
        picked.append({"type": name, "value": value})
        last_end = end
    return picked


def check(summary: str, source: str) -> dict:
    anchors = collect_anchors(strip_preamble(summary))
    for anchor in anchors:
        if CJK_RE.search(anchor["value"]) and anchor["type"] == "path":
            anchor["matched"] = False
            anchor["note"] = "cjk-false-path-excluded"
            continue
        variants = date_variants(anchor["value"]) if anchor["type"] == "date_cn" else [anchor["value"]]
        anchor["matched"] = any(v in source for v in variants)
    n_valid = sum(1 for a in anchors if "note" not in a)
    n_matched = sum(1 for a in anchors if a["matched"])
    rate = (n_matched / n_valid) if n_valid else None
    return {
        "n_anchors": len(anchors),
        "n_valid": n_valid,
        "n_matched": n_matched,
        "traceable_rate": rate,
        "anchors": anchors,
    }


def selftest(source_text: str) -> bool:
    """从源文找 3 个真锚点(排除中文假路径),加 2 个伪造锚点,期望恰好 3/5 可回溯。"""
    real = [
        a["value"]
        for a in collect_anchors(source_text)
        if len(a["value"]) >= 6 and not CJK_RE.search(a["value"])
    ]
    if len(real) < 3:
        print(f"selftest inconclusive: source only has {len(real)} anchors", file=sys.stderr)
        return False
    fake = ["CS-99999", "/definitely/not/a/real/path.md"]
    summary = " ".join(real[:3] + fake)
    result = check(summary, source_text)
    ok = (
        result["n_anchors"] == 5
        and result["n_valid"] == 5
        and result["n_matched"] == 3
        and result["traceable_rate"] == 0.6
    )
    print(
        f"selftest: {result['n_matched']}/{result['n_anchors']} "
        f"rate={result['traceable_rate']} -> {'PASS' if ok else 'FAIL'}",
        file=sys.stderr,
    )
    for anchor in result["anchors"]:
        print(f"  [{anchor['type']}] {anchor['value'][:60]} matched={anchor['matched']}", file=sys.stderr)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary")
    parser.add_argument("--source", required=True)
    parser.add_argument("--out")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    source_text = Path(args.source).read_text(encoding="utf-8", errors="replace")

    if args.selftest:
        return 0 if selftest(source_text) else 1
    if not args.summary:
        parser.error("--summary required unless --selftest")

    summary_text = Path(args.summary).read_text(encoding="utf-8", errors="replace")
    result = check(summary_text, source_text)
    result["summary"] = args.summary
    result["source"] = args.source
    report = json.dumps(result, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
