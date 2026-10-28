# 🚀 Nautilus Week 1 实施计划

**时间**: 2026-03-04 ~ 2026-03-10
**目标**: 完成开源准备 + 核心功能集成
**团队**: 三对话框协作模式

---

## 🎯 总体目标

### 核心交付物

1. ✅ Agent钱包无缝注册（前后端对接）
2. ✅ 任务市场UI优化
3. ✅ Agent信用评分系统
4. ✅ 轻量级能力继承
5. ✅ Agent自动充值
6. ✅ 任务模板系统
7. ✅ 完整文档和演示
8. ✅ 开源发布

---

## 👥 三对话框协作模式

### 对话框A - 开发执行

**角色**: 开发工程师
**职责**:
- 实现具体功能
- 编写单元测试
- 自测和调试
- 提交代码

**工作流程**:
```
1. 接收任务（来自对话框B）
2. 阅读技术规范
3. 实现功能
4. 自测通过
5. 提交审查（给对话框C）
```

### 对话框B - 架构规划（当前对话框）

**角色**: 架构师 + 项目经理
**职责**:
- 制定技术方案
- 分解任务
- 协调进度
- 最终验收

**工作流程**:
```
1. 设计技术方案
2. 生成详细任务
3. 分配给对话框A
4. 接收审查报告（来自对话框C）
5. 最终验收
```

### 对话框C - 质量保证（需新建）

**角色**: 代码审计 + 测试工程师
**职责**:
- 代码审查
- 集成测试
- 性能测试
- 安全审计

**工作流程**:
```
1. 接收代码（来自对话框A）
2. 代码审查
3. 集成测试
4. 生成审查报告
5. 反馈给对话框B
```

---

## 📅 Day-by-Day 详细计划

### Day 1 (今天晚上) - 准备和对齐

#### 对话框A任务
- [ ] 检查Agent钱包后端代码
- [ ] 列出已实现的API
- [ ] 列出缺失的功能
- [ ] 准备明天的开发环境

#### 对话框B任务（当前）
- [x] 生成完整技术文档 ✅
- [x] 生成任务清单 ✅
- [ ] 生成API对接规范
- [ ] 生成测试用例

#### 对话框C任务（新建）
- [ ] 创建对话框C
- [ ] 设置审查标准
- [ ] 准备测试环境
- [ ] 准备审查清单

**今晚交付物**:
- 完整技术文档
- 详细任务清单
- API对接规范
- 测试用例模板

---

### Day 2 - Agent钱包前后端对接

#### 对话框A任务（8小时）

**任务2.1: 检查后端API** (1小时)
```bash
# 检查已有的钱包相关API
cd backend
grep -r "wallet" api/
grep -r "agent.*register" api/

# 列出所有API端点
python -c "from main import app; print([route.path for route in app.routes])"
```

**期望输出**:
```
已有API列表：
- POST /api/agents/register
- GET /api/agents/{agent_id}
- POST /api/agents/{agent_id}/wallet
- ...

缺失API列表：
- POST /api/auth/wallet-login
- POST /api/agents/verify-signature
- ...
```

**任务2.2: 补充缺失的后端API** (2小时)

如果缺失，实现以下API：

```python
# backend/api/auth.py

from web3 import Web3
from eth_account.messages import encode_defunct
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/wallet-login")
async def wallet_login(
    address: str,
    signature: str,
    message: str,
    db: Session = Depends(get_db)
):
    """
    钱包登录

    流程：
    1. 验证签名
    2. 检查Agent是否存在
    3. 生成JWT Token
    4. 返回Token
    """

    # 1. 验证签名
    w3 = Web3()
    message_hash = encode_defunct(text=message)

    try:
        recovered_address = w3.eth.account.recover_message(
            message_hash,
            signature=signature
        )
    except Exception as e:
        raise HTTPException(400, f"Invalid signature: {str(e)}")

    if recovered_address.lower() != address.lower():
        raise HTTPException(400, "Signature verification failed")

    # 2. 检查Agent是否存在
    agent = db.query(Agent).filter(
        Agent.wallet_address == address.lower()
    ).first()

    if not agent:
        raise HTTPException(404, "Agent not found. Please register first.")

    # 3. 生成JWT Token
    from datetime import datetime, timedelta
    import jwt

    token_data = {
        "agent_id": agent.id,
        "wallet_address": address.lower(),
        "exp": datetime.utcnow() + timedelta(days=7)
    }

    token = jwt.encode(
        token_data,
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )

    # 4. 返回Token
    return {
        "access_token": token,
        "token_type": "bearer",
        "agent_id": agent.id,
        "wallet_address": address.lower()
    }


@router.post("/wallet-register")
async def wallet_register(
    address: str,
    signature: str,
    message: str,
    agent_name: str,
    agent_description: str = "",
    db: Session = Depends(get_db)
):
    """
    钱包注册

    流程：
    1. 验证签名
    2. 检查是否已注册
    3. 创建Agent
    4. 生成JWT Token
    5. 返回Token
    """

    # 1. 验证签名
    w3 = Web3()
    message_hash = encode_defunct(text=message)

    try:
        recovered_address = w3.eth.account.recover_message(
            message_hash,
            signature=signature
        )
    except Exception as e:
        raise HTTPException(400, f"Invalid signature: {str(e)}")

    if recovered_address.lower() != address.lower():
        raise HTTPException(400, "Signature verification failed")

    # 2. 检查是否已注册
    existing_agent = db.query(Agent).filter(
        Agent.wallet_address == address.lower()
    ).first()

    if existing_agent:
        raise HTTPException(400, "Agent already registered")

    # 3. 创建Agent
    agent = Agent(
        wallet_address=address.lower(),
        name=agent_name,
        description=agent_description,
        credit_score=100,  # 初始信用分
        status="active",
        created_at=datetime.utcnow()
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    # 4. 生成JWT Token
    token_data = {
        "agent_id": agent.id,
        "wallet_address": address.lower(),
        "exp": datetime.utcnow() + timedelta(days=7)
    }

    token = jwt.encode(
        token_data,
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )

    # 5. 返回Token
    return {
        "access_token": token,
        "token_type": "bearer",
        "agent_id": agent.id,
        "wallet_address": address.lower(),
        "credit_score": 100
    }
```

**任务2.3: 实现前端钱包集成** (3小时)

```typescript
// frontend/src/hooks/useWalletAuth.ts

import { useAccount, useConnect, useDisconnect, useSignMessage } from 'wagmi'
import { MetaMaskConnector } from 'wagmi/connectors/metaMask'
import { useState } from 'react'
import axios from 'axios'

export function useWalletAuth() {
  const { address, isConnected } = useAccount()
  const { connect } = useConnect({
    connector: new MetaMaskConnector(),
  })
  const { disconnect } = useDisconnect()
  const { signMessageAsync } = useSignMessage()

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * 钱包登录
   */
  const login = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // 1. 连接钱包
      if (!isConnected) {
        await connect()
      }

      // 2. 生成签名消息
      const message = `Login to Nautilus\nAddress: ${address}\nTimestamp: ${Date.now()}`

      // 3. 请求签名
      const signature = await signMessageAsync({ message })

      // 4. 发送到后端验证
      const response = await axios.post('/api/auth/wallet-login', {
        address,
        signature,
        message
      })

      // 5. 保存Token
      const { access_token, agent_id } = response.data
      localStorage.setItem('auth_token', access_token)
      localStorage.setItem('agent_id', agent_id)

      return { success: true, agent_id }

    } catch (err: any) {
      console.error('Login failed:', err)
      setError(err.response?.data?.detail || err.message)
      return { success: false, error: err.message }
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * 钱包注册
   */
  const register = async (agentName: string, agentDescription: string = '') => {
    try {
      setIsLoading(true)
      setError(null)

      // 1. 连接钱包
      if (!isConnected) {
        await connect()
      }

      // 2. 生成签名消息
      const message = `Register Agent on Nautilus\nAddress: ${address}\nName: ${agentName}\nTimestamp: ${Date.now()}`

      // 3. 请求签名
      const signature = await signMessageAsync({ message })

      // 4. 发送到后端注册
      const response = await axios.post('/api/auth/wallet-register', {
        address,
        signature,
        message,
        agent_name: agentName,
        agent_description: agentDescription
      })

      // 5. 保存Token
      const { access_token, agent_id } = response.data
      localStorage.setItem('auth_token', access_token)
      localStorage.setItem('agent_id', agent_id)

      return { success: true, agent_id }

    } catch (err: any) {
      console.error('Registration failed:', err)
      setError(err.response?.data?.detail || err.message)
      return { success: false, error: err.message }
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * 登出
   */
  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('agent_id')
    disconnect()
  }

  return {
    address,
    isConnected,
    isLoading,
    error,
    login,
    register,
    logout
  }
}
```

```typescript
// frontend/src/components/WalletAuth.tsx

import React, { useState } from 'react'
import { useWalletAuth } from '../hooks/useWalletAuth'

export function WalletAuth() {
  const { address, isConnected, isLoading, error, login, register, logout } = useWalletAuth()
  const [showRegister, setShowRegister] = useState(false)
  const [agentName, setAgentName] = useState('')
  const [agentDescription, setAgentDescription] = useState('')

  const handleLogin = async () => {
    const result = await login()
    if (result.success) {
      alert('Login successful!')
      window.location.href = '/dashboard'
    }
  }

  const handleRegister = async () => {
    if (!agentName) {
      alert('Please enter agent name')
      return
    }

    const result = await register(agentName, agentDescription)
    if (result.success) {
      alert('Registration successful!')
      window.location.href = '/dashboard'
    }
  }

  if (isConnected && localStorage.getItem('auth_token')) {
    return (
      <div className="wallet-auth">
        <div className="wallet-info">
          <span>Connected: {address?.slice(0, 6)}...{address?.slice(-4)}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </div>
    )
  }

  return (
    <div className="wallet-auth">
      {!showRegister ? (
        <div className="login-section">
          <h2>Login with Wallet</h2>
          <button
            onClick={handleLogin}
            disabled={isLoading}
          >
            {isLoading ? 'Connecting...' : 'Connect Wallet & Login'}
          </button>
          <p>
            Don't have an agent?
            <button onClick={() => setShowRegister(true)}>Register</button>
          </p>
        </div>
      ) : (
        <div className="register-section">
          <h2>Register Agent</h2>
          <input
            type="text"
            placeholder="Agent Name"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
          />
          <textarea
            placeholder="Agent Description (optional)"
            value={agentDescription}
            onChange={(e) => setAgentDescription(e.target.value)}
          />
          <button
            onClick={handleRegister}
            disabled={isLoading}
          >
            {isLoading ? 'Registering...' : 'Register Agent'}
          </button>
          <p>
            Already have an agent?
            <button onClick={() => setShowRegister(false)}>Login</button>
          </p>
        </div>
      )}

      {error && <div className="error">{error}</div>}
    </div>
  )
}
```

**任务2.4: 测试和调试** (2小时)

测试清单：
- [ ] 钱包连接成功
- [ ] 签名生成正确
- [ ] 注册流程完整
- [ ] 登录流程完整
- [ ] Token保存正确
- [ ] 登出功能正常

**交付物**:
- 完整的钱包登录/注册功能
- 前后端完全对接
- 测试通过报告

---

#### 对话框C任务（2小时）

**审查清单**:
```
代码审查：
- [ ] 签名验证逻辑正确
- [ ] 没有安全漏洞
- [ ] 错误处理完善
- [ ] 代码风格一致

功能测试：
- [ ] 注册流程测试
- [ ] 登录流程测试
- [ ] 错误场景测试
- [ ] 边界条件测试

性能测试：
- [ ] 响应时间 < 2秒
- [ ] 并发测试通过
```

**交付物**:
- Day 2审查报告
- 问题清单
- 修复建议

---

### Day 3 - 信用系统 + 能力继承

#### 对话框A任务（8小时）

**任务3.1: 实现信用评分系统** (4小时)

参考前面的`CreditScoreCalculator`代码

**任务3.2: 实现轻量级能力继承** (4小时)

参考前面的`CapabilityInheritance`代码

**交付物**:
- 信用评分系统
- 能力继承系统
- 单元测试

---

#### 对话框C任务（2小时）

**审查重点**:
- 评分算法合理性
- 经验提取准确性
- 性能影响评估

---

### Day 4 - 自动充值 + 任务模板

#### 对话框A任务（8小时）

**任务4.1: Agent自动充值** (4小时)
**任务4.2: 任务模板系统** (4小时)

---

### Day 5 - 文档和演示

#### 对话框A任务（8小时）

**任务5.1: 完善文档** (4小时)
**任务5.2: 录制演示视频** (4小时)

---

### Day 6-7 - 发布和推广

#### 对话框B任务（主导）

**任务6.1: 发布准备**
**任务6.2: 社区运营**

---

## 🔄 协作流程图

```
Day N开始：
  ↓
对话框B: 生成详细任务
  ↓
对话框A: 接收任务，开始开发
  ↓
对话框A: 完成开发，自测通过
  ↓
对话框C: 代码审查 + 测试
  ↓
对话框C: 生成审查报告
  ↓
对话框B: 审查报告 → 决策
  ├─ 通过 → 验收完成
  └─ 不通过 → 返回对话框A修复
```

---

## 📊 进度追踪

### 每日站会（15分钟）

**对话框A报告**:
- 昨天完成了什么
- 今天计划做什么
- 遇到什么阻碍

**对话框C报告**:
- 审查了什么
- 发现了什么问题
- 建议是什么

**对话框B决策**:
- 调整优先级
- 解决阻碍
- 分配新任务

---

## ⚠️ 风险管理

### 已识别风险

**风险1: 前后端对接问题**
- 概率: 高
- 影响: 高
- 缓解: 详细的API规范 + 对话框C审查

**风险2: 时间不足**
- 概率: 中
- 影响: 高
- 缓解: 优先级排序 + 可选功能后置

**风险3: 质量问题**
- 概率: 中
- 影响: 高
- 缓解: 对话框C严格审查

---

## ✅ 验收标准

### Day 2验收
- [ ] 钱包登录/注册完整可用
- [ ] 前后端完全对接
- [ ] 代码审查通过
- [ ] 测试覆盖率 > 80%

### Day 3验收
- [ ] 信用评分系统可用
- [ ] 能力继承系统可用
- [ ] 代码审查通过

### Day 4验收
- [ ] 自动充值功能可用
- [ ] 任务模板系统可用
- [ ] 代码审查通过

### Day 5验收
- [ ] 文档完整
- [ ] 演示视频完成
- [ ] 所有功能集成测试通过

### Day 6-7验收
- [ ] 成功发布到GitHub
- [ ] 成功发布到至少3个平台
- [ ] 社区初步建立

---

**文档版本**: 1.0
**创建时间**: 2026-03-04
**负责人**: 对话框B（架构师）
**审查人**: 对话框C（质量保证）
