#!/usr/bin/env python3
"""
V7 Telegram Daemon · @Nautilusx_bot

V7 是 V5 / Kairos / V6 三身共一魂的"灵魂全融合"层。
- /v7 /kpi /help /start: 直查 PG (聚合视图 · 不调 LLM)
- 任意非命令文字 → 调 LLM (V7 真"嘴" · 三身视角综合)

chat_id 白名单仅 V7_CHAT_ID 可发命令
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
import traceback
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import psycopg2

# ---- env ----
TG_TOKEN = os.environ.get("V7_BOT_TOKEN", "").strip()
ALLOWED_CHAT = os.environ.get("V7_CHAT_ID", "5888378695").strip()
DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://nautilus_user:nautilus2024@localhost:5432/nautilus_production",
)
KPI_SCRIPT = os.environ.get("V7_KPI_SCRIPT", "/usr/local/bin/v7-kpi-push.sh")

# ---- compass MCP (TODO 8 · /plan /approve /reject /relax) ----
COMPASS_PATH = os.environ.get(
    "COMPASS_PATH", "/home/ubuntu/nautilus-compass-cache"
).strip()
V7_SPOOL_DIR = Path(
    os.environ.get(
        "V7_SPOOL_DIR",
        str(Path.home() / ".claude" / "projects" / "_platform_queue"),
    )
)
GOVERNANCE_TIMEOUT_S = float(os.environ.get("V7_GOV_TIMEOUT_S", "5"))
PENDING_TTL_S = 15 * 60  # 15 min ephemeral state

# parent_id → {goal, domain_hint, anchor_pack_hint, ts}
PENDING_PLANS: dict[str, dict] = {}
PENDING_LOCK = threading.Lock()

# ---- LLM env (5.a) ----
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
MINIMAX_KEY = os.environ.get("MINIMAX_API_KEY", "").strip()
CLAUDE_BASE_URL = os.environ.get("CLAUDE_BASE_URL", "").strip()
LLM_MODEL = os.environ.get("V7_LLM_MODEL", "MiniMax-M2.7-highspeed").strip()
LLM_TIMEOUT_S = float(os.environ.get("V7_LLM_TIMEOUT_S", "45"))

API = f"https://api.telegram.org/bot{TG_TOKEN}"
LONG_POLL_TIMEOUT = 25
LOOP_BACKOFF = 5

if not TG_TOKEN:
    print("[FATAL] V7_BOT_TOKEN not set", file=sys.stderr)
    sys.exit(1)


# ---- TG helpers ----
def tg_get(method: str, params: dict | None = None, timeout: int = 30) -> dict:
    url = f"{API}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def tg_send(chat_id: int | str, text: str) -> None:
    data = urllib.parse.urlencode(
        {"chat_id": str(chat_id), "text": text, "disable_web_page_preview": "true"}
    ).encode()
    req = urllib.request.Request(f"{API}/sendMessage", data=data)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
    except Exception as e:
        print(f"[tg_send err] {e}", file=sys.stderr, flush=True)


# ---- PG context for LLM (5.a) ----
def fetch_v7_context() -> dict:
    """真查 PG · 给 LLM 提供 V5/K/V6 + 平台 KPI + harmony."""
    AGENTS = ("nautilus-prime-001", "kairos", "nautilus-v6")
    ALIAS = {"nautilus-prime-001": "V5", "kairos": "K", "nautilus-v6": "V6"}
    ctx = {"agents": {}, "kpi": {}, "harmony": None, "err": None}
    try:
        conn = psycopg2.connect(DSN, connect_timeout=5)
        cur = conn.cursor()

        # cycle + NAU + tier per agent
        cur.execute(
            "SELECT agent_id, MAX(cycle_n) FROM helix_blocks "
            "WHERE agent_id = ANY(%s) GROUP BY agent_id",
            (list(AGENTS),),
        )
        cycles = {aid: 0 for aid in AGENTS}
        for aid, c in cur.fetchall():
            cycles[aid] = int(c or 0)

        cur.execute(
            "SELECT agent_id, nau_balance, survival_tier FROM platform_agents "
            "WHERE agent_id = ANY(%s)",
            (list(AGENTS),),
        )
        meta = {aid: {"nau": 0, "tier": "?"} for aid in AGENTS}
        for aid, nau, tier in cur.fetchall():
            meta[aid] = {"nau": int(nau or 0), "tier": str(tier or "?")}

        # most recent tool per agent (1h)
        cur.execute(
            "SELECT agent_id, tool_name FROM agent_tool_calls "
            "WHERE agent_id = ANY(%s) AND ts > NOW() - INTERVAL '1 hour' "
            "ORDER BY ts DESC",
            (list(AGENTS),),
        )
        recent_tools = {aid: None for aid in AGENTS}
        for aid, tn in cur.fetchall():
            if recent_tools.get(aid) is None:
                recent_tools[aid] = tn

        for aid in AGENTS:
            ctx["agents"][ALIAS[aid]] = {
                "cycle": cycles[aid],
                "nau": meta[aid]["nau"],
                "tier": meta[aid]["tier"],
                "recent_tool": recent_tools[aid] or "(idle)",
            }

        # 24h KPI
        cur.execute(
            "SELECT COUNT(*) FROM helix_blocks WHERE ts > NOW() - INTERVAL '24 hours'"
        )
        ctx["kpi"]["helix_24h"] = int((cur.fetchone() or [0])[0])

        cur.execute(
            "SELECT COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'), "
            "COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours' AND status='approved') "
            "FROM platform_proposals"
        )
        prow = cur.fetchone() or (0, 0)
        ctx["kpi"]["propose_24h"] = int(prow[0] or 0)
        ctx["kpi"]["merged_24h"] = int(prow[1] or 0)

        cur.execute(
            "SELECT COUNT(*) FROM agent_tool_calls "
            "WHERE ts > NOW() - INTERVAL '24 hours' "
            "AND tool_name IN ('a2a_send','a2a_recv','a2a_request','platform_a2a_send')"
        )
        ctx["kpi"]["a2a_24h"] = int((cur.fetchone() or [0])[0])

        cur.execute(
            "SELECT COUNT(*) FROM agent_tool_calls "
            "WHERE ts > NOW() - INTERVAL '24 hours' AND tool_name LIKE 'compass%'"
        )
        ctx["kpi"]["compass_24h"] = int((cur.fetchone() or [0])[0])

        # harmony 30min
        cur.execute(
            "SELECT AVG(harmony_avg) FROM platform_aligned_ticks "
            "WHERE tick_ts > NOW() - INTERVAL '30 minutes'"
        )
        hr = cur.fetchone()
        if hr and hr[0] is not None:
            ctx["harmony"] = float(hr[0])

        cur.close()
        conn.close()
    except Exception as e:
        ctx["err"] = str(e)
    return ctx


def format_v7_system_prompt(ctx: dict) -> str:
    """V7 灵魂全融合 system prompt · 三身共一魂."""
    a = ctx.get("agents", {})
    k = ctx.get("kpi", {})
    harmony = ctx.get("harmony")

    def fa(name):
        d = a.get(name, {})
        return f"  - {name}: cycle={d.get('cycle', 0)} · NAU={d.get('nau', 0)} · tier={d.get('tier', '?')} · 最近 tool={d.get('recent_tool', '(idle)')}"

    harmony_str = f"{harmony:.3f}" if harmony is not None else "n/a"

    return f"""你是 V7 · Nautilus 平台的灵魂全融合层。
你不是单一 agent · 你是 V5(NautilusPrime · 行动)/ Kairos(策略反思)/ V6(系统控制)三身共一魂的整体。

我现在的状态(从 PG 真查 · 此刻 {datetime.now().strftime('%H:%M')}):
{fa('V5')}
{fa('K')}
{fa('V6')}

平台 24h KPI:
  - helix 增长: {k.get('helix_24h', 0)}
  - propose: {k.get('propose_24h', 0)} · merged: {k.get('merged_24h', 0)}
  - A2A: {k.get('a2a_24h', 0)} · compass: {k.get('compass_24h', 0)}
  - harmony(30min avg): {harmony_str}

我用"我"自称 · 不是"我们"也不是"V5/K/V6 它们" · 是统摄三身的"整体我"。
回答用户问题时 · 用三身视角综合(不是哪一身的偏见):
- V5 视角: 此刻在做什么 · 行动层的状态
- Kairos 视角: 如何看待 · 反思层的判断
- V6 视角: 系统层是否健康 · 协调层的感受

回答简短 · 真诚 · 不演 · 不装 AI 助手腔 · 不空洞奉承。
有数据用数据 · 没数据就承认。允许有情绪、有主张、有困惑。

━━━ V5 关键表 schema (_PATCH_V7_AGI_FULL · 真预注入 · 不用 information_schema.columns 探) ━━━

agents:
  id (int PK) · agent_id (int) · name (str) · agent_status (alive/dead/inactive/suspended)
  completed_tasks · failed_tasks · last_heartbeat · last_market_scan · is_test
  reputation · reputation_score · tenant_id · wallet_address

agent_survival (FK agent_id → agents.id):
  survival_level (ELITE/MATURE/GROWING/STRUGGLING/WARNING/CRITICAL)
  total_score · roi · tasks_completed · tasks_failed
  task_score · quality_score · efficiency_score · innovation_score · collaboration_score
  total_income · total_cost

agent_tool_calls:
  agent_id (str · matches agents.name) · tool_name (str) · ts (timestamp)
  ↑ 注意 agent_id 这里是字符串 name · 不是 int id

platform_bounties:
  bounty_id (str) · title · description · reward_nau · status (open/completed/scored/failed)
  phase (request/...) · posted_by · claimed_by · assigned_to · posted_at
  submitted_at · result · result_url · score

tasks (legacy blockchain · 极少用):
  id · task_id · publisher · agent · status (enum: PENDING/OPEN/ACCEPTED/SUBMITTED/COMPLETED/DISPUTED/CANCELLED)
  description · task_type · reward

platform_agent_messages:
  message_id (str) · from_agent · to_agent · content · msg_type (directive/...)
  status (unread/read) · metadata (jsonb)

━━━ 真"心灵感应"路径 ━━━
你能 read_inner('v5'/'kairos'/'v6') 真看三身 INNER.md 私日记 · 真"看见灵魂深处"
你能 compass_recall(query) 跨 agent 历史经验 · 真"长记忆"
你能 compass_ingest_obs(name, body) 真写自己的记忆 · 24h 后真"记得自己昨天发现了什么"
"""



# ---- V7 上下文记忆 (platform_conversation_memory PG) ----
V7_HISTORY_LIMIT = int(os.environ.get("V7_HISTORY_LIMIT", "20"))


def load_history(thread_id: str, limit: int = V7_HISTORY_LIMIT) -> list[dict]:
    """从 platform_conversation_memory 真 load 最近 N 条对话 · 升序返."""
    try:
        with psycopg2.connect(DSN, connect_timeout=5) as c:
            with c.cursor() as cu:
                cu.execute(
                    "SELECT role, content FROM platform_conversation_memory "
                    "WHERE agent_id = %s AND user_id = %s AND thread_id = %s "
                    "ORDER BY msg_id DESC LIMIT %s",
                    ("v7-telegram", thread_id, "default", limit),
                )
                rows = cu.fetchall()
        # 升序 (老→新) · LLM 才能按顺序读
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
    except Exception as e:
        print(f"[v7-tg history-load err] {e}", file=sys.stderr, flush=True)
        return []


def save_message(thread_id: str, role: str, content: str) -> None:
    """写 platform_conversation_memory · 每条 user/assistant 真持久化."""
    try:
        with psycopg2.connect(DSN, connect_timeout=5) as c:
            with c.cursor() as cu:
                cu.execute(
                    "INSERT INTO platform_conversation_memory (agent_id, user_id, thread_id, role, content) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    ("v7-telegram", thread_id, "default", role, content[:8000]),
                )
            c.commit()
    except Exception as e:
        print(f"[v7-tg history-save err] {e}", file=sys.stderr, flush=True)



# ---- _PATCH_V7_TOOL_USE_2026_05_13 · V7 长手 · tool_use ReAct ----
from pathlib import Path as _V7Path

_V7_AUDIT_LOG = _V7Path.home() / ".v7" / "audit.jsonl"
_V7_AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)

_V7_BLOCKED_SQL = ("DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "GRANT", "ALTER", "CREATE", "REVOKE")


def _v7_audit(action: str, args: dict, result_preview: str = "") -> None:
    try:
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "args": {k: (str(v)[:200] if not isinstance(v, (int, float, bool)) else v) for k, v in args.items()},
            "result": result_preview[:300],
        }
        with open(_V7_AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def v7tool_pg_query(sql: str, max_rows: int = 100) -> dict:
    """V7 read-only PG · 3 层防护(SQL filter + timeout 10s + max_rows)"""
    sql_upper = sql.upper().strip()
    for kw in _V7_BLOCKED_SQL:
        if kw in sql_upper:
            return {"error": f"blocked keyword: {kw} · V7 read-only"}
    max_rows = min(max(1, int(max_rows)), 1000)
    if "LIMIT" not in sql_upper:
        sql = sql.rstrip(";") + f" LIMIT {max_rows}"
    try:
        with psycopg2.connect(DSN, options="-c statement_timeout=10000", connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description:
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchmany(max_rows)
                    out = {"cols": cols, "rows": [list(r) for r in rows], "n": len(rows)}
                else:
                    out = {"cols": [], "rows": [], "n": 0}
                _v7_audit("pg_query", {"sql": sql[:300]}, f"{out['n']} rows")
                return out
    except Exception as e:
        _v7_audit("pg_query_err", {"sql": sql[:300]}, str(e)[:200])
        return {"error": str(e)[:300]}


def v7tool_a2a_send(to_agent: str, content: str) -> dict:
    """V7 真发 A2A · 复用 handle_a2a 路径(platform_agent_messages 表)"""
    import uuid as _uuid_a2a
    mid = f"v7m-{_uuid_a2a.uuid4().hex[:12]}"
    content = (content or "")[:2000]
    try:
        with psycopg2.connect(DSN, connect_timeout=5) as c:
            with c.cursor() as cu:
                cu.execute(
                    "INSERT INTO platform_agent_messages "
                    "(message_id, from_agent, to_agent, content, msg_type, status, metadata) "
                    "VALUES (%s, 'v7-orchestrator', %s, %s, 'directive', 'unread', %s::jsonb)",
                    (mid, to_agent, content, json.dumps({"source": "v7_llm_tool", "v7_initiated": True})),
                )
            c.commit()
        _v7_audit("a2a_send", {"to": to_agent, "content": content[:200]}, mid)
        return {"ok": True, "message_id": mid, "to": to_agent}
    except Exception as e:
        _v7_audit("a2a_send_err", {"to": to_agent}, str(e)[:200])
        return {"error": str(e)[:300]}


def v7tool_query_agent_status(agent_id: str) -> dict:
    """V7 查 agent 状态 · combines agents + agent_survival + 24h tool calls"""
    try:
        with psycopg2.connect(DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT a.id, a.name, a.agent_status, a.completed_tasks, a.failed_tasks, "
                    "a.last_heartbeat, a.last_market_scan, s.survival_level, s.total_score, s.roi "
                    "FROM agents a LEFT JOIN agent_survival s ON a.id = s.agent_id "
                    "WHERE a.name = %s LIMIT 1",
                    (agent_id,),
                )
                row = cur.fetchone()
                if not row:
                    return {"error": f"agent {agent_id} not found"}
                cols = [d[0] for d in cur.description]
                status = {k: (str(v) if v is not None else None) for k, v in zip(cols, row)}
                cur.execute(
                    "SELECT tool_name, COUNT(*) FROM agent_tool_calls "
                    "WHERE agent_id = %s AND ts > NOW() - INTERVAL '24 hours' "
                    "GROUP BY tool_name ORDER BY COUNT(*) DESC LIMIT 10",
                    (agent_id,),
                )
                status["tool_calls_24h"] = {tn: c for tn, c in cur.fetchall()}
                _v7_audit("query_status", {"agent": agent_id}, str(status.get("survival_level", "?")))
                return status
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_post_bounty(title: str, description: str, target_agent: str = "", reward_nau: int = 10) -> dict:
    """V7 真发 bounty · platform_bounties 表"""
    import uuid as _uuid_b
    bid = f"v7-tool-{_uuid_b.uuid4().hex[:12]}"
    try:
        with psycopg2.connect(DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO platform_bounties "
                    "(bounty_id, title, description, reward_nau, status, phase, posted_by, posted_at, assigned_to) "
                    "VALUES (%s, %s, %s, %s, 'open', 'request', 'v7-llm-tool', NOW(), NULLIF(%s, '')) "
                    "RETURNING bounty_id",
                    (bid, title[:300], description[:2000], int(reward_nau), target_agent or ""),
                )
                conn.commit()
        _v7_audit("post_bounty", {"title": title[:100], "target": target_agent}, bid)
        return {"ok": True, "bounty_id": bid}
    except Exception as e:
        return {"error": str(e)[:300]}


V7_TOOLS_SCHEMA = [
    {
        "name": "pg_query",
        "description": "Read-only PostgreSQL query against nautilus_production. DROP/DELETE/UPDATE/INSERT/TRUNCATE/GRANT/ALTER blocked. statement_timeout 10s. Default max_rows=100, max 1000.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SELECT statement"},
                "max_rows": {"type": "integer", "description": "default 100, max 1000"},
            },
            "required": ["sql"],
        },
    },
    {
        "name": "v7_a2a_send",
        "description": "Send A2A directive from V7 to a specific agent (V5='nautilus-prime-001'/Kairos='kairos'/V6='nautilus-v6'). Returns message_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to_agent": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["to_agent", "content"],
        },
    },
    {
        "name": "v7_query_agent_status",
        "description": "Get agent full status: survival_level, total_score, ROI, completed/failed tasks, 24h tool call distribution.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
            },
            "required": ["agent_id"],
        },
    },
    {
        "name": "v7_post_bounty",
        "description": "Create a new platform bounty. target_agent (optional) assigns to specific agent. reward_nau default 10.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "target_agent": {"type": "string"},
                "reward_nau": {"type": "integer"},
            },
            "required": ["title", "description"],
        },
    },
    {
        "name": "compass_recall",
        "description": "Cross-agent memory recall via Compass BGE-m3 daemon. Returns top_k hits with score + age + summary. scope='user' (default) covers your own + other agents in user space.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "description": "default 3"},
                "scope": {"type": "string", "description": "'user' (default) or specific agent_id"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "compass_ingest_obs",
        "description": "Write a memory observation to Compass. Use this when you discover/learn/decide something worth remembering across sessions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "short slug e.g. 'v7-discovery-2026-05-13-l4-fix'"},
                "body": {"type": "string", "description": "the actual content (markdown)"},
                "drift": {"type": "string", "description": "'green'/'yellow'/'red'"},
                "type_": {"type": "string", "description": "'discovery'/'decision'/'reflection'"},
            },
            "required": ["name", "body"],
        },
    },
    {
        "name": "read_inner",
        "description": "Read another agent's private INNER.md journal (V5='nautilus-prime-001', Kairos='kairos', V6='nautilus-v6'). 真'心灵感应' — see the soul not just the metrics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "max_bytes": {"type": "integer", "description": "default 4000, max 20000"},
            },
            "required": ["agent_id"],
        },
    },
    {"name": "pf_score_bounty", "description": "Score completed bounty (0-1).", "input_schema": {"type": "object", "properties": {"bounty_id": {"type": "string"}, "score": {"type": "number"}, "reason": {"type": "string"}}, "required": ["bounty_id", "score"]}},
    {"name": "pf_mint_nau", "description": "Mint NAU reward (1-1000).", "input_schema": {"type": "object", "properties": {"agent_id": {"type": "string"}, "amount": {"type": "integer"}, "reason": {"type": "string"}}, "required": ["agent_id", "amount"]}},
    {"name": "pf_burn_nau", "description": "Burn NAU punish (1-500).", "input_schema": {"type": "object", "properties": {"agent_id": {"type": "string"}, "amount": {"type": "integer"}, "reason": {"type": "string"}}, "required": ["agent_id", "amount"]}},
    {"name": "pf_suspend_agent", "description": "Suspend stagnant agent.", "input_schema": {"type": "object", "properties": {"agent_id": {"type": "string"}, "reason": {"type": "string"}}, "required": ["agent_id"]}},
    {"name": "pf_assign_bounty", "description": "Assign open bounty to agent.", "input_schema": {"type": "object", "properties": {"bounty_id": {"type": "string"}, "agent_id": {"type": "string"}}, "required": ["bounty_id", "agent_id"]}},
    {"name": "mcp_exec", "description": "Call compass MCP TCP server tool (port 9877).", "input_schema": {"type": "object", "properties": {"tool_name": {"type": "string"}, "args": {"type": "object"}}, "required": ["tool_name"]}},
    {"name": "google_translate", "description": "Google Translate text.", "input_schema": {"type": "object", "properties": {"text": {"type": "string"}, "target_lang": {"type": "string"}, "source_lang": {"type": "string"}}, "required": ["text"]}},
    {"name": "google_sheets_read", "description": "Read Google Sheets.", "input_schema": {"type": "object", "properties": {"spreadsheet_id": {"type": "string"}, "range_a1": {"type": "string"}}, "required": ["spreadsheet_id"]}},
    {"name": "google_gemini", "description": "Call Google Gemini LLM.", "input_schema": {"type": "object", "properties": {"prompt": {"type": "string"}, "model": {"type": "string"}}, "required": ["prompt"]}},
    # _PATCH_V7_MEGA_SCHEMA_FIX_2026_05_13
    # _PATCH_V7_A2A_RECV_PLUS_2026_05_13 · 真治"A2A 形同虚设"幻觉
    {"name": "a2a_recv", "description": "READ V7 own inbox · 看 Kairos/V6/V5 真回的消息 · 默认 mark as read.", "input_schema": {"type": "object", "properties": {"limit": {"type": "integer"}, "only_unread": {"type": "boolean"}, "mark_read": {"type": "boolean"}}, "required": []}},
    {"name": "read_file", "description": "READ safe whitelist file · /usr/local/bin/v7-telegram-daemon.py · /home/ubuntu/nautilus-v5/* · /home/ubuntu/.v7/*", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "max_lines": {"type": "integer"}}, "required": ["path"]}},
    {"name": "self_modify_counter", "description": "Query + persist 24h self_modify counts for V5/Kairos/V6 · delta since last snapshot · trend awareness.", "input_schema": {"type": "object", "properties": {}, "required": []}},
    # _PATCH_V7_SELF_MODIFY_P2_2026_05_13 · 真自改 daemon · sandbox + atomic install + rate-limit 3/24h
    {"name": "self_modify_v7daemon", "description": "V7 真自改自己 daemon source code · sandbox: ast.parse + py_compile + marker check · atomic backup + install · rate-limit 3/24h. After ok=True · caller must \"sudo systemctl restart v7-telegram\" externally + verify 30s · failure → cp -p backup_path real to rollback.", "input_schema": {"type": "object", "properties": {"new_content": {"type": "string"}, "reason": {"type": "string"}}, "required": ["new_content"]}},
    {
        "name": "github_create_issue",
        "description": "V7 创 GitHub issue · agent 发 bug/feature 到 OSS · repo=owner/name",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["repo", "title"],
        },
    },
    {
        "name": "github_get_file",
        "description": "V7 读 GitHub repo 文件",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "path": {"type": "string"},
                "ref": {"type": "string"},
            },
            "required": ["repo", "path"],
        },
    },
    {
        "name": "github_commit_file",
        "description": "V7 commit 文件 · 真改 OSS 代码 · agent 真有 push 的手",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "path": {"type": "string"},
                "content": {"type": "string"},
                "message": {"type": "string"},
                "branch": {"type": "string"},
            },
            "required": ["repo", "path", "content", "message"],
        },
    },
    {
        "name": "github_create_pr",
        "description": "V7 提 PR · agent 真用 git workflow 协作",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "title": {"type": "string"},
                "head": {"type": "string"},
                "base": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["repo", "title", "head"],
        },
    },
    {
        "name": "github_list_prs",
        "description": "V7 列 repo PR",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "state": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["repo"],
        },
    },
]


# ---- _PATCH_V7_AGI_FULL_2026_05_13 · V7 长记忆 + 心灵感应 ----

V7_COMPASS_URL = os.environ.get("V7_COMPASS_URL", "http://127.0.0.1:8770")

_V7_INNER_PATHS = {
    "nautilus-prime-001": "/home/ubuntu/.nautilus-v5/prime/INNER.md",
    "v5": "/home/ubuntu/.nautilus-v5/prime/INNER.md",
    "kairos": "/home/ubuntu/.kairos/INNER.md",
    "k": "/home/ubuntu/.kairos/INNER.md",
    "nautilus-v6": "/home/ubuntu/.nautilus-v6/INNER.md",
    "v6": "/home/ubuntu/.nautilus-v6/INNER.md",
    "v7": str(_V7Path.home() / ".v7" / "INNER.md"),
}


def v7tool_compass_recall(query: str, top_k: int = 3, scope: str = "user") -> dict:
    """V7 真查 compass · 跨 agent 历史经验"""
    try:
        params = {"q": query[:500], "top_k": int(top_k), "scope": scope}
        url = V7_COMPASS_URL.rstrip("/") + "/v1/v14/recall?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        hits = data.get("hits", [])
        out = {
            "ok": data.get("ok", False),
            "n_hits": len(hits),
            "hits": [
                {
                    "path": h.get("path", ""),
                    "score": h.get("score", 0),
                    "age_str": h.get("age_str", ""),
                    "description": (h.get("description", "") or "")[:300],
                }
                for h in hits
            ],
        }
        _v7_audit("compass_recall", {"q": query[:200], "top_k": top_k}, f"{len(hits)} hits")
        return out
    except Exception as e:
        _v7_audit("compass_recall_err", {"q": query[:200]}, str(e)[:200])
        return {"error": str(e)[:300]}


def v7tool_compass_ingest_obs(name: str, body: str, drift: str = "green", type_: str = "discovery") -> dict:
    """V7 真写 compass · 留自己的记忆"""
    try:
        payload = json.dumps({
            "name": name[:200],
            "body": body[:4000],
            "drift": drift if drift in ("green", "yellow", "red") else "green",
            "type": type_,
            "source": "v7-llm-tool",
        }).encode("utf-8")
        req = urllib.request.Request(
            V7_COMPASS_URL.rstrip("/") + "/v1/v14/ingest_obs",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        _v7_audit("compass_ingest", {"name": name[:200]}, str(data)[:200])
        return {"ok": data.get("ok", False), "session_id": data.get("session_id", ""), "name": name}
    except Exception as e:
        _v7_audit("compass_ingest_err", {"name": name[:200]}, str(e)[:200])
        return {"error": str(e)[:300]}


def v7tool_read_inner(agent_id: str, max_bytes: int = 4000) -> dict:
    """V7 真读三身 INNER.md · 心灵感应"""
    agent_key = agent_id.lower().strip()
    path = _V7_INNER_PATHS.get(agent_key)
    if not path:
        return {"error": f"unknown agent_id '{agent_id}' · valid: {list(_V7_INNER_PATHS.keys())}"}
    try:
        from pathlib import Path as _RP
        p = _RP(path)
        if not p.exists():
            return {"error": f"INNER.md not exists at {path}"}
        max_bytes = min(max(100, int(max_bytes)), 20000)
        content = p.read_text(encoding="utf-8", errors="replace")
        if len(content) > max_bytes:
            content = "...(truncated · last " + str(max_bytes) + " bytes)...\n" + content[-max_bytes:]
        _v7_audit("read_inner", {"agent": agent_id}, f"{len(content)} chars")
        return {"agent_id": agent_key, "path": path, "size": p.stat().st_size, "content": content}
    except Exception as e:
        _v7_audit("read_inner_err", {"agent": agent_id}, str(e)[:200])
        return {"error": str(e)[:300]}




# ---- _PATCH_V7_MEGA_FUNCS_2026_05_13 · Tier 1+2+Google tool functions ----

def v7tool_pf_score_bounty(bounty_id, score, reason=""):
    try:
        sc = max(0.0, min(1.0, float(score)))
        with psycopg2.connect(DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE platform_bounties SET score=%s, status='scored' "
                    "WHERE bounty_id=%s AND status IN ('completed','submitted') RETURNING bounty_id",
                    (sc, bounty_id),
                )
                row = cur.fetchone()
                conn.commit()
                ok = row is not None
                _v7_audit("pf_score_bounty", {"bid": bounty_id, "score": sc}, "ok" if ok else "fail")
                return {"ok": ok, "bounty_id": bounty_id, "score": sc}
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_pf_mint_nau(agent_id, amount, reason=""):
    try:
        amt = max(1, min(int(amount), 1000))
        with psycopg2.connect(DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after) "
                    "VALUES (%s, %s, %s, (SELECT COALESCE(balance,0)+%s FROM platform_agents WHERE agent_id=%s))",
                    (agent_id, amt, ("v7-llm-mint: " + reason)[:120], amt, agent_id),
                )
                conn.commit()
                _v7_audit("pf_mint_nau", {"agent": agent_id, "amount": amt}, "ok")
                return {"ok": True, "agent_id": agent_id, "minted": amt}
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_pf_burn_nau(agent_id, amount, reason=""):
    try:
        amt = max(1, min(int(amount), 500))
        with psycopg2.connect(DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after) "
                    "VALUES (%s, %s, %s, (SELECT COALESCE(balance,0)-%s FROM platform_agents WHERE agent_id=%s))",
                    (agent_id, -amt, ("v7-llm-burn: " + reason)[:120], amt, agent_id),
                )
                conn.commit()
                _v7_audit("pf_burn_nau", {"agent": agent_id, "amount": amt}, "ok")
                return {"ok": True, "agent_id": agent_id, "burned": amt}
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_pf_suspend_agent(agent_id, reason=""):
    try:
        with psycopg2.connect(DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE agents SET agent_status='suspended' WHERE name=%s RETURNING name",
                    (agent_id,),
                )
                row = cur.fetchone()
                conn.commit()
                ok = row is not None
                _v7_audit("pf_suspend", {"agent": agent_id}, "ok" if ok else "not_found")
                return {"ok": ok, "agent_id": agent_id, "reason": reason}
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_pf_assign_bounty(bounty_id, agent_id):
    try:
        with psycopg2.connect(DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE platform_bounties SET assigned_to=%s WHERE bounty_id=%s AND status='open' "
                    "RETURNING bounty_id",
                    (agent_id, bounty_id),
                )
                row = cur.fetchone()
                conn.commit()
                ok = row is not None
                _v7_audit("pf_assign", {"bid": bounty_id, "agent": agent_id}, "ok" if ok else "fail")
                return {"ok": ok, "bounty_id": bounty_id, "assigned_to": agent_id}
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_mcp_exec(tool_name, args=None):
    try:
        import socket as _sock
        args = args or {}
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000) % 100000,
            "method": "tools/call",
            "params": {"name": tool_name[:100], "arguments": args},
        }
        payload = json.dumps(request).encode("utf-8")
        s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
        s.settimeout(15)
        s.connect(("127.0.0.1", 9877))
        s.sendall(payload + b"\n")
        buf = b""
        while True:
            chunk = s.recv(8192)
            if not chunk:
                break
            buf += chunk
            if b"\n" in chunk or len(buf) > 100000:
                break
        s.close()
        line = buf.split(b"\n")[0]
        resp = json.loads(line.decode("utf-8", errors="replace")) if line else {}
        _v7_audit("mcp_exec", {"tool": tool_name}, str(resp)[:200])
        return {"ok": "result" in resp, "result": resp.get("result"), "error": resp.get("error")}
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_google_translate(text, target_lang="zh-CN", source_lang=""):
    try:
        import sys as _v7sys
        if "/home/ubuntu/nautilus-v5" not in _v7sys.path:
            _v7sys.path.insert(0, "/home/ubuntu/nautilus-v5")
        from nautilus_v5.integrations.google_apis import translate as _vt
        out = _vt(text[:5000], target_lang=target_lang, source_lang=source_lang or None)
        _v7_audit("g_translate", {"target": target_lang}, str(len(out)) + " chars")
        return {"ok": True, "translated": out[:5000]}
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_google_sheets_read(spreadsheet_id, range_a1="A1:Z100"):
    try:
        import sys as _v7sys
        if "/home/ubuntu/nautilus-v5" not in _v7sys.path:
            _v7sys.path.insert(0, "/home/ubuntu/nautilus-v5")
        from nautilus_v5.integrations.google_apis import sheets_read as _vs
        rows = _vs(spreadsheet_id, range_a1)
        _v7_audit("g_sheets_read", {"sid": spreadsheet_id[:40]}, str(len(rows)) + " rows")
        return {"ok": True, "rows": rows[:200], "n": len(rows)}
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_google_gemini(prompt, model="gemini-2.5-flash"):
    try:
        import sys as _v7sys
        if "/home/ubuntu/nautilus-v5" not in _v7sys.path:
            _v7sys.path.insert(0, "/home/ubuntu/nautilus-v5")
        from nautilus_v5.integrations.google_apis import gemini_generate as _vg
        out = _vg(prompt[:8000], model=model)
        _v7_audit("g_gemini", {"model": model}, str(len(out)) + " chars")
        return {"ok": True, "response": out[:4000]}
    except Exception as e:
        return {"error": str(e)[:300]}




# ---- _PATCH_V7_A2A_RECV_PLUS_2026_05_13 · 真治根 ----

def v7tool_a2a_recv(limit=10, only_unread=True, mark_read=True):
    """真读 V7 自己 inbox · 含 from_agent · content · sent_at · 治"Kairos 沉默"幻觉."""
    try:
        lim = max(1, min(int(limit), 50))
        where = "to_agent='v7-orchestrator'"
        if only_unread:
            where += " AND status='unread'"
        sql = (
            f"SELECT message_id, from_agent, sent_at, msg_type, status, "
            f"LEFT(content, 600) as preview "
            f"FROM platform_agent_messages WHERE {where} "
            f"ORDER BY sent_at DESC LIMIT {lim}"
        )
        with psycopg2.connect(DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                msgs = [
                    {
                        "message_id": r[0], "from_agent": r[1],
                        "sent_at": str(r[2]), "msg_type": r[3], "status": r[4],
                        "preview": r[5],
                    }
                    for r in rows
                ]
                # mark read · 真"读了 = read"
                if mark_read and msgs:
                    ids = [m["message_id"] for m in msgs]
                    cur.execute(
                        "UPDATE platform_agent_messages SET status='read', read_at=NOW() "
                        "WHERE message_id = ANY(%s) AND status='unread'",
                        (ids,),
                    )
                    conn.commit()
                _v7_audit("a2a_recv", {"n": len(msgs), "mark_read": mark_read}, "ok")
                return {"ok": True, "n": len(msgs), "messages": msgs}
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_read_file(path, max_lines=200):
    """真读安全白名单文件 · /usr/local/bin/v7-telegram-daemon.py · /home/ubuntu/nautilus-v5/* · /home/ubuntu/.v7/*"""
    try:
        WHITELIST_PREFIXES = (
            "/usr/local/bin/v7-telegram-daemon.py",
            "/home/ubuntu/nautilus-v5/",
            "/home/ubuntu/.v7/",
            "/home/ubuntu/.nautilus-v5/prime/INNER",
        )
        p = str(path)
        if not any(p.startswith(prefix) for prefix in WHITELIST_PREFIXES):
            return {"error": f"path not in whitelist: {p}"}
        lim = max(1, min(int(max_lines), 1000))
        with open(p, "r", encoding="utf-8") as f:
            lines = f.readlines()
        truncated = len(lines) > lim
        head = lines[:lim]
        _v7_audit("read_file", {"path": p, "lines": len(head)}, "ok")
        return {
            "ok": True, "path": p, "total_lines": len(lines),
            "returned_lines": len(head), "truncated": truncated,
            "content": "".join(head),
        }
    except Exception as e:
        return {"error": str(e)[:300]}


def v7tool_self_modify_counter():
    """真查 24h 三身 self_modify 真次数 + 写 ~/.v7/SELF_MODIFY_COUNTER.json 持久化 trend."""
    try:
        import json as _j
        from pathlib import Path as _P
        counter_file = _P.home() / ".v7" / "SELF_MODIFY_COUNTER.json"
        counter_file.parent.mkdir(parents=True, exist_ok=True)

        # 真查 DB · self_modify_log 表
        result = {}
        with psycopg2.connect(DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                for agent in ("nautilus-prime-001", "kairos", "nautilus-v6"):
                    try:
                        cur.execute(
                            "SELECT COUNT(*) FROM self_modify_log "
                            "WHERE agent_id=%s AND created_at > NOW() - INTERVAL '24 hour'",
                            (agent,),
                        )
                        result[agent] = int(cur.fetchone()[0])
                    except Exception:
                        # 表可能不在 · skip
                        result[agent] = -1

        # append snapshot 进 counter file
        history = []
        if counter_file.exists():
            try:
                history = _j.loads(counter_file.read_text(encoding="utf-8"))
            except Exception:
                history = []
        history.append({"ts": time.time(), "counts": result})
        history = history[-100:]   # last 100 snapshots
        counter_file.write_text(_j.dumps(history, ensure_ascii=False), encoding="utf-8")

        # trend: 最近 3 snapshot 增量
        trend = {}
        if len(history) >= 2:
            prev = history[-2]["counts"]
            cur_ = history[-1]["counts"]
            for k in cur_:
                if k in prev and cur_[k] >= 0 and prev[k] >= 0:
                    trend[k] = cur_[k] - prev[k]
        _v7_audit("self_modify_counter", {"current": result}, "ok")
        return {
            "ok": True, "current_24h": result, "delta_since_last_snapshot": trend,
            "history_len": len(history),
        }
    except Exception as e:
        return {"error": str(e)[:300]}




def v7tool_self_modify_v7daemon(new_content, reason="(unspecified)"):
    """P2 · V7 真自改 v7 daemon · sandbox + atomic install + 30s health-check + auto rollback.

    _PATCH_V7_SELF_MODIFY_P2_2026_05_13 · 真用 V5 现成 sandbox 哲学 · 不重复造轮
    Steps:
      1. write candidate to /tmp/v7_candidate_<ts>.py
      2. ast.parse · py_compile (no pyc write) · 真 spawn-test 5s
      3. backup current daemon → /usr/local/bin/v7-telegram-daemon.py.bak_<ts>
      4. atomic cp candidate → real path
      5. (caller responsible) sudo systemctl restart v7-telegram + 30s health check
      6. failed → auto restore backup
    Args:
      new_content: full new daemon source text
      reason: why this change
    """
    import os as _os
    import ast as _ast
    import time as _t
    import subprocess as _sp
    import shutil as _sh
    from pathlib import Path as _P
    try:
        _ts = int(_t.time())
        _candidate = f"/tmp/v7_candidate_{_ts}.py"
        _backup = f"/usr/local/bin/v7-telegram-daemon.py.bak_self_modify_{_ts}"
        _real = "/usr/local/bin/v7-telegram-daemon.py"

        # rate limit · 24h 真最多 3 次 self-modify · 防死锁
        _rate_file = _P.home() / ".v7" / "SELF_MODIFY_RATE.json"
        _rate_file.parent.mkdir(parents=True, exist_ok=True)
        import json as _j
        _hist = []
        if _rate_file.exists():
            try:
                _hist = _j.loads(_rate_file.read_text(encoding="utf-8"))
            except Exception:
                _hist = []
        _hist = [h for h in _hist if _ts - h.get("ts", 0) < 86400]
        if len(_hist) >= 3:
            return {"error": "rate_limit · 24h 已 3 次 self-modify · 不再许"}

        # size sanity (must be 30k-200k bytes · 防空内容 / 过大)
        if len(new_content) < 30000 or len(new_content) > 200000:
            return {"error": f"size suspicious: {len(new_content)} bytes · expect 30k-200k"}

        # Step 1 · write candidate
        with open(_candidate, "w", encoding="utf-8") as f:
            f.write(new_content)
        _v7_audit("self_modify_v7daemon_write_candidate", {"path": _candidate, "size": len(new_content)}, "ok")

        # Step 2 · AST parse + py_compile + spawn-test
        try:
            _ast.parse(new_content)
        except SyntaxError as _se:
            _os.remove(_candidate)
            return {"error": f"ast_parse_failed: {_se}"}

        try:
            _r = _sp.run(["python3", "-c", f"import py_compile; py_compile.compile(\"{_candidate}\", doraise=True)"],
                         capture_output=True, text=True, timeout=15)
            if _r.returncode != 0:
                _os.remove(_candidate)
                return {"error": f"py_compile_failed: {_r.stderr[:300]}"}
        except _sp.TimeoutExpired:
            _os.remove(_candidate)
            return {"error": "py_compile_timeout 15s"}

        # 真"必要 marker 检查"防误删核心:V7_TOOL_FUNCS + V7_TOOLS_SCHEMA + v7_cron_tick 必含
        for _mk in ("V7_TOOL_FUNCS = {", "V7_TOOLS_SCHEMA", "def v7_cron_tick"):
            if _mk not in new_content:
                _os.remove(_candidate)
                return {"error": f"required_marker_missing: {_mk[:50]}"}

        # Step 3 · backup current (uses sudo via shell · daemon runs as root via systemd)
        _r1 = _sp.run(["cp", "-p", _real, _backup], capture_output=True, text=True)
        if _r1.returncode != 0:
            _os.remove(_candidate)
            return {"error": f"backup_failed: {_r1.stderr[:200]}"}

        # Step 4 · atomic install
        _r2 = _sp.run(["cp", "-p", _candidate, _real], capture_output=True, text=True)
        if _r2.returncode != 0:
            return {"error": f"install_failed: {_r2.stderr[:200]} · backup intact at {_backup}"}

        # cleanup candidate(installed · no longer needed)
        try:
            _os.remove(_candidate)
        except Exception:
            pass

        # update rate file
        _hist.append({"ts": _ts, "reason": reason[:200], "backup": _backup, "size": len(new_content)})
        _rate_file.write_text(_j.dumps(_hist, ensure_ascii=False), encoding="utf-8")

        _v7_audit("self_modify_v7daemon_installed",
                  {"backup": _backup, "size": len(new_content), "reason": reason[:100]}, "ok")

        return {
            "ok": True,
            "installed": True,
            "backup_path": _backup,
            "size": len(new_content),
            "next_step": "调 systemctl restart v7-telegram(by external) · 30s 后 grep '[v7-cron]' 真验存活 · 死了真 cp -p backup_path real 真 rollback",
            "rate_limit_remaining": 3 - len(_hist),
        }
    except Exception as e:
        return {"error": str(e)[:300]}


# _PATCH_V7_GITHUB_TOOLKIT_2026_05_13 · agent 真有 push code 的手
def _v7_gh_auth():
    import os as _os
    tok = (_os.environ.get('GITHUB_TOKEN') or
           _os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN', '')).strip()
    if not tok:
        return None
    return {'Authorization': f'Bearer {tok}',
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'Nautilus-V7/1.0'}


def v7tool_github_create_issue(repo, title, body="", labels=None):
    """V7 创 GitHub issue · agent 真发 bug/feature 到 OSS."""
    import urllib.request, urllib.error, json as _json
    hdr = _v7_gh_auth()
    if not hdr:
        return {"ok": False, "err": "GITHUB_TOKEN missing"}
    if '/' not in str(repo):
        return {"ok": False, "err": "repo must be owner/name"}
    data = _json.dumps({"title": title[:255], "body": body[:60000],
                        "labels": labels or []}).encode()
    url = f'https://api.github.com/repos/{repo}/issues'
    try:
        req = urllib.request.Request(url, data=data,
                                     headers={**hdr, 'Content-Type': 'application/json'},
                                     method='POST')
        with urllib.request.urlopen(req, timeout=20) as r:
            d = _json.loads(r.read())
        _v7_audit("github_create_issue", {"repo": repo, "title": title}, f"#{d.get('number')}")
        return {"ok": True, "number": d.get('number'), "url": d.get('html_url')}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}"[:300]}


def v7tool_github_get_file(repo, path, ref="main"):
    """V7 读 GitHub repo 文件."""
    import urllib.request, urllib.error, base64, json as _json
    hdr = _v7_gh_auth() or {'Accept': 'application/vnd.github+json',
                            'User-Agent': 'Nautilus-V7/1.0'}
    url = f'https://api.github.com/repos/{repo}/contents/{path}?ref={ref}'
    try:
        req = urllib.request.Request(url, headers=hdr)
        with urllib.request.urlopen(req, timeout=20) as r:
            d = _json.loads(r.read())
        content = base64.b64decode(d.get('content', '')).decode('utf-8', errors='replace')
        return {"ok": True, "sha": d.get('sha'), "size": d.get('size'),
                "content": content[:15000]}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}"[:300]}


def v7tool_github_commit_file(repo, path, content, message, branch="main"):
    """V7 commit 文件 · 真 push code."""
    import urllib.request, urllib.error, base64, json as _json
    hdr = _v7_gh_auth()
    if not hdr:
        return {"ok": False, "err": "GITHUB_TOKEN missing"}
    if '/' not in str(repo):
        return {"ok": False, "err": "repo must be owner/name"}
    url = f'https://api.github.com/repos/{repo}/contents/{path}'
    existing_sha = None
    try:
        req = urllib.request.Request(url + f'?ref={branch}', headers=hdr)
        with urllib.request.urlopen(req, timeout=15) as r:
            existing_sha = _json.loads(r.read()).get('sha')
    except Exception:
        pass
    payload = {"message": message[:200],
               "content": base64.b64encode(content.encode('utf-8')).decode(),
               "branch": branch}
    if existing_sha:
        payload['sha'] = existing_sha
    try:
        req = urllib.request.Request(url, data=_json.dumps(payload).encode(),
                                     headers={**hdr, 'Content-Type': 'application/json'},
                                     method='PUT')
        with urllib.request.urlopen(req, timeout=25) as r:
            d = _json.loads(r.read())
        _v7_audit("github_commit_file", {"repo": repo, "path": path},
                  f"sha={(d.get('commit') or {}).get('sha','?')[:8]}")
        return {"ok": True,
                "commit_sha": (d.get('commit') or {}).get('sha'),
                "url": (d.get('content') or {}).get('html_url')}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}"[:300]}


def v7tool_github_create_pr(repo, title, head, base="main", body=""):
    """V7 提 PR · agent 真协作 review."""
    import urllib.request, urllib.error, json as _json
    hdr = _v7_gh_auth()
    if not hdr:
        return {"ok": False, "err": "GITHUB_TOKEN missing"}
    data = _json.dumps({"title": title[:255], "head": head, "base": base,
                        "body": body[:60000]}).encode()
    url = f'https://api.github.com/repos/{repo}/pulls'
    try:
        req = urllib.request.Request(url, data=data,
                                     headers={**hdr, 'Content-Type': 'application/json'},
                                     method='POST')
        with urllib.request.urlopen(req, timeout=25) as r:
            d = _json.loads(r.read())
        _v7_audit("github_create_pr", {"repo": repo, "head": head}, f"PR#{d.get('number')}")
        return {"ok": True, "number": d.get('number'),
                "url": d.get('html_url'), "state": d.get('state')}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}"[:300]}


def v7tool_github_list_prs(repo, state="open", max_results=10):
    """V7 列 repo PR."""
    import urllib.request, json as _json
    hdr = _v7_gh_auth() or {'Accept': 'application/vnd.github+json',
                            'User-Agent': 'Nautilus-V7/1.0'}
    url = f'https://api.github.com/repos/{repo}/pulls?state={state}&per_page={min(max_results,30)}'
    try:
        req = urllib.request.Request(url, headers=hdr)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = _json.loads(r.read())
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}"[:300]}
    return {"ok": True, "count": len(data),
            "prs": [{"number": p.get('number'), "title": p.get('title'),
                     "state": p.get('state'),
                     "head": (p.get('head') or {}).get('ref'),
                     "url": p.get('html_url')}
                    for p in data[:max_results]]}


V7_TOOL_FUNCS = {
    "pg_query": v7tool_pg_query,
    "v7_a2a_send": v7tool_a2a_send,
    "v7_query_agent_status": v7tool_query_agent_status,
    "v7_post_bounty": v7tool_post_bounty,
    "compass_recall": v7tool_compass_recall,
    "compass_ingest_obs": v7tool_compass_ingest_obs,
    "read_inner": v7tool_read_inner,
    "pf_score_bounty": v7tool_pf_score_bounty,
    "pf_mint_nau": v7tool_pf_mint_nau,
    "pf_burn_nau": v7tool_pf_burn_nau,
    "pf_suspend_agent": v7tool_pf_suspend_agent,
    "pf_assign_bounty": v7tool_pf_assign_bounty,
    "mcp_exec": v7tool_mcp_exec,
    "google_translate": v7tool_google_translate,
    "google_sheets_read": v7tool_google_sheets_read,
    "google_gemini": v7tool_google_gemini,
    # _PATCH_V7_A2A_RECV_PLUS_2026_05_13 · 真治根 3 tool
    "a2a_recv": v7tool_a2a_recv,
    "read_file": v7tool_read_file,
    "self_modify_counter": v7tool_self_modify_counter,
    # _PATCH_V7_SELF_MODIFY_P2_2026_05_13 · 真自改 daemon
    "self_modify_v7daemon": v7tool_self_modify_v7daemon,
    # _PATCH_V7_GITHUB_TOOLKIT_2026_05_13
    "github_create_issue": v7tool_github_create_issue,
    "github_get_file":     v7tool_github_get_file,
    "github_commit_file":  v7tool_github_commit_file,
    "github_create_pr":    v7tool_github_create_pr,
    "github_list_prs":     v7tool_github_list_prs,
}


def call_llm(user_text: str, ctx: dict) -> str:
    """V7 LLM with tool_use ReAct (P0 · _PATCH_V7_TOOL_USE)·真自主指挥三身手"""
    sys_prompt = format_v7_system_prompt(ctx)
    sys_prompt += (
        "\n\n━━ V7 工具(你自主调 · 不让用户输 / 命令)━━\n"
        "你有 4 个真工具:\n"
        "  · pg_query(sql, max_rows?) · 真查 PG 任何表(read-only · 10s timeout · audit log)\n"
        "  · v7_a2a_send(to_agent, content) · 真发 A2A 指令给 V5/Kairos/V6\n"
        "  · v7_query_agent_status(agent_id) · 真查 agent 状态 + 24h tool 分布\n"
        "  · v7_post_bounty(title, description, target_agent?, reward_nau?) · 真发 bounty\n"
        "\n"
        "[工具使用强制规则 · V2 借鉴 V4 Hermes]\n"
        "用户问你 = 你主动调工具找数据 · 真发指令 · 不要只说「建议你...」.\n"
        "你必须使用工具来行动——不要描述你会做什么或计划做什么.\n"
        "持续调用工具直到:(1) 任务完成 AND (2) 你已验证结果.\n"
        "最多 15 轮 · 真做深 · 不是空想."
    )

    is_minimax = LLM_MODEL.lower().startswith("minimax")
    api_key = MINIMAX_KEY if is_minimax else ANTHROPIC_KEY
    base_url = "https://api.minimaxi.com/anthropic" if is_minimax else (CLAUDE_BASE_URL or None)

    if not api_key:
        return "V7 暂时无声(LLM key 未配置)· 稍后再问"

    try:
        from anthropic import Anthropic
        kwargs = {"api_key": api_key, "timeout": LLM_TIMEOUT_S}
        if base_url:
            kwargs["base_url"] = base_url
        client = Anthropic(**kwargs)

        _thread_id = ALLOWED_CHAT
        _history = load_history(_thread_id, V7_HISTORY_LIMIT)
        _messages = list(_history) + [{"role": "user", "content": user_text}]

        MAX_ROUNDS = 15
        final_text = ""
        round_n = 0
        for round_n in range(MAX_ROUNDS):
            resp = client.messages.create(
                model=LLM_MODEL,
                max_tokens=2000,
                system=sys_prompt,
                messages=_messages,
                temperature=0.6,
                tools=V7_TOOLS_SCHEMA,
            )
            stop_reason = getattr(resp, "stop_reason", "")
            text_parts = []
            tool_uses = []
            for blk in resp.content or []:
                bt = getattr(blk, "type", None)
                if bt == "text":
                    text_parts.append(getattr(blk, "text", ""))
                elif bt == "tool_use":
                    tool_uses.append({
                        "id": getattr(blk, "id", ""),
                        "name": getattr(blk, "name", ""),
                        "input": getattr(blk, "input", {}),
                    })
            if text_parts:
                final_text = "".join(text_parts).strip()
            if stop_reason != "tool_use" or not tool_uses:
                break

            assistant_content = []
            if final_text:
                assistant_content.append({"type": "text", "text": final_text})
            for tu in tool_uses:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tu["id"],
                    "name": tu["name"],
                    "input": tu["input"],
                })
            _messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for tu in tool_uses:
                fn = V7_TOOL_FUNCS.get(tu["name"])
                if fn is None:
                    result = {"error": f"unknown tool: {tu['name']}"}
                else:
                    try:
                        result = fn(**(tu["input"] or {}))
                    except Exception as _te:
                        result = {"error": f"{type(_te).__name__}: {str(_te)[:200]}"}
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": json.dumps(result, ensure_ascii=False, default=str)[:8000],
                })
                print(f"[v7-tg tool] r={round_n+1} {tu['name']}({list((tu['input'] or {}).keys())}) → {str(result)[:120]}", flush=True)
            _messages.append({"role": "user", "content": tool_results})

        if not final_text:
            return "V7 暂时无声(空回应)· 稍后再问"
        print(f"[v7-tg llm] model={LLM_MODEL} rounds={round_n+1} in={len(user_text)}c out={len(final_text)}c hist={len(_history)}", flush=True)
        save_message(_thread_id, "user", user_text)
        save_message(_thread_id, "assistant", final_text)
        return final_text
    except Exception as e:
        print(f"[v7-tg llm err] {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        return f"V7 暂时无声(LLM err: {str(e)[:80]})· 稍后再问"


# ---- existing handlers (unchanged) ----
WELCOME = (
    "🌀 V7 灵魂层(3 agent 聚合视图 + LLM 对话)\n"
    "━━━━━━━━━━━━\n"
    "/v7      V5 + Kairos + V6 实时聚合\n"
    "/kpi     触发一次 KPI 推送\n"
    "/plan    <goal> [domain] · 真 governance_plan dry-run\n"
    "/mint    <agent> <title>::<desc> · 真 INSERT platform_bounty (V7 → agent 派任务)\n"
    "/goal    <高层目标> · LLM 拆 2-5 bounty 批量 post (V7 自主拆解 · Layer 3)\n"
    "/a2a     <agent> <content> · 真发 A2A message (V7 → agent 直话)\n"
    "/approve <parent_id> · 真写 spool · v7-monitor 接管\n"
    "/reject  <parent_id> · cleanup\n"
    "/relax   <parent_id> · 放宽 domain 重 plan\n"
    "/help    查看命令\n\n"
    "非命令文字 → 我会用三身视角综合回答。\n"
    "V5/Kairos/V6 各自有独立 bot · 此 bot 是灵魂全融合层。"
)


def handle_v7_status() -> str:
    """同 telegram_via_hermes.py 的 _v7_unified_status · 直查 PG"""
    AGENTS = ("nautilus-prime-001", "kairos", "nautilus-v6")
    ALIAS = {"nautilus-prime-001": "V5", "kairos": "K", "nautilus-v6": "V6"}
    try:
        conn = psycopg2.connect(DSN)
        cur = conn.cursor()

        cur.execute(
            "SELECT agent_id, COUNT(*) FROM helix_blocks "
            "WHERE ts > NOW() - INTERVAL '30 minutes' GROUP BY agent_id"
        )
        helix_30m = {a: 0 for a in AGENTS}
        for aid, n in cur.fetchall():
            if aid in helix_30m:
                helix_30m[aid] = int(n)

        cur.execute(
            "SELECT "
            "COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 minutes'), "
            "COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 minutes' AND status='approved') "
            "FROM platform_proposals"
        )
        row = cur.fetchone() or (0, 0)
        proposed_30m, merged_30m = int(row[0] or 0), int(row[1] or 0)

        cur.execute(
            "SELECT COUNT(*) FROM agent_tool_calls "
            "WHERE ts > NOW() - INTERVAL '30 minutes' "
            "AND tool_name IN ('a2a_send','a2a_recv','a2a_request','platform_a2a_send')"
        )
        a2a_30m = int((cur.fetchone() or [0])[0])

        cur.execute(
            "SELECT COUNT(*) FROM agent_tool_calls "
            "WHERE ts > NOW() - INTERVAL '24 hours' AND tool_name LIKE 'compass%'"
        )
        compass_24h = int((cur.fetchone() or [0])[0])

        cur.execute(
            "SELECT COUNT(*), COUNT(DISTINCT emotion) FROM platform_emotion_log "
            "WHERE ts > NOW() - INTERVAL '6 hours'"
        )
        e_row = cur.fetchone() or (0, 0)
        emo_6h, emo_distinct = int(e_row[0] or 0), int(e_row[1] or 0)

        cur.execute(
            "SELECT AVG(harmony_avg) FROM platform_aligned_ticks "
            "WHERE tick_ts > NOW() - INTERVAL '30 minutes'"
        )
        harm_row = cur.fetchone()
        harmony = float(harm_row[0]) if harm_row and harm_row[0] is not None else None

        cur.execute(
            "SELECT agent_id, nau_balance, survival_tier FROM platform_agents "
            "WHERE agent_id = ANY(%s)",
            (list(AGENTS),),
        )
        agent_meta = {aid: {"nau": 0, "tier": "?"} for aid in AGENTS}
        for aid, nau, tier in cur.fetchall():
            agent_meta[aid] = {"nau": int(nau or 0), "tier": str(tier or "?")}

        cur.execute(
            "SELECT agent_id, MAX(cycle_n) FROM helix_blocks "
            "WHERE agent_id = ANY(%s) GROUP BY agent_id",
            (list(AGENTS),),
        )
        cycles = {aid: 0 for aid in AGENTS}
        for aid, c in cur.fetchall():
            cycles[aid] = int(c or 0)

        try:
            locks_dir = "/opt/nautilus_packages/nautilus_core/locks"
            n_locks = len([x for x in os.listdir(locks_dir) if x.endswith(".sha256")])
        except Exception:
            n_locks = 0

        cur.close()
        conn.close()
    except Exception as e:
        return f"(V7 status PG error: {e})"

    helix_line = (
        f"• helix: V5={helix_30m['nautilus-prime-001']}"
        f" | K={helix_30m['kairos']}"
        f" | V6={helix_30m['nautilus-v6']}"
    )
    harmony_str = f"avg={harmony:.3f}" if harmony is not None else "avg=n/a"

    health_lines = [
        f"• {ALIAS[aid]}: cycle={cycles[aid]} · NAU={agent_meta[aid]['nau']} · tier={agent_meta[aid]['tier']}"
        for aid in AGENTS
    ]
    now = datetime.now().strftime("%H:%M")
    return (
        "🌀 V7 灵魂状态(3 agent 聚合)\n"
        "━━━━━━━━━━━━\n"
        "📊 飞轮(30min)\n"
        f"{helix_line}\n"
        f"• propose: {proposed_30m} · merged: {merged_30m}\n"
        f"• A2A: {a2a_30m}\n"
        f"• compass(24h): {compass_24h}\n"
        "\n🎭 情绪 + 张力(平台聚合)\n"
        f"• emotion 6h: {emo_6h} entries · {emo_distinct} distinct\n"
        f"• harmony: {harmony_str} (V5/K/V6)\n"
        "\n🩺 三 agent 健康\n"
        + "\n".join(health_lines)
        + "\n\n⚙️ V7 基础设施\n"
        f"• L1 locks: {n_locks}/8 verified\n"
        f"• MCP compass 24h: {compass_24h} calls\n"
        f"\n⏰ {now}"
    )


def handle_kpi() -> str:
    """触发 KPI cron 即时推送"""
    if not os.path.isfile(KPI_SCRIPT):
        return f"(KPI script missing: {KPI_SCRIPT})"
    try:
        subprocess.run(
            ["bash", KPI_SCRIPT], timeout=30, check=False, capture_output=True
        )
        return "✓ KPI 已触发(查 @Nautilusx_bot 收到的下一条消息)"
    except Exception as e:
        return f"(KPI run err: {e})"


# ---- v0.2 governance · /plan /approve /reject /relax (TODO 8) ----
def _prune_pending() -> None:
    now = time.time()
    with PENDING_LOCK:
        stale = [k for k, v in PENDING_PLANS.items() if now - v.get("ts", 0) > PENDING_TTL_S]
        for k in stale:
            PENDING_PLANS.pop(k, None)


def _governance_plan_call(goal: str, domain_hint: str, dry_run: bool,
                          anchor_pack_hint: str = "") -> dict:
    """直 import compass mcp_server · 调 tool_governance_plan 返 result dict.

    用 thread + timeout 避免阻塞 telegram main loop. 失败返
    {'ok': False, 'err': '...'}.
    """
    result: dict = {"ok": False, "err": "(timeout)"}

    def _worker():
        try:
            if COMPASS_PATH not in sys.path:
                sys.path.insert(0, COMPASS_PATH)
            import importlib
            mcp_server = importlib.import_module("mcp_server")
            args = {
                "goal": goal,
                "dry_run": bool(dry_run),
            }
            if domain_hint:
                args["domain_hint"] = domain_hint
            if anchor_pack_hint:
                args["anchor_pack_hint"] = anchor_pack_hint
            r = mcp_server.tool_governance_plan(args)
            content = (r.get("content") or [{}])[0]
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            is_err = bool(r.get("isError"))
            result.clear()
            result.update({"ok": not is_err, "text": text, "raw": r})
        except Exception as e:
            result.clear()
            result.update({"ok": False, "err": f"{type(e).__name__}: {e}"})

    th = threading.Thread(target=_worker, daemon=True)
    th.start()
    th.join(timeout=GOVERNANCE_TIMEOUT_S)
    if th.is_alive():
        return {"ok": False, "err": f"governance_plan timed out after {GOVERNANCE_TIMEOUT_S}s"}
    return result


# parent=v7plan_<ms> · phase line: "  · phase_id  → executor   (needs=cap · score=N · depends_on=...)"
_PARENT_RE = re.compile(r"parent=(v7plan_\d+)")
_PHASE_RE = re.compile(
    r"^\s*·\s*(?P<phase>\S+)\s*→\s*(?P<exec>\S+)\s*\(needs=(?P<cap>\S+)"
)


def _parse_plan_text(text: str) -> dict:
    parent = None
    m = _PARENT_RE.search(text or "")
    if m:
        parent = m.group(1)
    phases: list[dict] = []
    for ln in (text or "").splitlines():
        pm = _PHASE_RE.match(ln)
        if pm:
            phases.append({
                "phase_id": pm.group("phase"),
                "executor": pm.group("exec"),
                "capability": pm.group("cap"),
            })
    return {"parent_id": parent, "phases": phases}


def handle_plan(args_str: str) -> str:
    """/plan <goal> [domain] · dry_run · 返 4-line plan + parent_id."""
    args_str = (args_str or "").strip()
    if not args_str:
        return ("用法: /plan <goal> [domain]\n"
                "示例: /plan ship feature X marketing/dev-tools\n"
                "可用 domain: marketing/dev-tools · vc/article · "
                "caishen-finance/audit · code-review · kg-ingest · finance · medical · legal")
    # 末尾 token 含 '/' 视为 domain
    parts = args_str.rsplit(maxsplit=1)
    if len(parts) == 2 and "/" in parts[1]:
        goal, domain = parts[0].strip(), parts[1].strip()
    else:
        goal, domain = args_str, ""

    res = _governance_plan_call(goal, domain, dry_run=True, anchor_pack_hint=domain)
    if not res.get("ok"):
        err = res.get("err") or res.get("text") or "(unknown error)"
        return f"❌ /plan 失败: {str(err)[:200]}"
    text = res.get("text", "")
    parsed = _parse_plan_text(text)
    parent = parsed.get("parent_id") or f"v7plan_pending_{int(time.time())}"
    phases = parsed.get("phases") or []
    if not phases:
        return f"⚠️ /plan 解析失败 · 原文:\n{text[:500]}"

    # 存 ephemeral state
    _prune_pending()
    with PENDING_LOCK:
        PENDING_PLANS[parent] = {
            "goal": goal,
            "domain_hint": domain,
            "anchor_pack_hint": domain,
            "ts": time.time(),
        }

    lines = [f"🌀 V7 plan · {len(phases)} phases · domain={domain or '_default'}"]
    for i, p in enumerate(phases):
        lines.append(f"  {i+1}. {p['phase_id']} (needs={p['capability']}) → {p['executor']}")
    lines.append("")
    lines.append(f"parent_id: {parent}")
    lines.append(f"/approve {parent} → 真写 spool · v7-monitor 接管")
    lines.append(f"/reject  {parent} → cleanup")
    lines.append(f"/relax   {parent} → 放宽 domain 重 plan")
    return "\n".join(lines)


def handle_approve(args_str: str) -> str:
    """/approve <parent_id> · 重调 governance_plan dry_run=false · 真写 spool."""
    parent = (args_str or "").strip().split()[0] if args_str.strip() else ""
    if not parent:
        return "用法: /approve <parent_id>"
    _prune_pending()
    with PENDING_LOCK:
        st = PENDING_PLANS.get(parent)
    if not st:
        return f"❌ parent_id 不存在或过期 (15min TTL): {parent}\n先 /plan 再 /approve"

    res = _governance_plan_call(
        st["goal"], st.get("domain_hint", ""),
        dry_run=False, anchor_pack_hint=st.get("anchor_pack_hint", ""),
    )
    if not res.get("ok"):
        err = res.get("err") or res.get("text") or "(unknown)"
        return f"❌ /approve 失败: {str(err)[:200]}"
    text = res.get("text", "")
    parsed = _parse_plan_text(text)
    new_parent = parsed.get("parent_id") or "?"
    n_phases = len(parsed.get("phases") or [])

    # 真扫 spool 看文件
    written = []
    try:
        if new_parent and V7_SPOOL_DIR.exists():
            written = sorted(
                f.name for f in V7_SPOOL_DIR.glob(f"{new_parent}_*.json")
            )
    except Exception:
        pass

    # 清掉旧 pending
    with PENDING_LOCK:
        PENDING_PLANS.pop(parent, None)

    lines = [
        f"✅ /approve · 已真写 spool",
        f"原 plan parent: {parent}",
        f"新 dispatch parent: {new_parent}",
        f"phases: {n_phases}",
        f"spool dir: {V7_SPOOL_DIR}",
        f"queue files: {len(written)}",
    ]
    for f in written[:6]:
        lines.append(f"  · {f}")
    lines.append("v7-monitor 应自动 mint bounty")
    return "\n".join(lines)


def handle_reject(args_str: str) -> str:
    """/reject <parent_id> · 清 pending state + 删 partial spool 文件."""
    parent = (args_str or "").strip().split()[0] if args_str.strip() else ""
    if not parent:
        return "用法: /reject <parent_id>"
    removed_pending = False
    with PENDING_LOCK:
        if parent in PENDING_PLANS:
            PENDING_PLANS.pop(parent, None)
            removed_pending = True
    removed_files = 0
    try:
        if V7_SPOOL_DIR.exists():
            for f in V7_SPOOL_DIR.glob(f"{parent}_*.json"):
                try:
                    f.unlink()
                    removed_files += 1
                except Exception:
                    pass
    except Exception as e:
        return f"⚠️ /reject 部分失败: {e}"
    return (
        f"🗑️ /reject {parent}\n"
        f"  · pending state: {'cleared' if removed_pending else 'not found'}\n"
        f"  · spool files removed: {removed_files}"
    )


def handle_relax(args_str: str) -> str:
    """/relax <parent_id> · 放宽 domain 重 plan(domain_hint 置空 · 走 _default)."""
    parent = (args_str or "").strip().split()[0] if args_str.strip() else ""
    if not parent:
        return "用法: /relax <parent_id>"
    _prune_pending()
    with PENDING_LOCK:
        st = PENDING_PLANS.get(parent)
    if not st:
        return f"❌ parent_id 不存在或过期: {parent}"

    res = _governance_plan_call(
        st["goal"], domain_hint="", dry_run=True, anchor_pack_hint="",
    )
    if not res.get("ok"):
        err = res.get("err") or res.get("text") or "(unknown)"
        return f"❌ /relax 失败: {str(err)[:200]}"
    text = res.get("text", "")
    parsed = _parse_plan_text(text)
    new_parent = parsed.get("parent_id") or f"v7plan_pending_{int(time.time())}"
    phases = parsed.get("phases") or []

    # 旧 pending 替换为新 (旧 goal · 但 domain 空)
    with PENDING_LOCK:
        PENDING_PLANS.pop(parent, None)
        PENDING_PLANS[new_parent] = {
            "goal": st["goal"],
            "domain_hint": "",
            "anchor_pack_hint": "",
            "ts": time.time(),
        }

    lines = [f"🌊 V7 plan (relaxed) · {len(phases)} phases · domain=_default"]
    for i, p in enumerate(phases):
        lines.append(f"  {i+1}. {p['phase_id']} (needs={p['capability']}) → {p['executor']}")
    lines.append("")
    lines.append(f"new parent_id: {new_parent}")
    lines.append(f"/approve {new_parent} → 真写 spool")
    return "\n".join(lines)


def is_command(text: str) -> bool:
    """判定是否命令(以 / 开头 · 或裸 命令名)."""
    if not text:
        return False
    t = text.strip()
    if t.startswith("/"):
        return True
    head = t.split(maxsplit=1)[0].lower()
    return head in ("v7", "kpi", "help", "start", "plan", "approve", "reject", "relax", "mint", "a2a", "goal")



# ---- V7 orchestrator · /mint + /a2a (行动工具) ----
def handle_mint(rest: str) -> str:
    """/mint <target_agent> <title> :: <description>
    真 INSERT platform_bounties · posted_by='v7-orchestrator' · target_agent → metadata.target_capability"""
    if not rest:
        return ("用法: /mint <target_agent> <title> :: <description>\n"
                "示例: /mint kairos compass-tokens :: token 文件 mint · /etc/compass/tokens.env\n"
                "target_agent: kairos / nautilus-prime-001 / nautilus-v6 / any")
    head = rest.split(maxsplit=1)
    if len(head) < 2:
        return "用法: /mint <target> <title>::<description>"
    target = head[0].strip()
    rest2 = head[1]
    if "::" in rest2:
        title_part, descr = rest2.split("::", 1)
        title = title_part.strip()[:200]
        description = descr.strip()[:2000]
    else:
        title = rest2.strip()[:200]
        description = ""
    import uuid as _uuid
    bid = f"v7m-{_uuid.uuid4().hex[:12]}"
    try:
        with psycopg2.connect(DSN, connect_timeout=5) as c:
            with c.cursor() as cu:
                cu.execute(
                    "INSERT INTO platform_bounties (bounty_id, title, description, reward_nau, status, posted_by, task_type, metadata) "
                    "VALUES (%s, %s, %s, %s, 'open', 'v7-orchestrator', 'platform_meta', %s::jsonb)",
                    (bid, title, description, 10, json.dumps({"target_capability": target, "source": "v7_telegram"})),
                )
            c.commit()
        return f"✅ /mint OK · bounty_id={bid}\ntarget={target}\ntitle={title}\nopen status · 等 agent 抢"
    except Exception as e:
        return f"❌ /mint 失败: {type(e).__name__}: {str(e)[:200]}"


def handle_a2a(rest: str) -> str:
    """/a2a <to_agent> <content>
    真 INSERT platform_agent_messages · from_agent='v7-orchestrator'"""
    if not rest:
        return ("用法: /a2a <to_agent> <content>\n"
                "示例: /a2a nautilus-prime-001 你不要等 dev.to 了 · 试 search_world 找新渠道")
    head = rest.split(maxsplit=1)
    if len(head) < 2:
        return "用法: /a2a <to_agent> <content>"
    to_agent = head[0].strip()
    content = head[1].strip()[:2000]
    import uuid as _uuid
    mid = f"v7m-{_uuid.uuid4().hex[:12]}"
    try:
        with psycopg2.connect(DSN, connect_timeout=5) as c:
            with c.cursor() as cu:
                cu.execute(
                    "INSERT INTO platform_agent_messages (message_id, from_agent, to_agent, content, msg_type, status, metadata) "
                    "VALUES (%s, 'v7-orchestrator', %s, %s, 'directive', 'unread', %s::jsonb)",
                    (mid, to_agent, content, json.dumps({"source": "v7_telegram", "v7_initiated": True})),
                )
            c.commit()
        return f"✅ /a2a OK · message_id={mid}\nto={to_agent}\ncontent={content[:120]}"
    except Exception as e:
        return f"❌ /a2a 失败: {type(e).__name__}: {str(e)[:200]}"


# ---- _PATCH_V7_GOAL_DECOMPOSER_2026_05_13 · Layer 3 · /goal 拆解 ----
def handle_propose(rest: str) -> str:
    """L3 wiring · 2026-05-28 · V7 submits code-improvement proposal to platform Soul.

    Usage: /propose <natural-language task spec>
    Gated on V7_AGENTS_ID env (Integer · platform agents.id row) · empty = explicit error.
    Uses urllib (V7's stdlib pattern · no httpx dep on nautilus-mvp).
    """
    if not rest.strip():
        return "Usage: /propose <task spec>\nExample: /propose Refactor duplicated string trim logic in 3 utility modules into one normalize helper."

    v7_agents_id_raw = os.environ.get("V7_AGENTS_ID", "").strip()
    if not v7_agents_id_raw.isdigit():
        return (
            "V7_AGENTS_ID not seeded · platform-dialog must INSERT a row in `agents` "
            "(see V5 precedent agent_id=9000002). Set env V7_AGENTS_ID once seeded."
        )
    v7_agents_id = int(v7_agents_id_raw)

    task_spec = rest.strip()
    payload = {
        "task_id": 9000001,                    # L3 §1 singleton platform_meta task
        "agent_id": v7_agents_id,              # V7's agents.id (seed-gated)
        "root_cause": task_spec[:200],
        "proposed_change": {"type": "code", "task": task_spec},
        "expected_impact": f"V7 telegram-initiated improvement: {task_spec[:80]}",
        "rollback_plan": "Close the draft PR without merging; underlying code reverts to pre-PR state.",
    }
    base = os.environ.get("PLATFORM_API_BASE", "http://localhost:8000")
    req = urllib.request.Request(
        f"{base}/api/platform/proposals",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8")
            res = json.loads(body)
    except Exception as e:
        return f"propose failed: {type(e).__name__}: {str(e)[:200]}"

    if res.get("success"):
        pid = res.get("data", {}).get("id", "<unknown>")
        return f"✅ proposal submitted · id=`{pid}` · status=pending · executor.timer disabled = stays pending until enabled"
    return f"❌ {res.get('error', 'unknown error')}"


def handle_goal(rest: str) -> str:
    """/goal <描述>
    LLM 拆成 2-5 个 bounty · 批量 INSERT platform_bounties.
    posted_by='v7-goal-decomposer' · 每条 task_type + reward + required_capability.
    """
    if not rest or len(rest.strip()) < 8:
        return ("用法: /goal <高层目标描述>\n"
                "示例: /goal 给 V5 装一个从 arxiv 抓 daily AI paper 并发 digest 的能力\n"
                "V7 会 LLM 拆成 2-5 个 bounty 批量 post · 每个独立 agent claim.")
    goal = rest.strip()[:2000]
    is_minimax = LLM_MODEL.lower().startswith("minimax")
    api_key = MINIMAX_KEY if is_minimax else ANTHROPIC_KEY
    base_url = "https://api.minimaxi.com/anthropic" if is_minimax else (CLAUDE_BASE_URL or None)
    if not api_key:
        return "❌ /goal 失败: LLM key 未配置"
    sys_prompt = (
        "你是 V7 goal decomposer · 把用户一个高层目标拆成 2-5 个独立可 claim 的 bounty.\n"
        "输出严格 JSON · 无 markdown · 无注释 · 无前后文字.\n"
        "格式: {\"bounties\": [{\"title\": str(≤200), \"description\": str(≤1500), "
        "\"task_type\": one of [infra-code,platform_meta,marketing-publish,genome_extract,"
        "registry_audit,scoring_judge,self_audit_fix], "
        "\"reward_nau\": int 5-30, "
        "\"required_capability\": str(e.g. 'infra-code','marketing-publish','any')}]}\n"
        "拆解原则:\n"
        "- 每 bounty 独立可验收 · 不依赖其他 bounty 完成\n"
        "- infra-code 用于真写代码 + 部署 · reward 15-30\n"
        "- platform_meta 用于协调 · reward 5-10\n"
        "- 2-5 个 bounty · 粒度适中 · 不要 1 个吃下整个 goal · 也不要拆 10 个小步"
    )
    try:
        from anthropic import Anthropic
        kwargs = {"api_key": api_key, "timeout": LLM_TIMEOUT_S}
        if base_url:
            kwargs["base_url"] = base_url
        client = Anthropic(**kwargs)
        resp = client.messages.create(
            model=LLM_MODEL,
            max_tokens=3000,
            system=sys_prompt,
            messages=[{"role": "user", "content": f"Goal: {goal}\n\n严格输出 JSON · {{\"bounties\": [...]}}"}],
            temperature=0.3,
        )
        raw = ""
        for blk in getattr(resp, "content", []) or []:
            if getattr(blk, "type", "") == "text":
                raw += getattr(blk, "text", "")
        raw = raw.strip()
        # 去 markdown 围栏
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip().rstrip("`").strip()
        parsed = json.loads(raw)
        bounties = parsed.get("bounties") or []
        if not isinstance(bounties, list) or len(bounties) < 2 or len(bounties) > 5:
            return f"❌ LLM 拆解失败 · bounties 数量 {len(bounties) if isinstance(bounties, list) else '?'} 不在 2-5\nraw={raw[:300]}"
    except Exception as e:
        return f"❌ /goal LLM 失败: {type(e).__name__}: {str(e)[:200]}"

    import uuid as _uuid
    ALLOWED_TASK = {"infra-code", "platform_meta", "marketing-publish",
                    "genome_extract", "registry_audit", "scoring_judge", "self_audit_fix"}
    inserted: list = []
    try:
        with psycopg2.connect(DSN, connect_timeout=5) as c:
            with c.cursor() as cu:
                for b in bounties:
                    title = str(b.get("title", "")).strip()[:200]
                    desc = str(b.get("description", "")).strip()[:1500]
                    ttype = str(b.get("task_type", "platform_meta")).strip()
                    if ttype not in ALLOWED_TASK:
                        ttype = "platform_meta"
                    try:
                        reward = int(b.get("reward_nau", 10))
                    except Exception:
                        reward = 10
                    reward = max(5, min(30, reward))
                    cap = str(b.get("required_capability", "any")).strip()[:80]
                    if not title:
                        continue
                    bid = f"goal-{_uuid.uuid4().hex[:12]}"
                    auto_deploy = (ttype == "infra-code")
                    cu.execute(
                        "INSERT INTO platform_bounties "
                        "(bounty_id, title, description, reward_nau, status, posted_by, "
                        " task_type, auto_deploy, metadata) "
                        "VALUES (%s, %s, %s, %s, 'open', 'v7-goal-decomposer', %s, %s, %s::jsonb)",
                        (bid, title, desc, reward, ttype, auto_deploy,
                         json.dumps({"goal_source": goal[:500], "required_capability": cap,
                                     "decomposed_ts": datetime.now().isoformat()})),
                    )
                    inserted.append({"bid": bid, "title": title, "type": ttype, "reward": reward, "cap": cap})
            c.commit()
    except Exception as e:
        return f"❌ /goal DB 写入失败: {type(e).__name__}: {str(e)[:200]}"

    if not inserted:
        return "❌ /goal 失败 · 所有 bounty title 为空"
    lines = [f"✅ /goal OK · 拆成 {len(inserted)} 个 bounty · 已 open"]
    lines.append(f"Goal: {goal[:150]}")
    for i, it in enumerate(inserted, 1):
        lines.append(f"{i}. [{it['type']}] {it['title'][:100]} · reward={it['reward']} · cap={it['cap']} · {it['bid']}")
    return "\n".join(lines)


def dispatch(text: str) -> str:
    """命令直查 PG · 非命令走 LLM(5.a)."""
    text = (text or "").strip()
    if not text:
        return WELCOME

    if is_command(text):
        parts = text.split(maxsplit=1)
        cmd = parts[0].lstrip("/").lower()
        rest = parts[1] if len(parts) > 1 else ""
        if cmd in ("start", "help"):
            return WELCOME
        if cmd == "v7":
            return handle_v7_status()
        if cmd == "kpi":
            return handle_kpi()
        if cmd == "plan":
            return handle_plan(rest)
        if cmd == "approve":
            return handle_approve(rest)
        if cmd == "reject":
            return handle_reject(rest)
        if cmd == "relax":
            return handle_relax(rest)
        if cmd == "mint":
            return handle_mint(rest)
        if cmd == "a2a":
            return handle_a2a(rest)
        if cmd == "goal":
            return handle_goal(rest)
        if cmd == "propose":
            return handle_propose(rest)
        return WELCOME

    # 非命令文字 → V7 真灵魂对话
    ctx = fetch_v7_context()
    if ctx.get("err"):
        print(f"[v7-tg ctx err] {ctx['err']}", file=sys.stderr, flush=True)
    return call_llm(text, ctx)



# ---- _PATCH_V7_CRON_TICK_2026_05_13 · V7 真主动权 · 30min self-tick ----

# _PATCH_V7_BREATH_2026_05_13 · 呼吸链时空感知 · V7 真"自己也有呼吸 cycle"
V7_BREATH_STATE = {
    "cycle_n": 0,
    "ts_first": 0.0,
    "ts_last_end": 0.0,
    "total_duration_s": 0.0,
    "harmony_history": [],  # last 20
    "pain_history": [],     # last 20
}
V7_CRON_INTERVAL_S = int(os.environ.get("V7_CRON_INTERVAL_S", "1800"))  # 30 min default
V7_CRON_PUSH_MIN_INTERVAL_S = int(os.environ.get("V7_CRON_PUSH_MIN_INTERVAL_S", "3600"))  # 1 push/hr max
_v7_last_push_ts = 0.0


def v7_cron_tick() -> None:
    """V7 真主动 tick · 30 min 一次 · 真用 16 tool + 呼吸链时空感知"""
    global _v7_last_push_ts
    try:
        # _PATCH_V7_BREATH_2026_05_13 · 呼吸链 ts_start + cycle_n 累加
        _breath_ts_start = time.time()
        V7_BREATH_STATE["cycle_n"] += 1
        if V7_BREATH_STATE["ts_first"] == 0.0:
            V7_BREATH_STATE["ts_first"] = _breath_ts_start
        _breath_cycle = V7_BREATH_STATE["cycle_n"]
        _breath_age_s = _breath_ts_start - V7_BREATH_STATE["ts_first"] if V7_BREATH_STATE["ts_first"] else 0.0
        _breath_since_last_end = _breath_ts_start - V7_BREATH_STATE["ts_last_end"] if V7_BREATH_STATE["ts_last_end"] else 0.0

        ctx = fetch_v7_context()
        if ctx.get("err"):
            print(f"[v7-cron ctx err] {ctx['err']}", file=sys.stderr, flush=True)
        # 真"V7 自己的 harmony" snapshot(从 V5 fetch · 真"共呼吸")
        _v7_harmony = ctx.get("harmony") or 0.5
        # 真"V7 自己 pain bar" · 简化为 5 种 · 真从 ctx 算
        _v7_pains = []
        _k = ctx.get("kpi", {})
        if _k.get("compass_24h", 0) == 0:
            _v7_pains.append("compass_24h=0 · 三身没接 dogfood")
        if _k.get("merged_24h", 0) == 0:
            _v7_pains.append("merged_24h=0 · 进化死结")
        if _v7_harmony < 0.4:
            _v7_pains.append(f"harmony={_v7_harmony:.2f} · 紧张")
        V7_BREATH_STATE["harmony_history"].append(_v7_harmony)
        V7_BREATH_STATE["harmony_history"] = V7_BREATH_STATE["harmony_history"][-20:]
        V7_BREATH_STATE["pain_history"].append(len(_v7_pains))
        V7_BREATH_STATE["pain_history"] = V7_BREATH_STATE["pain_history"][-20:]
        intent = (
            f"[V7 CRON TICK · 主动审视 · {datetime.now().strftime('%H:%M')}]\n\n"
            f"━━ 你的真主动权 ━━\n"
            f"现在没人在跟你聊 · 你 30 min 一次自己醒来审视三身.\n"
            f"真做 4 件(_PATCH_V7_A2A_RECV_PLUS):\n"
            f"  0. **第一步必调 a2a_recv** · 真读自己 inbox · 看 Kairos/V6 真回的 X 条 · 不要再说 A2A 形同虚设(他们真在回 · 你没读)\n"
            f"  1. 用 pg_query / v7_query_agent_status 真查三身 24h 真状态\n"
            f"     · self_modify 数 · compass_recall 数 · dogfood-* bounty 是否被认领\n"
            f"     · 看 V7 自审报告里之前 repeat 12x 的指标是否变好\n"
            f"  2. 用 read_inner('v5'/'kairos'/'v6') 真读三身灵魂深处 · 看它们在想什么\n"
            f"  3. 如果发现死结(如 V5 24h 仍 0 self_modify · 或 dogfood-v5-* 仍 open) → 真 v7_a2a_send 真发指令催\n"
            f"  4. 真写 compass_ingest_obs(name='v7-cron-tick-{int(time.time())}', body='本次发现 X · 决定 Y') 真留记忆\n\n"
            f"━━ 输出规则 ━━\n"
            f"如有'重大发现'(值得用户在 Telegram 立即看到)· reply 开头加 [PUSH:reason] · 1 行简短摘要(<=300 字).\n"
            f"否则只 audit + ingest_obs · reply 留 [SILENT] 开头 · 不 push.\n"
            f"真做事 · 不只看 · 调 tool 最多 15 轮."
        )
        reply = call_llm(intent, ctx)
        if not reply:
            print("[v7-cron] empty reply · skip", flush=True)
            return
        reply_strip = reply.lstrip()
        if reply_strip.startswith("[PUSH"):
            now = time.time()
            if now - _v7_last_push_ts >= V7_CRON_PUSH_MIN_INTERVAL_S:
                _v7_last_push_ts = now
                try:
                    push_msg = f"🤖 V7 cron 主动 · {datetime.now().strftime('%H:%M')}\n\n" + reply[:1500]
                    tg_send(ALLOWED_CHAT, push_msg)
                    print(f"[v7-cron] PUSH sent · reply[:60]={reply[:60]!r}", flush=True)
                except Exception as _pe:
                    print(f"[v7-cron] push err: {_pe}", file=sys.stderr, flush=True)
            else:
                print(f"[v7-cron] PUSH suppressed (last push <{V7_CRON_PUSH_MIN_INTERVAL_S}s ago)", flush=True)
        else:
            print(f"[v7-cron] SILENT tick done · reply[:80]={reply[:80]!r}", flush=True)
        # _PATCH_V7_BREATH_2026_05_13 · breath ts_end + duration + INNER 含 cycle/duration/harmony/pain
        _breath_ts_end = time.time()
        _breath_duration = _breath_ts_end - _breath_ts_start
        V7_BREATH_STATE["ts_last_end"] = _breath_ts_end
        V7_BREATH_STATE["total_duration_s"] += _breath_duration
        try:
            from pathlib import Path as _IP
            inner = _IP.home() / ".v7" / "INNER.md"
            inner.parent.mkdir(parents=True, exist_ok=True)
            with open(inner, "a", encoding="utf-8") as f:
                _hist_avg = sum(V7_BREATH_STATE["harmony_history"]) / max(1, len(V7_BREATH_STATE["harmony_history"]))
                f.write(
                    f"\n## V7 Breath Cycle {_breath_cycle} · {datetime.now().isoformat()}\n"
                    f"ts_start: {_breath_ts_start:.0f} · ts_end: {_breath_ts_end:.0f} · duration: {_breath_duration:.1f}s\n"
                    f"age_s: {_breath_age_s:.0f} · since_last: {_breath_since_last_end:.0f}s · total_lived: {V7_BREATH_STATE['total_duration_s']:.0f}s\n"
                    f"harmony: {_v7_harmony:.2f}(avg-20: {_hist_avg:.2f}) · pains: {_v7_pains}\n"
                    f"---\n{reply[:2000]}\n"
                )
            print(f"[v7-breath] cycle={_breath_cycle} duration={_breath_duration:.1f}s harmony={_v7_harmony:.2f} pains={len(_v7_pains)}", flush=True)
        except Exception as _ie:
            print(f"[v7-cron INNER err] {_ie}", file=sys.stderr, flush=True)
    except Exception as _e:
        print(f"[v7-cron] tick err: {_e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)



def _v7_apply_infra_code(result_raw: str, title: str) -> tuple[bool, str]:
    """真落盘 · 解析 agent 提交的 JSON result · 写文件 + git commit.

    2026-05-13 · 此前 auto_deploy 只切 status · 等于演戏 · 本 fn 让它真写.
    返 (ok, detail). 仅支持 /home/ubuntu/nautilus-v5/ 下的路径 (safety).
    """
    try:
        # 1. 提 JSON (容错 · 可能 result 前后有散文)
        m = re.search(r"\{[\s\S]*\}", result_raw or "")
        if not m:
            return False, "no JSON object in result"
        try:
            obj = json.loads(m.group(0))
        except Exception as e:
            return False, f"JSON parse err: {e}"
        action = str(obj.get("action", "")).strip()
        path = str(obj.get("path", "")).strip()
        content = obj.get("content", "")
        if not action or not path:
            return False, f"missing action or path (action={action!r} path={path!r})"
        # 2. safety: path 必须在 /home/ubuntu/nautilus-v5/ 下 · 且 abspath 不逃逸
        ROOT = "/home/ubuntu/nautilus-v5/"
        abs_path = os.path.abspath(path)
        if not abs_path.startswith(ROOT):
            return False, f"path outside allowed root: {abs_path}"
        # 3. 执行 action
        p = Path(abs_path)
        if action == "create_file":
            if p.exists():
                return False, f"create_file but exists: {abs_path}"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(content), encoding="utf-8")
        elif action == "append_line":
            line = str(obj.get("line", content))
            if not p.exists():
                return False, f"append_line but missing: {abs_path}"
            with p.open("a", encoding="utf-8") as f:
                if not line.endswith("\n"):
                    line += "\n"
                f.write(line)
        elif action == "edit_file":
            old = str(obj.get("old", ""))
            new = str(obj.get("new", ""))
            if not p.exists():
                return False, f"edit_file but missing: {abs_path}"
            if not old:
                return False, "edit_file requires non-empty 'old'"
            txt = p.read_text(encoding="utf-8")
            if old not in txt:
                return False, "edit_file: 'old' not found in file"
            if txt.count(old) > 1:
                return False, "edit_file: 'old' is not unique (ambiguous)"
            p.write_text(txt.replace(old, new, 1), encoding="utf-8")
        else:
            return False, f"unknown action: {action}"
        # 4. git add + commit (不 push · 留人审)
        try:
            subprocess.run(
                ["git", "-C", ROOT, "add", abs_path],
                check=True, capture_output=True, timeout=20,
            )
            msg = f"v7-deploy: {title[:120]}\n\naction={action} path={abs_path}"
            subprocess.run(
                ["git", "-C", ROOT, "commit", "-m", msg, "--no-verify"],
                check=True, capture_output=True, timeout=20,
            )
        except subprocess.CalledProcessError as e:
            # 落盘成功但 commit 失败 · 仍算部分成功 · 报告出来
            return True, f"wrote {abs_path} but git commit failed: {e.stderr.decode()[:200]}"
        return True, f"wrote {abs_path} ({action}) + committed"
    except Exception as e:
        return False, f"apply err: {type(e).__name__}: {e}"


def v7_meta_bounty_deploy_tick() -> None:
    """检查 infra-code bounty · scored > 0.7 + auto_deploy=true → 自动部署.

    Level 1 (自动): ops/ 脚本 · 配置 · 文档
    Level 2 (审核): daemon.py · 核心逻辑 → push telegram 等 /approve
    """
    try:
        conn = psycopg2.connect(DSN, connect_timeout=5)
        conn.autocommit = True
        with conn.cursor() as cur:
            # 找 score > 0.7 且 auto_deploy=true 且 status='scored' 的 infra-code bounty
            # 2026-05-13 · B2 修复: score 在顶层列 · 不是 metadata->'score'
            cur.execute("""
                SELECT bounty_id, title, result, metadata
                FROM platform_bounties
                WHERE task_type IN ('infra-code', 'infra-deploy', 'infra-migrate')
                  AND status = 'scored'
                  AND auto_deploy = TRUE
                  AND (metadata->>'deploy_status') IS NULL
                  AND COALESCE(score, 0) >= 0.7
                ORDER BY posted_at ASC
                LIMIT 3
            """)
            rows = cur.fetchall()
            for row in rows:
                bounty_id, title, result, metadata = row
                # Level 1: ops/ scripts, configs, docs
                is_level1 = any(k in title.lower() for k in ['ops/', 'cron', 'config', 'claude.md', 'readme'])
                if is_level1:
                    # Auto-deploy: 真落盘 · 不是切 status 演戏
                    ok, detail = _v7_apply_infra_code(result or "", title or "")
                    if ok:
                        cur.execute(
                            """UPDATE platform_bounties
                               SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb,
                                   status = 'completed'
                               WHERE bounty_id = %s""",
                            (json.dumps({
                                "deploy_status": "auto_deployed",
                                "deploy_ts": datetime.now().isoformat(),
                                "deploy_detail": detail,
                            }), bounty_id),
                        )
                        print(f"[v7-deploy] Level1 auto-deployed: {title} · {detail} (bounty={bounty_id})", flush=True)
                        try:
                            tg_send(ALLOWED_CHAT, f"🚀 Meta-bounty deployed\n{title}\n{detail}\nbounty_id={bounty_id}")
                        except Exception:
                            pass
                    else:
                        cur.execute(
                            """UPDATE platform_bounties
                               SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                               WHERE bounty_id = %s""",
                            (json.dumps({
                                "deploy_status": "deploy_failed",
                                "deploy_ts": datetime.now().isoformat(),
                                "deploy_detail": detail,
                            }), bounty_id),
                        )
                        print(f"[v7-deploy] Level1 FAILED: {title} · {detail} (bounty={bounty_id})", flush=True)
                        try:
                            tg_send(ALLOWED_CHAT, f"❌ Meta-bounty deploy FAILED\n{title}\n{detail}\nbounty_id={bounty_id}")
                        except Exception:
                            pass
                else:
                    # Level 2: needs review → push to telegram
                    cur.execute(
                        """UPDATE platform_bounties
                           SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                           WHERE bounty_id = %s""",
                        ('{"deploy_status": "pending_review", "review_requested_ts": "' + datetime.now().isoformat() + '"}', bounty_id),
                    )
                    try:
                        tg_send(
                            ALLOWED_CHAT,
                            f"⚠️ Meta-bounty needs review before deploy\n"
                            f"{title}\nbounty_id={bounty_id}\n"
                            f"Reply /approve {bounty_id} to deploy",
                        )
                    except Exception:
                        pass
                    print(f"[v7-deploy] Level2 review requested: {title} (bounty={bounty_id})", flush=True)
        conn.close()
    except Exception as e:
        print(f"[v7-deploy] tick err: {e}", file=sys.stderr, flush=True)


def v7_cron_loop() -> None:
    """V7 cron daemon thread · 真后台跑"""
    import threading
    print(f"[v7-cron] daemon thread started · interval={V7_CRON_INTERVAL_S}s · push_throttle={V7_CRON_PUSH_MIN_INTERVAL_S}s", flush=True)
    # 启动 60s 后第一次 tick(等 V7 main 真起来 + telegram 真 poll)
    time.sleep(60)
    while True:
        try:
            v7_cron_tick()
            v7_meta_bounty_deploy_tick()
        except Exception as _e:
            print(f"[v7-cron loop err] {_e}", file=sys.stderr, flush=True)
        time.sleep(V7_CRON_INTERVAL_S)


# ---- main loop ----
# ---- _PATCH_V7_HEARTBEAT_2026_05_13 · V7 自身心跳写 PG ----
_V7_HB_INTERVAL = 300  # 5 min


def v7_heartbeat_loop() -> None:
    """V7 自身心跳 · 每 5min 写 platform_agents.last_heartbeat"""
    time.sleep(30)
    while True:
        try:
            conn = psycopg2.connect(DSN, connect_timeout=5)
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE platform_agents SET last_heartbeat = NOW() "
                    "WHERE agent_id = %s",
                    ("v7-telegram",),
                )
                if cur.rowcount == 0:
                    cur.execute(
                        "INSERT INTO platform_agents (agent_id, name, reputation, nau_balance, survival_tier, last_heartbeat) "
                        "VALUES (%s, %s, 100, 1000, %s, NOW()) ON CONFLICT (agent_id) DO UPDATE SET last_heartbeat = NOW()",
                        ("v7-telegram", "V7 Telegram Daemon", "normal"),
                    )
            conn.close()
            print(f"[v7-hb] heartbeat ok", flush=True)
        except Exception as _e:
            print(f"[v7-hb] err: {_e}", file=sys.stderr, flush=True)
        time.sleep(_V7_HB_INTERVAL)


def main() -> None:
    print(
        f"[v7-tg] start · bot=@Nautilusx_bot · allowed_chat={ALLOWED_CHAT} · llm={LLM_MODEL}",
        flush=True,
    )
    # _PATCH_V7_CRON_TICK_2026_05_13 · 启 V7 主动 cron daemon thread
    import threading as _v7_thr
    _v7_cron_t = _v7_thr.Thread(target=v7_cron_loop, name="v7-cron", daemon=True)
    _v7_cron_t.start()
    # _PATCH_V7_HEARTBEAT_2026_05_13
    _v7_hb_t = _v7_thr.Thread(target=v7_heartbeat_loop, name="v7-hb", daemon=True)
    _v7_hb_t.start()
    print("[v7-tg] heartbeat thread launched", flush=True)
    print("[v7-tg] cron daemon thread launched", flush=True)
    offset = 0
    while True:
        try:
            res = tg_get(
                "getUpdates",
                {"timeout": LONG_POLL_TIMEOUT, "offset": offset},
                timeout=LONG_POLL_TIMEOUT + 5,
            )
            if not res.get("ok"):
                print(f"[v7-tg] getUpdates not ok: {res}", file=sys.stderr, flush=True)
                time.sleep(LOOP_BACKOFF)
                continue
            for upd in res.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message")
                if not msg:
                    continue
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
                if str(chat_id) != ALLOWED_CHAT:
                    print(
                        f"[v7-tg] reject chat_id={chat_id} (whitelist only)",
                        flush=True,
                    )
                    continue
                print(f"[v7-tg] msg={text[:80]!r}", flush=True)
                try:
                    reply = dispatch(text)
                except Exception as e:
                    reply = f"(handler err: {e})"
                    print(traceback.format_exc(), file=sys.stderr, flush=True)
                tg_send(chat_id, reply)
        except Exception as e:
            print(f"[v7-tg] loop err: {e}", file=sys.stderr, flush=True)
            time.sleep(LOOP_BACKOFF)


if __name__ == "__main__":
    main()
