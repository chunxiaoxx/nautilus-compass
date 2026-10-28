"""
Enterprise WeChat Bot - WebSocket long connection.

Maintains a persistent WebSocket connection to Enterprise WeChat,
receives messages, processes them via AgentBrain, and replies.

Protocol:
1. Connect via wss:// to Enterprise WeChat
2. Authenticate with aibot_subscribe + BotID + Secret
3. Maintain heartbeat every 30s
4. Receive user messages as JSON
5. Reply via the same connection or REST API

Usage:
    python -m services.wechat_ws_bot
"""
import asyncio
import json
import logging
import os
import signal
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration
BOT_ID = os.getenv("WECHAT_BOT_ID", "")
BOT_SECRET = os.getenv("WECHAT_BOT_SECRET", "")
WS_URL = os.getenv(
    "WECHAT_WS_URL",
    "wss://bot.work.weixin.qq.com/ws",
)
HEARTBEAT_INTERVAL = 25  # seconds (server expects 30s, we send early)
RECONNECT_DELAY = 5  # seconds before reconnect attempt
MAX_RECONNECT_DELAY = 60


class WeChatWSBot:
    """WebSocket-based Enterprise WeChat bot with auto-reconnect."""

    def __init__(
        self,
        bot_id: str = "",
        bot_secret: str = "",
        ws_url: str = "",
    ):
        self.bot_id = bot_id or BOT_ID
        self.bot_secret = bot_secret or BOT_SECRET
        self.ws_url = ws_url or WS_URL
        self._ws = None
        self._running = False
        self._reconnect_delay = RECONNECT_DELAY

        if not self.bot_id or not self.bot_secret:
            raise ValueError(
                "WECHAT_BOT_ID and WECHAT_BOT_SECRET must be set"
            )

    async def start(self) -> None:
        """Start the bot with auto-reconnect loop."""
        self._running = True
        logger.info("WeChatWSBot starting: bot_id=%s", self.bot_id)

        while self._running:
            try:
                await self._connect_and_run()
            except Exception as e:
                logger.error("WebSocket error: %s", e)

            if self._running:
                logger.info(
                    "Reconnecting in %ds...", self._reconnect_delay
                )
                await asyncio.sleep(self._reconnect_delay)
                # Exponential backoff capped at MAX_RECONNECT_DELAY
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, MAX_RECONNECT_DELAY
                )

    async def stop(self) -> None:
        """Gracefully stop the bot."""
        self._running = False
        if self._ws:
            await self._ws.close()
        logger.info("WeChatWSBot stopped")

    async def _connect_and_run(self) -> None:
        """Single connection lifecycle."""
        try:
            import websockets
        except ImportError:
            logger.error("websockets package required: pip install websockets")
            raise

        logger.info("Connecting to %s ...", self.ws_url)
        async with websockets.connect(
            self.ws_url,
            ping_interval=None,  # We handle ping manually
            close_timeout=10,
        ) as ws:
            self._ws = ws
            self._reconnect_delay = RECONNECT_DELAY  # Reset on success
            logger.info("WebSocket connected")

            # Step 1: Subscribe (authenticate)
            await self._subscribe(ws)

            # Step 2: Run message loop + heartbeat
            heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))
            try:
                await self._message_loop(ws)
            finally:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

    async def _subscribe(self, ws) -> None:
        """Authenticate with the Enterprise WeChat server."""
        subscribe_msg = {
            "action": "aibot_subscribe",
            "data": {
                "bot_id": self.bot_id,
                "secret": self.bot_secret,
            },
        }
        await ws.send(json.dumps(subscribe_msg))
        logger.info("Sent aibot_subscribe")

        # Wait for subscribe response
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(resp)
            logger.info("Subscribe response: %s", data)

            if data.get("errcode", 0) != 0:
                raise RuntimeError(
                    f"Subscribe failed: {data.get('errmsg', 'unknown')}"
                )
        except asyncio.TimeoutError:
            logger.warning("No subscribe response within 10s, continuing...")

    async def _heartbeat_loop(self, ws) -> None:
        """Send periodic ping to keep connection alive."""
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            try:
                await ws.ping()
                logger.debug("Heartbeat ping sent")
            except Exception as e:
                logger.warning("Heartbeat failed: %s", e)
                break

    async def _message_loop(self, ws) -> None:
        """Receive and process messages."""
        async for raw_msg in ws:
            try:
                data = json.loads(raw_msg)
                msg_type = data.get("type", data.get("action", ""))

                logger.info(
                    "Received message: type=%s keys=%s",
                    msg_type, list(data.keys()),
                )

                # Skip system/ack messages
                if msg_type in ("ack", "pong", "subscribe_ack", ""):
                    continue

                # Handle user messages
                await self._handle_message(ws, data)

            except json.JSONDecodeError:
                logger.warning("Non-JSON message: %s", raw_msg[:200])
            except Exception:
                logger.exception("Error handling message")

    async def _handle_message(self, ws, data: dict) -> None:
        """Process a user message through AgentBrain and reply."""
        # Extract message content - adapt to actual protocol format
        content = (
            data.get("content", "")
            or data.get("data", {}).get("content", "")
            or data.get("data", {}).get("text", "")
            or data.get("text", "")
        )
        if not content:
            logger.debug("Empty content, skipping: %s", data)
            return

        # Extract user info
        user_id = (
            data.get("from", "")
            or data.get("data", {}).get("from", "")
            or data.get("data", {}).get("user_id", "")
            or "unknown"
        )
        msg_id = data.get("msg_id", data.get("data", {}).get("msg_id", ""))

        logger.info(
            "Processing message from %s: %s",
            user_id, content[:100],
        )

        # Call AgentBrain
        try:
            from services.agent_executor import process_message

            reply = await process_message(
                wechat_user_id=str(user_id),
                content=content,
                msg_type="text",
                wechat_msg_id=str(msg_id),
            )
        except Exception:
            logger.exception("AgentBrain failed for user %s", user_id)
            reply = "抱歉，我暂时遇到了一些问题，请稍后再试。"

        # Send reply
        await self._send_reply(ws, data, reply)

    async def _send_reply(self, ws, original_msg: dict, reply_text: str) -> None:
        """Send reply back via WebSocket."""
        # Build reply message - adapt to actual protocol format
        reply_msg = {
            "action": "send_message",
            "data": {
                "content": reply_text,
                "msg_type": "text",
            },
        }

        # Include conversation/chat context from original message
        chat_id = (
            original_msg.get("chat_id", "")
            or original_msg.get("data", {}).get("chat_id", "")
        )
        if chat_id:
            reply_msg["data"]["chat_id"] = chat_id

        reply_to = (
            original_msg.get("from", "")
            or original_msg.get("data", {}).get("from", "")
        )
        if reply_to:
            reply_msg["data"]["to"] = reply_to

        # Reply reference
        msg_id = original_msg.get("msg_id", original_msg.get("data", {}).get("msg_id", ""))
        if msg_id:
            reply_msg["data"]["reply_msg_id"] = msg_id

        await ws.send(json.dumps(reply_msg, ensure_ascii=False))
        logger.info("Reply sent: %s", reply_text[:100])

    async def send_proactive(self, user_id: str, content: str) -> None:
        """Send a proactive message (follow-up, notification, etc.)."""
        if not self._ws:
            logger.warning("Not connected, cannot send proactive message")
            return

        msg = {
            "action": "send_message",
            "data": {
                "to": user_id,
                "content": content,
                "msg_type": "text",
            },
        }
        await self._ws.send(json.dumps(msg, ensure_ascii=False))
        logger.info("Proactive message sent to %s: %s", user_id, content[:100])


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

async def run_bot() -> None:
    """Run the bot as a standalone service."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    bot = WeChatWSBot()

    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.stop()))
        except NotImplementedError:
            pass  # Windows doesn't support add_signal_handler

    await bot.start()


if __name__ == "__main__":
    asyncio.run(run_bot())
