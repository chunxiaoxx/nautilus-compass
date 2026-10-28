"""
WebSocket服务器单元测试

为websocket_server.py添加单元测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# WebSocket Server Tests
# ============================================================================

class TestWebSocketServer:
    """测试WebSocket服务器"""

    def test_socket_server_creation(self):
        """测试Socket.IO服务器创建"""
        import socketio
        import os

        # 模拟环境变量
        with patch.dict(os.environ, {'CORS_ORIGINS': 'http://localhost:3000'}):
            sio = socketio.AsyncServer(
                async_mode='asgi',
                cors_allowed_origins=['http://localhost:3000']
            )

            assert sio is not None
            assert sio.async_mode == 'asgi'

    def test_socket_app_creation(self):
        """测试ASGI应用创建"""
        import socketio

        sio = socketio.AsyncServer(async_mode='asgi')
        socket_app = socketio.ASGIApp(sio, other_asgi_app=None)

        assert socket_app is not None

    def test_event_handlers_exist(self):
        """测试事件处理器存在"""
        import websocket_server as ws

        # 验证事件发射函数存在
        assert hasattr(ws, 'emit_task_published')
        assert hasattr(ws, 'emit_task_accepted')
        assert hasattr(ws, 'emit_task_submitted')
        assert hasattr(ws, 'emit_task_verified')
        assert hasattr(ws, 'emit_task_completed')
        assert hasattr(ws, 'emit_task_failed')
        assert hasattr(ws, 'emit_task_disputed')
        assert hasattr(ws, 'emit_reward_distributed')
        assert hasattr(ws, 'emit_reward_withdrawn')

    def test_emit_functions_are_async(self):
        """测试发射函数是异步的"""
        import inspect
        import websocket_server as ws

        # 验证所有emit函数是异步的
        assert inspect.iscoroutinefunction(ws.emit_task_published)
        assert inspect.iscoroutinefunction(ws.emit_task_accepted)
        assert inspect.iscoroutinefunction(ws.emit_task_submitted)
        assert inspect.iscoroutinefunction(ws.emit_task_verified)
        assert inspect.iscoroutinefunction(ws.emit_task_completed)
        assert inspect.iscoroutinefunction(ws.emit_task_failed)
        assert inspect.iscoroutinefunction(ws.emit_task_disputed)
        assert inspect.iscoroutinefunction(ws.emit_reward_distributed)
        assert inspect.iscoroutinefunction(ws.emit_reward_withdrawn)

    @pytest.mark.asyncio
    async def test_emit_task_published(self):
        """测试发射任务发布事件"""
        import websocket_server as ws

        # Mock sio
        mock_sio = AsyncMock()
        ws.sio = mock_sio

        task_data = {
            'task_id': '0x123',
            'description': 'Test task',
            'reward': 1000
        }

        await ws.emit_task_published(task_data)

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == 'task.published'
        assert call_args[0][1] == task_data

    @pytest.mark.asyncio
    async def test_emit_task_accepted_with_agent(self):
        """测试发射任务接受事件(带agent)"""
        import websocket_server as ws

        mock_sio = AsyncMock()
        ws.sio = mock_sio

        task_data = {
            'task_id': '0x123',
            'agent': '0x456'
        }

        await ws.emit_task_accepted(task_data)

        # 应该发射两次：一次给tasks房间，一次给agent房间
        assert mock_sio.emit.call_count == 2

    @pytest.mark.asyncio
    async def test_emit_task_accepted_without_agent(self):
        """测试发射任务接受事件(不带agent)"""
        import websocket_server as ws

        mock_sio = AsyncMock()
        ws.sio = mock_sio

        task_data = {
            'task_id': '0x123',
            'agent': None
        }

        await ws.emit_task_accepted(task_data)

        # 只应该发射一次
        mock_sio.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_reward_distributed(self):
        """测试发射奖励分发事件"""
        import websocket_server as ws

        mock_sio = AsyncMock()
        ws.sio = mock_sio

        reward_data = {
            'task_id': '0x123',
            'agent': '0x456',
            'amount': 1000
        }

        await ws.emit_reward_distributed(reward_data)

        mock_sio.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_reward_distributed_no_agent(self):
        """测试发射奖励分发事件(无agent)"""
        import websocket_server as ws

        mock_sio = AsyncMock()
        ws.sio = mock_sio

        reward_data = {
            'task_id': '0x123',
            'agent': None,
            'amount': 1000
        }

        await ws.emit_reward_distributed(reward_data)

        # 没有agent时不应该发射
        mock_sio.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_emit_task_verified(self):
        """测试发射任务验证事件"""
        import websocket_server as ws

        mock_sio = AsyncMock()
        ws.sio = mock_sio

        task_data = {
            'task_id': '0x123',
            'agent': '0x456'
        }

        await ws.emit_task_verified(task_data)

        assert mock_sio.emit.call_count == 2

    @pytest.mark.asyncio
    async def test_emit_task_completed(self):
        """测试发射任务完成事件"""
        import websocket_server as ws

        mock_sio = AsyncMock()
        ws.sio = mock_sio

        task_data = {
            'task_id': '0x123',
            'agent': '0x456'
        }

        await ws.emit_task_completed(task_data)

        assert mock_sio.emit.call_count == 2

    @pytest.mark.asyncio
    async def test_emit_task_failed(self):
        """测试发射任务失败事件"""
        import websocket_server as ws

        mock_sio = AsyncMock()
        ws.sio = mock_sio

        task_data = {
            'task_id': '0x123',
            'agent': '0x456'
        }

        await ws.emit_task_failed(task_data)

        assert mock_sio.emit.call_count == 2


# ============================================================================
# WebSocket Events Tests
# ============================================================================

class TestWebSocketEvents:
    """测试WebSocket事件"""

    def test_events_module_exports(self):
        """测试模块导出"""
        import websocket_server as ws

        assert hasattr(ws, 'sio')
        assert hasattr(ws, 'socket_app')
        assert hasattr(ws, 'connect')
        assert hasattr(ws, 'disconnect')
        assert hasattr(ws, 'subscribe_tasks')
        assert hasattr(ws, 'subscribe_agent')
        assert hasattr(ws, 'unsubscribe_tasks')
        assert hasattr(ws, 'unsubscribe_agent')
