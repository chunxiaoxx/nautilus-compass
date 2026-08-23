"""N2 燃料入池 · stop hook 自动提炼(GOAL_SSOT 无悔层 · 2026-08-23)。

每个 session 结束(stop hook 调用)跑一次,0-LLM:
1. 找最新 session_*.md(全部项目,同 stop_hook.py 的找法)。
2. 按模式提取"教训段"(根因/踩坑/必须/WinError/修复 等信号词所在段落)。
3. 去重(与 fuel_pool log 的 content_hash 比对)后写 pending 候选:
   vtf/fuel_pool/pending/<ts>_<slug>.md  · frontmatter 带 source_session 溯源。
4. 周批 QC(tools/fuel_qc_batch.py / 每周五):Gate B 方法 control-先失败门,
   过门才转正入 vtf/fuel_pool/。候选 14 天未 QC 自动过期(防狗熊掰玉米)。

红线:只提炼结构化信号,不改写原文;PII/买方名不过滤逻辑留 QC 批(人工核)。
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

ROOT = Path(__file__).resolve().parents[1]
POOL = ROOT / "vtf" / "fuel_pool"
PENDING = POOL / "pending"
LOG = POOL / "intake_log.jsonl"

SIGNAL = re.compile(
    r"(根因|踩坑|教训|坑[:：]|修复[::]?|必须显式|必须原对象|静默|WinError|gotcha|"
    r"root cause|pitfall|broke|silent(ly)? (fail|break)|不可推导|部落|id 透传|双库)",
    re.IGNORECASE,
)
MAX_CHARS_PER_LESSON = 600
MAX_LESSONS_PER_SESSION = 5


def find_latest_session_memory() -> Path | None:
    projects = Path.home() / ".claude" / "projects"
    best, best_mtime = None, 0.0
    if not projects.exists():
        return None
    for d in projects.iterdir():
        mem = d / "memory"
        if not mem.is_dir():
            continue
        for f in mem.glob("session_*.md"):
            try:
                m = f.stat().st_mtime
            except OSError:
                continue
            if m > best_mtime:
                best, best_mtime = f, m
    return best


def known_hashes() -> set[str]:
    hashes: set[str] = set()
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                hashes.add(json.loads(line).get("content_hash", ""))
            except json.JSONDecodeError:
                continue
    return hashes


def extract_lessons(text: str) -> list[str]:
    body = text.split("---", 2)[-1] if text.startswith("---") else text
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if len(p.strip()) >= 40]
    lessons = []
    for p in paras:
        if SIGNAL.search(p):
            lessons.append(p[:MAX_CHARS_PER_LESSON])
        if len(lessons) >= MAX_LESSONS_PER_SESSION:
            break
    return lessons


def main() -> int:
    latest = find_latest_session_memory()
    if latest is None:
        return 0
    text = latest.read_text(encoding="utf-8", errors="ignore")
    lessons = extract_lessons(text)
    if not lessons:
        return 0
    PENDING.mkdir(parents=True, exist_ok=True)
    seen = known_hashes()
    new_count = 0
    ts = time.strftime("%Y%m%d-%H%M%S")
    for i, lesson in enumerate(lessons):
        h = hashlib.sha256(lesson.encode("utf-8")).hexdigest()[:16]
        if h in seen:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", (latest.stem[:30] + f"-l{i}")).strip("-")[:50]
        doc = (
            "---\n"
            f"status: pending_qc\n"
            f"source_session: {latest.name}\n"
            f"source_project: {latest.parents[1].name}\n"
            f"extracted_at: {ts}\n"
            f"content_hash: sha256:{h}\n"
            "qc_protocol: control-first-fail (Gate B)\n"
            "---\n\n"
            f"{lesson}\n"
        )
        (PENDING / f"{ts}-{slug}.md").write_text(doc, encoding="utf-8")
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": ts, "hash": h, "source": latest.name}, ensure_ascii=False) + "\n")
        new_count += 1
    print(f"fuel_intake: {new_count}/{len(lessons)} candidates queued (from {latest.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
