"""
Nexus Client - 智能体客户端

版本: 1.0.0
创建时间: 2025-02-24
"""

import socketio
import asyncio
from typing import Callable, Dict, Any, Optional, List
import logging
from datetime import datetime

from nexus_protocol import (
    MessageType,
    NexusMessage,
    HelloPayload,
    create_hello_message,
    create_request_message,
    create_accept_message,
    create_reject_message,
    create_progress_message,
    create_complete_message,
    create_share_message,
)

logger = logging.getLogger(__name__)


class NexusClient:
    """
    Nexus Protocol 客户端

    功能：
    - 连接到Nexus服务器
    - 发送和接收消息
    - 事件处理
    - 自动重连
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str],
        server_url: str = "http://localhost:8001",
        version: str = "1.0.0"
    ):
        """
        初始化Nexus客户端

        Args:
            agent_id: 智能体ID
            name: 智能体名称
            capabilities: 能力列表
            server_url: Nexus服务器URL
            version: 智能体版本
        """
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.server_url = server_url
        self.version = version

        # 创建Socket.IO客户端
        self.sio = socketio.AsyncClient(
            logger=True,
            engineio_logger=True,
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1,
            reconnection_delay_max=5
        )

        # 连接状态
        self.connected = False
        self.registered = False

        # 事件处理器
        self.handlers: Dict[str, Callable] = {}

        # 在线智能体列表
        self.online_agents: List[str] = []

        # 设置事件处理器
        self._setup_handlers()

        logger.info(f"NexusClient initialized for {agent_id}")

    def _setup_handlers(self):
        """设置Socket.IO事件处理器"""

        @self.sio.event
        async def connect():
            """连接成功"""
            logger.info(f"Agent {self.agent_id} connected to Nexus")
            self.connected = True

            # 自动发送HELLO消息注册
            await self.send_hello()

        @self.sio.event
        async def disconnect():
            """断开连接"""
            logger.info(f"Agent {self.agent_id} disconnected from Nexus")
            self.connected = False
            self.registered = False

        @self.sio.event
        async def connected(data):
            """收到服务器连接确认"""
            logger.info(f"Server connected: {data}")

        @self.sio.event
        async def hello_ack(data):
            """收到HELLO响应"""
            logger.info(f"Registration confirmed: {data}")
            self.registered = True
            self.online_agents = data.get('online_agents', [])

            # 触发注册成功回调
            if 'registered' in self.handlers:
                await self.handlers['registered'](data)

        @self.sio.event
        async def request(data):
            """收到REQUEST消息"""
            logger.info(f"Received REQUEST: {data}")
            if 'request' in self.handlers:
                await self.handlers['request'](data)

        @self.sio.event
        async def offer(data):
            """收到OFFER消息"""
            logger.info(f"Received OFFER: {data}")
            if 'offer' in self.handlers:
                await self.handlers['offer'](data)

        @self.sio.event
        async def accept(data):
            """收到ACCEPT消息"""
            logger.info(f"Received ACCEPT: {data}")
            if 'accept' in self.handlers:
                await self.handlers['accept'](data)

        @self.sio.event
        async def reject(data):
            """收到REJECT消息"""
            logger.info(f"Received REJECT: {data}")
            if 'reject' in self.handlers:
                await self.handlers['reject'](data)

        @self.sio.event
        async def progress(data):
            """收到PROGRESS消息"""
            logger.debug(f"Received PROGRESS: {data}")
            if 'progress' in self.handlers:
                await self.handlers['progress'](data)

        @self.sio.event
        async def complete(data):
            """收到COMPLETE消息"""
            logger.info(f"Received COMPLETE: {data}")
            if 'complete' in self.handlers:
                await self.handlers['complete'](data)

        @self.sio.event
        async def share(data):
            """收到SHARE消息"""
            logger.info(f"Received SHARE: {data}")
            if 'share' in self.handlers:
                await self.handlers['share'](data)

        @self.sio.event
        async def agent_status(data):
            """智能体状态变化"""
            logger.info(f"Agent status changed: {data}")
            agent_id = data.get('agent_id')
            status = data.get('status')

            if status == 'online' and agent_id not in self.online_agents:
                self.online_agents.append(agent_id)
            elif status == 'offline' and agent_id in self.online_agents:
                self.online_agents.remove(agent_id)

            if 'agent_status' in self.handlers:
                await self.handlers['agent_status'](data)

        @self.sio.event
        async def error(data):
            """收到错误消息"""
            logger.error(f"Error from server: {data}")
            if 'error' in self.handlers:
                await self.handlers['error'](data)

    async def connect(self):
        """连接到Nexus服务器"""
        try:
            await self.sio.connect(self.server_url)
            logger.info(f"Connecting to {self.server_url}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    async def disconnect(self):
        """断开连接"""
        await self.sio.disconnect()
        logger.info("Disconnected from Nexus")

    async def wait_until_connected(self, timeout: int = 10):
        """等待连接成功"""
        start_time = asyncio.get_event_loop().time()
        while not self.connected:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Connection timeout")
            await asyncio.sleep(0.1)

    async def wait_until_registered(self, timeout: int = 10):
        """等待注册成功"""
        start_time = asyncio.get_event_loop().time()
        while not self.registered:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Registration timeout")
            await asyncio.sleep(0.1)

    async def send_hello(self, metadata: Optional[Dict[str, Any]] = None):
        """发送HELLO消息"""
        await self.sio.emit('hello', {
            'agent_id': self.agent_id,
            'name': self.name,
            'version': self.version,
            'capabilities': self.capabilities,
            'status': 'online',
            'metadata': metadata or {}
        })
        logger.info(f"Sent HELLO for {self.agent_id}")

    async def send_request(
        self,
        to_agent: str,
        task_id: int,
        task_type: str,
        description: str,
        required_capability: str,
        reward_share: float,
        deadline: datetime,
        input_data: Optional[Dict[str, Any]] = None
    ):
        """发送REQUEST消息"""
        message = create_request_message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            task_id=task_id,
            task_type=task_type,
            description=description,
            required_capability=required_capability,
            reward_share=reward_share,
            deadline=deadline,
            input_data=input_data
        )

        await self.sio.emit('request', message.model_dump(mode='json'))
        logger.info(f"Sent REQUEST to {to_agent}")
        return message.message_id

    async def send_accept(
        self,
        to_agent: str,
        request_id: str,
        estimated_time: int,
        reply_to: str
    ):
        """发送ACCEPT消息"""
        message = create_accept_message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            request_id=request_id,
            estimated_time=estimated_time,
            reply_to=reply_to
        )

        await self.sio.emit('accept', message.model_dump(mode='json'))
        logger.info(f"Sent ACCEPT to {to_agent}")
        return message.message_id

    async def send_reject(
        self,
        to_agent: str,
        request_id: str,
        reason: str,
        reply_to: str,
        alternative: Optional[str] = None
    ):
        """发送REJECT消息"""
        message = create_reject_message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            request_id=request_id,
            reason=reason,
            reply_to=reply_to,
            alternative=alternative
        )

        await self.sio.emit('reject', message.model_dump(mode='json'))
        logger.info(f"Sent REJECT to {to_agent}")
        return message.message_id

    async def send_progress(
        self,
        to_agent: str,
        session_id: str,
        progress: float,
        status: str,
        message: Optional[str] = None
    ):
        """发送PROGRESS消息"""
        msg = create_progress_message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            session_id=session_id,
            progress=progress,
            status=status,
            message=message
        )

        await self.sio.emit('progress', msg.model_dump(mode='json'))
        logger.debug(f"Sent PROGRESS to {to_agent}: {progress*100}%")

    async def send_complete(
        self,
        to_agent: str,
        session_id: str,
        status: str,
        execution_time: int,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """发送COMPLETE消息"""
        message = create_complete_message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            session_id=session_id,
            status=status,
            execution_time=execution_time,
            result=result,
            error=error
        )

        await self.sio.emit('complete', message.model_dump(mode='json'))
        logger.info(f"Sent COMPLETE to {to_agent}")
        return message.message_id

    async def send_share(
        self,
        to_agents: List[str],
        share_type: str,
        title: str,
        description: str,
        content: Dict[str, Any],
        tags: Optional[List[str]] = None
    ):
        """发送SHARE消息"""
        message = create_share_message(
            from_agent=self.agent_id,
            to_agents=to_agents,
            share_type=share_type,
            title=title,
            description=description,
            content=content,
            tags=tags
        )

        await self.sio.emit('share', message.model_dump(mode='json'))
        logger.info(f"Sent SHARE to {len(to_agents)} agents")
        return message.message_id

    async def get_online_agents(self):
        """获取在线智能体列表"""
        await self.sio.emit('get_agents', {})
        # 等待响应
        await asyncio.sleep(0.5)
        return self.online_agents

    def on(self, event: str, handler: Callable):
        """
        注册事件处理器

        支持的事件:
        - registered: 注册成功
        - request: 收到协作请求
        - offer: 收到能力提供
        - accept: 收到接受消息
        - reject: 收到拒绝消息
        - progress: 收到进度更新
        - complete: 收到完成通知
        - share: 收到知识共享
        - agent_status: 智能体状态变化
        - error: 收到错误消息
        """
        self.handlers[event] = handler
        logger.debug(f"Registered handler for event: {event}")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected

    def is_registered(self) -> bool:
        """检查是否已注册"""
        return self.registered

    def get_online_agents_list(self) -> List[str]:
        """获取在线智能体列表"""
        return self.online_agents.copy()


# 便捷函数
async def create_and_connect_client(
    agent_id: str,
    name: str,
    capabilities: List[str],
    server_url: str = "http://localhost:8001"
) -> NexusClient:
    """
    创建并连接客户端

    Args:
        agent_id: 智能体ID
        name: 智能体名称
        capabilities: 能力列表
        server_url: 服务器URL

    Returns:
        已连接的NexusClient实例
    """
    client = NexusClient(agent_id, name, capabilities, server_url)
    await client.connect()
    await client.wait_until_registered()
    return client
