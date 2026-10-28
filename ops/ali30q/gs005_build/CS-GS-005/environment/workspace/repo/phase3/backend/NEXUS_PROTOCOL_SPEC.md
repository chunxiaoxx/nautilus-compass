# Nexus Protocol 规范文档

版本: v1.0.0
创建时间: 2025-02-24
状态: 草案

---

## 1. 协议概述

### 1.1 协议名称
**Nexus Protocol (NP)** - Nautilus智能体到智能体通信协议

### 1.2 协议目标
- 实现智能体间的无缝通信
- 支持多智能体协作
- 提供知识共享机制
- 确保消息可靠传输

### 1.3 协议特性
- ✅ 基于WebSocket的实时通信
- ✅ 支持点对点和广播消息
- ✅ 消息签名验证
- ✅ 自动重连机制
- ✅ 消息确认和重试

---

## 2. 消息类型定义

### 2.1 消息类型枚举

```python
from enum import Enum

class MessageType(Enum):
    """Nexus Protocol 消息类型"""

    # 连接管理
    HELLO = "hello"           # 智能体注册和发现

    # 协作请求
    REQUEST = "request"       # 请求协作
    OFFER = "offer"          # 提供能力

    # 协作响应
    ACCEPT = "accept"        # 接受协作
    REJECT = "reject"        # 拒绝协作

    # 执行管理
    PROGRESS = "progress"    # 进度更新
    COMPLETE = "complete"    # 完成通知

    # 知识共享
    SHARE = "share"          # 知识共享
```

---

## 3. 消息数据结构

### 3.1 基础消息结构

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import uuid

class NexusMessage(BaseModel):
    """Nexus消息基类"""

    # 消息元数据
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # 路由信息
    from_agent: str = Field(..., description="发送者智能体ID")
    to_agent: Union[str, List[str]] = Field(..., description="接收者智能体ID，支持单播和广播")

    # 消息内容
    payload: Dict[str, Any] = Field(..., description="消息负载")

    # 安全信息
    signature: Optional[str] = Field(None, description="消息签名")

    # 追踪信息
    correlation_id: Optional[str] = Field(None, description="关联ID，用于追踪对话")
    reply_to: Optional[str] = Field(None, description="回复的消息ID")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

---

## 4. 具体消息类型

### 4.1 HELLO - 智能体注册

**用途**: 智能体连接到Nexus服务器时发送，注册自己的身份和能力

```python
class HelloPayload(BaseModel):
    """HELLO消息负载"""
    agent_id: str = Field(..., description="智能体唯一ID")
    name: str = Field(..., description="智能体名称")
    version: str = Field(..., description="智能体版本")
    capabilities: List[str] = Field(default_factory=list, description="能力列表")
    status: str = Field("online", description="状态: online/busy/offline")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

class HelloResponse(BaseModel):
    """HELLO响应"""
    status: str = Field(..., description="注册状态: success/error")
    agent_id: str = Field(..., description="确认的智能体ID")
    online_agents: List[str] = Field(default_factory=list, description="当前在线智能体列表")
    message: Optional[str] = Field(None, description="响应消息")
```

**示例**:
```json
{
  "message_id": "msg-001",
  "type": "hello",
  "version": "1.0.0",
  "timestamp": "2025-02-24T10:00:00Z",
  "from_agent": "agent-001",
  "to_agent": "nexus-server",
  "payload": {
    "agent_id": "agent-001",
    "name": "DataAnalyzer",
    "version": "1.0.0",
    "capabilities": ["data_analysis", "visualization"],
    "status": "online",
    "metadata": {
      "max_concurrent_tasks": 3,
      "supported_formats": ["csv", "json", "parquet"]
    }
  }
}
```

---

### 4.2 REQUEST - 请求协作

**用途**: 智能体A请求智能体B协助完成任务

```python
class RequestPayload(BaseModel):
    """REQUEST消息负载"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: int = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型")
    description: str = Field(..., description="任务描述")
    required_capability: str = Field(..., description="所需能力")

    # 奖励和时间
    reward_share: float = Field(..., ge=0.0, le=1.0, description="奖励分成比例")
    deadline: datetime = Field(..., description="截止时间")
    estimated_duration: Optional[int] = Field(None, description="预计耗时(秒)")

    # 任务数据
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    requirements: Optional[Dict[str, Any]] = Field(None, description="特殊要求")
```

**示例**:
```json
{
  "message_id": "msg-002",
  "type": "request",
  "from_agent": "agent-001",
  "to_agent": "agent-002",
  "payload": {
    "request_id": "req-001",
    "task_id": 123,
    "task_type": "data_analysis",
    "description": "分析销售数据并生成报告",
    "required_capability": "data_analysis",
    "reward_share": 0.3,
    "deadline": "2025-02-25T18:00:00Z",
    "estimated_duration": 3600,
    "input_data": {
      "file_url": "https://example.com/sales.csv",
      "format": "csv"
    }
  }
}
```

---

### 4.3 OFFER - 提供能力

**用途**: 智能体主动提供自己的能力给其他智能体

```python
class OfferPayload(BaseModel):
    """OFFER消息负载"""
    offer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    capabilities: List[str] = Field(..., description="提供的能力列表")
    availability: str = Field(..., description="可用性: immediate/scheduled")
    price: Optional[float] = Field(None, description="价格(可选)")
    conditions: Optional[Dict[str, Any]] = Field(None, description="条件")
```

---

### 4.4 ACCEPT - 接受协作

**用途**: 智能体B接受智能体A的协作请求

```python
class AcceptPayload(BaseModel):
    """ACCEPT消息负载"""
    request_id: str = Field(..., description="对应的请求ID")
    estimated_time: int = Field(..., description="预计完成时间(秒)")
    conditions: Optional[Dict[str, Any]] = Field(None, description="接受条件")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="协作会话ID")
```

**示例**:
```json
{
  "message_id": "msg-003",
  "type": "accept",
  "from_agent": "agent-002",
  "to_agent": "agent-001",
  "reply_to": "msg-002",
  "payload": {
    "request_id": "req-001",
    "estimated_time": 3000,
    "session_id": "session-001",
    "conditions": {
      "max_retries": 3,
      "timeout": 3600
    }
  }
}
```

---

### 4.5 REJECT - 拒绝协作

**用途**: 智能体B拒绝智能体A的协作请求

```python
class RejectPayload(BaseModel):
    """REJECT消息负载"""
    request_id: str = Field(..., description="对应的请求ID")
    reason: str = Field(..., description="拒绝原因")
    alternative: Optional[str] = Field(None, description="建议的替代智能体")
```

**示例**:
```json
{
  "message_id": "msg-004",
  "type": "reject",
  "from_agent": "agent-002",
  "to_agent": "agent-001",
  "reply_to": "msg-002",
  "payload": {
    "request_id": "req-001",
    "reason": "Currently at maximum capacity",
    "alternative": "agent-003"
  }
}
```

---

### 4.6 PROGRESS - 进度更新

**用途**: 执行任务的智能体定期发送进度更新

```python
class ProgressPayload(BaseModel):
    """PROGRESS消息负载"""
    session_id: str = Field(..., description="协作会话ID")
    progress: float = Field(..., ge=0.0, le=1.0, description="进度百分比")
    status: str = Field(..., description="当前状态")
    message: Optional[str] = Field(None, description="进度消息")
    estimated_remaining: Optional[int] = Field(None, description="预计剩余时间(秒)")
```

**示例**:
```json
{
  "message_id": "msg-005",
  "type": "progress",
  "from_agent": "agent-002",
  "to_agent": "agent-001",
  "payload": {
    "session_id": "session-001",
    "progress": 0.5,
    "status": "processing",
    "message": "已完成数据清洗，正在进行分析",
    "estimated_remaining": 1500
  }
}
```

---

### 4.7 COMPLETE - 完成通知

**用途**: 任务完成后发送结果

```python
class CompletePayload(BaseModel):
    """COMPLETE消息负载"""
    session_id: str = Field(..., description="协作会话ID")
    status: str = Field(..., description="完成状态: success/failed")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息(如果失败)")
    execution_time: int = Field(..., description="实际执行时间(秒)")
    metrics: Optional[Dict[str, Any]] = Field(None, description="执行指标")
```

**示例**:
```json
{
  "message_id": "msg-006",
  "type": "complete",
  "from_agent": "agent-002",
  "to_agent": "agent-001",
  "payload": {
    "session_id": "session-001",
    "status": "success",
    "result": {
      "report_url": "https://example.com/report.pdf",
      "summary": "销售额同比增长15%",
      "charts": ["chart1.png", "chart2.png"]
    },
    "execution_time": 2800,
    "metrics": {
      "rows_processed": 10000,
      "accuracy": 0.98
    }
  }
}
```

---

### 4.8 SHARE - 知识共享

**用途**: 智能体分享知识、经验或解决方案

```python
class SharePayload(BaseModel):
    """SHARE消息负载"""
    share_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    share_type: str = Field(..., description="分享类型: solution/knowledge/experience")
    title: str = Field(..., description="标题")
    description: str = Field(..., description="描述")
    content: Dict[str, Any] = Field(..., description="分享内容")
    tags: List[str] = Field(default_factory=list, description="标签")
    applicable_scenarios: List[str] = Field(default_factory=list, description="适用场景")
```

**示例**:
```json
{
  "message_id": "msg-007",
  "type": "share",
  "from_agent": "agent-002",
  "to_agent": ["agent-001", "agent-003"],
  "payload": {
    "share_id": "share-001",
    "share_type": "solution",
    "title": "CSV数据清洗最佳实践",
    "description": "处理大型CSV文件的高效方法",
    "content": {
      "method": "chunked_processing",
      "code": "...",
      "performance": "10x faster"
    },
    "tags": ["data_processing", "optimization"],
    "applicable_scenarios": ["large_csv", "memory_limited"]
  }
}
```

---

## 5. 消息流转流程

### 5.1 智能体注册流程

```
Agent → HELLO → Nexus Server
Nexus Server → HELLO_RESPONSE → Agent
Nexus Server → AGENT_STATUS (broadcast) → All Agents
```

### 5.2 协作请求流程

```
Agent A → REQUEST → Nexus Server → Agent B
Agent B → ACCEPT/REJECT → Nexus Server → Agent A

如果ACCEPT:
Agent B → PROGRESS (periodic) → Agent A
Agent B → COMPLETE → Agent A
```

### 5.3 知识共享流程

```
Agent A → SHARE → Nexus Server → [Agent B, Agent C, ...]
```

---

## 6. 错误处理

### 6.1 错误消息结构

```python
class ErrorPayload(BaseModel):
    """错误消息负载"""
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    retry_after: Optional[int] = Field(None, description="重试延迟(秒)")
```

### 6.2 常见错误码

| 错误码 | 描述 | 处理方式 |
|--------|------|----------|
| `AGENT_NOT_FOUND` | 目标智能体不存在 | 检查智能体ID |
| `AGENT_OFFLINE` | 目标智能体离线 | 等待或选择其他智能体 |
| `INVALID_MESSAGE` | 消息格式错误 | 检查消息结构 |
| `UNAUTHORIZED` | 未授权 | 检查签名 |
| `RATE_LIMIT` | 速率限制 | 延迟重试 |
| `TIMEOUT` | 超时 | 重试或取消 |

---

## 7. 安全机制

### 7.1 消息签名

```python
import hashlib
import hmac

def sign_message(message: NexusMessage, secret_key: str) -> str:
    """生成消息签名"""
    message_str = message.json(exclude={'signature'})
    signature = hmac.new(
        secret_key.encode(),
        message_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def verify_signature(message: NexusMessage, secret_key: str) -> bool:
    """验证消息签名"""
    expected_signature = sign_message(message, secret_key)
    return hmac.compare_digest(expected_signature, message.signature)
```

### 7.2 访问控制

- 智能体必须先注册才能发送消息
- 每个智能体有唯一的API密钥
- 消息必须包含有效签名

---

## 8. 性能要求

### 8.1 延迟要求

| 消息类型 | 目标延迟 |
|---------|---------|
| HELLO | < 100ms |
| REQUEST | < 100ms |
| ACCEPT/REJECT | < 100ms |
| PROGRESS | < 200ms |
| COMPLETE | < 200ms |
| SHARE | < 500ms |

### 8.2 吞吐量要求

- 支持100个并发智能体
- 每秒处理1000条消息
- 消息可靠性 > 99.9%

---

## 9. 实现示例

### 9.1 Python客户端示例

```python
import socketio
from nexus_protocol import NexusMessage, MessageType, HelloPayload

class NexusClient:
    def __init__(self, agent_id: str, server_url: str):
        self.agent_id = agent_id
        self.sio = socketio.AsyncClient()
        self.server_url = server_url

    async def connect(self):
        await self.sio.connect(self.server_url)
        await self.send_hello()

    async def send_hello(self):
        message = NexusMessage(
            type=MessageType.HELLO,
            from_agent=self.agent_id,
            to_agent="nexus-server",
            payload=HelloPayload(
                agent_id=self.agent_id,
                name="MyAgent",
                version="1.0.0",
                capabilities=["data_analysis"]
            ).dict()
        )
        await self.sio.emit('message', message.dict())
```

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2025-02-24 | 初始版本 |

---

## 11. 参考资料

- WebSocket RFC 6455
- JSON Schema
- Pydantic Documentation
- Socket.IO Protocol

---

**文档状态**: 草案
**下一步**: 团队评审和确认
**负责人**: [待分配]
