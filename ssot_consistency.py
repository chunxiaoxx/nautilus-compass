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
EVENT_PREFIXES = ("_OUTBOUND", "_BROADCAST", "INBOUND", "_INBOUND")

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


def check_event_freshness(repo_roots: list[Path] | None = None) -> dict:
    """返回每个 repo 最新跨框事件文件与 stale 状态."""
    roots = repo_roots if repo_roots is not None else _default_repo_roots()
    threshold_h = float(os.environ.get("COMPASS_EVENT_STALE_HOURS", "24"))
    now = datetime.now().timestamp()
    report: dict = {"threshold_h": threshold_h, "repos": {}}
    for root in roots:
        latest = None
        try:
            for p in root.iterdir():
                if not p.is_file():
                    continue
                if not any(p.name.startswith(prefix) for prefix in EVENT_PREFIXES):
                    continue
                mtime = p.stat().st_mtime
                if latest is None or mtime > latest[1]:
                    latest = (p.name, mtime)
        except OSError:
            report["repos"][root.name] = {"missing": True, "stale": True}
            continue
        if latest is None:
            report["repos"][root.name] = {"missing": False, "latest": None, "stale": True}
            continue
        age_h = (now - latest[1]) / 3600.0
        report["repos"][root.name] = {
            "missing": False,
            "latest": latest[0],
            "mtime": datetime.fromtimestamp(latest[1]).strftime("%m-%d %H:%M"),
            "age_h": round(age_h, 1),
            "stale": age_h > threshold_h,
        }
    return report


def _format_event_freshness(report: dict | None = None) -> str:
    rep = report if report is not None else check_event_freshness()
    repos = rep.get("repos", {})
    stale = {k: v for k, v in repos.items() if v.get("stale")}
    cells = []
    for repo, data in repos.items():
        if data.get("missing"):
            cells.append(f"{repo}=缺repo")
        elif not data.get("latest"):
            cells.append(f"{repo}=无事件")
        else:
            cells.append(f"{repo}={data['mtime']}({data['age_h']}h)")
    if stale:
        names = ", ".join(stale.keys())
        return (
            f"🔴 跨框事件协议 stale({names}; 阈值 {rep.get('threshold_h')}h): "
            + " | ".join(cells)
        )
    return "✅ 跨框事件协议活跃: " + " | ".join(cells)


def format_for_prompt_injection(report: dict | None = None) -> str:
    """一致 → 单行 ✅;漂移 → 🔴 亮牌 + 各副本 哈希/mtime,提示最新副本。"""
    try:
        rep = report if report is not None else check_ssot_consistency()
        drifted = {f: d for f, d in rep.items() if not d.get("consistent", True)}
        event_line = _format_event_freshness()
        if not drifted:
            return "✅ 承重锚副本一致(" + "/".join(ANCHOR_FILES) + ")\n" + event_line
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
        lines.append(event_line)
        return "\n".join(lines)
    except Exception:
        return ""


if __name__ == "__main__":
    print(format_for_prompt_injection())
