# Nautilus 大脑-身体接口协议 (BBI Protocol)

> Brain-Body Interface Protocol v1.0
> 定义数字大脑(Nautilus)与物理身体(机器人)之间的通信标准

---

## 1. 协议概述

### 1.1 设计目标

| 目标 | 说明 |
|------|------|
| **标准化** | 统一数字-物理交互接口 |
| **可扩展** | 支持多种机器人平台 |
| **可靠性** | 任务可追溯、可撤销 |
| **实时性** | 状态同步延迟 < 1s |

### 1.2 架构

```
┌─────────────┐     BBI Protocol      ┌─────────────┐
│   Nautilus  │ ◄─────────────────► │  机器人端   │
│  (数字大脑) │   JSON/WebSocket     │  (物理身体) │
└─────────────┘                      └─────────────┘
     ↓                                     ↓
  任务规划                            运动控制
  环境感知                            传感器数据
  决策推理                            执行反馈
```

---

## 2. 消息格式

### 2.1 基础消息结构

```json
{
  "version": "1.0",
  "message_id": "msg_001",
  "timestamp": "2026-03-21T12:00:00Z",
  "message_type": "task_request",
  "source": "nautilus",
  "target": "robot_01",
  "payload": { }
}
```

### 2.2 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| `task_request` | N→R | 任务请求 |
| `task_accept` | R→N | 任务接受 |
| `task_progress` | R→N | 任务进度 |
| `task_complete` | R→N | 任务完成 |
| `task_failed` | R→N | 任务失败 |
| `sensor_data` | R→N | 传感器数据 |
| `status_query` | N→R | 状态查询 |
| `status_response` | R→N | 状态响应 |
| `emergency_stop` | N→R | 紧急停止 |

---

## 3. 任务请求 (task_request)

### 3.1 完整结构

```json
{
  "version": "1.0",
  "message_id": "task_001",
  "timestamp": "2026-03-21T12:00:00Z",
  "message_type": "task_request",
  "source": "nautilus",
  "target": "robot_01",
  "payload": {
    "task_id": "nautilus_12345",
    "task_type": "hybrid",
    "priority": "high",
    "deadline": "2026-03-21T12:30:00Z",
    
    "digital_steps": [
      {
        "step_id": "d1",
        "action": "search",
        "params": {
          "query": "附近最近的药店",
          "radius": 1000
        },
        "expected_result": "药店位置列表"
      },
      {
        "step_id": "d2",
        "action": "order",
        "params": {
          "item": "感冒药",
          "quantity": 1
        },
        "expected_result": "订单确认"
      }
    ],
    
    "physical_steps": [
      {
        "step_id": "p1",
        "action": "move_to",
        "params": {
          "target": "pharmacy_location",
          "navigation": "local"
        },
        "preconditions": ["d1_complete"],
        "expected_result": "到达目的地"
      },
      {
        "step_id": "p2",
        "action": "pick_up",
        "params": {
          "item": "package",
          "location": "counter"
        },
        "preconditions": ["p1_complete"],
        "expected_result": "物品已取"
      },
      {
        "step_id": "p3",
        "action": "deliver",
        "params": {
          "destination": "user_location"
        },
        "preconditions": ["p2_complete"],
        "expected_result": "交付完成"
      }
    ],
    
    "verification": {
      "conditions": [
        {
          "type": "state",
          "entity": "package",
          "state": "delivered"
        },
        {
          "type": "photo",
          "verify_at": "p3_complete",
          "description": "用户签收照片"
        }
      ],
      "fallback": {
        "action": "notify",
        "params": {
          "message": "任务可能未完全成功，需要人工确认"
        }
      }
    },
    
    "context": {
      "user_id": "user_001",
      "session_id": "session_001",
      "location": {
        "lat": 39.9042,
        "lng": 116.4074
      },
      "preferences": {
        "route_preference": "shortest",
        "avoid_stairs": true
      }
    }
  }
}
```

### 3.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | ✓ | Nautilus 任务ID |
| `task_type` | enum | ✓ | digital/physical/hybrid |
| `priority` | enum | - | low/normal/high/urgent |
| `deadline` | datetime | - | 任务截止时间 |
| `digital_steps` | array | - | 数字操作步骤 |
| `physical_steps` | array | - | 物理操作步骤 |
| `verification` | object | ✓ | 验证条件 |
| `context` | object | - | 上下文信息 |

---

## 4. 任务响应

### 4.1 接受 (task_accept)

```json
{
  "message_type": "task_accept",
  "payload": {
    "task_id": "nautilus_12345",
    "robot_task_id": "robot_001_task",
    "estimated_duration": 1800,
    "accepted_steps": ["p1", "p2", "p3"]
  }
}
```

### 4.2 进度 (task_progress)

```json
{
  "message_type": "task_progress",
  "payload": {
    "task_id": "nautilus_12345",
    "current_step": "p2",
    "step_status": "in_progress",
    "progress_percent": 50,
    "sensor_data": {
      "battery": 85,
      "location": { "lat": 39.905, "lng": 116.408 }
    }
  }
}
```

### 4.3 完成 (task_complete)

```json
{
  "message_type": "task_complete",
  "payload": {
    "task_id": "nautilus_12345",
    "completed_steps": ["d1", "d2", "p1", "p2", "p3"],
    "verification_results": [
      { "type": "state", "passed": true },
      { "type": "photo", "passed": true, "photo_url": "..." }
    ],
    "final_state": {
      "location": { "lat": 39.906, "lng": 116.409 },
      "battery": 72
    }
  }
}
```

---

## 5. 错误处理

### 5.1 失败消息 (task_failed)

```json
{
  "message_type": "task_failed",
  "payload": {
    "task_id": "nautilus_12345",
    "failed_step": "p2",
    "error_code": "NAVIGATION_OBSTACLE",
    "error_message": "导航路径被障碍物阻挡",
    "retry_available": true,
    "current_state": {
      "location": { "lat": 39.905, "lng": 116.408 },
      "battery": 65
    }
  }
}
```

### 5.2 错误码

| 错误码 | 说明 | 可重试 |
|--------|------|--------|
| `NAVIGATION_OBSTACLE` | 导航障碍 | ✓ |
| `NAVIGATION_FAILED` | 导航失败 | ✓ |
| `GRIPPER_ERROR` | 夹爪错误 | ✗ |
| `BATTERY_LOW` | 电量低 | ✓ |
| `SENSOR_ERROR` | 传感器错误 | ✗ |
| `COMMUNICATION_LOST` | 通信丢失 | ✓ |
| `TASK_TIMEOUT` | 任务超时 | ✓ |
| `VERIFICATION_FAILED` | 验证失败 | ✓ |

---

## 6. 通信协议

### 6.1 WebSocket

```javascript
// 连接
const ws = new WebSocket('wss://nautilus.local:8765/robot');

// 认证
ws.send(JSON.stringify({
  type: 'auth',
  token: 'robot_token_xxx'
}));

// 消息
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  // 处理消息
};
```

### 6.2 REST API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/robot/register` | POST | 注册机器人 |
| `/api/robot/{id}/task` | POST | 提交任务 |
| `/api/robot/{id}/status` | GET | 获取状态 |
| `/api/robot/{id}/cancel` | POST | 取消任务 |

---

## 7. 实现状态

| 模块 | 状态 | 文件 |
|------|------|------|
| 消息格式定义 | ✅ 完成 | `bbi_protocol.py` |
| WebSocket 服务 | ⏳ 待实现 | - |
| REST API | ⏳ 待实现 | - |
| 机器人端 SDK | ⏳ 待实现 | - |

---

## 8. 后续计划

- [ ] 实现 WebSocket 服务端
- [ ] 实现 REST API
- [ ] 开发机器人端 Python SDK
- [ ] 对接章鱼动力 SYNTH 机器人
- [ ] 真人测试验证
