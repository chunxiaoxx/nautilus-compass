"""V5 Memory Plugin · Strategy Store · DPT-Agent 蒸馏推理路径.

复用 V5 nautilus-v5/learning/strategy_store.py 设计 · 跨 session 持久化.

存储: ~/.claude/plugins/nautilus-compass/.cache/strategies.jsonl
schema:
  {
    "id": "st-xxx",
    "task_key": "<query 前 50 字 sha256[:10]>",
    "task_summary": "用户问 V5 飞轮真转吗",
    "steps": ["先 git log --since=昨天", "看 stake fulfilled 数", "对照宪法 3 Yes"],
    "trigger_keywords": ["飞轮", "转", "stake", "蓝图实现度"],
    "evidence_count": 3,
    "success_count": 2,
    "fail_count": 0,
    "confidence": 0.65,
    "last_used_at": "2026-04-27T...",
    "created_at": "2026-04-27T...",
    "source": "manual|session_distill"
  }

Hook 时 (UserPromptSubmit): query 命中 task_key 或语义相似 → 注入 steps 提示
Stop 时 (session 结束): LLM 蒸馏新 strategy (后续 v0.5+)
当前 v0.4: 用户手动 publish strategy via CLI · 后续自动蒸馏

R1: 修 stub claude-mem 不存判断框架 → 真蒸馏 strategy
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PLUGIN_DIR = Path.home() / ".claude" / "plugins" / "nautilus-compass"
CACHE_DIR = PLUGIN_DIR / ".cache"
STRATEGY_PATH = CACHE_DIR / "strategies.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def task_key_from_query(query: str, length: int = 50) -> str:
    head = (query or "").strip()[:length]
    return hashlib.sha256(head.encode("utf-8")).hexdigest()[:10]


class StrategyStore:
    def __init__(self, jsonl_path: Path = STRATEGY_PATH):
        self._path = Path(jsonl_path)
        self._strategies: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    self._strategies.append(json.loads(line))
        except Exception:
            pass

    def _rewrite(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".jsonl.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                for s in self._strategies:
                    f.write(json.dumps(s, ensure_ascii=False) + "\n")
            tmp.replace(self._path)
        except Exception:
            pass

    def append(
        self, task_summary: str, steps: List[str],
        trigger_keywords: Optional[List[str]] = None,
        confidence: float = 0.5, source: str = "manual",
    ) -> Dict[str, Any]:
        """新蒸馏 strategy · 同 task_key 已存在则 update steps + ev++"""
        task_key = task_key_from_query(task_summary)
        sid = f"st-{hashlib.sha256(f'{task_key}{_now_iso()}'.encode()).hexdigest()[:8]}"
        with self._lock:
            for s in self._strategies:
                if s.get("task_key") == task_key and not s.get("archived"):
                    s["steps"] = steps
                    s["trigger_keywords"] = trigger_keywords or s.get("trigger_keywords", [])
                    s["evidence_count"] = s.get("evidence_count", 1) + 1
                    s["confidence"] = round(min(1.0, s.get("confidence", 0.5) * 1.05), 4)
                    s["updated_at"] = _now_iso()
                    self._rewrite()
                    return s
            entry = {
                "id": sid, "task_key": task_key,
                "task_summary": task_summary[:200],
                "steps": steps,
                "trigger_keywords": trigger_keywords or [],
                "evidence_count": 1,
                "success_count": 0, "fail_count": 0,
                "confidence": round(confidence, 4),
                "last_used_at": None,
                "created_at": _now_iso(), "source": source,
                "archived": False,
            }
            self._strategies.append(entry)
            self._rewrite()
            return entry

    def lookup(self, query: str) -> List[Dict[str, Any]]:
        """按 task_key 精确查 + 关键词匹配 · 返活跃 strategies."""
        with self._lock:
            results = []
            target_key = task_key_from_query(query)
            q_lower = query.lower()
            for s in self._strategies:
                if s.get("archived"):
                    continue
                # 精确 task_key
                if s.get("task_key") == target_key:
                    s["last_used_at"] = _now_iso()
                    results.append((1.0, s))
                    continue
                # 关键词匹配 · v0.7 改 · 阈值 0.3 → 命中 ≥ 2 词即可
                # 旧: hits/len(kws) >= 0.3 · 7 词的 strategy 必须命中 3 个 · 太严
                # 新: 命中 2+ 词 OR 比例 ≥ 0.3 · 任一即可
                kws = s.get("trigger_keywords") or []
                hits = sum(1 for kw in kws if kw.lower() in q_lower)
                if hits and kws:
                    score = hits / len(kws)
                    if hits >= 2 or score >= 0.3:
                        s["last_used_at"] = _now_iso()
                        results.append((score + (0.05 if hits >= 2 else 0), s))
            if results:
                self._rewrite()
            results.sort(key=lambda x: -x[0])
            return [s for _, s in results[:3]]

    def update_outcome(self, strategy_id: str, success: bool) -> None:
        with self._lock:
            for s in self._strategies:
                if s.get("id") == strategy_id:
                    if success:
                        s["success_count"] = s.get("success_count", 0) + 1
                        s["confidence"] = round(min(1.0, s.get("confidence", 0.5) * 1.05), 4)
                    else:
                        s["fail_count"] = s.get("fail_count", 0) + 1
                        s["confidence"] = round(max(0.0, s.get("confidence", 0.5) * 0.95), 4)
                    self._rewrite()
                    return

    def render_for_prompt(self, query: str, max_chars: int = 800) -> str:
        """hook 注入用 · 命中 strategy 时格式化."""
        hits = self.lookup(query)
        if not hits:
            return ""
        lines = [f"[Strategy 蒸馏 · 你历史走通的路径 · {len(hits)} 条命中]"]
        for s in hits:
            line = (
                f"  · {s.get('task_summary', '')[:80]} "
                f"(conf={s.get('confidence',0.5):.2f} · used {s.get('success_count',0)} 次)"
            )
            lines.append(line)
            for step in s.get("steps", [])[:5]:
                lines.append(f"    · {step[:120]}")
        text = "\n".join(lines)
        return text[:max_chars]

    def apply_ebbinghaus_decay(
        self,
        decay_rate: float = 0.95,
        decay_after_days: int = 30,
        archive_threshold: float = 0.2,
    ) -> Dict[str, int]:
        """v1.6 · 自然淘汰: 30+天未用 confidence ×0.95 · <0.2 archived.

        last_used_at 为 null 时按 created_at 算年龄.
        """
        now_utc = datetime.now(timezone.utc)
        decayed = 0
        archived = 0
        with self._lock:
            for s in self._strategies:
                if s.get("archived"):
                    continue
                ref = s.get("last_used_at") or s.get("created_at")
                try:
                    ref_dt = datetime.fromisoformat(ref.replace("Z", "+00:00"))
                    age_days = (now_utc - ref_dt).days
                except Exception:
                    age_days = 9999
                if age_days >= decay_after_days:
                    s["confidence"] = round(s.get("confidence", 0.5) * decay_rate, 4)
                    decayed += 1
                    if s["confidence"] < archive_threshold and s.get("evidence_count", 1) >= 3:
                        s["archived"] = True
                        s["archive_reason"] = f"decay-low-conf<{archive_threshold}"
                        s["archived_at"] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                        archived += 1
            if decayed:
                self._rewrite()
        return {"decayed": decayed, "archived": archived}

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._strategies)
            archived = sum(1 for s in self._strategies if s.get("archived"))
            ever_used = sum(1 for s in self._strategies if s.get("last_used_at"))
        return {
            "total": total, "active": total - archived,
            "archived": archived, "ever_used": ever_used,
        }


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    store = StrategyStore()

    if cmd == "stats":
        s = store.stats()
        print(json.dumps(s, indent=2, ensure_ascii=False))

    elif cmd == "list":
        for s in store._strategies:
            if s.get("archived"):
                continue
            print(f"[{s['id']}] conf={s.get('confidence',0.5):.2f} · {s.get('task_summary','')[:80]}")
            for step in s.get("steps", []):
                print(f"  · {step}")

    elif cmd == "decay":
        result = store.apply_ebbinghaus_decay()
        print(f"decayed={result['decayed']} · archived={result['archived']}")

    elif cmd == "lookup" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        text = store.render_for_prompt(query)
        if text:
            print(text)
        else:
            print(f"无匹配 strategy · query: {query[:60]}")

    elif cmd == "add":
        # 交互式: stdin 读 JSON
        # python3 strategy_store.py add < strategy.json
        # {"task_summary":"...", "steps":[...], "trigger_keywords":[...]}
        import sys
        try:
            data = json.loads(sys.stdin.read())
            entry = store.append(
                task_summary=data["task_summary"],
                steps=data["steps"],
                trigger_keywords=data.get("trigger_keywords", []),
                confidence=data.get("confidence", 0.6),
                source=data.get("source", "manual"),
            )
            print(f"✅ added {entry['id']} · {entry['task_summary'][:60]}")
        except Exception as e:
            print(f"❌ {e}")
            sys.exit(1)

    else:
        print("usage: strategy_store.py [stats|list|lookup <query>|add <stdin json>]")
        sys.exit(1)
