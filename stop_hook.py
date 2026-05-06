"""V5 Memory Plugin v0.6 · Stop hook · session 结束自动蒸馏 strategy.

Claude Code Stop hook · 每个 session 结束时跑 ·
读 latest claude-mem 写的 session memory · 提取关键词扩 strategy_store.

设计 (R3 守 · 0 LLM):
  · 读 ~/.claude/projects/<encoded>/memory/session_*.md · 取最新一个
  · 提取 frontmatter description (这是 claude-mem 已写的总结)
  · 取所有现有 strategy 的 trigger_keywords · 算跟新 description 的重合
  · 重合度 ≥ 50% 的 strategy → 自动 +1 evidence_count + log
  · 不创建新 strategy (留给人工 audit)

输出: 写到 .cache/auto_distill_log.jsonl 让用户 review
"""
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass

PLUGIN_DIR = Path.home() / ".claude" / "plugins" / "nautilus-compass"
CACHE_DIR = PLUGIN_DIR / ".cache"
LOG_FILE = CACHE_DIR / "auto_distill_log.jsonl"


def find_latest_session_memory() -> Path | None:
    """从所有项目的 memory 找 modified 最近的 session_*.md."""
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return None
    candidates = []
    for proj in projects_dir.iterdir():
        if not (proj / "memory").exists():
            continue
        for f in (proj / "memory").glob("session_*.md"):
            try:
                candidates.append((f.stat().st_mtime, f))
            except Exception:
                pass
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def parse_session_summary(path: Path) -> str:
    """读 session memory · 提 description + body 前 1500 字."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return ""
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end > 0:
            fm_block = text[4:end]
            body = text[end + 4:].strip()
            desc = ""
            for line in fm_block.split("\n"):
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
                    break
            return f"{desc}\n{body[:1500]}"
    return text[:1500]


def main():
    sys.path.insert(0, str(PLUGIN_DIR))
    from strategy_store import StrategyStore

    # v0.8 · session_writer (替代 claude-mem 的 writer)
    # 先写本次 session memory · 再走 distill 链路接力
    try:
        from session_writer import main as _writer_main
        _writer_main()
    except Exception as _we:
        sys.stderr.write(f"[stop_hook] session_writer fail: {_we}\n")

    latest = find_latest_session_memory()
    if not latest:
        print("[stop_hook] no session memory found · skip")
        return 0

    age_s = time.time() - latest.stat().st_mtime
    if age_s > 3600:
        # 上次 session memory > 1h 旧 · 不是本次 session
        print(f"[stop_hook] latest session {latest.name} is {age_s/60:.1f} min old · skip")
        return 0

    summary = parse_session_summary(latest).lower()
    if not summary:
        return 0

    store = StrategyStore()
    matched = []
    for s in store._strategies:
        if s.get("archived"):
            continue
        kws = s.get("trigger_keywords") or []
        if not kws:
            continue
        hits = [kw for kw in kws if kw.lower() in summary]
        if len(hits) >= max(1, len(kws) // 2):
            matched.append({
                "id": s["id"],
                "task": s.get("task_summary", "")[:60],
                "hit_keywords": hits,
            })
            # +1 evidence_count
            s["evidence_count"] = s.get("evidence_count", 1) + 1
            s["last_used_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # v1.1 · LLM 真蒸馏 (有 API key 时跑 · 自动加新 strategy)
    try:
        from llm_distill import distill_from_session_memory, get_api_key
        if get_api_key():
            distill_from_session_memory(latest, store)
    except Exception as _le:
        sys.stderr.write(f"[stop_hook] llm_distill fail: {_le}\n")

    # v1.6 · Ebbinghaus decay (无论 matched 与否都跑)
    decay = store.apply_ebbinghaus_decay()
    if decay["decayed"] > 0 or decay["archived"] > 0:
        print(f"[stop_hook decay] decayed={decay['decayed']} archived={decay['archived']}")

    if matched:
        store._rewrite()
        log_entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "session_memory": latest.name,
            "matched_strategies": matched,
        }
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print(f"[stop_hook] {len(matched)} strategies +ev · log: {LOG_FILE.name}")
        for m in matched:
            print(f"  · {m['id']} '{m['task']}' hits={m['hit_keywords']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"stop_hook fail: {e}\n")
        sys.exit(0)
