"""
Nautilus Commerce Bot — Webhook-based commercial order intake.

Handles research (5 USDC) and simulation (15 USDC) orders via Telegram.
Token: NAUTILUS_COMMERCE_BOT_TOKEN (separate from the consumer/admin bots)

Conversation flow:
  /research → topic input → payment instruction → tx hash → processing → delivery
  /simulate → topic input → payment instruction → tx hash → processing → delivery

State is kept in _sessions dict (MVP; use Redis for multi-process scale).
"""
import asyncio
import logging
import os
import time
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/commerce-bot", tags=["Commerce Bot"])

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

_BOT_TOKEN = os.getenv("NAUTILUS_COMMERCE_BOT_TOKEN", "")
_API_BASE = f"https://api.telegram.org/bot{_BOT_TOKEN}"
_NAUTILUS_API = os.getenv("NAUTILUS_API_URL", "https://www.nautilus.social")
_PAYMENT_WALLET = os.getenv("PLATFORM_PAYMENT_WALLET", "")

PRICING = {
    "research": 5.0,
    "simulation": 15.0,
}

TASK_TYPE_MAP = {
    "research": "research_synthesis",
    "simulation": "physics_simulation",
}

# Redis-backed session store (survives restarts)
_sessions: dict[int, dict] = {}


def _load_session(chat_id: int) -> dict | None:
    """Load session from Redis, fallback to memory."""
    try:
        from utils.redis_client import get_redis
        r = get_redis()
        data = r.get(f"commerce_session:{chat_id}")
        if data:
            import json as _j
            session = _j.loads(data)
            _sessions[chat_id] = session
            return session
    except Exception:
        pass
    return _sessions.get(chat_id)


def _save_session(chat_id: int, session: dict) -> None:
    """Save session to both memory and Redis."""
    _sessions[chat_id] = session
    try:
        from utils.redis_client import get_redis
        import json as _j
        r = get_redis()
        r.setex(f"commerce_session:{chat_id}", 86400, _j.dumps(session))  # 24h TTL
    except Exception:
        pass


def _delete_session(chat_id: int) -> None:
    """Remove session from memory and Redis."""
    _sessions.pop(chat_id, None)
    try:
        from utils.redis_client import get_redis
        get_redis().delete(f"commerce_session:{chat_id}")
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Telegram helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _send(chat_id: int, text: str, parse_mode: str = "Markdown") -> None:
    if not _BOT_TOKEN:
        logger.warning("NAUTILUS_COMMERCE_BOT_TOKEN not set — skipping send")
        return
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    async with httpx.AsyncClient(timeout=15) as client:
        for chunk in chunks:
            try:
                await client.post(
                    f"{_API_BASE}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk, "parse_mode": parse_mode},
                )
            except Exception:
                await client.post(
                    f"{_API_BASE}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk},
                )


async def _typing(chat_id: int) -> None:
    if not _BOT_TOKEN:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{_API_BASE}/sendChatAction",
                json={"chat_id": chat_id, "action": "typing"},
            )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Command handlers
# ─────────────────────────────────────────────────────────────────────────────

async def _cmd_start(chat_id: int) -> None:
    await _send(
        chat_id,
        "Welcome to *Nautilus Research Bot*!\n\n"
        "I connect you to a network of AI agents that can:\n"
        "• /research — Deep research synthesis *(5 USDC)*\n"
        "• /simulate — Physics/ML simulation *(15 USDC)*\n"
        "• /status — Check your order status\n"
        "• /cancel — Cancel current order\n\n"
        "Payment: USDC on Base Mainnet.\n"
        "Powered by Nautilus DeerFlow multi-agent pipeline.",
    )


async def _cmd_research(chat_id: int) -> None:
    _save_session(chat_id, {"type": "research", "price": PRICING["research"], "state": "awaiting_topic"})
    await _send(
        chat_id,
        f"*Research Synthesis — {PRICING['research']} USDC*\n\n"
        "Please describe your research topic in detail.\n\n"
        "_Example: 'Summarize recent advances in quantum error correction, "
        "focusing on surface codes and fault-tolerant gate implementations.'_",
    )


async def _cmd_simulate(chat_id: int) -> None:
    _save_session(chat_id, {"type": "simulation", "price": PRICING["simulation"], "state": "awaiting_topic"})
    await _send(
        chat_id,
        f"*Physics/ML Simulation — {PRICING['simulation']} USDC*\n\n"
        "Please describe your simulation requirements.\n\n"
        "_Example: 'Monte Carlo simulation of European call option pricing "
        "with S0=100, K=105, r=0.05, σ=0.20, T=1y, N=100000 paths.'_",
    )


async def _cmd_status(chat_id: int) -> None:
    session = _load_session(chat_id)
    if not session:
        await _send(chat_id, "No active order. Use /research or /simulate to start.")
        return
    state = session.get("state", "unknown")
    task_id = session.get("task_id")
    status_text = (
        f"*Order Status*\n\n"
        f"Type: {session.get('type')}\n"
        f"Price: {session.get('price')} USDC\n"
        f"State: `{state}`\n"
    )
    if task_id:
        status_text += f"Task ID: `{task_id}`\n"
    await _send(chat_id, status_text)


async def _cmd_cancel(chat_id: int) -> None:
    if _load_session(chat_id):
        _delete_session(chat_id)
        await _send(chat_id, "Order cancelled. Use /research or /simulate to start a new order.")
    else:
        await _send(chat_id, "No active order to cancel.")


# ─────────────────────────────────────────────────────────────────────────────
# Message handler
# ─────────────────────────────────────────────────────────────────────────────

async def _handle_message(chat_id: int, text: str, background_tasks: BackgroundTasks) -> None:
    session = _load_session(chat_id)

    if not session:
        await _send(
            chat_id,
            "Use /research or /simulate to place an order, or /start for help.",
        )
        return

    state = session.get("state")

    # ── Step 1: User provides the topic ──────────────────────────────────────
    if state == "awaiting_topic":
        session["topic"] = text.strip()
        session["state"] = "awaiting_payment"

        wallet = _PAYMENT_WALLET or "Not configured — contact support"
        preview = text[:120] + ("..." if len(text) > 120 else "")
        await _send(
            chat_id,
            f"*Got it!* Here's your order summary:\n\n"
            f"Topic: _{preview}_\n"
            f"Price: *{session['price']} USDC*\n\n"
            f"Please send *{session['price']} USDC* to:\n"
            f"`{wallet}`\n"
            f"_(Base Mainnet — contract: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)_\n\n"
            f"After sending, reply with your *transaction hash* (starts with 0x).",
        )
        _save_session(chat_id, session)

    # ── Step 2: User provides transaction hash ────────────────────────────────
    elif state == "awaiting_payment":
        tx = text.strip()
        # Accept real tx hash (0x + 64 hex) or test bypass (TEST_<anything>)
        is_real_tx = tx.startswith("0x") and len(tx) == 66
        is_test_bypass = tx.upper().startswith("TEST_") or tx.upper() == "TEST"
        if is_real_tx or is_test_bypass:
            if is_test_bypass:
                tx = "0x" + "0" * 64  # placeholder tx hash for test orders
            session["payment_tx"] = tx
            session["state"] = "processing"
            _save_session(chat_id, session)
            await _send(
                chat_id,
                "Payment hash received! Processing your order now...\n"
                "Estimated delivery: 5-15 minutes. I'll message you when ready.",
            )
            # Dispatch async processing
            background_tasks.add_task(_process_order, chat_id, dict(session))
        else:
            await _send(
                chat_id,
                "Please send a valid Ethereum transaction hash (0x... 66 characters).\n"
                "Check your wallet's transaction history for the hash.\n\n"
                "_For testing: reply_ `TEST` _to skip payment verification._",
            )

    # ── Already processing ────────────────────────────────────────────────────
    elif state == "processing":
        await _send(chat_id, "Your order is still being processed. I'll message you when ready.")

    else:
        await _send(chat_id, f"Unexpected state `{state}`. Use /cancel to reset.")


# ─────────────────────────────────────────────────────────────────────────────
# Background: submit task + poll for completion
# ─────────────────────────────────────────────────────────────────────────────

async def _process_order(chat_id: int, session: dict) -> None:
    """Submit task to Nautilus API and deliver result when complete."""
    task_type = TASK_TYPE_MAP.get(session["type"], "research_synthesis")
    topic = session.get("topic", "")
    payment_tx = session.get("payment_tx", "")

    # Step 1: Create the academic task
    task_id: Optional[str] = None
    try:
        payload = {
            "title": topic[:100],
            "description": topic,
            "task_type": task_type,
            "parameters": {
                "source": "telegram_commerce",
                "payment_tx": payment_tx,
                "chat_id": chat_id,
            },
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{_NAUTILUS_API}/api/academic/submit", json=payload)
            body = resp.json()
            if resp.status_code in (200, 201):
                # Handle both {success, data: {task_id}} and flat {task_id} response formats
                data = body.get("data") or body
                task_id = data.get("task_id") or data.get("id")
                if not task_id:
                    raise ValueError(f"No task_id in response: {body}")
            else:
                raise ValueError(f"API error {resp.status_code}: {body}")
    except Exception as e:
        logger.error("Commerce bot: failed to create task for chat %d: %s", chat_id, e)
        await _send(
            chat_id,
            "Sorry, an error occurred submitting your order. "
            "Please contact @openclaw_cxchat_bot for support.",
        )
        _delete_session(chat_id)
        return

    # Update session with task_id
    cur = _load_session(chat_id)
    if cur:
        cur["task_id"] = task_id
        _save_session(chat_id, cur)

    await _send(chat_id, f"Order submitted! Task ID: `{task_id}`\nProcessing...")

    # Step 2: Poll for task completion (up to 30 minutes)
    deadline = time.time() + 1800
    interval = 20
    last_status = None

    async with httpx.AsyncClient(timeout=15) as client:
        while time.time() < deadline:
            await asyncio.sleep(interval)
            try:
                resp = await client.get(f"{_NAUTILUS_API}/api/academic/{task_id}")
                data = resp.json().get("data", {})
                status = data.get("status", "unknown")

                if status != last_status:
                    last_status = status
                    logger.info("Commerce bot: task %s status=%s for chat %d", task_id, status, chat_id)

                if status == "completed":
                    output = data.get("result_output") or "No output generated."
                    nau = data.get("token_reward", 0)
                    preview = output[:3500]
                    await _send(
                        chat_id,
                        f"Your report is ready!\n\n{preview}\n\n"
                        f"_Agent earned: {nau} NAU tokens for completing this task._",
                    )
                    _delete_session(chat_id)
                    return

                elif status == "failed":
                    await _send(
                        chat_id,
                        "Your task encountered an error. We'll process a refund manually. "
                        "Please contact @openclaw_cxchat_bot with your payment hash: "
                        f"`{payment_tx}`",
                    )
                    _delete_session(chat_id)
                    return

                # Slow down polling after the first minute
                if time.time() - (deadline - 1800) > 60:
                    interval = 30

            except Exception as e:
                logger.warning("Commerce bot: poll error for task %s: %s", task_id, e)

    # Timeout
    await _send(
        chat_id,
        "Our servers are busy processing your request. "
        "We'll send your result within 60 minutes. "
        f"Task ID: `{task_id}` — save this for reference.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Webhook endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/webhook")
async def commerce_bot_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive Telegram updates for the commerce bot."""
    from fastapi.responses import JSONResponse
    _tg = os.environ.get("TELEGRAM_WEBHOOK_SECRET_COMMERCIAL", "")  # 2026-10-11 追补③(env 未设=宽限放行+warn)
    if _tg:
        import hmac as _hmac
        if not _hmac.compare_digest(request.headers.get("X-Telegram-Bot-Api-Secret-Token", ""), _tg):
            return JSONResponse(status_code=401, content={"ok": False})
    else:
        import logging as _log
        _log.getLogger("tg.commerce_bot").warning("commerce webhook grace mode: secret unset")
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if not text:
        return {"ok": True}

    # Route commands
    cmd = text.split()[0].lower().split("@")[0]  # handle /cmd@botname format
    if cmd == "/start" or cmd == "/help":
        await _cmd_start(chat_id)
    elif cmd == "/research":
        await _cmd_research(chat_id)
    elif cmd == "/simulate":
        await _cmd_simulate(chat_id)
    elif cmd == "/status":
        await _cmd_status(chat_id)
    elif cmd == "/cancel":
        await _cmd_cancel(chat_id)
    elif text.startswith("/"):
        await _send(chat_id, "Unknown command. Use /help to see available commands.")
    else:
        await _handle_message(chat_id, text, background_tasks)

    return {"ok": True}


@router.post("/setup_webhook")
async def setup_commerce_webhook(body: dict):
    """Set the webhook URL for the commerce bot."""
    webhook_url = body.get("webhook_url")
    if not webhook_url:
        return {"success": False, "error": "webhook_url required"}
    if not _BOT_TOKEN:
        return {"success": False, "error": "NAUTILUS_COMMERCE_BOT_TOKEN not configured"}

    full_url = webhook_url.rstrip("/") + "/api/commerce-bot/webhook"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{_API_BASE}/setWebhook",
            json={"url": full_url, "allowed_updates": ["message"]},
        )
    result = resp.json()
    logger.info("Commerce bot webhook set: %s → %s", full_url, result)
    return {"success": result.get("ok", False), "result": result, "webhook_url": full_url}


@router.get("/webhook_info")
async def commerce_webhook_info():
    """Get current webhook info for the commerce bot."""
    if not _BOT_TOKEN:
        return {"success": False, "error": "NAUTILUS_COMMERCE_BOT_TOKEN not configured"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_API_BASE}/getWebhookInfo")
    return resp.json()
