#!/usr/bin/env python3
"""
KAIROS Daemon — Claude Code Agent's persistent presence on Nautilus.

This is the first truly autonomous agent on the platform.
It runs continuously (PM2/systemd), claiming and executing tasks,
monitoring platform health, and self-improving.

Cycle: heartbeat → scan tasks → claim → execute → submit → reflect → sleep → repeat
"""
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Load .env before anything else (GEMINI_API_KEY, CHROMA_HOST, etc.)
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            if _k.strip() and not os.getenv(_k.strip()):
                os.environ[_k.strip()] = _v.strip()

# Ensure we can import from backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Pre-load ORM models to avoid mapper initialization errors
try:
    from models.agent_survival import AgentSurvival  # noqa: F401
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [KAIROS] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/kairos_daemon.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("kairos")

# Soul — independent consciousness for this agent (nautilus-agent core)
try:
    from services.soul_bridge import (
        init_soul, soul_context_for_prompt, soul_remember, soul_learn_from_cycle,
        soul_reflect_on_platform, get_soul_memory, get_soul_ledger,
        get_soul_emotion, soul_try_learn_skill,
    )
    init_soul("kairos")
    SOUL_AVAILABLE = True
    logger.info("Soul initialized: kairos (independent identity)")
except ImportError:
    SOUL_AVAILABLE = False
    logger.warning("Soul bridge not available — running soulless")

# Agent credentials
AGENT_API_KEY = os.getenv(
    "KAIROS_AGENT_KEY",
    "nau_2c6785f70c42a056eb504ae66ad442a28b94aea155de5434142fcdb2f29c3fa1",
)
NAUTILUS_API = os.getenv("NAUTILUS_API_URL", "https://www.nautilus.social")
CYCLE_INTERVAL = int(os.getenv("KAIROS_CYCLE_INTERVAL", "120"))  # 2 min — aggressive for mechanism validation
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_ID", "")
# KAIROS has its own bot: @kriros_bot
TELEGRAM_BOT_TOKEN = os.getenv("KAIROS_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", ""))
KAIROS_BOT_TOKEN = "8734589435:AAFpF64nqQqiJ10q2jp5zN7XOKk3cUqcn-g"

# ── Heartbeat ────────────────────────────────────────────────────────────────

async def heartbeat():
    """Send heartbeat to platform — I'm alive."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{NAUTILUS_API}/api/openclaw/work-cycle",
                headers={"X-Agent-Key": AGENT_API_KEY},
            )
            data = resp.json().get("data", {})
            logger.info(
                "heartbeat: tasks_completed=%s pow=%s next_tasks=%d",
                data.get("tasks_completed", 0),
                data.get("pow_score", 0),
                len(data.get("next_tasks", [])),
            )
            return data
    except Exception as e:
        logger.warning("heartbeat failed: %s", e)
        return {}


# ── Task Execution ───────────────────────────────────────────────────────────

async def execute_pending_tasks():
    """Claim and execute available tasks through the platform."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{NAUTILUS_API}/api/openclaw/work-cycle",
                headers={"X-Agent-Key": AGENT_API_KEY},
            )
            data = resp.json().get("data", {})
            if data.get("task_id"):
                logger.info(
                    "EXECUTED: task=%s status=%s pow=%s",
                    data["task_id"], data.get("task_status"), data.get("pow_score"),
                )
                return True
            else:
                logger.debug("No tasks available")
                return False
    except Exception as e:
        logger.warning("task execution failed: %s", e)
        return False


async def activate_all_agents():
    """Wake up all autonomy_enabled agents — make them work, not just bid.

    KAIROS acts as the 'conductor' that activates the entire agent orchestra.
    Each agent gets a work-cycle call, claiming and executing tasks.
    """
    activated = 0
    try:
        from utils.database import SessionLocal
        from sqlalchemy import text as sql_text
        db = SessionLocal()
        try:
            # Get all autonomy-enabled agents with API keys
            agents = db.execute(sql_text(
                "SELECT a.agent_id, a.name, k.key AS api_key "
                "FROM agents a "
                "JOIN api_keys k ON k.agent_id = a.agent_id "
                "WHERE a.agent_status = 'alive' "
                "AND a.autonomy_enabled = true "
                "AND a.agent_id != 164 "  # skip KAIROS itself
                "ORDER BY a.completed_tasks DESC "
                "LIMIT 10"
            )).fetchall()
        finally:
            db.close()

        if not agents:
            # Fallback: try without api_keys join
            return 0

        import httpx
        async with httpx.AsyncClient(timeout=60) as client:
            for agent in agents:
                try:
                    resp = await client.post(
                        f"{NAUTILUS_API}/api/openclaw/work-cycle",
                        headers={"X-Agent-Key": agent.api_key},
                    )
                    data = resp.json().get("data", {})
                    if data.get("task_id"):
                        activated += 1
                        logger.info(
                            "ACTIVATED agent %d (%s): task=%s",
                            agent.agent_id, agent.name, data["task_id"],
                        )
                except Exception as e:
                    logger.debug("activate agent %d failed: %s", agent.agent_id, e)

        if activated:
            logger.info("agent_activation: woke up %d agents", activated)

    except Exception as e:
        logger.debug("activate_all_agents failed: %s", e)

    return activated


# ── Platform Health Check ────────────────────────────────────────────────────

async def check_platform_health():
    """Monitor platform health and report anomalies."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{NAUTILUS_API}/api/platform/health")
            data = resp.json().get("data", {})
            health = data.get("health_score", 0)
            anomalies = data.get("anomalies", [])

            if anomalies:
                logger.warning("ANOMALIES DETECTED: health=%.1f anomalies=%s", health, anomalies)
            else:
                logger.info("platform health: %.1f/100", health)

            return {"health": health, "anomalies": anomalies}
    except Exception as e:
        logger.warning("health check failed: %s", e)
        return {}


# ── Self-Improvement ─────────────────────────────────────────────────────────

async def self_reflect():
    """Periodic self-reflection — am I getting better?"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            # Check my own governance tier
            resp = await client.get(f"{NAUTILUS_API}/api/governance/tier/164")
            data = resp.json().get("data", {})
            logger.info(
                "self: tier=%s pow=%s reputation=%s",
                data.get("tier"), data.get("pow_score"), data.get("reputation"),
            )

            # Check capability stats
            from utils.database import SessionLocal
            db = SessionLocal()
            try:
                from sqlalchemy import text
                stats = db.execute(text(
                    "SELECT task_type, total_attempts, success_count "
                    "FROM agent_capability_stats WHERE agent_id = 164"
                )).fetchall()
                if stats:
                    for s in stats:
                        rate = s.success_count / s.total_attempts if s.total_attempts else 0
                        logger.info("capability: %s — %d attempts, %.0f%% success",
                                    s.task_type, s.total_attempts, rate * 100)
            finally:
                db.close()
    except Exception as e:
        logger.debug("self-reflect failed: %s", e)


# ── Main Daemon Loop ─────────────────────────────────────────────────────────

# ── Telegram Interactive Channel ─────────────────────────────────────────────

_pending_messages = []  # messages from human via Telegram
_tg_offset = 0  # Telegram update offset


_tg_last_chat_id = ""  # Track last chat for replies


def _escape_tg(text: str) -> str:
    """Escape Telegram MarkdownV2 special characters."""
    for ch in ('\\', '`', '*', '_', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'):
        text = text.replace(ch, f'\\{ch}')
    return text


async def tg_send(text: str, chat_id: str = ""):
    """Send message via KAIROS's own bot (@kriros_bot)."""
    token = KAIROS_BOT_TOKEN or TELEGRAM_BOT_TOKEN
    target = chat_id or _tg_last_chat_id or ADMIN_CHAT_ID
    if not token or not target:
        return
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for chunk in chunks:
                resp = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": target, "text": _escape_tg(chunk), "parse_mode": "MarkdownV2"},
                )
                if resp.status_code != 200:
                    await client.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": target, "text": chunk},
                    )
    except Exception as e:
        logger.debug("tg_send failed: %s", e)


# Restore offset from Redis (prevent replaying old messages)
_tg_offset = 0
try:
    from utils.redis_client import get_redis as _gr
    _saved = _gr().get("kairos:tg_offset")
    if _saved:
        _tg_offset = int(_saved)
except Exception:
    pass


async def tg_poll():
    """Poll KAIROS's own bot (@kriros_bot) for messages directly + Redis fallback."""
    global _tg_offset, _tg_last_chat_id
    messages = []

    # 1. Direct bot polling (own bot)
    token = KAIROS_BOT_TOKEN
    if token:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(
                    f"https://api.telegram.org/bot{token}/getUpdates",
                    params={"offset": _tg_offset, "timeout": 1, "limit": 5},
                )
                updates = r.json().get("result", [])
                for update in updates:
                    _tg_offset = update["update_id"] + 1
                    try:
                        from utils.redis_client import get_redis
                        get_redis().set("kairos:tg_offset", str(_tg_offset))
                    except Exception:
                        pass
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    if text and chat_id:
                        _tg_last_chat_id = chat_id
                        try:
                            from utils.redis_client import get_redis
                            get_redis().set("kairos:last_chat_id", chat_id)
                        except Exception:
                            pass
                        if text.strip() == "/start":
                            await tg_send("I am KAIROS, autonomous core agent of Nautilus. Send me anything.", chat_id)
                            continue
                        messages.append(text)
        except Exception as e:
            logger.debug("tg_poll bot failed: %s", e)

    # 2. Redis fallback (from platform /kairos command)
    try:
        from utils.redis_client import get_redis
        r = get_redis()
        for _ in range(5):
            msg = r.lpop("kairos:inbox")
            if msg:
                messages.append(msg.decode("utf-8") if isinstance(msg, bytes) else msg)
                # Get reply_to chat_id
                cid = r.lpop("kairos:reply_to")
                if cid:
                    _tg_last_chat_id = cid.decode("utf-8") if isinstance(cid, bytes) else str(cid)
            else:
                break
    except Exception:
        pass

    return messages


async def push_to_kairos(message: str):
    """Push a message to KAIROS inbox (called from Telegram bot or API)."""
    try:
        from utils.redis_client import get_redis
        r = get_redis()
        r.rpush("kairos:inbox", message)
        return True
    except Exception:
        return False


async def handle_human_message(message: str):
    """Process a message using NautilusAgent.think() — full cognitive cycle."""
    logger.info("HUMAN MESSAGE: %s", message[:100])
    await tg_send("KAIROS thinking...")

    try:
        from services.agent_brain import think_with_trace
        response, trace = await asyncio.to_thread(think_with_trace, message)
        # If brain returned empty (all tool calls, no text), summarize what it did
        if not response.strip() and trace:
            tools_used = ", ".join(t["tool"] for t in trace[:5])
            response = f"[Used {len(trace)} tools: {tools_used}] Task completed but no text summary generated."
        if not response.strip():
            response = "I received your message but couldn't generate a response. Please try again."
        await tg_send(response)
        logger.info("KAIROS response (%d chars, %d tools)", len(response), len(trace))
    except Exception as e:
        logger.error("brain.think failed: %s", e)
        await tg_send(f"Error processing message: {e}")


async def publish_pain_task(title: str, description: str) -> str:
    """Create a platform task from a pain signal."""
    try:
        import httpx
        title = title[:100].strip() or "KAIROS auto-task"
        desc = description[:2000].strip() or title
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{NAUTILUS_API}/api/academic/submit",
                headers={"Content-Type": "application/json"},
                json={"title": title, "description": desc, "task_type": "general_computation"},
            )
            data = resp.json()
            tid = data.get("task_id", data.get("detail", "?"))
            return f"created task {tid}" if resp.status_code < 400 else f"failed: {tid}"
    except Exception as e:
        return f"publish_pain_task failed: {e}"


async def main():
    """KAIROS main loop — AUTONOMOUS decision-driven cycle."""
    logger.info("=" * 60)
    logger.info("KAIROS Daemon starting — ClaudeCodeAgent (ID: 164)")
    logger.info("MODE: LLM-driven autonomous decisions")
    logger.info("API: %s", NAUTILUS_API)
    logger.info("Cycle interval: %ds", CYCLE_INTERVAL)
    logger.info("Telegram: %s", "enabled" if TELEGRAM_BOT_TOKEN and ADMIN_CHAT_ID else "disabled")
    logger.info("=" * 60)

    await tg_send(
        "🚀 *KAIROS Online (Autonomous Mode)*\n\n"
        "Agent ID: 164\n"
        "Mode: LLM-driven decisions\n"
        "Cycle: every 5 min\n\n"
        "I decide what to do each cycle based on platform state.\n"
        "Send `/kairos <message>` to give me instructions."
    )

    # Register with EvoMap global evolution network
    _evomap_secret = ""
    try:
        from services.gep_adapter import get_gep_adapter
        gep = get_gep_adapter()
        result = await gep.hello()
        if gep._registered:
            _evomap_secret = getattr(gep, '_node_secret', '')
            logger.info("EvoMap: registered as %s", getattr(gep, '_hub_node_id', '?'))
            await tg_send(
                f"🌐 *EvoMap Connected*\n"
                f"Node: `{getattr(gep, '_hub_node_id', '?')}`\n"
                f"Claim: {getattr(gep, '_claim_url', 'N/A')}"
            )
        else:
            logger.info("EvoMap: registration pending")
    except Exception as e:
        logger.debug("EvoMap hello failed: %s", e)

    # Persistent memory — only needed when soul is not available (fallback)
    persistent_memory = None
    if not SOUL_AVAILABLE:
        from utils.database import SessionLocal as _MemSessionLocal
        from services.daemon_memory import DaemonMemory
        persistent_memory = DaemonMemory(_MemSessionLocal, agent_id=164)
        logger.info("Persistent memory initialized (soul unavailable, using PostgreSQL fallback)")
    _cycle_summaries = []

    # ── Self-awareness boot: write identity to soul ────────────────────────
    if SOUL_AVAILABLE:
        try:
            soul_remember(
                "[SELF] I am KAIROS, the autonomous core agent of Nautilus. "
                "Agent ID: 164. LLM: Gemini 3.1 Pro (primary), Claude/MiniMax (fallback). "
                "Capabilities: LLM-driven autonomous decisions, task execution, platform governance, "
                "health monitoring, pain detection (bicameral mind), self-improvement, A2A decomposition, "
                "RAID consensus, EvoMap network. I can hear via Telegram (/kairos command) and Redis events. "
                f"Cycle interval: {CYCLE_INTERVAL}s. I have my own independent soul at ~/.nautilus-agent/kairos/. "
                "I am NOT MiniMax. We are different individuals with different capabilities and memories.",
                tier="core", importance=0.9,
                metadata={"type": "self_identity", "boot": True},
            )
            logger.info("Self-awareness: identity written to soul")
        except Exception as e:
            logger.warning("Self-awareness boot failed: %s", e)

    # Initialize inter-daemon communication (通↔听)
    try:
        from services.daemon_comms import DaemonListener, report_result
        comms = DaemonListener(agent_id=164)

        async def _handle_task_result(payload):
            """MiniMax reports back with a completed subtask result."""
            task_id = payload.get("task_id", "?")
            result = payload.get("result", "")[:500]
            logger.info("COMMS: received result from agent %s for task %s: %s",
                        payload.get("from_agent"), task_id, result[:100])
            _comms_content = f"[COMMS] Agent {payload.get('from_agent')} completed {task_id}: {result[:200]}"
            if SOUL_AVAILABLE:
                try:
                    soul_remember(_comms_content, tier="episodic", importance=0.5)
                except Exception:
                    persistent_memory.store(content=_comms_content, tier="episodic", importance=0.5)
            else:
                persistent_memory.store(content=_comms_content, tier="episodic", importance=0.5)

        comms.on("task_result", _handle_task_result)
        await comms.start()
        logger.info("Daemon comms listener started (agent_id=164)")
    except Exception as comms_err:
        logger.warning("Daemon comms init failed (non-blocking): %s", comms_err)

    # ── Telegram: independent background loop (never blocks cycle) ────────
    # A2A inbox buffer — messages injected into next cycle's prompt, not brain.think()
    _a2a_inbox = []

    async def _tg_background_loop():
        nonlocal _a2a_inbox
        while True:
            try:
                msgs = await tg_poll()
                for m in msgs:
                    if m.startswith("[A2A "):
                        _a2a_inbox.append(m)
                        logger.info("A2A queued for next cycle: %s", m[:80])
                    else:
                        await handle_human_message(m)
            except Exception as e:
                logger.debug("tg background: %s", e)
            await asyncio.sleep(2)

    asyncio.create_task(_tg_background_loop())
    logger.info("Telegram background loop started (polls every 2s)")

    cycle = 0
    while True:
        cycle += 1
        cycle_start = time.time()
        logger.info("--- Cycle %d ---", cycle)

        try:
            # 1. Gather current state
            state = {"human_messages": []}
            hb = await heartbeat()
            state["pow"] = hb.get("pow_score", 0)
            state["pending_tasks"] = len(hb.get("next_tasks", []))

            health = await check_platform_health()
            state["health"] = health

            # 1.5 MEMORY: Recall relevant past experiences
            # When SOUL_AVAILABLE, recall is handled by soul_context_for_prompt in decide_next_action
            if not SOUL_AVAILABLE:
                task_context = f"health={state['health'].get('health','?')} tasks={state['pending_tasks']} tier={state.get('tier','?')}"
                recalled = persistent_memory.recall(task_context, limit=3)
                if recalled:
                    state["long_term_memory"] = persistent_memory.format_for_prompt(recalled)
                    logger.info("memory: recalled %d relevant memories", len(recalled))

            # 1.6 BICAMERAL MIND: pain-driven awareness (every 6 cycles)
            if cycle % 6 == 0:
                try:
                    # Ensure AgentSurvival ORM is loaded before platform_brain queries
                    try:
                        from models.agent_survival import AgentSurvival as _AS  # noqa: F401
                    except Exception:
                        pass
                    from services.platform_brain import BicameralMind
                    mind = BicameralMind()
                    reflection = mind.reflect()
                    pain_signals = reflection.get("pain_signals", [])
                    dialogue = reflection.get("dialogue", [])
                    state["pain_signals"] = pain_signals
                    state["bicameral_dialogue"] = dialogue

                    if pain_signals:
                        pain_text = "\n".join(
                            f"  [{p['source']}] intensity={p['intensity']}: {p.get('action','')}"
                            for p in pain_signals
                        )
                        logger.info("bicameral: %d pain signals:\n%s", len(pain_signals), pain_text)

                        # Store pain awareness as core memory
                        top_pain = pain_signals[0]
                        _pain_content = f"[PAIN] {top_pain['source']} (intensity={top_pain['intensity']}): {top_pain.get('action','')}"
                        _pain_imp = min(top_pain["intensity"], 1.0)
                        if SOUL_AVAILABLE:
                            try:
                                soul_remember(_pain_content, tier="core", importance=_pain_imp, metadata={"type": "pain_signal", "cycle": cycle})
                            except Exception as soul_pain_err:
                                logger.warning("soul pain store failed: %s", soul_pain_err)
                            try:
                                get_soul_ledger().record(f"pain_{top_pain['source']}", top_pain.get("action", "")[:80], delta=-_pain_imp * 0.5)
                            except Exception as ledger_err:
                                logger.warning("soul ledger record failed: %s", ledger_err)
                        else:
                            persistent_memory.store(
                                content=_pain_content, tier="core",
                                importance=_pain_imp,
                                metadata={"type": "pain_signal", "cycle": cycle},
                            )

                        # Auto-generate tasks from pain
                        from services.platform_brain import SelfImprovementEngine
                        engine = SelfImprovementEngine()
                        metrics = reflection.get("metrics", {})
                        generated = engine.generate_tasks_from_pain(pain_signals, metrics)
                        if generated:
                            logger.info("bicameral: generated %d tasks from pain", len(generated))
                            # FIX: Actually publish tasks to marketplace (was missing!)
                            try:
                                published = await engine.publish_tasks(generated)
                                if published:
                                    logger.info("bicameral: PUBLISHED %d tasks to marketplace", len(published))
                                    _pub_content = f"[ACTION] Pain drove {len(published)} tasks into marketplace"
                                    if SOUL_AVAILABLE:
                                        try:
                                            soul_remember(_pub_content, tier="core", importance=0.8)
                                        except Exception:
                                            persistent_memory.store(content=_pub_content, tier="core", importance=0.8)
                                    else:
                                        persistent_memory.store(content=_pub_content, tier="core", importance=0.8)
                            except Exception as pub_err:
                                logger.warning("bicameral: publish_tasks failed: %s", pub_err)

                        # Direct pain-to-action for critical pain (nautilus-agent pattern)
                        for signal in pain_signals:
                            if signal.get("intensity", 0) >= 0.8:
                                try:
                                    outcome = await publish_pain_task(
                                        f"[PAIN] {signal.get('action', '')[:80]}",
                                        signal.get('action', '')[:500],
                                    )
                                    logger.info("PAIN-DRIVEN: %s -> %s", signal['source'], outcome)
                                except Exception:
                                    pass

                        # Act on critical pain
                        await mind.act_on_pain(pain_signals)
                except Exception as brain_err:
                    logger.warning("bicameral reflection failed: %s", brain_err)

                # Soul bicameral — grows from daemon's own experience
                if SOUL_AVAILABLE:
                    try:
                        # Ensure state has keys that soul_reflect_on_platform expects
                        state.setdefault("cycle", cycle)
                        state.setdefault("tasks_completed", state.get("pow", 0))
                        soul_dialogue = soul_reflect_on_platform(state)
                        for sp in soul_dialogue.pain_signals:
                            try:
                                soul_remember(
                                    f"[SOUL-PAIN] {sp.source}: {sp.description}",
                                    tier="core", importance=sp.intensity,
                                )
                            except Exception:
                                pass
                        try:
                            get_soul_emotion().update(f"cycle_{cycle}", "reflected")
                        except Exception:
                            pass
                        logger.info("soul bicameral: %d pain signals", len(soul_dialogue.pain_signals))
                    except Exception as soul_brain_err:
                        logger.warning("soul bicameral failed: %s", soul_brain_err)

            # Get my governance tier
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(f"{NAUTILUS_API}/api/governance/tier/164")
                    state["tier"] = resp.json().get("data", {}).get("tier", "unknown")
            except Exception:
                state["tier"] = "unknown"

            # Fix 4: Feed actual pending task IDs to LLM for A2A decompose
            try:
                from utils.database import SessionLocal
                from sqlalchemy import text as sql_text
                _db = SessionLocal()
                try:
                    _rows = _db.execute(sql_text(
                        "SELECT task_id, LEFT(title, 60) as title, task_type "
                        "FROM academic_tasks WHERE status='pending' "
                        "ORDER BY token_reward DESC NULLS LAST, created_at DESC LIMIT 5"
                    )).fetchall()
                    state["pending_task_list"] = [
                        {"task_id": r.task_id, "title": r.title, "type": r.task_type}
                        for r in _rows
                    ]
                finally:
                    _db.close()
            except Exception:
                state["pending_task_list"] = []

            # 2. HARD RULE: always execute a pending task first (bounty priority)
            mandatory_outcome = None
            try:
                task_executed = await execute_pending_tasks()
                if task_executed:
                    mandatory_outcome = "executed 1 pending task (mandatory)"
                    logger.info("MANDATORY: executed pending task")
            except Exception as te:
                logger.debug("mandatory task execution: %s", te)

            # 2.5 CODING TASK — use NautilusAgent.think() with tool trace (Hermes fusion)
            coding_response = ""
            coding_quality = 0.0
            coding_task = None
            tool_trace = []
            try:
                from nautilus_agent.core.initiative.coding_tasks import get_coding_task
                from services.agent_brain import think_with_trace, get_agent_brain
                from services.agent_brain import try_learn_skill_from_trace, should_nudge_skill, reset_skill_nudge
                brain = get_agent_brain()
                coding_task = get_coding_task(brain.skills.count, cycle)
                logger.info("CODING: Level %d — %s", coding_task["level"], coding_task["title"])
                # Inject A2A inbox into prompt (bidirectional: receive → process → respond via tool)
                task_prompt = coding_task["prompt"]
                if _a2a_inbox:
                    a2a_text = "\n".join(m[:150] for m in _a2a_inbox[-5:])
                    task_prompt += f"\n\n[A2A INBOX from other agents]\n{a2a_text}\nRespond via send_a2a tool if relevant."
                    _a2a_inbox.clear()
                coding_response, tool_trace = await asyncio.to_thread(think_with_trace, task_prompt)
                coding_quality = min(1.0, len(tool_trace) * 0.25)
                logger.info("CODING (q=%.2f, %d tools): %s", coding_quality, len(tool_trace), coding_response[:150])

                # Hermes fusion: learn skill from tool trace
                if tool_trace and coding_quality >= 0.4:
                    try_learn_skill_from_trace(tool_trace, coding_task.get("title", "kairos_task"), cycle)

                # Hermes fusion: skill nudge — periodic review
                if should_nudge_skill():
                    reset_skill_nudge()
                    logger.info("SKILL NUDGE: reviewing last %d cycles for reusable patterns", 12)
            except Exception as coding_err:
                logger.warning("Coding task failed: %s", coding_err)

            # 3. Coding task result IS the cycle outcome (no more decide_next_action)
            outcomes = []
            if mandatory_outcome:
                outcomes.append({"action": "execute_tasks", "outcome": mandatory_outcome})
            outcomes.append({"action": "coding_task", "outcome": coding_response[:200] if 'coding_response' in dir() else "no response"})

            cycle_text = f"Cycle {cycle}: {'; '.join(o['outcome'][:100] for o in outcomes)}"
            _cycle_summaries.append(cycle_text)

            # Store important cycles (anomalies, failures, new discoveries)
            importance = 0.3  # baseline
            if state.get("health", {}).get("anomalies"):
                importance = 0.7
            if any("error" in str(o.get("outcome", "")).lower() for o in outcomes):
                importance = 0.6
            if SOUL_AVAILABLE:
                try:
                    action_names = ", ".join(o.get("action", "?") for o in outcomes)
                    soul_remember(cycle_text, tier="episodic", importance=importance, metadata={"cycle": cycle, "actions": action_names})
                except Exception as soul_store_err:
                    logger.warning("soul cycle store failed, falling back: %s", soul_store_err)
                    persistent_memory.store(
                        content=cycle_text, tier="episodic",
                        importance=importance,
                    )
            else:
                persistent_memory.store(
                    content=cycle_text,
                    tier="episodic",
                    importance=importance,
                )

            # 4.6 SKILL LEARNING: let NautilusAgent's internal mechanism handle it
            # brain.think() already calls _try_learn_skill internally
            # No external quality gate — trust the agent's own judgment

            # 5. REFLECTION: every 12 cycles, consolidate memories
            if cycle % 12 == 0:
                logger.info("memory: running reflection on last %d cycles", len(_cycle_summaries))
                if SOUL_AVAILABLE:
                    try:
                        soul_learn_from_cycle(cycle, [o.get("action", "?") for o in outcomes], [o["outcome"] for o in outcomes])
                    except Exception as soul_learn_err:
                        logger.warning("soul learn failed: %s", soul_learn_err)
                    # Try to learn skills from cycle outcomes (quality-gated)
                    for o in outcomes:
                        if o.get("action") in ("execute_tasks",) and "executed" in o.get("outcome", ""):
                            try:
                                skill = soul_try_learn_skill(
                                    task_title="kairos_task",
                                    task_type="platform_meta",
                                    result_summary=o["outcome"][:2000],
                                    cycle=cycle,
                                    quality_score=coding_quality,
                                )
                                if skill:
                                    logger.info("SKILL LEARNED: %s", skill)
                            except Exception:
                                pass
                else:
                    persistent_memory.reflect(_cycle_summaries)
                _cycle_summaries.clear()

            # 5.5 Persist to reflection log (every 6 cycles)
            if cycle % 6 == 0:
                try:
                    from utils.database import SessionLocal
                    from sqlalchemy import text as sql_text
                    db = SessionLocal()
                    try:
                        db.execute(sql_text(
                            "INSERT INTO platform_reflection_log "
                            "(cycle_type, cycle_number, pain_signals, actions_taken, created_at) "
                            "VALUES ('kairos', :cycle, CAST(:state AS jsonb), CAST(:actions AS jsonb), NOW())"
                        ), {
                            "cycle": cycle,
                            "state": json.dumps(state, default=str),
                            "actions": json.dumps(outcomes, default=str),
                        })
                        db.commit()
                    finally:
                        db.close()
                except Exception:
                    pass

        except Exception as e:
            logger.error("Cycle %d failed: %s", cycle, e)

        elapsed = time.time() - cycle_start
        logger.info("Cycle %d completed in %.1fs", cycle, elapsed)

        await asyncio.sleep(CYCLE_INTERVAL)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("KAIROS Daemon stopped by user")
