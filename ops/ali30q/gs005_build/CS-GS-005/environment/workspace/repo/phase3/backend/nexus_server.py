"""
Nexus Server - 智能体通信服务器

版本: 1.0.0
创建时间: 2025-02-24
"""

import socketio
from fastapi import FastAPI
from typing import Dict, Set, Optional, Any
import asyncio
import logging
from datetime import datetime, timezone

from nexus_protocol import (
    MessageType,
    NexusMessage,
    HelloPayload,
    HelloResponse,
    validate_message,
    is_message_expired,
)

logger = logging.getLogger(__name__)


class NexusServer:
    """
    Nexus Protocol 服务器

    功能：
    - 智能体注册和发现
    - 消息路由
    - 状态管理
    - 消息持久化
    """

    def __init__(self, cors_origins: str = "*", max_queue_size: int = 1000, max_agents: int = 100):
        """
        初始化Nexus服务器

        Args:
            cors_origins: CORS允许的源
            max_queue_size: 消息队列最大大小
            max_agents: 最大智能体连接数
        """
        # 创建Socket.IO服务器
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins=cors_origins,
            logger=True,
            engineio_logger=True
        )

        # 智能体注册表: {agent_id: agent_info}
        self.agents: Dict[str, Dict[str, Any]] = {}

        # 在线智能体: {agent_id}
        self.online_agents: Set[str] = set()

        # SID到Agent ID的映射: {sid: agent_id}
        self.sid_to_agent: Dict[str, str] = {}

        # 消息队列（带大小限制）
        self.message_queue = asyncio.Queue(maxsize=max_queue_size)

        # 并发控制配置
        self.max_queue_size = max_queue_size
        self.max_agents = max_agents

        # 统计信息
        self.stats = {
            "total_messages": 0,
            "total_agents": 0,
            "messages_by_type": {},
            "queue_size": 0,
            "dropped_messages": 0,
            "total_connections": 0,  # 添加兼容字段
        }

        # 设置事件处理器
        self._setup_handlers()

        logger.info(f"NexusServer initialized (max_queue_size={max_queue_size}, max_agents={max_agents})")

    def _setup_handlers(self):
        """设置Socket.IO事件处理器"""

        @self.sio.event
        async def connect(sid, environ):
            """客户端连接"""
            logger.info(f"Client connected: {sid}")
            self.stats['total_connections'] += 1
            await self.sio.emit('connected', {
                'message': 'Connected to Nexus Protocol Server',
                'version': '1.0.0',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=sid)

        @self.sio.event
        async def disconnect(sid):
            """客户端断开"""
            # 查找并移除智能体
            agent_id = self.sid_to_agent.get(sid)

            if agent_id:
                self.online_agents.discard(agent_id)
                del self.sid_to_agent[sid]

                if agent_id in self.agents:
                    self.agents[agent_id]['status'] = 'offline'
                    self.agents[agent_id]['disconnected_at'] = datetime.now(timezone.utc)

                logger.info(f"Agent {agent_id} disconnected (sid: {sid})")

                # 广播智能体离线
                await self.broadcast_agent_status(agent_id, "offline")

        @self.sio.event
        async def hello(sid, data):
            """处理HELLO消息 - 智能体注册"""
            try:
                # 检查智能体数量限制
                if len(self.online_agents) >= self.max_agents:
                    logger.warning(f"Max agents limit reached ({self.max_agents})")
                    await self.sio.emit('error', {
                        'error_code': 'MAX_AGENTS_REACHED',
                        'error_message': f'Maximum number of agents ({self.max_agents}) reached'
                    }, room=sid)
                    return

                # 解析payload
                payload = HelloPayload(**data)
                agent_id = payload.agent_id

                logger.info(f"HELLO from {agent_id} (sid: {sid})")

                # 注册智能体
                self.agents[agent_id] = {
                    'sid': sid,
                    'agent_id': agent_id,
                    'name': payload.name,
                    'version': payload.version,
                    'capabilities': payload.capabilities,
                    'status': payload.status,
                    'metadata': payload.metadata,
                    'registered_at': datetime.now(timezone.utc),
                    'last_seen': datetime.now(timezone.utc),
                }

                self.online_agents.add(agent_id)
                self.sid_to_agent[sid] = agent_id
                self.stats['total_agents'] = len(self.agents)

                # 返回注册成功响应
                response = HelloResponse(
                    status='success',
                    agent_id=agent_id,
                    online_agents=list(self.online_agents),
                    message=f'Agent {agent_id} registered successfully'
                )

                await self.sio.emit('hello_ack', response.model_dump(mode='json'), room=sid)

                # 广播新智能体上线
                await self.broadcast_agent_status(agent_id, "online")

                logger.info(f"Agent {agent_id} registered. Total online: {len(self.online_agents)}")

            except Exception as e:
                logger.error(f"Error handling HELLO: {e}")
                await self.sio.emit('error', {
                    'error_code': 'HELLO_ERROR',
                    'error_message': str(e)
                }, room=sid)

        @self.sio.event
        async def message(sid, data):
            """处理通用消息"""
            try:
                # 解析消息
                msg = NexusMessage(**data)

                # 验证消息
                if not validate_message(msg):
                    await self.sio.emit('error', {
                        'error_code': 'INVALID_MESSAGE',
                        'error_message': 'Message validation failed'
                    }, room=sid)
                    return

                # 检查消息是否过期
                if is_message_expired(msg):
                    logger.warning(f"Message expired: {msg.message_id}")
                    self.stats['dropped_messages'] += 1
                    await self.sio.emit('error', {
                        'error_code': 'MESSAGE_EXPIRED',
                        'error_message': 'Message has expired'
                    }, room=sid)
                    return

                # 检查队列是否已满
                if self.message_queue.full():
                    logger.warning(f"Message queue full ({self.max_queue_size}), dropping message")
                    self.stats['dropped_messages'] += 1
                    await self.sio.emit('error', {
                        'error_code': 'QUEUE_FULL',
                        'error_message': 'Message queue is full, please retry later'
                    }, room=sid)
                    return

                # 更新统计
                self.stats['total_messages'] += 1
                self.stats['queue_size'] = self.message_queue.qsize()
                msg_type = msg.type.value
                self.stats['messages_by_type'][msg_type] = \
                    self.stats['messages_by_type'].get(msg_type, 0) + 1

                # 路由消息
                await self.route_message(msg)

                logger.debug(f"Message routed: {msg.type.value} from {msg.from_agent} to {msg.to_agent}")

            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await self.sio.emit('error', {
                    'error_code': 'MESSAGE_ERROR',
                    'error_message': str(e)
                }, room=sid)

        @self.sio.event
        async def request(sid, data):
            """处理REQUEST消息 - 请求协作"""
            await self._handle_typed_message(sid, data, MessageType.REQUEST)

        @self.sio.event
        async def offer(sid, data):
            """处理OFFER消息 - 提供能力"""
            await self._handle_typed_message(sid, data, MessageType.OFFER)

        @self.sio.event
        async def accept(sid, data):
            """处理ACCEPT消息 - 接受协作"""
            await self._handle_typed_message(sid, data, MessageType.ACCEPT)

        @self.sio.event
        async def reject(sid, data):
            """处理REJECT消息 - 拒绝协作"""
            await self._handle_typed_message(sid, data, MessageType.REJECT)

        @self.sio.event
        async def progress(sid, data):
            """处理PROGRESS消息 - 进度更新"""
            await self._handle_typed_message(sid, data, MessageType.PROGRESS)

        @self.sio.event
        async def complete(sid, data):
            """处理COMPLETE消息 - 完成通知"""
            await self._handle_typed_message(sid, data, MessageType.COMPLETE)

        @self.sio.event
        async def share(sid, data):
            """处理SHARE消息 - 知识共享"""
            await self._handle_typed_message(sid, data, MessageType.SHARE)

        @self.sio.event
        async def get_agents(sid, data):
            """获取在线智能体列表"""
            agents_list = [
                {
                    'agent_id': agent_id,
                    'name': info['name'],
                    'capabilities': info['capabilities'],
                    'status': info['status']
                }
                for agent_id, info in self.agents.items()
                if agent_id in self.online_agents
            ]

            await self.sio.emit('agents_list', {
                'agents': agents_list,
                'total': len(agents_list)
            }, room=sid)

        @self.sio.event
        async def get_stats(sid, data):
            """获取服务器统计信息"""
            await self.sio.emit('stats', self.stats, room=sid)

    async def _handle_typed_message(self, sid: str, data: dict, msg_type: MessageType):
        """处理特定类型的消息"""
        try:
            from_agent = data.get('from_agent')
            to_agent = data.get('to_agent')

            if not from_agent or not to_agent:
                await self.sio.emit('error', {
                    'error_code': 'MISSING_FIELDS',
                    'error_message': 'from_agent and to_agent are required'
                }, room=sid)
                return

            # 检查目标智能体是否在线
            if isinstance(to_agent, str):
                if to_agent not in self.online_agents:
                    await self.sio.emit('error', {
                        'error_code': 'AGENT_OFFLINE',
                        'error_message': f'Agent {to_agent} is not online'
                    }, room=sid)
                    return

                # 转发消息
                target_sid = self.agents[to_agent]['sid']
                await self.sio.emit(msg_type.value, data, room=target_sid)

                logger.info(f"{msg_type.value.upper()} from {from_agent} to {to_agent}")

            elif isinstance(to_agent, list):
                # 广播消息
                for agent_id in to_agent:
                    if agent_id in self.online_agents:
                        target_sid = self.agents[agent_id]['sid']
                        await self.sio.emit(msg_type.value, data, room=target_sid)

                logger.info(f"{msg_type.value.upper()} from {from_agent} to {len(to_agent)} agents")

            # 更新统计
            self.stats['total_messages'] += 1
            self.stats['messages_by_type'][msg_type.value] = \
                self.stats['messages_by_type'].get(msg_type.value, 0) + 1

        except Exception as e:
            logger.error(f"Error handling {msg_type.value}: {e}")
            await self.sio.emit('error', {
                'error_code': f'{msg_type.value.upper()}_ERROR',
                'error_message': str(e)
            }, room=sid)

    async def route_message(self, message: NexusMessage):
        """路由消息到目标智能体"""
        to_agent = message.to_agent

        if isinstance(to_agent, str):
            # 单播
            if to_agent in self.online_agents:
                target_sid = self.agents[to_agent]['sid']
                await self.sio.emit(
                    message.type.value,
                    message.model_dump(mode='json'),
                    room=target_sid
                )
            else:
                # 目标智能体不在线
                from_sid = self.agents.get(message.from_agent, {}).get('sid')
                if from_sid:
                    await self.sio.emit('error', {
                        'error_code': 'AGENT_OFFLINE',
                        'error_message': f'Agent {to_agent} is not online',
                        'message_id': message.message_id
                    }, room=from_sid)

        elif isinstance(to_agent, list):
            # 广播
            for agent_id in to_agent:
                if agent_id in self.online_agents:
                    target_sid = self.agents[agent_id]['sid']
                    await self.sio.emit(
                        message.type.value,
                        message.model_dump(mode='json'),
                        room=target_sid
                    )

    async def broadcast_agent_status(self, agent_id: str, status: str):
        """广播智能体状态变化"""
        await self.sio.emit('agent_status', {
            'agent_id': agent_id,
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体信息"""
        return self.agents.get(agent_id)

    def get_online_agents(self) -> list:
        """获取在线智能体列表"""
        return list(self.online_agents)

    def get_stats(self) -> Dict[str, Any]:
        """获取服务器统计信息"""
        return {
            **self.stats,
            'online_agents': len(self.online_agents),
            'registered_agents': len(self.agents)
        }

    def get_app(self) -> socketio.ASGIApp:
        """获取ASGI应用"""
        return socketio.ASGIApp(self.sio)


# 创建全局实例
nexus_server = NexusServer()


# FastAPI集成
def create_nexus_app() -> FastAPI:
    """创建集成Nexus的FastAPI应用"""
    app = FastAPI(
        title="Nexus Protocol Server",
        description="智能体到智能体通信服务器",
        version="1.0.0"
    )

    # 挂载Socket.IO 到 /socket.io 路径，避免拦截FastAPI路由
    app.mount("/socket.io", nexus_server.get_app())

    @app.get("/")
    async def root():
        """根端点"""
        return {
            "message": "Nexus Protocol Server",
            "status": "running",
            "version": "1.0.0"
        }

    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "online_agents": len(nexus_server.online_agents)
        }

    @app.get("/stats")
    async def get_stats():
        """获取统计信息"""
        return nexus_server.get_stats()

    @app.get("/agents")
    async def get_agents():
        """获取在线智能体"""
        agents = [
            {
                'agent_id': agent_id,
                'name': info['name'],
                'capabilities': info['capabilities'],
                'status': info['status']
            }
            for agent_id, info in nexus_server.agents.items()
            if agent_id in nexus_server.online_agents
        ]
        return {
            "agents": agents,
            "total": len(agents)
        }

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_nexus_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
