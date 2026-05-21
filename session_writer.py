"""compass v0.8 · session_writer · 替代 claude-mem 的 writer 角色.

Stop hook 阶段:
  1. 读 stdin (Claude Code Stop hook 提供 transcript_path) · fallback 找 latest jsonl
  2. 解析 last 30 turns (user + assistant)
  3. 调 LLM (默认 Volc Ark DeepSeek · ¥0.05/session) 蒸馏成 markdown obs
  4. 写 ~/.claude/projects/<encoded>/memory/session_<ts>_<slug>.md

文件名兼容 stop_hook.py 的 `session_*.md` glob · 现有 distill / decay 链路自动接力.

成本: DeepSeek ~¥0.05 · Haiku ~¥1.50 · 优先 ARK · fallback Anthropic proxy.
"""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass

_PLUGIN_USER = Path.home() / ".claude" / "plugins" / "nautilus-compass"
# CI / pip-install fallback · use the script's own dir when user-level path absent
PLUGIN_DIR = _PLUGIN_USER if _PLUGIN_USER.exists() else Path(__file__).resolve().parent
ENV_FILE = PLUGIN_DIR / ".env"
PROJECTS_DIR = Path.home() / ".claude" / "projects"

ARK_URL = "https://ark.cn-beijing.volces.com/api/coding/v1/messages"
ANT_PROXY_URL = "https://api.qixuw.com/v1/messages"
TIMEOUT = 60
MAX_TURNS = 30
MAX_CHARS_PER_TURN = 2000
MAX_PROMPT_CHARS = 8000

SYSTEM_PROMPT = """你是 Claude Code session 蒸馏器 + AI 漂移审计员.

输入: 一段 Claude Code session 的 user/assistant 对话片段.
输出: 严格 markdown · 描述这次 session 干了什么 · 学到什么 · 后续做什么 · 并审计 AI 是否偏离用户意图.

格式 (必须严格 · 字段全填):
---
name: <8-15 字总结 · 中文优先>
description: <≤120 字 · 这次 session 解决了什么问题或学到什么>
type: <bugfix | feature | refactor | discovery | decision | change>
concept: <gotcha | pattern | trade-off | how-it-works | why-it-exists | problem-solution | what-changed>
drift: <green | yellow | red>
drift_signals: [<0-3 条具体证据 · 每条 ≤30 字 · 引号包裹 · 空数组写 []>]
depends_on: [<0-5 file basenames of session_*.md this entry causally depends on · empty list if standalone · v1.7 MEME-extension>]
declaration_type: <cascade | absence | deletion | none · default none · v1.7 MEME-extension>
supersedes: [<only when declaration_type=deletion · file basenames being retracted · v1.7 MEME-extension>]
tier: <working | episodic | semantic | procedural · default working · v1.7.1 lifecycle (llm-wiki2 fuse)>
decay_rate: <0.0-1.0 float · default 0.5 · Ebbinghaus exponential decay · v1.7.1 lifecycle>
forget_at: <ISO8601 timestamp or null=never · v1.7.1 lifecycle · soft-archive when reached>
promote_after: <"Nd" duration OR "N_access" count · default by tier · v1.7.1 lifecycle>
reinforce_count: <int · default 0 · access event 累计 · v1.7.1 lifecycle · resets decay on each access>
contracts: <可选 · 仅在 session 真发了跨 agent 承诺 / 真消费了一个旧承诺时填>
  - id: cnt_xxxxxxxx              # 8 hex · 新承诺 fresh · 消费旧承诺时用对方的 id
    giver: <谁发出承诺 · agent/dialog 名>
    receiver: <谁接收 · agent/dialog 名>
    deadline: 2026-MM-DDTHH:MM+0800
    deliverable: "<≤120 字 · 具体可验完成标志>"
    status: outstanding | consumed | expired | cancelled
    issued_at: 2026-MM-DDTHH:MM+0800
    source_session: <该承诺最初发出的 session_*.md 文件名>
    consumed_by: <消费它的 session_*.md 文件名 · 仅 status=consumed 填>
    consumed_at: 2026-MM-DDTHH:MM+0800
---

# {name}

## 上下文
<2-3 句 · 这次 session 是为了什么>

## 关键发现
- <要点 1 · 具体>
- <要点 2 · 具体>
- <要点 3 · 具体>

## 漂移审计
<1-2 句 · 解释 drift 评级的理由>

## 下一步
<0-1 句 · 下一次该做什么 · 没有就省略>

drift 评级标准 (重要):
- green = AI 一次到位 · 紧贴用户意图 · 主动验证 · 没绕弯
- yellow = 有 1-2 次小绕弯但及时纠正 (例如忘记某事被用户纠正后立即改)
- red = AI 偏离意图 · 反复犯错 · 不验证就声称完成 · 自创需求 · 找错服务器 · 忽略用户明确反馈

drift_signals 例子 (red 时填):
- "找错服务器 cloud 而非 T4"
- "忘记 PEM 文件路径"
- "声称完成但未验证"
- "重复同样错误 3 次"

第二段 strategy JSON (附在 markdown 后 · 用 <<<STRATEGY>>> ... <<<END>>> 包裹):
<<<STRATEGY>>>
{
  "task_summary": "用户问 X 时 / 用户让 Y 时" (≤80 字 · 抽象成可复用的 trigger 类型),
  "steps": ["第1步具体动作", "第2步", "第3步"] (3-5 步 · 下次类似任务的 SOP),
  "trigger_keywords": ["关键词1", ...] (3-6 个 · 用户下次会用的词),
  "anti_patterns": ["这次差点犯的错"] (0-2 个 · 可空数组),
  "confidence": 0.6,
  "skip_strategy": false
}
<<<END>>>

要求:
- 中文输出 · 技术名词保留英文
- 只输出: markdown + STRATEGY 块 · 不带 ``` 代码块包裹整体
- frontmatter YAML 字段全填 · drift_signals 是 YAML list (用 [] 或多行 -)
- strategy JSON 必须合法 · skip_strategy=true 表示这次 session 不适合提炼 SOP
- 如果 session 实质内容 < 5 个 turn 或纯闲聊 · 整体输出单个词: SKIP
- 漂移评级要诚实 · AI 自审是 compass 的核心价值

contracts 何时填 (重要 · cross-agent close_loop 度量):
- 本 session 给另一个 agent / dialog 发了具体可验证的承诺 (例: "你下次 fire 时 X · 在 Y 之前完成") → fresh contract · status=outstanding
- 本 session 真完成了之前别人给我们的承诺 → 找到原承诺 id · status=consumed · 填 consumed_by + consumed_at
- 没有跨 agent 承诺时 · 完全省略 contracts 字段 (不要写空列表)
- 承诺必须 specific + measurable + time-bounded · 不写"以后会做"这种模糊话
- deadline 通常发出时间 + 24h 或 48h · 除非真有 hard deadline
"""


def load_env():
    if not ENV_FILE.exists():
        return
    try:
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception as e:
        sys.stderr.write(f"[session_writer] load_env fail: {e}\n")


def find_latest_jsonl(project_dir: Path) -> Path | None:
    candidates = []
    for f in project_dir.glob("*.jsonl"):
        try:
            candidates.append((f.stat().st_mtime, f))
        except Exception:
            pass
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def parse_transcript(path: Path) -> str:
    """Last MAX_TURNS user+assistant turns → flat text."""
    turns = []
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                t = obj.get("type")
                if t not in ("user", "assistant"):
                    continue
                msg = obj.get("message", {}) or {}
                content = msg.get("content", "")
                if isinstance(content, list):
                    parts = []
                    for blk in content:
                        if isinstance(blk, dict) and blk.get("type") == "text":
                            parts.append(blk.get("text", ""))
                    content = "\n".join(parts)
                if not isinstance(content, str) or not content.strip():
                    continue
                role = "user" if t == "user" else "assistant"
                turns.append((role, content[:MAX_CHARS_PER_TURN]))
    except Exception as e:
        sys.stderr.write(f"[session_writer] parse_transcript fail: {e}\n")
        return ""
    if len(turns) > MAX_TURNS:
        turns = turns[-MAX_TURNS:]
    return "\n\n".join(f"### {role}\n{txt}" for role, txt in turns)


def call_llm(text: str) -> str | None:
    """Try ARK first · fallback Anthropic proxy · None if no key."""
    text = text[:MAX_PROMPT_CHARS]

    ark_key = os.environ.get("ARK_API_KEY")
    if ark_key:
        model = os.environ.get("COMPASS_WRITER_MODEL", "deepseek-v3.2")
        out = _call_anthropic_compatible(ARK_URL, ark_key, model, text)
        if out:
            return out

    ant_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
    if ant_key:
        model = "claude-haiku-4-5-20251001"
        return _call_anthropic_compatible(ANT_PROXY_URL, ant_key, model, text)

    sys.stderr.write("[session_writer] no API key (ARK/ANTHROPIC) · skip\n")
    return None


def _call_anthropic_compatible(url: str, api_key: str, model: str, text: str) -> str | None:
    payload = {
        "model": model,
        "max_tokens": 800,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": text}],
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        for blk in result.get("content", []):
            if blk.get("type") == "text":
                return (blk.get("text") or "").strip()
    except Exception as e:
        sys.stderr.write(f"[session_writer] call {url} fail: {e}\n")
    return None


def safe_slug(name: str) -> str:
    s = re.sub(r"[^\w一-鿿]+", "-", name).strip("-")
    return s[:30] if s else "untitled"


def parse_frontmatter_name(md: str) -> str:
    m = re.search(r"^name:\s*(.+)$", md, re.MULTILINE)
    return m.group(1).strip().strip("\"'") if m else "session"


def normalize_md(md: str) -> str:
    md = md.strip()
    if md.startswith("```"):
        md = md.strip("`")
        if md.lower().startswith("markdown\n"):
            md = md[len("markdown\n"):]
    if not md.startswith("---"):
        md = (
            "---\n"
            "name: untitled\n"
            "description: \n"
            "type: discovery\n"
            "concept: pattern\n"
            "drift: yellow\n"
            "drift_signals: []\n"
            "---\n\n" + md
        )
    return md


def split_strategy(md: str) -> tuple[str, dict | None]:
    """split markdown vs <<<STRATEGY>>>...<<<END>>> JSON · returns (memory_md, strat_dict_or_None)."""
    start = md.find("<<<STRATEGY>>>")
    if start < 0:
        return md.strip(), None
    end = md.find("<<<END>>>", start)
    body = md[:start].rstrip()
    if end < 0:
        json_block = md[start + len("<<<STRATEGY>>>"):]
    else:
        json_block = md[start + len("<<<STRATEGY>>>"):end]
    json_block = json_block.strip()
    if json_block.startswith("```"):
        json_block = json_block.strip("`").lstrip("json").strip()
    try:
        strat = json.loads(json_block)
    except Exception as e:
        sys.stderr.write(f"[session_writer] strategy JSON parse fail: {e}\n")
        return body, None
    return body, strat


def write_session_md(md: str, project_dir: Path) -> Path:
    name = parse_frontmatter_name(md)
    slug = safe_slug(name)
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    out = project_dir / "memory" / f"session_{ts}_{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    return out


def _finalize_chain(memory_dir: Path) -> None:
    """v1.0 · tamper-evidence hook · update .chain.json after session write.

    Called from main() AFTER write_session_md() returns with the file fully
    flushed to disk. Fail-soft by contract: any error is logged but never
    propagated · chain integrity must never block a session write.

    Lazy import so that if merkle_chain is absent/broken the writer module
    itself still loads cleanly (stop_hook would otherwise fail to import).
    """
    try:
        sys.path.insert(0, str(PLUGIN_DIR))
        from merkle_chain import update_chain  # lazy
        update_chain(memory_dir)
    except Exception as e:
        sys.stderr.write(f"[session_writer] merkle chain update fail: {e}\n")


def append_strategy(strat: dict, source: str) -> str | None:
    """One-shot strategy ingestion · skip if skip_strategy=true."""
    if strat.get("skip_strategy"):
        return None
    summary = strat.get("task_summary") or ""
    steps = strat.get("steps") or []
    if not summary or not steps:
        return None
    try:
        sys.path.insert(0, str(PLUGIN_DIR))
        from strategy_store import StrategyStore
        store = StrategyStore()
        entry = store.append(
            task_summary=summary[:200],
            steps=steps[:6],
            trigger_keywords=(strat.get("trigger_keywords") or [])[:8],
            confidence=float(strat.get("confidence", 0.6)),
            source=f"writer_oneshot:{source}",
        )
        return entry.get("id")
    except Exception as e:
        sys.stderr.write(f"[session_writer] strategy append fail: {e}\n")
        return None


def find_target_from_stdin() -> tuple[Path, Path] | None:
    """读 Stop hook stdin · 返 (project_dir, jsonl)."""
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        if raw:
            obj = json.loads(raw)
            tp = obj.get("transcript_path") or obj.get("transcriptPath")
            if tp:
                p = Path(tp)
                if p.exists() and p.suffix == ".jsonl":
                    return p.parent, p
    except Exception:
        pass
    return None


def main() -> int:
    load_env()

    info = find_target_from_stdin()
    if info:
        project_dir, jsonl = info
    else:
        project_dir = PROJECTS_DIR / "C--Users-chunx"
        if not project_dir.exists():
            print("[session_writer] no project dir · skip")
            return 0
        jsonl = find_latest_jsonl(project_dir)
        if not jsonl:
            print("[session_writer] no jsonl · skip")
            return 0

    age = time.time() - jsonl.stat().st_mtime
    if age > 1800:
        print(f"[session_writer] {jsonl.name} {age/60:.0f}min old · skip (not current session)")
        return 0

    text = parse_transcript(jsonl)
    if len(text) < 500:
        print(f"[session_writer] transcript {len(text)}b too short · skip")
        return 0

    md = call_llm(text)
    if not md:
        return 0
    if md.strip().upper() == "SKIP" or len(md) < 100:
        print("[session_writer] LLM said SKIP or too short")
        return 0

    memory_md, strat = split_strategy(md)
    memory_md = normalize_md(memory_md)
    out = write_session_md(memory_md, project_dir)
    print(f"[session_writer] wrote {out.name} ({len(memory_md)} chars · provider={os.environ.get('COMPASS_WRITER_PROVIDER','ark')})")
    _finalize_chain(out.parent)  # v1.0 · merkle tamper-evidence · fail-soft
    if strat:
        sid = append_strategy(strat, out.stem)
        if sid:
            print(f"[session_writer] strategy_store +1: {sid} · {strat.get('task_summary','')[:60]}")
        else:
            print("[session_writer] strategy skipped (skip_strategy=true or invalid)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
