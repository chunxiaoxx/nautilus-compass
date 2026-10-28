"""
NMACS Module - 节点间通信协议
预留接口，用于未来实现节点间通信
"""
from typing import Dict, Optional, Callable
import asyncio


class Message:
    """消息对象"""

    def __init__(self, sender: str, receiver: str, content: Dict, msg_type: str = "default"):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.msg_type = msg_type


class NMACSProtocol:
    """NMACS 通信协议"""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.handlers: Dict[str, Callable] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()

    def register_handler(self, msg_type: str, handler: Callable):
        """注册消息处理器"""
        self.handlers[msg_type] = handler

    async def send(self, receiver: str, content: Dict, msg_type: str = "default"):
        """发送消息"""
        message = Message(self.node_id, receiver, content, msg_type)
        # 实际实现需要网络传输
        await self.message_queue.put(message)

    async def receive(self) -> Optional[Message]:
        """接收消息"""
        try:
            message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
            return message
        except asyncio.TimeoutError:
            return None

    async def handle_message(self, message: Message):
        """处理消息"""
        handler = self.handlers.get(message.msg_type)
        if handler:
            await handler(message)


__all__ = ["Message", "NMACSProtocol"]
