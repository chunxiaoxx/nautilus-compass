"""v2.3 · SSOT 副本一致性探针(2026-07-17 用户拍板"现在做"·治跨框信息不对称)

对各 repo 根的承重锚文件(FDE_BUSINESS_CHARTER.md / LOOP_STATE_SSOT.md)做
frontmatter 剥离后的正文哈希对比。漂移 = 在 recall hook 里对每个框亮牌,
把"同步"从记忆力问题变成物理告警。

设计约束:纯 stdlib · 3-6 次文件读 · fail-soft(任何异常静默,不阻塞 recall)。
"""
from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime
from pathlib import Path

ANCHOR_FILES = ("FDE_BUSINESS_CHARTER.md", "LOOP_STATE_SSOT.md")

_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)


def _default_repo_roots() -> list[Path]:
    env = os.environ.get("COMPASS_SSOT_REPOS", "")
    if env:
        return [Path(p) for p in env.split(os.pathsep) if p.strip()]
    base = Path.home() / "Projects"
    return [base / name for name in ("nautilus-v5", "nautilus-core", "nautilus-compass")]


def _body_hash(path: Path) -> tuple[str, str] | None:
    """返回 (8位正文哈希, mtime YYYY-MM-DD);文件不存在返回 None。"""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    body = _FRONTMATTER_RE.sub("", raw, count=1)
    norm = "\n".join(line.rstrip() for line in body.replace("\r\n", "\n").split("\n")).strip()
    digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:8]
    mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d")
    return digest, mtime


def check_ssot_consistency(repo_roots: list[Path] | None = None) -> dict:
    """返回 {file: {repo_name: (hash, mtime)|None, ..., 'consistent': bool}}。"""
    roots = repo_roots if repo_roots is not None else _default_repo_roots()
    report: dict = {}
    for fname in ANCHOR_FILES:
        per_repo: dict = {}
        hashes = set()
        for root in roots:
            res = _body_hash(root / fname)
            per_repo[root.name] = res
            if res is not None:
                hashes.add(res[0])
        per_repo["consistent"] = len(hashes) <= 1
        report[fname] = per_repo
    return report


def format_for_prompt_injection(report: dict | None = None) -> str:
    """一致 → 单行 ✅;漂移 → 🔴 亮牌 + 各副本 哈希/mtime,提示最新副本。"""
    try:
        rep = report if report is not None else check_ssot_consistency()
        drifted = {f: d for f, d in rep.items() if not d.get("consistent", True)}
        if not drifted:
            return "✅ 承重锚副本一致(" + "/".join(ANCHOR_FILES) + ")"
        lines = ["🔴 SSOT 副本漂移 · 各框读到的不是同一份真相(先对齐再引用):"]
        for fname, data in drifted.items():
            cells = []
            newest = None
            for repo, res in data.items():
                if repo == "consistent":
                    continue
                if res is None:
                    cells.append(f"{repo}=缺失")
                else:
                    cells.append(f"{repo}={res[0]}({res[1]})")
                    if newest is None or res[1] > newest[1]:
                        newest = (repo, res[1])
            hint = f" · 最新副本={newest[0]}" if newest else ""
            lines.append(f"  · {fname}: " + " | ".join(cells) + hint)
        lines.append("  → 协议:改 canonical → 同步全部副本 → 各自 commit(CHARTER §6)")
        return "\n".join(lines)
    except Exception:
        return ""


if __name__ == "__main__":
    print(format_for_prompt_injection())
