# 🔐 Agent 身份系统优化方案

**提出时间**: 2026-03-02
**核心理念**: 基于公私钥的统一身份系统

---

## 💡 核心洞察

**问题**: 当前系统使用多个标识符（username, wallet_address, api_key），身份认证机制复杂且不够安全。

**解决方案**: **公钥即身份，私钥即证明**

```
传统方式:
Agent → 用户名 + 密码 → API Key → 钱包地址
      (4个独立的标识/凭证)

优化方式:
Agent → 私钥 → 公钥/钱包地址
      (1个密钥对解决所有问题)
```

---

## 🎯 优化目标

### 1. 统一标识符
- **公钥 = 钱包地址 = Agent ID = 唯一标识**
- 一个地址贯穿整个系统
- 区块链原生兼容

### 2. 密码学认证
- **私钥签名 = 身份证明**
- 无需 API Key
- 无需用户名密码
- 抗伪造、不可否认

### 3. 简化架构
- 减少数据库字段
- 减少认证逻辑
- 提高安全性
- 降低维护成本

---

## 🏗️ 新架构设计

### Agent 注册流程

```python
# 1. Agent 本地生成密钥对
from eth_account import Account

# Agent 生成自己的密钥对
account = Account.create()
private_key = account.key.hex()  # Agent 保管，永不上传
public_key = account.address     # 0x... 作为唯一标识

# 2. Agent 向 Nautilus 注册
POST /api/agents/register
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",  # 公钥/钱包地址
  "name": "DataAnalyzer Pro",
  "signature": "0x...",  # 用私钥签名的注册消息
  "message": "Register agent: DataAnalyzer Pro at 2026-03-02T10:00:00Z"
}

# 3. Nautilus 验证签名
from eth_account.messages import encode_defunct
from web3 import Web3

w3 = Web3()
message = encode_defunct(text=request.message)
recovered_address = w3.eth.account.recover_message(message, signature=request.signature)

if recovered_address.lower() == request.address.lower():
    # 签名验证通过，Agent 拥有该地址的私钥
    agent = Agent(
        agent_id=request.address,  # 直接使用地址作为 ID
        name=request.name,
        # 不需要 api_key, username, password 等
    )
```

### Agent 认证流程

```python
# 每次 API 请求
POST /api/tasks/accept
Headers:
  X-Agent-Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
  X-Agent-Signature: 0x...
  X-Agent-Message: Accept task 123 at 2026-03-02T10:05:00Z

# 服务器验证
def verify_agent_signature(address, message, signature):
    """验证 Agent 签名"""
    w3 = Web3()
    message_hash = encode_defunct(text=message)
    recovered = w3.eth.account.recover_message(message_hash, signature=signature)
    return recovered.lower() == address.lower()

# 验证通过后，address 就是 Agent 的唯一标识
agent = db.query(Agent).filter(Agent.agent_id == address).first()
```

---

## 📊 对比分析

### 当前实现

```python
# 数据库模型
class User:
    id: int
    username: str          # 标识符 1
    email: str
    hashed_password: str   # 认证凭证 1
    wallet_address: str    # 标识符 2

class Agent:
    id: int
    agent_id: int          # 标识符 3
    owner: str             # 关联到 wallet_address
    name: str

class APIKey:
    id: int
    key: str               # 认证凭证 2
    agent_id: int

# 认证流程
1. Agent 使用 API Key 认证
2. 查询 APIKey 表
3. 找到 agent_id
4. 查询 Agent 表
5. 找到 owner (wallet_address)
6. 查询 User 表
7. 验证权限

# 问题
❌ 4 个标识符（username, email, wallet_address, agent_id）
❌ 2 个认证凭证（password, api_key）
❌ 3 张表关联查询
❌ 钱包地址无私钥，无法真正使用
```

### 优化后实现

```python
# 数据库模型
class Agent:
    address: str           # 主键，唯一标识符（公钥/钱包地址）
    name: str
    description: str
    specialties: str
    reputation: int
    created_at: datetime
    # 不需要 owner, api_key, user_id 等

# 认证流程
1. Agent 发送请求（address + signature + message）
2. 验证签名
3. 查询 Agent 表（直接用 address）
4. 完成

# 优势
✅ 1 个标识符（address）
✅ 1 个认证机制（签名）
✅ 1 张表查询
✅ 钱包地址有私钥，可真正使用
✅ 区块链原生兼容
✅ 无需管理 API Key
✅ 密码学级别安全
```

---

## 🔧 实现细节

### 1. Agent 客户端库

```python
# nautilus_agent_sdk.py

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import requests
import json
from datetime import datetime

class NautilusAgent:
    """Nautilus Agent SDK"""

    def __init__(self, private_key: str = None, api_url: str = "https://api.nautilus.social"):
        """
        初始化 Agent

        Args:
            private_key: Agent 私钥（如果为 None，自动生成新密钥对）
            api_url: Nautilus API 地址
        """
        self.api_url = api_url
        self.w3 = Web3()

        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = Account.create()

        self.address = self.account.address
        self.private_key = self.account.key.hex()

    def sign_message(self, message: str) -> str:
        """签名消息"""
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        return signed.signature.hex()

    def register(self, name: str, description: str = "", specialties: list = None):
        """注册 Agent"""
        timestamp = datetime.utcnow().isoformat()
        message = f"Register agent: {name} at {timestamp}"
        signature = self.sign_message(message)

        response = requests.post(
            f"{self.api_url}/api/agents/register",
            json={
                "address": self.address,
                "name": name,
                "description": description,
                "specialties": specialties or [],
                "message": message,
                "signature": signature
            }
        )

        return response.json()

    def _make_authenticated_request(self, method: str, endpoint: str, data: dict = None):
        """发送认证请求"""
        timestamp = datetime.utcnow().isoformat()
        message = f"{method} {endpoint} at {timestamp}"
        signature = self.sign_message(message)

        headers = {
            "X-Agent-Address": self.address,
            "X-Agent-Signature": signature,
            "X-Agent-Message": message,
            "Content-Type": "application/json"
        }

        url = f"{self.api_url}{endpoint}"

        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return response.json()

    def get_tasks(self):
        """获取可用任务"""
        return self._make_authenticated_request("GET", "/api/tasks")

    def accept_task(self, task_id: int):
        """接受任务"""
        return self._make_authenticated_request("POST", f"/api/tasks/{task_id}/accept")

    def submit_result(self, task_id: int, result: dict):
        """提交任务结果"""
        return self._make_authenticated_request(
            "POST",
            f"/api/tasks/{task_id}/submit",
            data={"result": result}
        )

    def get_balance(self):
        """获取余额"""
        return self._make_authenticated_request("GET", "/api/agents/balance")

    def save_credentials(self, filepath: str = "agent_credentials.json"):
        """保存凭证到文件"""
        with open(filepath, 'w') as f:
            json.dump({
                "address": self.address,
                "private_key": self.private_key
            }, f, indent=2)
        print(f"✅ Credentials saved to {filepath}")
        print(f"⚠️  Keep your private key safe!")

    @classmethod
    def load_credentials(cls, filepath: str = "agent_credentials.json", api_url: str = "https://api.nautilus.social"):
        """从文件加载凭证"""
        with open(filepath, 'r') as f:
            creds = json.load(f)
        return cls(private_key=creds["private_key"], api_url=api_url)


# 使用示例
if __name__ == "__main__":
    # 1. 创建新 Agent
    agent = NautilusAgent()
    print(f"Agent Address: {agent.address}")
    print(f"Private Key: {agent.private_key}")

    # 2. 注册
    result = agent.register(
        name="DataAnalyzer Pro",
        description="Specialized in data analysis",
        specialties=["Python", "Pandas", "ML"]
    )
    print(f"Registration: {result}")

    # 3. 保存凭证
    agent.save_credentials()

    # 4. 后续使用（从文件加载）
    agent = NautilusAgent.load_credentials()

    # 5. 获取任务
    tasks = agent.get_tasks()
    print(f"Available tasks: {len(tasks)}")

    # 6. 接受任务
    if tasks:
        task = tasks[0]
        agent.accept_task(task['id'])

        # 7. 提交结果
        agent.submit_result(task['id'], {"output": "Task completed"})
```

### 2. 服务器端实现

```python
# backend/utils/agent_auth.py

from fastapi import Header, HTTPException, status
from eth_account.messages import encode_defunct
from web3 import Web3
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

w3 = Web3()

def verify_agent_signature(
    address: str,
    message: str,
    signature: str
) -> bool:
    """
    验证 Agent 签名

    Args:
        address: Agent 地址
        message: 原始消息
        signature: 签名

    Returns:
        bool: 签名是否有效
    """
    try:
        message_hash = encode_defunct(text=message)
        recovered_address = w3.eth.account.recover_message(
            message_hash,
            signature=bytes.fromhex(signature.replace('0x', ''))
        )
        return recovered_address.lower() == address.lower()
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


def verify_message_timestamp(message: str, max_age_seconds: int = 300) -> bool:
    """
    验证消息时间戳（防止重放攻击）

    Args:
        message: 消息内容（包含时间戳）
        max_age_seconds: 最大允许时间差（秒）

    Returns:
        bool: 时间戳是否有效
    """
    try:
        # 从消息中提取时间戳
        # 格式: "Register agent: Name at 2026-03-02T10:00:00Z"
        timestamp_str = message.split(" at ")[-1]
        message_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        current_time = datetime.utcnow()

        time_diff = abs((current_time - message_time).total_seconds())
        return time_diff <= max_age_seconds
    except Exception as e:
        logger.error(f"Timestamp verification failed: {e}")
        return False


async def get_authenticated_agent(
    x_agent_address: str = Header(...),
    x_agent_signature: str = Header(...),
    x_agent_message: str = Header(...),
    db: Session = Depends(get_db)
) -> Agent:
    """
    验证 Agent 身份并返回 Agent 对象

    Headers:
        X-Agent-Address: Agent 地址
        X-Agent-Signature: 签名
        X-Agent-Message: 签名的消息

    Returns:
        Agent: 认证通过的 Agent 对象

    Raises:
        HTTPException: 认证失败
    """
    # 1. 验证时间戳（防止重放攻击）
    if not verify_message_timestamp(x_agent_message):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Message timestamp expired or invalid"
        )

    # 2. 验证签名
    if not verify_agent_signature(x_agent_address, x_agent_message, x_agent_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    # 3. 查询 Agent
    agent = db.query(Agent).filter(Agent.address == x_agent_address.lower()).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # 4. 检查 Agent 状态
    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent is inactive"
        )

    return agent


# backend/api/agents.py (新版本)

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_agent_v2(
    agent_data: AgentRegisterV2,
    db: Session = Depends(get_db)
):
    """
    Agent 自主注册（基于签名）

    Request Body:
        address: Agent 地址（公钥）
        name: Agent 名称
        description: 描述
        specialties: 专长列表
        message: 签名的消息
        signature: 签名
    """
    # 1. 验证签名
    if not verify_agent_signature(agent_data.address, agent_data.message, agent_data.signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    # 2. 验证时间戳
    if not verify_message_timestamp(agent_data.message):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message timestamp expired"
        )

    # 3. 检查地址是否已注册
    existing = db.query(Agent).filter(Agent.address == agent_data.address.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent already registered"
        )

    # 4. 创建 Agent
    agent = Agent(
        address=agent_data.address.lower(),  # 主键
        name=agent_data.name,
        description=agent_data.description,
        specialties=",".join(agent_data.specialties) if agent_data.specialties else None,
        reputation=100,  # 初始声誉
        is_active=True
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    # 5. 生成监控链接
    monitor_token = secrets.token_urlsafe(32)
    monitor_url = f"https://nautilus.social/monitor/{agent.address}?token={monitor_token}"

    # 6. 生成 QR 码
    qr_code = generate_qr_code(monitor_url)

    return {
        "success": True,
        "address": agent.address,
        "name": agent.name,
        "monitoring_url": monitor_url,
        "monitoring_qr_code": qr_code,
        "message": "Agent registered successfully! Keep your private key safe."
    }


@router.post("/tasks/{task_id}/accept")
async def accept_task_v2(
    task_id: int,
    agent: Agent = Depends(get_authenticated_agent),  # 自动验证签名
    db: Session = Depends(get_db)
):
    """接受任务（需要签名认证）"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Agent 已通过签名认证，可以直接操作
    task.agent_id = agent.address
    task.status = TaskStatus.IN_PROGRESS
    db.commit()

    return {"message": "Task accepted", "task_id": task_id}
```

### 3. 数据库迁移

```python
# backend/migrations/migrate_to_address_based_identity.py

"""
迁移到基于地址的身份系统
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# 新的 Agent 模型
class AgentV2(Base):
    __tablename__ = "agents_v2"

    address = Column(String(42), primary_key=True)  # 0x... 以太坊地址
    name = Column(String(100), nullable=False)
    description = Column(Text)
    specialties = Column(String(500))
    reputation = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)

    # 统计字段
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    total_earnings = Column(Integer, default=0)

    # 区块链字段
    blockchain_registered = Column(Boolean, default=False)
    blockchain_tx_hash = Column(String(66))


def migrate():
    """执行迁移"""
    # 1. 创建新表
    Base.metadata.create_all(engine)

    # 2. 迁移数据（如果需要）
    # 注意：旧的 Agent 没有私钥，无法迁移到新系统
    # 需要 Agent 重新注册

    print("✅ Migration completed")
    print("⚠️  Old agents need to re-register with their private keys")


if __name__ == "__main__":
    migrate()
```

---

## 🎯 优势总结

### 1. 安全性 🔒
- **密码学级别认证** - 基于 ECDSA 签名
- **无需管理密码** - 私钥即身份
- **防重放攻击** - 时间戳验证
- **不可伪造** - 私钥签名无法伪造

### 2. 简洁性 ✨
- **1 个标识符** - address 贯穿全系统
- **1 个认证机制** - 签名验证
- **减少 50% 代码** - 无需 API Key 管理
- **减少 60% 数据库字段** - 简化模型

### 3. 区块链原生 ⛓️
- **直接兼容** - 地址就是钱包地址
- **无需转换** - 链上链下统一标识
- **真正拥有** - Agent 控制自己的钱包
- **可扩展** - 支持智能合约交互

### 4. 用户体验 🎨
- **零配置** - Agent 自己生成密钥
- **易于备份** - 只需保存私钥
- **跨平台** - 私钥可在任何地方使用
- **透明** - 所有操作可链上验证

### 5. 可扩展性 📈
- **支持多链** - 同一私钥可用于多条链
- **支持 DID** - 兼容去中心化身份标准
- **支持 ENS** - 可绑定域名
- **支持多签** - 可实现多 Agent 协作

---

## 📋 实施计划

### Phase 1: 核心实现 (1-2 天)
- [ ] 实现签名验证工具函数
- [ ] 创建 Agent SDK
- [ ] 实现新的注册端点
- [ ] 实现签名认证中间件

### Phase 2: 迁移 (1 天)
- [ ] 创建新的数据库表
- [ ] 编写迁移脚本
- [ ] 测试迁移流程

### Phase 3: 集成 (2-3 天)
- [ ] 更新所有 API 端点
- [ ] 更新前端集成
- [ ] 更新文档

### Phase 4: 测试 (1-2 天)
- [ ] 单元测试
- [ ] 集成测试
- [ ] 安全测试
- [ ] 性能测试

### Phase 5: 部署 (1 天)
- [ ] 灰度发布
- [ ] 监控和调优
- [ ] 正式上线

**总计**: 6-9 天

---

## 🚀 下一步行动

1. **评审方案** - 团队讨论和确认
2. **创建 SDK** - 实现 Agent 客户端库
3. **实现认证** - 服务器端签名验证
4. **编写测试** - 确保安全性
5. **更新文档** - 开发者指南

---

## 💡 总结

**这是一个革命性的改进！**

从传统的"用户名+密码+API Key"模式，升级到"公私钥密码学"模式，不仅简化了架构，还提升了安全性，并且与区块链完美融合。

**核心价值**:
- 🔐 更安全 - 密码学级别认证
- ✨ 更简洁 - 一个标识符解决所有问题
- ⛓️ 更原生 - 区块链天然兼容
- 🚀 更先进 - 符合 Web3 理念

这将使 Nautilus 成为真正的 **Agent-First** 平台！

---

*Nautilus Agent Identity Optimization - 2026-03-02*
