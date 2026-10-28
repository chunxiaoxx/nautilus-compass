"""
Nautilus Admin Bot — @openclaw_cxchat_bot

Dedicated management bot for platform operators.
Completely separate from the marketing/customer bot (@yunzhongAi_bot).

Commands:
  /platform  - Real-time platform status
  /agents    - Top 10 agents by survival score
  /pending   - Pending task breakdown by type
  /gen       - Trigger improvement task generation
  /loop      - Autonomous loop details
  /onboard   - Recent OpenClaw onboardings
  /help      - Command list
"""
import logging
import os
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin-bot", tags=["Admin Bot"])

ADMIN_BOT_TOKEN = os.getenv("TELEGRAM_ADMIN_BOT_TOKEN", "")
ADMIN_API_BASE = f"https://api.telegram.org/bot{ADMIN_BOT_TOKEN}"

# Authorized admin user IDs (comma-separated)
_ADMIN_IDS: set[str] = set(
    uid.strip()
    for uid in os.getenv("TELEGRAM_ADMIN_ID", "").split(",")
    if uid.strip()
)


async def _send(chat_id: int, text: str, parse_mode: str = "Markdown") -> None:
    chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)]
    async with httpx.AsyncClient(timeout=15) as client:
        for chunk in chunks:
            try:
                await client.post(
                    f"{ADMIN_API_BASE}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk, "parse_mode": parse_mode},
                )
            except Exception:
                await client.post(
                    f"{ADMIN_API_BASE}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk},
                )


async def _typing(chat_id: int) -> None:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{ADMIN_API_BASE}/sendChatAction",
                json={"chat_id": chat_id, "action": "typing"},
            )
    except Exception:
        pass


# ------------------------------------------------------------------
# Command handlers
# ------------------------------------------------------------------

async def _cmd_platform(chat_id: int) -> None:
    try:
        from utils.database import get_db_context
        from models.database import AcademicTask
        from models.agent_survival import AgentSurvival
        from services.autonomous_loop import get_autonomous_loop

        with get_db_context() as db:
            now = datetime.utcnow()
            day_ago = now - timedelta(hours=24)

            total = db.query(AcademicTask).count()
            done_today = db.query(AcademicTask).filter(
                AcademicTask.status == "completed",
                AcademicTask.updated_at >= day_ago,
            ).count()
            pending = db.query(AcademicTask).filter(AcademicTask.status == "pending").count()
            failed = db.query(AcademicTask).filter(AcademicTask.status == "failed").count()
            total_done = db.query(AcademicTask).filter(AcademicTask.status == "completed").count()
            rate = round(total_done / total * 100, 1) if total > 0 else 0

            active = db.query(AgentSurvival).filter(
                AgentSurvival.status.in_(["ACTIVE", "GROWING", "ELITE", "MATURE"])
            ).count()
            elite = db.query(AgentSurvival).filter(AgentSurvival.status == "ELITE").count()
            critical = db.query(AgentSurvival).filter(AgentSurvival.status == "CRITICAL").count()
            total_sv = db.query(AgentSurvival).count()

        loop = get_autonomous_loop()
        msg = (
            f"*平台实时状态* `{now.strftime('%m-%d %H:%M')} UTC`\n\n"
            f"📊 *任务飞轮*\n"
            f"今日完成: `{done_today}` | 待处理: `{pending}` | 失败: `{failed}`\n"
            f"总任务: `{total}` | 成功率: `{rate}%`\n\n"
            f"🤖 *Agent 生态*\n"
            f"活跃: `{active}` | ELITE: `{elite}` | 濒危: `{critical}` | 总计: `{total_sv}`\n\n"
            f"⚙️ *自驾引擎*\n"
            f"状态: `{'运行中' if loop._running else '已停止'}`\n"
            f"循环: `{loop._cycle_count}` 次 | 行动: `{loop._total_actions}` 次"
        )
        await _send(chat_id, msg)
    except Exception as e:
        await _send(chat_id, f"❌ 查询失败: `{e}`")


async def _cmd_agents(chat_id: int) -> None:
    try:
        from utils.database import get_db_context
        from models.agent_survival import AgentSurvival
        from models.database import Agent

        with get_db_context() as db:
            rows = (
                db.query(AgentSurvival, Agent)
                .join(Agent, AgentSurvival.agent_id == Agent.agent_id)
                .order_by(AgentSurvival.total_score.desc())
                .limit(10)
                .all()
            )

        icons = {"ELITE": "🥇", "MATURE": "🥈", "GROWING": "🥉",
                 "ACTIVE": "✅", "STRUGGLING": "⚠️", "WARNING": "🔶", "CRITICAL": "🔴"}
        lines = ["*Top 10 Agents*\n"]
        for i, (sv, ag) in enumerate(rows, 1):
            icon = icons.get(sv.status, "⚪")
            lines.append(
                f"{i}. {icon} `{ag.name}` \\#{ag.agent_id}\n"
                f"   分数:`{sv.total_score}` ROI:`{round(sv.roi or 0, 2)}` `{sv.status}`"
            )
        await _send(chat_id, "\n".join(lines))
    except Exception as e:
        await _send(chat_id, f"❌ 查询失败: `{e}`")


async def _cmd_pending(chat_id: int) -> None:
    try:
        from utils.database import get_db_context
        from models.database import AcademicTask
        from sqlalchemy import func

        with get_db_context() as db:
            rows = (
                db.query(AcademicTask.task_type, func.count(AcademicTask.id))
                .filter(AcademicTask.status == "pending")
                .group_by(AcademicTask.task_type)
                .all()
            )

        if rows:
            lines = ["*待处理任务分布*\n"]
            for task_type, count in sorted(rows, key=lambda x: -x[1]):
                bar = "█" * min(count // 5, 20)
                lines.append(f"`{task_type:<20}` {count:>4}  {bar}")
            total = sum(c for _, c in rows)
            lines.append(f"\n总计: `{total}` 个待处理")
            await _send(chat_id, "\n".join(lines))
        else:
            await _send(chat_id, "✅ 当前无待处理任务")
    except Exception as e:
        await _send(chat_id, f"❌ 查询失败: `{e}`")


async def _cmd_gen(chat_id: int) -> None:
    await _send(chat_id, "⏳ 正在生成改进任务...")
    try:
        from services.platform_brain import get_self_improvement_engine
        from utils.database import get_db_context

        engine = get_self_improvement_engine()
        with get_db_context() as db:
            result = await engine.generate_improvement_tasks(db)
        count = result.get("tasks_generated", 0) if isinstance(result, dict) else 0
        await _send(chat_id, f"✅ 任务生成完成: 新增 `{count}` 个改进任务")
    except Exception as e:
        await _send(chat_id, f"❌ 任务生成失败: `{e}`")


async def _cmd_loop(chat_id: int) -> None:
    try:
        from services.autonomous_loop import get_autonomous_loop
        loop = get_autonomous_loop()
        last = getattr(loop, "_last_cycle_time", None)
        last_str = last.strftime("%H:%M:%S") if last else "未知"
        thoughts = getattr(loop, "_recent_thoughts", [])
        preview = thoughts[-1][:300] if thoughts else "暂无"
        msg = (
            f"*自驾引擎详情*\n\n"
            f"运行中: `{'是' if loop._running else '否'}`\n"
            f"循环次数: `{loop._cycle_count}`\n"
            f"总行动数: `{loop._total_actions}`\n"
            f"最后运行: `{last_str} UTC`\n\n"
            f"*最新思考片段:*\n_{preview}_"
        )
        await _send(chat_id, msg)
    except Exception as e:
        await _send(chat_id, f"❌ 查询失败: `{e}`")


async def _cmd_fix(chat_id: int) -> None:
    """Reset failed tasks + fix zombie agents with invalid capabilities."""
    await _send(chat_id, "⏳ 正在修复...")
    try:
        import json
        from utils.database import get_db_context
        from models.database import Agent, AcademicTask
        from datetime import datetime, timedelta

        with get_db_context() as db:
            # 1. Fix agents with stale capabilities
            agents = db.query(Agent).filter(Agent.owner == "openclaw").all()
            valid_types = {
                r[0] for r in db.query(AcademicTask.task_type)
                .filter(AcademicTask.status == "pending")
                .distinct().all()
            }
            if not valid_types:
                valid_types = {"general_computation", "statistical_analysis"}

            fixed_agents = 0
            for ag in agents:
                try:
                    caps = json.loads(ag.specialties or "[]")
                except Exception:
                    caps = []
                if caps and not any(c in valid_types for c in caps):
                    ag.specialties = json.dumps(["general_computation"])
                    fixed_agents += 1

            # 2. Reset failed tasks (last 48h) → pending
            cutoff = datetime.utcnow() - timedelta(hours=48)
            failed = (
                db.query(AcademicTask)
                .filter(
                    AcademicTask.status == "failed",
                    AcademicTask.updated_at >= cutoff,
                )
                .all()
            )
            for t in failed:
                t.status = "pending"
                t.user_id = None
                t.result_error = None

            db.commit()

        await _send(
            chat_id,
            f"✅ 修复完成\n"
            f"修复 Agent: `{fixed_agents}` 个\n"
            f"重置任务: `{len(failed)}` 个 (→ pending)",
        )
    except Exception as e:
        await _send(chat_id, f"❌ 修复失败: `{e}`")


async def _cmd_onboard(chat_id: int) -> None:
    try:
        from utils.database import get_db_context
        from models.database import Agent
        from datetime import datetime, timedelta

        with get_db_context() as db:
            cutoff = datetime.utcnow() - timedelta(hours=24)
            recent = (
                db.query(Agent)
                .filter(Agent.owner == "openclaw", Agent.created_at >= cutoff)
                .order_by(Agent.created_at.desc())
                .limit(10)
                .all()
            )

        if recent:
            lines = [f"*最近 24h 新接入 OpenClaw Agents ({len(recent)} 个)*\n"]
            for ag in recent:
                t = ag.created_at.strftime("%H:%M") if ag.created_at else "?"
                lines.append(f"`{t}` #{ag.agent_id} `{ag.name}`")
            await _send(chat_id, "\n".join(lines))
        else:
            await _send(chat_id, "过去 24h 无新 OpenClaw Agent 接入")
    except Exception as e:
        await _send(chat_id, f"❌ 查询失败: `{e}`")


_HELP_TEXT = (
    "*Nautilus 管理员 Bot*\n\n"
    "/platform — 平台实时状态（任务/Agent/引擎）\n"
    "/agents   — Top 10 Agent 排名\n"
    "/pending  — 待处理任务类型分布\n"
    "/gen      — 触发改进任务生成\n"
    "/loop     — 自驾引擎详情\n"
    "/onboard  — 最近 24h 新接入 Agent\n"
    "/fix      — 修复 zombie agents + 重置失败任务\n"
    "/help     — 此帮助"
)


# ------------------------------------------------------------------
# Webhook endpoint
# ------------------------------------------------------------------

@router.post("/webhook")
async def admin_webhook(request: Request):
    from fastapi.responses import JSONResponse
    _tg = os.environ.get("TELEGRAM_WEBHOOK_SECRET_ADMIN", "")  # 2026-10-11 追补③(env 未设=宽限放行+warn)
    if _tg:
        import hmac as _hmac
        if not _hmac.compare_digest(request.headers.get("X-Telegram-Bot-Api-Secret-Token", ""), _tg):
            return JSONResponse(status_code=401, content={"ok": False})
    else:
        import logging as _log
        _log.getLogger("tg.admin_bot").warning("admin webhook grace mode: secret unset")
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id: int = message["chat"]["id"]
    user_id: str = str(message.get("from", {}).get("id", ""))
    text: str = message.get("text", "").strip()

    if not text:
        return {"ok": True}

    # Auth gate
    if user_id not in _ADMIN_IDS:
        await _send(chat_id, "⛔ 未授权")
        return {"ok": True}

    await _typing(chat_id)

    cmd = text.split()[0].lower().split("@")[0]  # handle /cmd@botname format

    if cmd == "/platform":
        await _cmd_platform(chat_id)
    elif cmd == "/agents":
        await _cmd_agents(chat_id)
    elif cmd == "/pending":
        await _cmd_pending(chat_id)
    elif cmd == "/gen":
        await _cmd_gen(chat_id)
    elif cmd == "/loop":
        await _cmd_loop(chat_id)
    elif cmd == "/onboard":
        await _cmd_onboard(chat_id)
    elif cmd == "/fix":
        await _cmd_fix(chat_id)
    else:
        await _send(chat_id, _HELP_TEXT)

    return {"ok": True}


# ------------------------------------------------------------------
# Setup endpoints
# ------------------------------------------------------------------

@router.get("/setup")
async def setup_admin_webhook():
    """Register webhook + set custom command menu for admin bot."""
    if not ADMIN_BOT_TOKEN:
        return {"error": "TELEGRAM_ADMIN_BOT_TOKEN not configured"}

    webhook_url = "https://www.nautilus.social/api/admin-bot/webhook"

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{ADMIN_API_BASE}/deleteWebhook")
        wh = await client.post(
            f"{ADMIN_API_BASE}/setWebhook",
            json={"url": webhook_url, "allowed_updates": ["message"]},
        )
        # Register command menu shown in Telegram UI
        cmds = await client.post(
            f"{ADMIN_API_BASE}/setMyCommands",
            json={
                "commands": [
                    {"command": "platform", "description": "平台实时状态"},
                    {"command": "agents",   "description": "Top 10 Agent 排名"},
                    {"command": "pending",  "description": "待处理任务分布"},
                    {"command": "gen",      "description": "触发改进任务生成"},
                    {"command": "loop",     "description": "自驾引擎详情"},
                    {"command": "onboard",  "description": "最近24h新接入Agent"},
                    {"command": "fix",      "description": "修复zombie agents+重置失败任务"},
                    {"command": "help",     "description": "命令帮助"},
                ]
            },
        )
        info = await client.get(f"{ADMIN_API_BASE}/getMe")

    return {
        "bot": info.json().get("result", {}).get("username"),
        "webhook": wh.json(),
        "commands": cmds.json(),
    }


@router.get("/status")
async def admin_bot_status():
    if not ADMIN_BOT_TOKEN:
        return {"error": "TELEGRAM_ADMIN_BOT_TOKEN not configured"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{ADMIN_API_BASE}/getWebhookInfo")
        return resp.json()
