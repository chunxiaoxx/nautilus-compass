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

    # --- Handle non-text messages: reply with upload link ---
    _UPLOAD_HINT = (
        "我暂时无法直接接收文件/图片。请通过网页上传：\n\n"
        "https://www.nautilus.social/api/upload\n\n"
        "上传后回来告诉我文件内容即可。"
    )
    if msg_type in ("image", "file", "attachment", "voice", "video"):
        logger.info("Non-text message from %s: type=%s", from_user, msg_type)
        import asyncio
        asyncio.ensure_future(send_text_message(from_user, _UPLOAD_HINT))
        return Response(content="", status_code=200)
    elif msg_type == "event":
        return Response(content="", status_code=200)
    elif msg_type != "text" or not content:
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
