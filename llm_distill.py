"""V5 Memory Plugin v1.1 · LLM 真蒸馏 strategy.

session 结束时 · 调 Haiku 总结 "用户让我做 X · 我应该走 Y · 不应该走 Z" ·
自动写新 strategy (或 update 已有).

R3 偏离: 加 LLM call · 但每 session 1 次 · ~$0.001 · 可控
触发条件: 环境变量 ANTHROPIC_API_KEY 或 CLAUDE_API_KEY 设置
没 key → 静默跳过 (留 v0.6 关键词模式)
"""
import io
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass

PLUGIN_DIR = Path.home() / ".claude" / "plugins" / "zenmind-mem"
HAIKU_MODEL = "claude-haiku-4-5-20251001"
PROXY_URL = "https://api.qixuw.com/v1/messages"   # qixuw 兼容 Anthropic API
TIMEOUT = 30


SYSTEM_PROMPT = """你是 Claude Code 的 strategy 蒸馏器.

输入: 一段 session 摘要 (用户跟我的对话内容)
输出: 严格 JSON · 描述"用户让我做什么类型的事 · 我应该走什么路径 · 不应该犯什么错"

输出格式:
{
  "task_summary": "用户问 X 时 / 用户让 Y 时" (≤80 字),
  "steps": ["第1步具体动作", "第2步", ...] (3-5 步),
  "trigger_keywords": ["关键词1", "关键词2"] (3-6 个 · 用户下次问类似时会出现的词),
  "anti_patterns": ["这次差点犯的错"] (0-2 个 · 可空数组),
  "confidence": 0.6
}

只输出 JSON · 不带 ``` · 不带解释.
如果 session 没有清晰的"用户类型 → 路径"对应 · 输出 {"skip": true}."""


def get_api_key() -> str | None:
    return (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("CLAUDE_API_KEY")
        or None
    )


def call_haiku(session_text: str) -> dict | None:
    """调 Haiku · 返 JSON 结果 · 失败返 None."""
    api_key = get_api_key()
    if not api_key:
        return None
    payload = {
        "model": HAIKU_MODEL,
        "max_tokens": 600,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": session_text[:4000]}],
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        PROXY_URL, data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        text = ""
        for block in result.get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "")
                break
        if not text:
            return None
        # parse JSON · LLM 可能加 ``` 包
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`").lstrip("json").strip()
        return json.loads(text)
    except Exception as e:
        sys.stderr.write(f"[llm_distill] call fail: {e}\n")
        return None


def distill_from_session_memory(session_path: Path, store) -> bool:
    """读 session memory · 调 LLM 蒸馏 · 写 strategy."""
    try:
        text = session_path.read_text(encoding="utf-8")
    except Exception:
        return False
    if len(text) < 200:
        return False

    result = call_haiku(text)
    if not result or result.get("skip"):
        return False
    if "task_summary" not in result or "steps" not in result:
        return False

    entry = store.append(
        task_summary=result["task_summary"],
        steps=result["steps"][:6],
        trigger_keywords=result.get("trigger_keywords", [])[:8],
        confidence=float(result.get("confidence", 0.6)),
        source=f"llm_distill:{session_path.name}",
    )
    print(f"[llm_distill] new strategy {entry['id']} from {session_path.name}")
    print(f"  task: {entry['task_summary'][:80]}")
    return True


if __name__ == "__main__":
    if not get_api_key():
        print("[llm_distill] no ANTHROPIC_API_KEY / CLAUDE_API_KEY · skip")
        sys.exit(0)
    if len(sys.argv) < 2:
        print("usage: llm_distill.py <session_memory.md>")
        sys.exit(1)
    sys.path.insert(0, str(PLUGIN_DIR))
    from strategy_store import StrategyStore
    store = StrategyStore()
    ok = distill_from_session_memory(Path(sys.argv[1]), store)
    sys.exit(0 if ok else 1)
