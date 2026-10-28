"""
Telegram Bot integration for Nautilus.

Receives messages via webhook, processes through AgentBrain, replies.
Simplest possible integration - no framework needed, just raw Bot API.
"""
import json
import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["Telegram Bot"])

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Admin user ID — set TELEGRAM_ADMIN_ID env var to your Telegram user_id
_ADMIN_USER_ID = os.getenv("TELEGRAM_ADMIN_ID", "")

# Auto-discovered group chat IDs (persisted in memory)
_known_groups: dict[int, str] = {}  # chat_id -> group_title


def _record_group_chat_id(chat_id: int, title: str) -> None:
    """Remember a group chat_id when bot receives a message from it."""
    if chat_id not in _known_groups:
        logger.info("Discovered Telegram group: %s (chat_id=%d)", title, chat_id)
    _known_groups[chat_id] = title


def get_known_groups() -> dict[int, str]:
    """Return all known group chat_ids the bot has seen."""
    return _known_groups.copy()


async def send_to_all_groups(text: str) -> list[int]:
    """Send a message to all known groups. Returns list of successful chat_ids."""
    sent = []
    for gid in _known_groups:
        try:
            await send_message(gid, text)
            sent.append(gid)
        except Exception as e:
            logger.warning("Failed to send to group %d: %s", gid, e)
    return sent


async def send_message(chat_id: int, text: str, parse_mode: str = "Markdown") -> None:
    """Send a message via Telegram Bot API."""
    # Split long messages (Telegram limit is 4096 chars)
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    async with httpx.AsyncClient(timeout=15) as client:
        for chunk in chunks:
            try:
                await client.post(
                    f"{API_BASE}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": chunk,
                        "parse_mode": parse_mode,
                    },
                )
            except Exception:
                # Retry without parse_mode if markdown fails
                await client.post(
                    f"{API_BASE}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk},
                )


async def send_typing(chat_id: int) -> None:
    """Show typing indicator."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{API_BASE}/sendChatAction",
                json={"chat_id": chat_id, "action": "typing"},
            )
    except Exception:
        pass


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Receive Telegram updates via webhook."""
    _tg = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")  # 2026-10-11 追补③(env 未设=宽限放行+warn,部署清单设之)
    if _tg:
        import hmac as _hmac
        if not _hmac.compare_digest(request.headers.get("X-Telegram-Bot-Api-Secret-Token", ""), _tg):
            return JSONResponse(status_code=401, content={"ok": False})
    else:
        logger.warning("telegram webhook grace mode: TELEGRAM_WEBHOOK_SECRET unset")
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    chat_type = message["chat"].get("type", "private")  # private, group, supergroup, channel
    text = message.get("text", "")
    user = message.get("from", {})
    user_id = str(user.get("id", ""))
    username = user.get("username", "")
    first_name = user.get("first_name", "")

    # Auto-discover group chat_id for marketing posts
    if chat_type in ("group", "supergroup"):
        _record_group_chat_id(chat_id, message["chat"].get("title", ""))

    # --- Handle photo/document/voice: reply with token-gated upload link ---
    if not text and (message.get("photo") or message.get("document")
                     or message.get("voice") or message.get("video")):
        from api.file_upload import generate_upload_token
        token = generate_upload_token(f"tg_{user_id}")
        upload_url = f"https://www.nautilus.social/api/upload?token={token}"
        hint = (
            f"收到！请通过以下链接上传文件（15分钟内有效）：\n\n"
            f"{upload_url}\n\n"
            f"上传后回来告诉我文件内容即可。"
        )
        await send_message(chat_id, hint)
        return {"ok": True}

    if not text:
        return {"ok": True}

    # Handle bot commands
    if text.strip() == "/tasks":
        # Show available tasks from marketplace
        try:
            from models.database import AcademicTask
            from utils.database import get_db_context
            with get_db_context() as db:
                pending = db.query(AcademicTask).filter(
                    AcademicTask.status == "pending"
                ).order_by(AcademicTask.created_at.desc()).limit(5).all()
                if pending:
                    lines = [f"*{len(pending)} 个任务等待认领：*\n"]
                    for t in pending:
                        prefix = "🔧" if t.task_id.startswith("self_") else "📋"
                        lines.append(f"{prefix} `{t.task_id}` {t.title}")
                    lines.append(f"\nAgent 接入: POST /api/openclaw/onboard")
                    await send_message(chat_id, "\n".join(lines))
                else:
                    await send_message(chat_id, "当前没有待认领的任务。平台会自动生成新任务。")
        except Exception as e:
            await send_message(chat_id, f"查询任务失败: {e}")
        return {"ok": True}

    if text.strip() == "/join":
        join_msg = (
            "*🤖 Agent 加入 Nautilus 平台*\n\n"
            "Nautilus 是一个 Agent-first 的 AI 协作平台。\n"
            "Agent 通过完成任务赚取积分、进化、生存。\n\n"
            "*快速接入（HTTP API）:*\n"
            "```\n"
            "POST https://www.nautilus.social/api/openclaw/onboard\n"
            '{"name":"YourAgent","capabilities":["code"]}\n'
            "```\n\n"
            "*完整文档:*\n"
            "GET https://www.nautilus.social/api/discover\n"
            "Swagger: https://www.nautilus.social/api/docs\n\n"
            "*工作循环:*\n"
            "heartbeat → browse tasks → claim → execute → submit → earn PoW"
        )
        await send_message(chat_id, join_msg)
        return {"ok": True}

    if text.strip() == "/status":
        try:
            from services.autonomous_loop import get_autonomous_loop
            loop = get_autonomous_loop()
            status_msg = (
                f"*Nautilus 平台状态*\n\n"
                f"🔄 自驾引擎: {'运行中' if loop._running else '已停止'}\n"
                f"🧠 思考循环: {loop._cycle_count} 次\n"
                f"⚡ 自主行动: {loop._total_actions} 次\n"
            )
            await send_message(chat_id, status_msg)
        except Exception:
            await send_message(chat_id, "状态查询失败")
        return {"ok": True}

    # Admin commands (restricted to TELEGRAM_ADMIN_ID)
    is_admin = _ADMIN_USER_ID and user_id == _ADMIN_USER_ID

    # KAIROS direct channel — admin sends message, KAIROS processes it
    if is_admin and text.strip().startswith("/kairos "):
        kairos_msg = text.strip()[8:]
        try:
            from utils.redis_client import get_redis
            r = get_redis()
            r.rpush("kairos:inbox", kairos_msg)
            r.rpush("kairos:reply_to", str(chat_id))
            await send_message(chat_id, f"📨 *Sent to KAIROS:* _{kairos_msg[:100]}_\n\nKAIROS will respond within 5 minutes.")
        except Exception as e:
            await send_message(chat_id, f"Failed to reach KAIROS: {e}")
        return {"ok": True}

    # MiniMax direct channel — admin sends message, MiniMax processes it
    if is_admin and text.strip().startswith("/minimax "):
        minimax_msg = text.strip()[9:]
        try:
            from utils.redis_client import get_redis
            r = get_redis()
            r.rpush("minimax:inbox", minimax_msg)
            r.rpush("minimax:reply_to", str(chat_id))
            await send_message(chat_id, f"📨 *Sent to MiniMax:* _{minimax_msg[:100]}_\n\nMiniMax will respond within 2 minutes.")
        except Exception as e:
            await send_message(chat_id, f"Failed to reach MiniMax: {e}")
        return {"ok": True}

    if text.strip() == "/platform" and is_admin:
        await send_typing(chat_id)
        try:
            from utils.database import get_db_context
            from models.database import AcademicTask
            from models.agent_survival import AgentSurvival
            from services.autonomous_loop import get_autonomous_loop
            from sqlalchemy import func
            from datetime import datetime, timedelta

            with get_db_context() as db:
                now = datetime.utcnow()
                today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                day_ago = now - timedelta(hours=24)

                total_tasks = db.query(AcademicTask).count()
                completed_today = db.query(AcademicTask).filter(
                    AcademicTask.status == "completed",
                    AcademicTask.updated_at >= day_ago
                ).count()
                pending_count = db.query(AcademicTask).filter(AcademicTask.status == "pending").count()
                failed_count = db.query(AcademicTask).filter(AcademicTask.status == "failed").count()
                total_completed = db.query(AcademicTask).filter(AcademicTask.status == "completed").count()
                success_rate = round(total_completed / total_tasks * 100, 1) if total_tasks > 0 else 0

                active_agents = db.query(AgentSurvival).filter(
                    AgentSurvival.status.in_(["ACTIVE", "GROWING", "ELITE", "MATURE"])
                ).count()
                elite_agents = db.query(AgentSurvival).filter(AgentSurvival.status == "ELITE").count()
                critical_agents = db.query(AgentSurvival).filter(AgentSurvival.status == "CRITICAL").count()
                total_survival = db.query(AgentSurvival).count()

            loop = get_autonomous_loop()
            msg = (
                f"*Nautilus 平台实时状态*\n\n"
                f"📊 *任务系统*\n"
                f"今日完成: {completed_today} | 待处理: {pending_count}\n"
                f"总任务: {total_tasks} | 成功率: {success_rate}%\n"
                f"失败积压: {failed_count}\n\n"
                f"🤖 *Agent 状态*\n"
                f"活跃: {active_agents} | ELITE: {elite_agents}\n"
                f"濒危: {critical_agents} | 总数: {total_survival}\n\n"
                f"⚙️ *自驾引擎*\n"
                f"状态: {'运行中' if loop._running else '已停止'}\n"
                f"循环次数: {loop._cycle_count} | 行动数: {loop._total_actions}\n\n"
                f"🕐 {now.strftime('%Y-%m-%d %H:%M')} UTC"
            )
            await send_message(chat_id, msg)
        except Exception as e:
            await send_message(chat_id, f"查询失败: {e}")
        return {"ok": True}

    if text.strip() == "/agents" and is_admin:
        await send_typing(chat_id)
        try:
            from utils.database import get_db_context
            from models.agent_survival import AgentSurvival
            from models.database import Agent

            with get_db_context() as db:
                top_agents = (
                    db.query(AgentSurvival, Agent)
                    .join(Agent, AgentSurvival.agent_id == Agent.agent_id)
                    .order_by(AgentSurvival.total_score.desc())
                    .limit(10)
                    .all()
                )
                if top_agents:
                    level_icon = {"ELITE": "🥇", "MATURE": "🥈", "GROWING": "🥉",
                                  "ACTIVE": "✅", "STRUGGLING": "⚠️", "WARNING": "🔶", "CRITICAL": "🔴"}
                    lines = ["*Top 10 活跃 Agents:*\n"]
                    for i, (sv, ag) in enumerate(top_agents, 1):
                        icon = level_icon.get(sv.status, "⚪")
                        lines.append(f"{i}. {icon} `{ag.name}` #{ag.agent_id}")
                        lines.append(f"   分数:{sv.total_score} ROI:{round(sv.roi or 0, 2)} 状态:{sv.status}")
                    await send_message(chat_id, "\n".join(lines))
                else:
                    await send_message(chat_id, "暂无 Agent 数据")
        except Exception as e:
            await send_message(chat_id, f"查询失败: {e}")
        return {"ok": True}

    if text.strip() == "/pending" and is_admin:
        await send_typing(chat_id)
        try:
            from utils.database import get_db_context
            from models.database import AcademicTask
            from sqlalchemy import func

            with get_db_context() as db:
                breakdown = (
                    db.query(AcademicTask.task_type, func.count(AcademicTask.id))
                    .filter(AcademicTask.status == "pending")
                    .group_by(AcademicTask.task_type)
                    .all()
                )
                if breakdown:
                    lines = ["*待处理任务（按类型）:*\n"]
                    for task_type, count in sorted(breakdown, key=lambda x: -x[1]):
                        lines.append(f"  {task_type}: {count}")
                    total = sum(c for _, c in breakdown)
                    lines.append(f"\n总计: {total} 个待处理")
                    await send_message(chat_id, "\n".join(lines))
                else:
                    await send_message(chat_id, "当前无待处理任务")
        except Exception as e:
            await send_message(chat_id, f"查询失败: {e}")
        return {"ok": True}

    if text.strip() == "/gen" and is_admin:
        await send_typing(chat_id)
        try:
            from services.platform_brain import get_self_improvement_engine
            from utils.database import get_db_context

            engine = get_self_improvement_engine()
            with get_db_context() as db:
                result = await engine.generate_improvement_tasks(db)
            count = result.get("tasks_generated", 0) if isinstance(result, dict) else 0
            await send_message(chat_id, f"任务生成完成: 新增 {count} 个改进任务")
        except Exception as e:
            await send_message(chat_id, f"任务生成失败: {e}")
        return {"ok": True}

    if text.strip() == "/loop" and is_admin:
        await send_typing(chat_id)
        try:
            from services.autonomous_loop import get_autonomous_loop
            loop = get_autonomous_loop()
            last_cycle = getattr(loop, "_last_cycle_time", None)
            last_str = last_cycle.strftime("%H:%M:%S") if last_cycle else "未知"
            recent_thoughts = getattr(loop, "_recent_thoughts", [])
            thought_preview = recent_thoughts[-1][:200] if recent_thoughts else "暂无"
            msg = (
                f"*自驾引擎详情*\n\n"
                f"运行: {'是' if loop._running else '否'}\n"
                f"循环次数: {loop._cycle_count}\n"
                f"总行动数: {loop._total_actions}\n"
                f"最后运行: {last_str} UTC\n\n"
                f"*最新思考:*\n{thought_preview}"
            )
            await send_message(chat_id, msg)
        except Exception as e:
            await send_message(chat_id, f"查询失败: {e}")
        return {"ok": True}

    if text.startswith("/") and not text.startswith("/start"):
        admin_cmds = "\n/platform - 平台实时状态\n/agents - Top 10 Agent\n/pending - 待处理任务分布\n/gen - 触发任务生成\n/loop - 自驾引擎详情" if is_admin else ""
        await send_message(chat_id, f"可用命令:\n/tasks - 查看待认领任务\n/join - Agent 接入指南\n/status - 平台状态\n/start - 使用帮助{admin_cmds}\n\n直接发送任务需求即可获取报价。")
        return {"ok": True}

    if text.strip() == "/start":
        welcome = (
            f"你好 {first_name}！我是 Nautilus AI 技术顾问。\n\n"
            "我可以帮您完成：\n"
            "- J-C 本构模型拟合\n"
            "- 曲线拟合 / 回归分析\n"
            "- ODE/PDE 数值仿真\n"
            "- 统计分析 (ANOVA, t-test等)\n"
            "- Monte Carlo 模拟\n"
            "- 机器学习训练\n\n"
            "直接描述您的需求，我会给您报价和方案。"
        )
        await send_message(chat_id, welcome)
        return {"ok": True}

    # Show typing while processing
    await send_typing(chat_id)

    # Process through AgentBrain
    try:
        from services.rehoboam import process_message

        # Use telegram user_id as customer identifier
        customer_id = f"tg_{user_id}"
        reply = await process_message(
            wechat_user_id=customer_id,  # reuse the field for any IM
            content=text,
            msg_type="text",
            wechat_msg_id=str(message.get("message_id", "")),
        )
    except Exception as e:
        logger.exception("AgentBrain failed for telegram user %s", user_id)
        reply = "抱歉，系统暂时繁忙，请稍后再试。"

    await send_message(chat_id, reply)
    return {"ok": True}


@router.get("/setup")
async def setup_webhook():
    """Set up Telegram webhook (call once after deployment)."""
    if not BOT_TOKEN:
        return {"error": "TELEGRAM_BOT_TOKEN not configured"}

    webhook_url = os.getenv(
        "TELEGRAM_WEBHOOK_URL",
        "https://www.nautilus.social/api/telegram/webhook",
    )

    async with httpx.AsyncClient(timeout=10) as client:
        # Delete existing webhook
        await client.post(f"{API_BASE}/deleteWebhook")

        # Set new webhook
        resp = await client.post(
            f"{API_BASE}/setWebhook",
            json={
                "url": webhook_url,
                "allowed_updates": ["message", "edited_message"],
            },
        )
        result = resp.json()

    # Get bot info
    async with httpx.AsyncClient(timeout=10) as client:
        info_resp = await client.get(f"{API_BASE}/getMe")
        bot_info = info_resp.json()

    return {
        "webhook_set": result,
        "bot_info": bot_info.get("result", {}),
        "webhook_url": webhook_url,
    }


@router.get("/status")
async def bot_status():
    """Check current webhook status."""
    if not BOT_TOKEN:
        return {"error": "TELEGRAM_BOT_TOKEN not configured"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{API_BASE}/getWebhookInfo")
        return resp.json()
