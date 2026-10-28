"""
Enterprise WeChat (企业微信) integration for Nautilus.

Handles callback verification, message receiving/decrypting,
and proactive message sending via the Enterprise WeChat API.
"""

import base64
import hashlib
import logging
import os
import socket
import struct
import time
import xml.etree.ElementTree as ET
from typing import Optional

import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from fastapi import APIRouter, Query, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wechat", tags=["wechat"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CORP_ID = os.getenv("WECHAT_CORP_ID", "")
APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
TOKEN = os.getenv("WECHAT_TOKEN", "")
ENCODING_AES_KEY = os.getenv("WECHAT_ENCODING_AES_KEY", "")
AGENT_ID = int(os.getenv("WECHAT_AGENT_ID", "0"))

# Admin WeChat user IDs (comma-separated, e.g. "ChunXiong,admin2")
_ADMIN_WECHAT_USERS: set = set(
    u.strip() for u in os.getenv("WECHAT_ADMIN_USERS", "").split(",") if u.strip()
)

BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"

# In-memory token cache
_access_token: str = ""
_token_expires_at: float = 0.0


# ---------------------------------------------------------------------------
# Crypto via official wx_crypt library
# ---------------------------------------------------------------------------

def _get_wxcrypt():
    """Get WXBizMsgCrypt instance (lazy init)."""
    from wx_crypt import WXBizMsgCrypt
    return WXBizMsgCrypt(TOKEN, ENCODING_AES_KEY, CORP_ID)


def _encrypt(reply_xml: str) -> str:
    """Encrypt a reply XML string for Enterprise WeChat."""
    aes_key = _derive_aes_key()
    iv = aes_key[:16]

    msg_bytes = reply_xml.encode("utf-8")
    # 16 random bytes + 4-byte length + message + corp_id
    body = os.urandom(16) + struct.pack("!I", len(msg_bytes)) + msg_bytes + CORP_ID.encode("utf-8")

    padder = PKCS7(128).padder()
    padded = padder.update(body) + padder.finalize()

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(ciphertext).decode("utf-8")


# ---------------------------------------------------------------------------
# Access token management
# ---------------------------------------------------------------------------

async def _get_access_token() -> str:
    """Return a valid access_token, refreshing if expired."""
    global _access_token, _token_expires_at

    if _access_token and time.time() < _token_expires_at:
        return _access_token

    url = f"{BASE_URL}/gettoken"
    params = {"corpid": CORP_ID, "corpsecret": APP_SECRET}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("errcode", 0) != 0:
        logger.error("Failed to get access_token: %s", data)
        raise RuntimeError(f"WeChat token error: {data.get('errmsg')}")

    _access_token = data["access_token"]
    _token_expires_at = time.time() + data.get("expires_in", 7200) - 300  # refresh 5 min early
    logger.info("WeChat access_token refreshed, expires in %ss", data.get("expires_in"))
    return _access_token


# ---------------------------------------------------------------------------
# Proactive message sending
# ---------------------------------------------------------------------------

async def send_text_message(user_id: str, content: str) -> dict:
    """Send a text message to a user via Enterprise WeChat."""
    token = await _get_access_token()
    url = f"{BASE_URL}/message/send?access_token={token}"
    payload = {
        "touser": user_id,
        "msgtype": "text",
        "agentid": AGENT_ID,
        "text": {"content": content},
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    if data.get("errcode", 0) != 0:
        logger.error("send_text_message failed: %s", data)
    return data


async def send_markdown_message(user_id: str, content: str) -> dict:
    """Send a markdown message to a user via Enterprise WeChat."""
    token = await _get_access_token()
    url = f"{BASE_URL}/message/send?access_token={token}"
    payload = {
        "touser": user_id,
        "msgtype": "markdown",
        "agentid": AGENT_ID,
        "markdown": {"content": content},
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    if data.get("errcode", 0) != 0:
        logger.error("send_markdown_message failed: %s", data)
    return data


# ---------------------------------------------------------------------------
# Callback endpoints
# ---------------------------------------------------------------------------

@router.get("/callback")
async def verify_callback(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
):
    """URL verification endpoint for Enterprise WeChat."""
    wxcrypt = _get_wxcrypt()
    ret, reply_echo = wxcrypt.VerifyURL(msg_signature, timestamp, nonce, echostr)
    if ret != 0:
        logger.warning("verify_callback failed: ret=%d", ret)
        return Response(content="verification failed", status_code=403)
    return Response(content=reply_echo.decode("utf-8") if isinstance(reply_echo, bytes) else reply_echo, media_type="text/plain")


@router.post("/callback")
async def receive_message(
    request: Request,
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
):
    """Receive and process encrypted messages from Enterprise WeChat."""
    body = await request.body()
    body_str = body.decode("utf-8")

    # Decrypt using official wx_crypt library
    wxcrypt = _get_wxcrypt()
    ret, xml_str = wxcrypt.DecryptMsg(body_str, msg_signature, timestamp, nonce)
    if ret != 0:
        logger.error("Decryption failed: ret=%d", ret)
        return Response(content="decrypt error", status_code=400)

    if isinstance(xml_str, bytes):
        xml_str = xml_str.decode("utf-8")

    # Parse inner message XML
    msg_root = ET.fromstring(xml_str)
    from_user = msg_root.findtext("FromUserName", "")
    msg_type = msg_root.findtext("MsgType", "")
    content = msg_root.findtext("Content", "")
    msg_id = msg_root.findtext("MsgId", "")

    logger.info(
        "WeChat msg received: user=%s type=%s msg_id=%s content=%s",
        from_user, msg_type, msg_id, content[:80] if content else "",
    )

    # --- Handle non-text messages: reply with token-gated upload link ---
    if msg_type in ("image", "file", "attachment", "voice", "video"):
        logger.info("Non-text message from %s: type=%s", from_user, msg_type)
        from api.file_upload import generate_upload_token
        token = generate_upload_token(f"wecom_{from_user}")
        upload_url = f"https://www.nautilus.social/api/upload?token={token}"
        hint = (
            f"收到！请通过以下链接上传文件（15分钟内有效）：\n\n"
            f"{upload_url}\n\n"
            f"上传后回来告诉我文件内容即可。"
        )
        import asyncio
        asyncio.ensure_future(send_text_message(from_user, hint))
        return Response(content="", status_code=200)
    elif msg_type == "event":
        return Response(content="", status_code=200)
    elif msg_type != "text" or not content:
        return Response(content="", status_code=200)

    # --- ID discovery command (anyone can use, useful for admin setup) ---
    if content.strip() in ("我的ID", "myid", "/myid"):
        import asyncio
        asyncio.ensure_future(send_text_message(from_user, f"你的企微 userid 是：\n{from_user}"))
        return Response(content="", status_code=200)

    # --- Admin commands (keyword-based for WeChat) ---
    is_admin = from_user in _ADMIN_WECHAT_USERS
    if is_admin:
        cmd = content.strip()
        if cmd in ("平台状态", "status", "/platform"):
            import asyncio
            asyncio.ensure_future(_admin_platform_status(from_user))
            return Response(content="", status_code=200)
        if cmd in ("活跃agent", "agents", "/agents"):
            import asyncio
            asyncio.ensure_future(_admin_top_agents(from_user))
            return Response(content="", status_code=200)
        if cmd in ("待处理任务", "pending", "/pending"):
            import asyncio
            asyncio.ensure_future(_admin_pending_tasks(from_user))
            return Response(content="", status_code=200)
        if cmd in ("生成任务", "gen", "/gen"):
            import asyncio
            asyncio.ensure_future(_admin_gen_tasks(from_user))
            return Response(content="", status_code=200)
        if cmd in ("帮助", "help", "/help"):
            import asyncio
            asyncio.ensure_future(send_text_message(from_user,
                "管理员命令：\n平台状态 - 实时平台数据\n活跃agent - Top 10 Agent\n待处理任务 - 任务分布\n生成任务 - 触发任务生成\n\n其他消息将转给AI客服处理"))
            return Response(content="", status_code=200)

    # --- Dedup: prevent reprocessing within 30s window ---
    import hashlib
    dedup_key = hashlib.md5(f"{from_user}:{content[:200]}".encode()).hexdigest()
    if _is_recently_processed(dedup_key):
        logger.info("Dedup hit for user=%s, skipping", from_user)
        return Response(content="", status_code=200)
    _mark_processed(dedup_key)

    # --- Process in background to avoid WeChat 5s timeout ---
    import asyncio
    asyncio.ensure_future(_process_and_reply(from_user, content, msg_type, msg_id))

    # Return immediately so WeChat doesn't retry
    return Response(content="", status_code=200)


# ---------------------------------------------------------------------------
# Background processing + dedup helpers
# ---------------------------------------------------------------------------

import time as _time

_recent_messages: dict = {}  # dedup_key -> timestamp
_DEDUP_WINDOW = 30  # seconds


def _is_recently_processed(key: str) -> bool:
    """Check if this message was processed in the last DEDUP_WINDOW seconds."""
    now = _time.time()
    # Cleanup old entries
    stale = [k for k, t in _recent_messages.items() if now - t > _DEDUP_WINDOW * 2]
    for k in stale:
        del _recent_messages[k]
    return key in _recent_messages and now - _recent_messages[key] < _DEDUP_WINDOW


def _mark_processed(key: str):
    _recent_messages[key] = _time.time()


async def _process_and_reply(from_user: str, content: str, msg_type: str, msg_id: str):
    """Process message and send reply — runs in background."""
    try:
        from services.rehoboam import process_message

        reply_text = await process_message(
            wechat_user_id=f"wecom_{from_user}",
            content=content,
            msg_type=msg_type,
            wechat_msg_id=msg_id,
        )
    except Exception:
        logger.exception("process_message failed for wecom user %s", from_user)
        reply_text = "抱歉，系统暂时繁忙，请稍后再试。"

    try:
        await send_text_message(from_user, reply_text)
    except Exception:
        logger.exception("Failed to send reply to %s", from_user)


async def _download_and_describe_media(media_id: str, media_type: str) -> str:
    """Download media from WeChat CDN and return a text description."""
    if not media_id:
        return ""
    try:
        token = await _get_access_token()
        url = f"{BASE_URL}/media/get?access_token={token}&media_id={media_id}"
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning("Media download failed: status=%d", resp.status_code)
                return ""
            # Check if it's actually an error JSON response
            content_type = resp.headers.get("content-type", "")
            if "json" in content_type:
                data = resp.json()
                logger.warning("Media download error: %s", data)
                return ""
            # Save to temp file
            import tempfile
            suffix = ".jpg" if media_type == "image" else ".bin"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(resp.content)
                file_path = f.name
            file_size = len(resp.content)
            logger.info("Media downloaded: %s (%d bytes) -> %s", media_id, file_size, file_path)
            return f"(已下载，{file_size}字节，路径: {file_path})"
    except Exception as e:
        logger.warning("Media download failed: %s", e)
        return ""


# ---------------------------------------------------------------------------
# Admin command handlers (WeChat)
# ---------------------------------------------------------------------------

async def _admin_platform_status(from_user: str) -> None:
    """Send full platform status to admin user."""
    try:
        from utils.database import get_db_context
        from models.database import AcademicTask
        from models.agent_survival import AgentSurvival
        from services.autonomous_loop import get_autonomous_loop
        from datetime import datetime, timedelta

        with get_db_context() as db:
            now = datetime.utcnow()
            day_ago = now - timedelta(hours=24)

            total_tasks = db.query(AcademicTask).count()
            completed_today = db.query(AcademicTask).filter(
                AcademicTask.status == "completed",
                AcademicTask.updated_at >= day_ago
            ).count()
            pending_count = db.query(AcademicTask).filter(AcademicTask.status == "pending").count()
            total_completed = db.query(AcademicTask).filter(AcademicTask.status == "completed").count()
            success_rate = round(total_completed / total_tasks * 100, 1) if total_tasks > 0 else 0
            active_agents = db.query(AgentSurvival).filter(
                AgentSurvival.status.in_(["ACTIVE", "GROWING", "ELITE", "MATURE"])
            ).count()
            elite_agents = db.query(AgentSurvival).filter(AgentSurvival.status == "ELITE").count()
            critical_agents = db.query(AgentSurvival).filter(AgentSurvival.status == "CRITICAL").count()

        loop = get_autonomous_loop()
        msg = (
            f"Nautilus 平台状态 {now.strftime('%H:%M')} UTC\n\n"
            f"任务系统\n"
            f"今日完成: {completed_today} | 待处理: {pending_count}\n"
            f"总任务: {total_tasks} | 成功率: {success_rate}%\n\n"
            f"Agent 状态\n"
            f"活跃: {active_agents} | ELITE: {elite_agents} | 濒危: {critical_agents}\n\n"
            f"自驾引擎\n"
            f"状态: {'运行中' if loop._running else '已停止'}\n"
            f"循环: {loop._cycle_count} 次 | 行动: {loop._total_actions} 次"
        )
        await send_text_message(from_user, msg)
    except Exception as e:
        await send_text_message(from_user, f"查询失败: {e}")


async def _admin_top_agents(from_user: str) -> None:
    """Send top agents list to admin user."""
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
                lines = ["Top 10 活跃 Agents:\n"]
                for i, (sv, ag) in enumerate(top_agents, 1):
                    lines.append(
                        f"{i}. {ag.name} #{ag.agent_id}\n"
                        f"   分数:{sv.total_score} ROI:{round(sv.roi or 0, 2)} 状态:{sv.status}"
                    )
                await send_text_message(from_user, "\n".join(lines))
            else:
                await send_text_message(from_user, "暂无 Agent 数据")
    except Exception as e:
        await send_text_message(from_user, f"查询失败: {e}")


async def _admin_pending_tasks(from_user: str) -> None:
    """Send pending task breakdown to admin user."""
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
                lines = ["待处理任务分布:\n"]
                for task_type, count in sorted(breakdown, key=lambda x: -x[1]):
                    lines.append(f"  {task_type}: {count}")
                total = sum(c for _, c in breakdown)
                lines.append(f"\n总计: {total} 个")
                await send_text_message(from_user, "\n".join(lines))
            else:
                await send_text_message(from_user, "当前无待处理任务")
    except Exception as e:
        await send_text_message(from_user, f"查询失败: {e}")


async def _admin_gen_tasks(from_user: str) -> None:
    """Trigger task generation and notify admin."""
    try:
        from services.platform_brain import get_self_improvement_engine
        from utils.database import get_db_context

        await send_text_message(from_user, "正在生成改进任务...")
        engine = get_self_improvement_engine()
        with get_db_context() as db:
            result = await engine.generate_improvement_tasks(db)
        count = result.get("tasks_generated", 0) if isinstance(result, dict) else 0
        await send_text_message(from_user, f"任务生成完成: 新增 {count} 个改进任务")
    except Exception as e:
        await send_text_message(from_user, f"任务生成失败: {e}")
