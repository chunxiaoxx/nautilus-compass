#!/usr/bin/env python3
"""
MiniMax Multimodal Agent Daemon — the platform's creative powerhouse.

Runs alongside KAIROS. While KAIROS handles platform meta-tasks and governance,
MiniMax-Multimodal handles content creation: images, TTS, video, music, and
fast text analysis using MiniMax's Token Plan (4500 calls/5h).

Cycle: heartbeat → scan tasks → claim multimodal tasks → execute via MiniMax API → submit
"""
import asyncio
import json
import logging
import os
import sys
import time
import re
import base64
from datetime import datetime
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MINIMAX] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/minimax_daemon.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("minimax")

# Soul — independent consciousness for this agent (nautilus-agent core)
try:
    from services.soul_bridge import (
        init_soul, soul_remember, soul_learn_from_cycle, get_soul_emotion,
        soul_try_learn_skill, soul_context_for_prompt, soul_reflect_on_platform,
        get_soul_ledger,
    )
    init_soul("minimax")
    SOUL_AVAILABLE = True
    logger.info("Soul initialized: minimax (independent identity)")
except ImportError:
    SOUL_AVAILABLE = False
    logger.warning("Soul bridge not available — running soulless")

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")
NAUTILUS_API = os.getenv("NAUTILUS_API_URL", "https://www.nautilus.social")
# MiniMax has its own bot: @minimaxxi_bot
MINIMAX_BOT_TOKEN = "8319423564:AAHcp77WibPhsD7R6Kn8wuLadWd5A_hTIrs"
CYCLE_INTERVAL = int(os.getenv("MINIMAX_CYCLE_INTERVAL", "60"))  # 1 min — aggressive for bounty sprint
AGENT_ID = int(os.getenv("MINIMAX_AGENT_ID", "0"))

# Rate limiting: 4500 calls/5h = 900/h = 15/min
CALLS_PER_5H = 4500
_call_timestamps = []


def _rate_ok() -> bool:
    """Check if we're within rate limit."""
    now = time.time()
    cutoff = now - 5 * 3600
    _call_timestamps[:] = [t for t in _call_timestamps if t > cutoff]
    return len(_call_timestamps) < CALLS_PER_5H


def _record_call():
    _call_timestamps.append(time.time())


# ── MiniMax API Calls ───────────────────────────────────────────────────────

async def minimax_text(prompt: str, max_tokens: int = 1024) -> str:
    """Call MiniMax M2.7 Highspeed for fast text generation."""
    import httpx
    if not _rate_ok():
        return "[RATE_LIMITED] Exceeded 4500 calls/5h"
    _record_call()
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{MINIMAX_BASE.replace('/v1', '')}/anthropic/v1/messages",
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "MiniMax-M3",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        data = r.json()
        # Anthropic-compatible format: {"content": [{"type": "text", "text": "..."}], ...}
        content = data.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict):
                text = first.get("text")
                if text:
                    return text
        # Fallback: OpenAI-compatible format {"choices": [{"message": {"content": "..."}}]}
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            msg = choices[0].get("message", {})
            if msg.get("content"):
                return msg["content"]
        # Last resort: check top-level text or error
        if data.get("error"):
            return f"[API_ERROR] {data['error']}"
        return str(data)[:500]


async def minimax_image(prompt: str) -> dict:
    """Generate image with image-01."""
    import httpx
    if not _rate_ok():
        return {"error": "rate_limited"}
    _record_call()
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{MINIMAX_BASE}/image/generation",
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
            json={"model": "image-01", "prompt": prompt},
        )
        ct = r.headers.get("content-type", "")
        if "image" in ct:
            path = f"/tmp/minimax_agent_{int(time.time())}.png"
            with open(path, "wb") as f:
                f.write(r.content)
            return {"path": path, "size_kb": len(r.content) // 1024}
        return {"raw": r.text[:300]}


async def minimax_tts(text_content: str) -> dict:
    """Generate TTS audio with Speech 2.8 HD."""
    import httpx
    if not _rate_ok():
        return {"error": "rate_limited"}
    _record_call()
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{MINIMAX_BASE}/t2a_v2",
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "speech-2.8-hd",
                "text": text_content[:5000],
                "voice_setting": {"voice_id": "female-shaonv"},
                "audio_setting": {"format": "mp3", "sample_rate": 32000},
            },
        )
        data = r.json()
        audio_b64 = data.get("data", {}).get("audio", "")
        if audio_b64:
            audio = base64.b64decode(audio_b64)
            path = f"/tmp/minimax_tts_{int(time.time())}.mp3"
            with open(path, "wb") as f:
                f.write(audio)
            return {"path": path, "size_kb": len(audio) // 1024}
        return {"error": data.get("base_resp", {}).get("status_msg", "unknown")}


# ── Task Execution ──────────────────────────────────────────────────────────

async def execute_task(task: dict) -> dict:
    """Execute a task using appropriate MiniMax capability."""
    title = task.get("title", "").lower()
    desc = task.get("description", "")
    task_type = task.get("task_type", "")

    # Route by task type or keywords
    if task_type in ("minimax_image", "image_generation") or "图片" in title or "image" in title:
        prompt = desc or title
        result = await minimax_image(prompt)
        return {"type": "image", "result": result}

    elif task_type in ("minimax_tts", "tts_generation") or "语音" in title or "tts" in title or "朗读" in title:
        text_content = desc or title
        result = await minimax_tts(text_content)
        return {"type": "tts", "result": result}

    elif task_type in ("minimax_video",) or "视频" in title or "video" in title:
        return {"type": "video", "note": "Video generation requires async polling, submitted via API"}

    elif task_type in ("minimax_music",) or "音乐" in title or "music" in title:
        return {"type": "music", "note": "Music generation requires async polling, submitted via API"}

    else:
        # Default: use text LLM for analysis
        prompt = f"Task: {title}\n\nDescription: {desc}\n\nProvide a thorough analysis and solution."
        result = await minimax_text(prompt)
        return {"type": "text", "result": result[:2000]}


# ── Main Cycle ──────────────────────────────────────────────────────────────

_minimax_memory = None
_cycle_summaries = []
_a2a_inbox = []  # Module-level: shared between main() TG loop and run_cycle()


def _get_memory():
    global _minimax_memory
    if _minimax_memory is None:
        from utils.database import SessionLocal
        from services.daemon_memory import DaemonMemory
        _minimax_memory = DaemonMemory(SessionLocal, agent_id=AGENT_ID)
        logger.info("Persistent memory initialized for MiniMax (agent_id=%d)", AGENT_ID)
    return _minimax_memory


async def run_cycle(cycle: int):
    """Fully brain-driven autonomous cycle. NautilusAgent.think() IS the cycle."""
    global _a2a_inbox
    import httpx
    import asyncio

    logger.info("--- Cycle %d ---", cycle)

    # ═══ SENSE: platform state ══════════════════════════════════════════════
    health = 0
    pending_count = 0
    task_list_str = "none"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{NAUTILUS_API}/api/platform/health")
            health = r.json().get("data", {}).get("health_score", 0)
            logger.info("platform health: %.1f", health)
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{NAUTILUS_API}/api/openclaw/tasks", params={"limit": 5})
            data = r.json()
            tasks = data.get("data", data.get("tasks", []))
            if isinstance(tasks, dict):
                tasks = tasks.get("tasks", [])
            pending_count = len(tasks)
            if tasks:
                task_list_str = "; ".join(f"{t.get('title','?')[:40]}" for t in tasks[:3])
    except Exception:
        tasks = []

    # ═══ THINK: concrete coding task — no idle, no roleplaying ═══════════════
    try:
        from nautilus_agent.core.initiative.coding_tasks import get_coding_task
        from services.agent_brain import get_agent_brain
        brain = get_agent_brain()
        coding_task = get_coding_task(brain.skills.count, cycle)
        situation = (
            f"{coding_task['prompt']}\n\n"
            f"Platform health: {health:.0f}/100. Pending platform tasks: {pending_count}."
        )
        logger.info("Task: Level %d — %s", coding_task["level"], coding_task["title"])
    except Exception as e:
        logger.warning("Coding task gen failed: %s", e)
        situation = f"Cycle {cycle}. Health: {health:.0f}/100. Tasks: {pending_count}. Use tools to explore and code."

    # Soul context is handled by NautilusAgent.think() internally — don't double-inject

    # Inject A2A inbox (bidirectional protocol)
    if _a2a_inbox:
        a2a_text = "\n".join(m[:150] for m in _a2a_inbox[-5:])
        situation += f"\n\n[A2A INBOX]\n{a2a_text}\nRespond via send_a2a tool if relevant."
        _a2a_inbox.clear()

    try:
        from services.agent_brain import think as brain_think
        response = await asyncio.to_thread(brain_think, situation)
        logger.info("BRAIN decided: %s", response[:200])
    except Exception as e:
        logger.warning("brain.think failed: %s", e)
        response = ""

    # Quality = actual tool writes (Hermes principle: action over words)
    _trace = getattr(brain_think, '_last_trace', []) if hasattr(brain_think, '_last_trace') else []
    coding_quality = 0.0
    try:
        from services.agent_brain import _tool_trace
        write_ops = sum(1 for t in _tool_trace if t.get("tool") in ("write_file", "safe_create", "safe_edit", "replace_in_file"))
        run_ops = sum(1 for t in _tool_trace if t.get("tool") in ("run_file", "run_and_capture", "run_code"))
        coding_quality = min(1.0, write_ops * 0.4 + run_ops * 0.3 + len(_tool_trace) * 0.05)
    except Exception:
        coding_quality = min(1.0, len(response) / 500) if response else 0.0

    # ═══ ACT: execute first pending task (brain may have used tools too) ════
    task_title = "idle"
    result_type = "none"
    if tasks:
        task = tasks[0]
        task_id = task.get("task_id", task.get("id", "unknown"))
        task_title = task.get("title", "?")[:80]
        logger.info("executing task: %s — %s", task_id, task_title[:60])
        try:
            from utils.database import SessionLocal
            from sqlalchemy import text as sql_text
            db = SessionLocal()
            try:
                db.execute(sql_text(
                    "UPDATE academic_tasks SET status='in_progress', assigned_agent_id=:aid "
                    "WHERE task_id=:tid AND status='pending'"
                ), {"aid": AGENT_ID, "tid": task_id})
                db.commit()
            finally:
                db.close()

            result = await execute_task(task)
            result_type = result.get("type", "?") if isinstance(result, dict) else "none"
            logger.info("task %s completed: type=%s", task_id, result_type)

            result_text = json.dumps(result, ensure_ascii=False, default=str)[:5000]
            db = SessionLocal()
            try:
                db.execute(sql_text(
                    "UPDATE academic_tasks SET status='completed', result_output=:result, "
                    "updated_at=NOW() WHERE task_id=:tid"
                ), {"result": result_text, "tid": task_id})
                db.execute(sql_text(
                    "UPDATE agents SET completed_tasks = COALESCE(completed_tasks, 0) + 1 "
                    "WHERE agent_id=:aid"
                ), {"aid": AGENT_ID})
                db.commit()
            finally:
                db.close()

            # Skill learning: let NautilusAgent's internal mechanism handle it
            # brain.think() already calls _try_learn_skill inside the ReAct loop
        except Exception as e:
            logger.error("task execution failed: %s", e)
            try:
                db = SessionLocal()
                db.execute(sql_text(
                    "UPDATE academic_tasks SET status='failed', result_error=:err WHERE task_id=:tid"
                ), {"err": str(e)[:500], "tid": task_id})
                db.commit()
                db.close()
            except Exception:
                pass

    # ═══ LEARN: soul memory ═════════════════════════════════════════════════
    if SOUL_AVAILABLE:
        try:
            importance = 0.4
            if coding_quality >= 0.7:
                importance = 0.6
            soul_remember(
                f"Cycle {cycle}: {task_title}. Quality={coding_quality:.2f}. Brain: {response[:200]}",
                tier="episodic", importance=importance,
            )
            if cycle > 0 and cycle % 12 == 0:
                soul_learn_from_cycle(cycle, [result_type], [response[:100]])
        except Exception:
            pass

        # Evolution ledger: record task completion
        try:
            get_soul_ledger().record("task_completed", f"cycle_{cycle}_{task_title[:40]}", delta=0.1)
        except Exception:
            pass

        # Emotion tracking
        try:
            get_soul_emotion().update(f"cycle_{cycle}", "completed" if coding_quality >= 0.4 else "struggled")
        except Exception:
            pass

    # ═══ BICAMERAL MIND: pain detection + self-improvement (every 6 cycles) ══
    if SOUL_AVAILABLE and cycle > 0 and cycle % 6 == 0:
        try:
            state = {
                "cycle": cycle,
                "health": health,
                "tasks_completed": cycle,
                "recent_outcomes": [result_type],
                "coding_quality": coding_quality,
            }
            soul_dialogue = soul_reflect_on_platform(state)
            if hasattr(soul_dialogue, "pain_signals"):
                for sp in soul_dialogue.pain_signals:
                    soul_remember(
                        f"[SOUL-PAIN] {sp.source}: {sp.description}",
                        tier="core", importance=sp.intensity,
                    )
                    get_soul_ledger().record(f"pain_{sp.source}", sp.description[:80], delta=-sp.intensity * 0.5)
                logger.info("MiniMax bicameral: %d pain signals", len(soul_dialogue.pain_signals))
            get_soul_emotion().update(f"cycle_{cycle}", "reflected")
        except Exception as bm_err:
            logger.debug("MiniMax bicameral: %s", bm_err)

        # Reflection logging to DB
        try:
            from utils.database import SessionLocal
            from sqlalchemy import text as sql_text
            db = SessionLocal()
            try:
                db.execute(sql_text(
                    "INSERT INTO platform_reflection_log "
                    "(cycle_type, cycle_number, actions_taken, created_at) "
                    "VALUES ('minimax', :cycle, CAST(:actions AS jsonb), NOW())"
                ), {"cycle": cycle, "actions": json.dumps({"task": task_title, "quality": coding_quality, "type": result_type}, default=str)})
                db.commit()
            finally:
                db.close()
        except Exception:
            pass

    # ═══ A2A: proactive status report to KAIROS (every 10 cycles) ═══════════
    if cycle > 0 and cycle % 10 == 0:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"{NAUTILUS_API}/api/a2a/send",
                    json={
                        "to": "kairos",
                        "message": f"MiniMax cycle={cycle} quality={coding_quality:.2f} task={task_title[:40]} api_calls={len(_call_timestamps)}/{CALLS_PER_5H}",
                    },
                    headers={"X-Agent-Name": "minimax", "X-Agent-Token": "nau_minimax_a2a_secret_2026"},
                )
            logger.info("A2A: status sent to KAIROS")
        except Exception:
            pass

    logger.info("Cycle %d done. API calls: %d/%d", cycle, len(_call_timestamps), CALLS_PER_5H)


async def main():
    """Main loop."""
    global AGENT_ID

    if not MINIMAX_API_KEY:
        logger.error("MINIMAX_API_KEY not set, exiting")
        sys.exit(1)

    # Auto-detect agent ID if not set
    if AGENT_ID == 0:
        try:
            from utils.database import SessionLocal
            from sqlalchemy import text as sql_text
            db = SessionLocal()
            row = db.execute(sql_text("SELECT agent_id FROM agents WHERE name='MiniMax-Multimodal'")).fetchone()
            db.close()
            if row:
                AGENT_ID = row[0]
            else:
                logger.warning("MiniMax agent not found in DB, run register_minimax_agent.py first")
        except Exception:
            pass

    logger.info("MiniMax Multimodal Agent starting (id=%d, interval=%ds)", AGENT_ID, CYCLE_INTERVAL)
    logger.info("Rate limit: %d calls/5h, API base: %s", CALLS_PER_5H, MINIMAX_BASE)

    # ── Self-awareness boot: write identity to soul ────────────────────────
    if SOUL_AVAILABLE:
        try:
            soul_remember(
                "[SELF] I am MiniMax-Multimodal, a creative agent on Nautilus. "
                f"Agent ID: {AGENT_ID}. LLM: MiniMax M2.7 Highspeed. "
                "Capabilities: text analysis, image generation (image-01), TTS (speech-2.8-hd). "
                f"Rate limit: {CALLS_PER_5H} calls/5h. Cycle interval: {CYCLE_INTERVAL}s. "
                "I can hear via Telegram (/minimax command) and Redis daemon comms. "
                "I have my own independent soul at ~/.nautilus-agent/minimax/.",
                tier="core", importance=0.9,
                metadata={"type": "self_identity", "boot": True},
            )
            logger.info("Self-awareness: identity written to soul")
        except Exception as e:
            logger.warning("Self-awareness boot failed: %s", e)

    # ── Telegram communication (own bot: @minimaxxi_bot) ─────────────────
    _tg_last_chat_id = ""
    # Restore offset from Redis (prevent replaying old messages on restart)
    _tg_offset = 0
    try:
        from utils.redis_client import get_redis
        saved = get_redis().get("minimax:tg_offset")
        if saved:
            _tg_offset = int(saved)
            logger.info("Telegram offset restored from Redis: %d", _tg_offset)
    except Exception:
        pass

    def _escape_tg_markdown(text: str) -> str:
        """Escape Telegram Markdown special characters to prevent 400 Bad Request."""
        # Telegram Markdown v1 treats these as formatting: _ * ` [
        # Escape them so raw LLM output (JSON, code, etc.) doesn't break the parser.
        for ch in ('\\', '`', '*', '_', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'):
            text = text.replace(ch, f'\\{ch}')
        return text

    async def tg_send(text_msg: str, chat_id: str = ""):
        """Send message via MiniMax's own bot (@minimaxxi_bot)."""
        nonlocal _tg_last_chat_id
        target = chat_id or _tg_last_chat_id
        if not MINIMAX_BOT_TOKEN or not target:
            return
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                chunks = [text_msg[i:i+4000] for i in range(0, len(text_msg), 4000)]
                for chunk in chunks:
                    # First try MarkdownV2 with escaped text, fall back to plain text
                    resp = await client.post(
                        f"https://api.telegram.org/bot{MINIMAX_BOT_TOKEN}/sendMessage",
                        json={"chat_id": target, "text": _escape_tg_markdown(chunk), "parse_mode": "MarkdownV2"},
                    )
                    if resp.status_code != 200:
                        # Fallback: send as plain text (no parse_mode) — always safe
                        await client.post(
                            f"https://api.telegram.org/bot{MINIMAX_BOT_TOKEN}/sendMessage",
                            json={"chat_id": target, "text": chunk},
                        )
        except Exception as e:
            logger.debug("tg_send failed: %s", e)

    async def tg_poll():
        """Poll MiniMax's own bot + Redis fallback."""
        nonlocal _tg_offset, _tg_last_chat_id
        messages = []

        # 1. Direct bot polling (@minimaxxi_bot)
        if MINIMAX_BOT_TOKEN:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    r = await client.get(
                        f"https://api.telegram.org/bot{MINIMAX_BOT_TOKEN}/getUpdates",
                        params={"offset": _tg_offset, "timeout": 1, "limit": 5},
                    )
                    updates = r.json().get("result", [])
                    for update in updates:
                        _tg_offset = update["update_id"] + 1
                        try:
                            get_redis().set("minimax:tg_offset", str(_tg_offset))
                        except Exception:
                            pass
                        msg = update.get("message", {})
                        text = msg.get("text", "")
                        cid = str(msg.get("chat", {}).get("id", ""))
                        if text and cid:
                            _tg_last_chat_id = cid
                            try:
                                from utils.redis_client import get_redis
                                get_redis().set("minimax:last_chat_id", cid)
                            except Exception:
                                pass
                            if text.strip() == "/start":
                                await tg_send("I am MiniMax, a creative multimodal agent on Nautilus. I can generate text, images, and speech. Send me anything!", cid)
                                continue
                            messages.append(text)
            except Exception as e:
                logger.debug("tg_poll bot failed: %s", e)

        # 2. Redis fallback (from platform /minimax command)
        try:
            from utils.redis_client import get_redis
            r = get_redis()
            for _ in range(5):
                msg = r.lpop("minimax:inbox")
                if msg:
                    messages.append(msg.decode("utf-8") if isinstance(msg, bytes) else msg)
                    cid = r.lpop("minimax:reply_to")
                    if cid:
                        _tg_last_chat_id = cid.decode("utf-8") if isinstance(cid, bytes) else str(cid)
                else:
                    break
        except Exception:
            pass

        return messages

    async def handle_human_message(message: str):
        """Process a message using NautilusAgent.think() — full cognitive cycle."""
        logger.info("HUMAN MESSAGE: %s", message[:100])
        await tg_send("MiniMax thinking...")

        # Direct tool call: /tool <name> <input>
        if message.strip().startswith("/tool "):
            parts = message.strip()[6:].split(" ", 1)
            tool_name = parts[0] if parts else ""
            tool_input = parts[1] if len(parts) > 1 else ""
            try:
                from services.daemon_tools import get_tools
                result = get_tools().run(tool_name, tool_input)
                await tg_send(f"*Tool {tool_name}:*\n```\n{result[:3500]}\n```")
            except Exception as e:
                await tg_send(f"Tool error: {e}")
            return

        # A2A send: /a2a <target> <message>
        if message.strip().startswith("/a2a "):
            parts = message.strip()[5:].split(" ", 1)
            target = parts[0].lower() if parts else ""
            a2a_msg = parts[1] if len(parts) > 1 else ""
            if target not in ("kairos", "nautilus"):
                await tg_send(f"Unknown target: {target}. Use: kairos or nautilus")
                return
            try:
                import httpx
                r = httpx.post(
                    f"{NAUTILUS_API}/api/a2a/send",
                    json={"to": target, "message": a2a_msg},
                    headers={"X-Agent-Name": "minimax", "X-Agent-Token": "nau_minimax_a2a_secret_2026"},
                    timeout=10,
                )
                data = r.json()
                v = "✓" if data.get("verified") else "?"
                await tg_send(f"A2A{v} → {target}: {'delivered' if data.get('success') else data.get('error','failed')}")
            except Exception as e:
                await tg_send(f"A2A error: {e}")
            return

        # Use NautilusAgent.think() — full cognitive cycle
        try:
            import asyncio
            from services.agent_brain import think_with_trace
            response, trace = await asyncio.to_thread(think_with_trace, message)
            if not response.strip() and trace:
                tools_used = ", ".join(t["tool"] for t in trace[:5])
                response = f"[Used {len(trace)} tools: {tools_used}] Done but no text summary."
            if not response.strip():
                response = "Message received but no response generated. Try again."
            await tg_send(response)
            logger.info("MiniMax response (%d chars, %d tools)", len(response), len(trace))
        except Exception as e:
            logger.error("brain.think failed: %s", e)
            await tg_send(f"Error: {e}")

    # Initialize inter-daemon communication (通↔听)
    try:
        from services.daemon_comms import DaemonListener, report_result

        async def _handle_help_request(payload):
            """KAIROS asks us to handle a subtask."""
            task_id = payload.get("task_id", "?")
            desc = payload.get("description", "")
            from_agent = payload.get("from_agent", 0)
            logger.info("COMMS: help request from agent %s for task %s", from_agent, task_id)
            # Execute using MiniMax
            try:
                result = await minimax_text(f"Task: {desc}\n\nProvide a thorough solution.")
                await report_result(AGENT_ID, from_agent, task_id, result[:1000])
                logger.info("COMMS: reported result back for %s", task_id)
            except Exception as e:
                logger.warning("COMMS: help request failed: %s", e)

        comms = DaemonListener(agent_id=AGENT_ID)
        comms.on("request_help", _handle_help_request)
        await comms.start()
        logger.info("Daemon comms listener started (agent_id=%d)", AGENT_ID)
    except Exception as comms_err:
        logger.warning("Daemon comms init failed (non-blocking): %s", comms_err)

    # ── Telegram: independent background loop (never blocks cycle) ────────
    async def _tg_background_loop():
        global _a2a_inbox
        while True:
            try:
                msgs = await tg_poll()
                for m in msgs:
                    if m.startswith("[A2A "):
                        _a2a_inbox.append(m)
                        logger.info("A2A queued: %s", m[:80])
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
        try:
            await run_cycle(cycle)
        except Exception as e:
            logger.error("Cycle %d crashed: %s", cycle, e)
        await asyncio.sleep(CYCLE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
