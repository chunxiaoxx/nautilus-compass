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
EVENT_REQUIRED_FIELDS = ("trace_id", "frame", "source_repo", "maturity", "proof")
DEFAULT_WATCH_TRACE_IDS = (
    "2026-07-20T22:00:00Z#prime-001#fuel-sync-20260720",
)

_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)
_KV_LINE_RE = re.compile(r"^\s*([A-Za-z0-9_\\-]+)\s*:\s*(.+)\s*$")


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


def _extract_event_fields(path: Path) -> dict:
    fields: dict[str, str] = {}
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return fields
    parsed = False
    for line in raw.replace("\r\n", "\n").split("\n")[:220]:
        if line.strip() == "---":
            parsed = not parsed
            continue
        if parsed and not line.strip():
            break
        m = _KV_LINE_RE.match(line)
        if not m:
            continue
        k = m.group(1).strip().lower().replace("-", "_")
        if k in EVENT_REQUIRED_FIELDS:
            fields[k] = m.group(2).strip()
    return fields


def check_event_protocol(repo_roots: list[Path] | None = None) -> dict:
    roots = repo_roots if repo_roots is not None else _default_repo_roots()
    rep: dict = {"complete": True, "repos": {}}
    for root in roots:
        latest = None
        try:
            for p in root.iterdir():
                if not p.is_file() or not any(p.name.startswith(prefix) for prefix in EVENT_PREFIXES):
                    continue
                mtime = p.stat().st_mtime
                if latest is None or mtime > latest[1]:
                    latest = (p, mtime)
        except OSError:
            rep["repos"][root.name] = {"missing_repo": True, "complete": False}
            rep["complete"] = False
            continue

        if latest is None:
            rep["repos"][root.name] = {"latest": None, "complete": False, "missing_events": True}
            rep["complete"] = False
            continue

        fields = _extract_event_fields(latest[0])
        missing = [f for f in EVENT_REQUIRED_FIELDS if f not in fields]
        rep["repos"][root.name] = {
            "latest": latest[0].name,
            "complete": len(missing) == 0,
            "missing_fields": missing,
            "trace_id": fields.get("trace_id", ""),
            "frame": fields.get("frame", ""),
        }
        if missing:
            rep["complete"] = False
    trace_ids = set()
    for data in rep["repos"].values():
        if not isinstance(data, dict):
            continue
        tid = data.get("trace_id")
        if tid:
            trace_ids.add(tid)
    rep["cross_repo_trace_ids"] = sorted(trace_ids)
    rep["cross_repo_trace_consistent"] = len(trace_ids) <= 1
    return rep


def _watch_trace_ids() -> list[str]:
    env = os.environ.get("COMPASS_WATCH_TRACE_IDS", "")
    if env:
        return [x.strip() for x in re.split(r"[;,]", env) if x.strip()]
    return list(DEFAULT_WATCH_TRACE_IDS)


def check_trace_coverage(
    trace_ids: list[str] | None = None,
    repo_roots: list[Path] | None = None,
) -> dict:
    """Check whether watched trace ids appear in cross-dialog files for each repo."""
    roots = repo_roots if repo_roots is not None else _default_repo_roots()
    targets = trace_ids if trace_ids is not None else _watch_trace_ids()
    report: dict = {"targets": targets, "complete": True, "traces": {}}
    for trace_id in targets:
        per_repo = {}
        for root in roots:
            hits: list[str] = []
            try:
                for p in root.iterdir():
                    if not p.is_file():
                        continue
                    if not any(p.name.startswith(prefix) for prefix in EVENT_PREFIXES):
                        continue
                    try:
                        raw = p.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    if trace_id in raw:
                        hits.append(p.name)
            except OSError:
                per_repo[root.name] = {"missing_repo": True, "covered": False, "hits": []}
                report["complete"] = False
                continue
            per_repo[root.name] = {"covered": bool(hits), "hits": hits[:5], "hit_count": len(hits)}
            if not hits:
                report["complete"] = False
        report["traces"][trace_id] = per_repo
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


def _format_trace_coverage(report: dict | None = None) -> str:
    rep = report if report is not None else check_trace_coverage()
    if not rep.get("targets"):
        return ""
    bad = []
    cells = []
    for trace_id, per_repo in rep.get("traces", {}).items():
        short = trace_id.split("#")[-1]
        for repo, data in per_repo.items():
            count = data.get("hit_count", 0)
            cells.append(f"{repo}:{short}={count}")
            if not data.get("covered"):
                bad.append(f"{repo}:{short}")
    if bad:
        return "🔴 跨框 trace 覆盖缺口: " + ", ".join(bad) + " | " + " ".join(cells)
    return "✅ 跨框 trace 覆盖完整: " + " ".join(cells)


def format_for_prompt_injection(report: dict | None = None) -> str:
    """一致 → 单行 ✅;漂移 → 🔴 亮牌 + 各副本 哈希/mtime,提示最新副本。"""
    try:
        rep = report if report is not None else check_ssot_consistency()
        drifted = {f: d for f, d in rep.items() if not d.get("consistent", True)}
        event_line = _format_event_freshness()
        trace_line = _format_trace_coverage()
        proto = check_event_protocol()
        if not proto.get("complete", True):
            proto_line = "🟡 跨框事件协议字段不完整: "
            details = []
            for repo, data in proto.get("repos", {}).items():
                if not data.get("complete"):
                    details.append(
                        f"{repo}:{data.get('latest', '无事件')},缺={data.get('missing_fields', [])}"
                    )
            proto_line += "; ".join(details) if details else "字段缺失"
        elif not proto.get("cross_repo_trace_consistent", True):
            proto_line = "🟠 跨框 trace_id 不一致: " + ", ".join(
                f"{repo}={data.get('trace_id', '缺失')}"
                for repo, data in proto.get("repos", {}).items()
            )
        else:
            proto_line = "✅ 跨框事件协议字段完整"
        protocol_lines = [event_line]
        if trace_line:
            protocol_lines.append(trace_line)
        protocol_lines.append(proto_line)
        if not drifted:
            return (
                "✅ 承重锚副本一致("
                + "/".join(ANCHOR_FILES)
                + ")\n"
                + "\n".join(protocol_lines)
            )
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
        lines.extend(protocol_lines)
        return "\n".join(lines)
    except Exception:
        return ""


if __name__ == "__main__":
    print(format_for_prompt_injection())
