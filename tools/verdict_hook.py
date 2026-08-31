"""verdict-hook · run verdict 自动提炼进燃料 pending 池(双环回流 · P0)。

fuel_intake.py 只覆盖 session 结束;评测/训练的 verdict 产物(aggregated_metrics、
裁决 evidence)没有回流——本 hook 补上:扫描 vtf/ 下 verdict 特征文件,
0-LLM 提炼"配方知识"条目,走与 fuel_intake 同一条 pending→Gate B QC→入池管道。

触发:评测收尾固化流程手动调用 `python tools/verdict_hook.py`
(后续可在 stop hook 追加一行,先独立跑稳)。

扫描范围(v0):
  1. 任意目录下的 aggregated_metrics.json(评测 run 产物)
  2. 路径含 evidence 或 verdict 的 .json/.md(裁决文档)
去重:内容 hash(与 fuel_intake 共用 intake_log.jsonl)+ mtime 游标
(verdict_cursor.json,只处理新增/变更文件)。

红线:只提炼结构化信号,不改写原文;PII/买方名过滤留 QC 批(与 fuel_intake 同约)。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [REPO / "vtf"]
PENDING = REPO / "vtf" / "fuel_pool" / "pending"
LOG = REPO / "vtf" / "fuel_pool" / "intake_log.jsonl"
CURSOR = REPO / "vtf" / "fuel_pool" / "verdict_cursor.json"

VERDICT_SIGNAL = re.compile(
    r"(NEGATIVE|PROVEN|INCONCLUSIVE|定案|退步|回落|负判|正判|过门|未通过|未达|"
    r"对照.*基线|预期.*落空|regress(?:ed|ion)?|beats? baseline)",
    re.IGNORECASE,
)
MAX_CHARS = 600
MIN_PARA_CHARS = 40


def candidate_files() -> list[Path]:
    out: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".json", ".md"):
                continue
            name = p.name.lower()
            if name == "aggregated_metrics.json":
                out.append(p)
            elif "evidence" in str(p).lower() or "verdict" in name:
                out.append(p)
    return out


def load_cursor() -> dict:
    if CURSOR.exists():
        try:
            return json.loads(CURSOR.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def known_hashes() -> set[str]:
    hashes: set[str] = set()
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                hashes.add(json.loads(line).get("hash", ""))
            except json.JSONDecodeError:
                continue
    return hashes


def _fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def extract_from_aggregated(path: Path) -> list[str]:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    ov = d.get("overall") or {}
    if "overall_full_set" not in ov:
        return []
    parts = [
        f"[run-verdict] {path.parent.name}: overall_full_set={_fmt_pct(ov['overall_full_set'])}"
        f" (n={ov.get('count_all_questions', '?')})",
        f"非弃答 {_fmt_pct(ov.get('overall_non_abstention_only', 0))}"
        f" · 弃答 {_fmt_pct(ov.get('overall_abstention_only', 0))}",
    ]
    cats = d.get("non_abstention_by_category") or {}
    scored = [(c, v.get("pct_correct", 0), v.get("count", 0)) for c, v in cats.items() if isinstance(v, dict)]
    if scored:
        best = max(scored, key=lambda t: t[1])
        worst = min(scored, key=lambda t: t[1])
        parts.append(f"强分类 {best[0]}={_fmt_pct(best[1])} · 弱分类 {worst[0]}={_fmt_pct(worst[1])}")
    return [" · ".join(parts)]


def extract_from_doc(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
            text = json.dumps(data, ensure_ascii=False, indent=1)
        except json.JSONDecodeError:
            return []
    items = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if len(para) >= MIN_PARA_CHARS and VERDICT_SIGNAL.search(para):
            items.append(para[:MAX_CHARS])
            if len(items) >= 3:
                break
    return items


def _extract_file(path: Path) -> list[str]:
    """单文件提炼:aggregated 走模板,其余走信号段落。"""
    if path.name == "aggregated_metrics.json":
        return extract_from_aggregated(path)
    return extract_from_doc(path)


def extract_from_run(run_dir: Path) -> list[str]:
    """从单个 run 目录提炼 verdict 条目(测试与 hook 共用入口)。"""
    items: list[str] = []
    if not run_dir.is_dir():
        return items
    for p in sorted(run_dir.iterdir()):
        if not p.is_file() or p.suffix.lower() not in (".json", ".md"):
            continue
        name = p.name.lower()
        if name == "aggregated_metrics.json" or "evidence" in name or "verdict" in name:
            items.extend(_extract_file(p))
    return items


def run_hook() -> int:
    cursor = load_cursor()
    seen = known_hashes()
    PENDING.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    new_cursor = dict(cursor)
    queued = 0
    for path in candidate_files():
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        rel = path.relative_to(REPO).as_posix()
        if cursor.get(rel) == mtime:
            continue
        new_cursor[rel] = mtime
        for i, body in enumerate(_extract_file(path)):
            h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
            if h in seen:
                continue
            # slug 用全相对路径:同名气 run 目录(d12/compass_web_small vs compass_web_small)不可同 slug,防同名覆盖
            rel_parent = path.parent.relative_to(REPO).as_posix().lower()
            slug = re.sub(r"[^a-z0-9]+", "-", rel_parent)[:60] or "verdict"
            doc = (
                "---\n"
                "status: pending_qc\n"
                f"verdict_type: run-verdict\n"
                f"source_verdict: {rel}\n"
                f"extracted_at: {ts}\n"
                f"content_hash: sha256:{h}\n"
                "qc_protocol: control-first-fail (Gate B)\n"
                "---\n\n"
                f"{body}\n"
            )
            (PENDING / f"{ts}-verdict-{slug}-{i}.md").write_text(doc, encoding="utf-8")
            with LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": ts, "hash": h, "source": rel, "kind": "run-verdict"}, ensure_ascii=False) + "\n")
            seen.add(h)
            queued += 1
    CURSOR.write_text(json.dumps(new_cursor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"verdict_hook: {queued} candidates queued · {len(new_cursor)} files on cursor")
    return queued


def main() -> int:
    run_hook()
    return 0


if __name__ == "__main__":
    sys.exit(main())
