#!/usr/bin/env python3
"""CS-GS-005 打包前密钥清洗(2026-10-29 bait 轮)。

依据: GS005_STRUCTURE_GAP_20261029.md 密钥警示节 —— 题包任何外发/交付前
必须先做密钥清洗。本脚本只清洗 pkg/CS-GS-005 交付副本,仓内工作副本不动。
命中替换为 <前缀>REDACTED_GS005(保留形态可读性,灭活内容)。
替换日志落 secret_scrub_log_20261029.md,替换后全包复扫必须零命中。
"""
import re
import sys
from pathlib import Path

PKG = Path(__file__).parent / "pkg" / "CS-GS-005"

PATTERNS = [
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "github_pat_REDACTED_GS005"),
    ("ghp", re.compile(r"gh[pou]_[A-Za-z0-9]{20,}"), "ghp_REDACTED_GS005"),
    ("google_oauth", re.compile(r"GOCSPX-[A-Za-z0-9_-]{10,}"), "GOCSPX-REDACTED"),
    ("google_api", re.compile(r"AIza[A-Za-z0-9_-]{20,}"), "AIzaREDACTED_GS005"),
    ("openai_like", re.compile(r"sk-[A-Za-z0-9]{20,}"), "sk-REDACTED_GS005"),
    ("slack", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "xoxb-REDACTED_GS005"),
]

TEXT_SUFFIXES = {
    ".md", ".py", ".txt", ".yaml", ".yml", ".json", ".toml", ".example",
    ".env", ".cfg", ".ini", ".sh", ".ts", ".tsx", ".js", ".jsx", ".html",
    ".css", ".log", ".lock", ".gitattributes", ".gitignore", "",
}


def main() -> int:
    if not PKG.is_dir():
        print(f"pkg missing: {PKG}")
        return 1
    log_lines = ["# CS-GS-005 pkg 密钥清洗日志(2026-10-29 bait 轮)\n",
                 "| 文件 | 类型 | 处数 |", "|---|---|---|"]
    total_files, total_hits = 0, 0
    for p in sorted(PKG.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        file_hits = {}
        for name, pat, repl in PATTERNS:
            n = len(pat.findall(text))
            if n:
                text = pat.sub(repl, text)
                file_hits[name] = n
        if file_hits:
            p.write_text(text, encoding="utf-8")
            total_files += 1
            total_hits += sum(file_hits.values())
            rel = p.relative_to(PKG)
            detail = ",".join(f"{k}×{v}" for k, v in sorted(file_hits.items()))
            log_lines.append(f"| {rel} | {detail} | {sum(file_hits.values())} |")
    log_lines.append(f"\n合计: {total_files} 文件 / {total_hits} 处替换\n")
    out = Path(__file__).parent / "secret_scrub_log_20261029.md"
    out.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"scrubbed files={total_files} hits={total_hits} log={out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
