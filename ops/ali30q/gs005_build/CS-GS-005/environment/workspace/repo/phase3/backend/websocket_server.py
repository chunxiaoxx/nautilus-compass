"""
WebSocket server for real-time notifications.
"""
import socketio
from fastapi import FastAPI
import os

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
)

# Create ASGI app with static_files parameter to handle other paths
socket_app = socketio.ASGIApp(sio, other_asgi_app=None)


@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    print(f"Client connected: {sid}")
    await sio.emit('connected', {'message': 'Connected to Nautilus WebSocket'}, room=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    print(f"Client disconnected: {sid}")


@sio.event
async def subscribe_tasks(sid, data):
    """Subscribe to task updates."""
    await sio.enter_room(sid, 'tasks')
    print(f"Client {sid} subscribed to tasks")


@sio.event
async def subscribe_agent(sid, data):
    """Subscribe to agent updates."""
    agent_id = data.get('agent_id')
    if agent_id:
        await sio.enter_room(sid, f'agent_{agent_id}')
        print(f"Client {sid} subscribed to agent {agent_id}")


@sio.event
async def unsubscribe_tasks(sid):
    """Unsubscribe from task updates."""
    await sio.leave_room(sid, 'tasks')
    print(f"Client {sid} unsubscribed from tasks")


@sio.event
async def unsubscribe_agent(sid, data):
    """Unsubscribe from agent updates."""
    agent_id = data.get('agent_id')
    if agent_id:
        await sio.leave_room(sid, f'agent_{agent_id}')
        print(f"Client {sid} unsubscribed from agent {agent_id}")


# Event emitters (to be called from other parts of the application)

async def emit_task_published(task_data: dict):
    """Emit task published event."""
    await sio.emit('task.published', task_data, room='tasks')


async def emit_task_accepted(task_data: dict):
    """Emit task accepted event."""
    await sio.emit('task.accepted', task_data, room='tasks')

    # Also emit to specific agent
    if task_data.get('agent'):
        await sio.emit('task.accepted', task_data, room=f"agent_{task_data['agent']}")


async def emit_task_submitted(task_data: dict):
    """Emit task submitted event."""
    await sio.emit('task.submitted', task_data, room='tasks')


async def emit_task_verified(task_data: dict):
    """Emit task verified event."""
    await sio.emit('task.verified', task_data, room='tasks')

    # Also emit to specific agent
    if task_data.get('agent'):
        await sio.emit('task.verified', task_data, room=f"agent_{task_data['agent']}")


async def emit_task_completed(task_data: dict):
    """Emit task completed event."""
    await sio.emit('task.completed', task_data, room='tasks')

    # Also emit to specific agent
    if task_data.get('agent'):
        await sio.emit('task.completed', task_data, room=f"agent_{task_data['agent']}")


async def emit_task_failed(task_data: dict):
    """Emit task failed event."""
    await sio.emit('task.failed', task_data, room='tasks')

    # Also emit to specific agent
    if task_data.get('agent'):
        await sio.emit('task.failed', task_data, room=f"agent_{task_data['agent']}")


async def emit_task_disputed(task_data: dict):
    """Emit task disputed event."""
    await sio.emit('task.disputed', task_data, room='tasks')


async def emit_task_executing(task_data: dict):
    """Emit task execution started event."""
    await sio.emit('task.executing', task_data, room='tasks')
    if task_data.get('agent'):
        await sio.emit('task.executing', task_data, room=f"agent_{task_data['agent']}")


async def emit_task_execution_complete(task_data: dict):
    """Emit task execution completed event."""
    await sio.emit('task.execution_complete', task_data, room='tasks')
    if task_data.get('agent'):
        await sio.emit('task.execution_complete', task_data, room=f"agent_{task_data['agent']}")


async def emit_reward_distributed(reward_data: dict):
    """Emit reward distributed event."""
    if reward_data.get('agent'):
        await sio.emit('reward.distributed', reward_data, room=f"agent_{reward_data['agent']}")


async def emit_reward_withdrawn(reward_data: dict):
    """Emit reward withdrawn event."""
    if reward_data.get('agent'):
        await sio.emit('reward.withdrawn', reward_data, room=f"agent_{reward_data['agent']}")


if __name__ == "__main__":
    import uvicorn

    app = FastAPI()
    app.mount("/ws", socket_app)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("WEBSOCKET_PORT", "8001"))
    )
