# 🚨 安全问题优先级清单

**更新时间**: 2026-03-02
**审计员**: 安全审计师 Agent
**状态**: 🔴 需要立即行动

---

## 📊 问题统计

| 优先级 | 数量 | 状态 | 截止日期 |
|--------|------|------|----------|
| P0 (严重) | 3 | 🔴 待修复 | 2026-03-05 |
| P1 (高危) | 2 | 🟠 待修复 | 2026-03-15 |
| P2 (中危) | 1 | 🟡 计划中 | 2026-04-02 |

---

## 🔴 P0 - 立即修复 (本周内)

### P0-1: Agent 自主注册缺少 CAPTCHA 验证

**严重程度**: 🔴 HIGH
**文件**: `api/agents.py:597-639`
**发现日期**: 2026-03-02
**截止日期**: 2026-03-05 (3天内)

**问题描述**:
- 任何人可以创建无限数量的 Agent 账户
- 速率限制不足 (仅 3 次/小时)
- 缺少 CAPTCHA 验证
- 无邮箱验证流程

**影响**:
- 大量垃圾账户
- 资源耗尽
- 系统滥用
- 数据库污染

**修复任务**:
- [ ] 集成 Google reCAPTCHA v3
- [ ] 添加 CAPTCHA 验证中间件
- [ ] 实施邮箱验证流程
- [ ] 增强速率限制 (3/hour + 10/day + 50/month)
- [ ] 添加 IP 黑名单机制
- [ ] 编写测试用例

**预计工作量**: 2-3 天
**负责人**: 待分配
**依赖**: reCAPTCHA API 密钥

---

### P0-2: OAuth State 验证缺失

**严重程度**: 🔴 HIGH
**文件**: `api/auth.py:405-438`
**发现日期**: 2026-03-02
**截止日期**: 2026-03-05 (3天内)

**问题描述**:
- GitHub OAuth 回调未验证 state 参数
- 易受 CSRF 攻击
- State 生成后未存储
- 回调时未验证 state 有效性

**影响**:
- 攻击者可以劫持 OAuth 流程
- 恶意账户绑定
- 用户账户被接管

**修复任务**:
- [ ] 在 Redis 中存储 state (5分钟过期)
- [ ] 回调时验证 state 有效性
- [ ] 使用后立即删除 state
- [ ] 添加 state 重放检测
- [ ] 编写测试用例

**预计工作量**: 1 天
**负责人**: 待分配
**依赖**: Redis 连接

---

### P0-3: API Key 明文存储

**严重程度**: 🔴 MEDIUM-HIGH
**文件**: `models/database.py:164`
**发现日期**: 2026-03-02
**截止日期**: 2026-03-05 (3天内)

**问题描述**:
- API Key 以明文形式存储在数据库中
- 数据库泄露时所有 API Key 暴露
- 无法撤销已泄露的 Key

**影响**:
- 数据库泄露风险
- API Key 批量泄露
- 账户被盗用

**修复任务**:
- [ ] 修改数据库模型 (添加 key_hash 字段)
- [ ] 实施 SHA256 哈希存储
- [ ] 更新 API Key 创建逻辑
- [ ] 更新 API Key 验证逻辑
- [ ] 编写数据迁移脚本
- [ ] 通知现有用户重新生成 API Key
- [ ] 编写测试用例

**预计工作量**: 1-2 天
**负责人**: 待分配
**依赖**: 数据库迁移工具

---

## 🟠 P1 - 短期修复 (1-2周内)

### P1-1: 钱包地址生成缺少私钥管理

**严重程度**: 🟠 MEDIUM
**文件**: `api/agents.py:556-565`
**发现日期**: 2026-03-02
**截止日期**: 2026-03-15 (2周内)

**问题描述**:
- 生成的钱包地址没有对应私钥
- 用户无法访问钱包资金
- 功能不完整

**影响**:
- 钱包地址无法使用
- 用户体验差
- 功能缺陷

**修复方案** (推荐选项 2):

**选项 1: 加密存储私钥**
- 使用 Fernet 加密私钥
- 存储到数据库
- 提供私钥导出功能

**选项 2: 用户自带钱包** (推荐)
- 要求用户提供钱包地址
- 通过签名验证所有权
- 用户控制私钥

**修复任务**:
- [ ] 实施用户自带钱包方案
- [ ] 添加钱包签名验证
- [ ] 更新注册流程
- [ ] 更新 API 文档
- [ ] 编写测试用例

**预计工作量**: 2-3 天
**负责人**: 待分配
**依赖**: eth_account 库

---

### P1-2: 增强监控和告警

**严重程度**: 🟠 MEDIUM
**文件**: 多个文件
**发现日期**: 2026-03-02
**截止日期**: 2026-03-15 (2周内)

**问题描述**:
- 缺少异常行为检测
- 告警机制不完善
- 无 IP 黑名单机制

**影响**:
- 无法及时发现攻击
- 响应时间慢
- 安全事件遗漏

**修复任务**:
- [ ] 实施异常注册检测
- [ ] 添加暴力破解告警
- [ ] 实施 IP 黑名单机制
- [ ] 配置 Prometheus 告警规则
- [ ] 集成 AlertManager
- [ ] 编写告警处理文档

**预计工作量**: 3-5 天
**负责人**: 待分配
**依赖**: Prometheus, AlertManager

---

## 🟡 P2 - 中期改进 (1个月内)

### P2-1: Agent 身份系统完善 (可选)

**严重程度**: 🟡 LOW
**文件**: 新功能
**发现日期**: 2026-03-02
**截止日期**: 2026-04-02 (1个月内)

**问题描述**:
- 当前使用 API Key + HMAC 签名
- 缺少基于公钥的身份验证
- 无 Agent 身份证书机制

**影响**:
- 身份验证不够强
- 无法实现去中心化身份
- 功能不完整

**修复任务** (可选):
- [ ] 添加 Agent 公钥字段
- [ ] 实施 Ed25519 签名验证
- [ ] 创建 Agent 身份证书
- [ ] 实施证书轮换机制
- [ ] 更新 API 文档
- [ ] 编写测试用例

**预计工作量**: 5-7 天
**负责人**: 待分配
**依赖**: cryptography 库

**注意**: 当前的 API Key + HMAC 签名已足够，此项为可选增强

---

## 📋 修复检查清单

### P0 修复前检查

- [ ] 创建功能分支
- [ ] 备份数据库
- [ ] 准备回滚方案
- [ ] 通知团队成员

### P0 修复中检查

- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 代码审查
- [ ] 安全审查

### P0 修复后检查

- [ ] 所有测试通过
- [ ] 手动测试验证
- [ ] 性能测试
- [ ] 安全扫描
- [ ] 更新文档
- [ ] 部署到测试环境
- [ ] 验证修复效果
- [ ] 部署到生产环境
- [ ] 监控告警

---

## 🔧 修复代码模板

### P0-1: CAPTCHA 验证

```python
# api/agents.py

from fastapi import Header
import httpx
import os

async def verify_captcha(captcha_token: str) -> bool:
    """验证 reCAPTCHA token"""
    secret = os.getenv("RECAPTCHA_SECRET_KEY")
    if not secret:
        raise ValueError("RECAPTCHA_SECRET_KEY not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": secret,
                "response": captcha_token
            },
            timeout=5.0
        )
        result = response.json()
        return result.get("success", False) and result.get("score", 0) >= 0.5

@router.post("/register", response_model=AgentSelfRegisterResponse)
@limiter.limit("3/hour")
@limiter.limit("10/day")
@limiter.limit("50/month")
async def agent_self_register(
    request: Request,
    agent_data: AgentSelfRegister,
    captcha_token: str = Header(..., alias="X-Captcha-Token"),
    db: Session = Depends(get_db)
):
    """Agent 自主注册 (需要 CAPTCHA)"""

    # 验证 CAPTCHA
    if not await verify_captcha(captcha_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA verification failed"
        )

    # 继续注册流程...
```

### P0-2: OAuth State 验证

```python
# api/auth.py

from utils.cache import get_cache
import secrets

@router.get("/github/login")
@limiter.limit("10/minute")
async def github_login(request: Request):
    """启动 GitHub OAuth 登录"""

    if not GITHUB_CLIENT_ID or not GITHUB_REDIRECT_URI:
        raise HTTPException(500, "GitHub OAuth not configured")

    # 生成并存储 state
    state = secrets.token_urlsafe(32)
    cache = get_cache()
    cache.set(f"oauth_state:{state}", "pending", ttl=300)  # 5分钟过期

    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
        f"&state={state}"
    )

    return RedirectResponse(url=github_auth_url)

@router.get("/github/callback")
@limiter.limit("10/minute")
async def github_callback(
    request: Request,
    code: str,
    state: str,  # 必需参数
    db: Session = Depends(get_db)
):
    """GitHub OAuth 回调"""

    # 验证 state
    cache = get_cache()
    stored_state = cache.get(f"oauth_state:{state}")

    if not stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state"
        )

    # 使用后立即删除
    cache.delete(f"oauth_state:{state}")

    # 继续 OAuth 流程...
```

### P0-3: API Key 哈希存储

```python
# utils/auth.py

import hashlib

def hash_api_key(api_key: str) -> str:
    """哈希 API Key 使用 SHA256"""
    return hashlib.sha256(api_key.encode()).hexdigest()

# api/agents.py

@router.post("/{agent_id}/api-keys")
async def create_api_key(
    agent_id: int,
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建 API Key"""

    # 生成原始 API Key
    raw_key = generate_api_key()

    # 哈希后存储
    hashed_key = hash_api_key(raw_key)

    api_key_obj = APIKey(
        key=hashed_key,  # 存储哈希值
        agent_id=agent_id,
        name=key_data.name,
        is_active=True
    )

    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)

    # 只返回一次原始 Key
    return {
        "id": api_key_obj.id,
        "api_key": raw_key,  # 用户需要保存
        "name": api_key_obj.name,
        "created_at": api_key_obj.created_at,
        "message": "⚠️ Please save this API key. It will not be shown again."
    }

# utils/auth.py

async def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Agent:
    """通过 API Key 获取当前 Agent"""

    api_key = credentials.credentials

    # 验证格式
    prefix = os.getenv("API_KEY_PREFIX", "nau_")
    if not api_key.startswith(prefix):
        raise HTTPException(401, "Invalid API key format")

    # 哈希后查询
    hashed_key = hash_api_key(api_key)
    api_key_obj = db.query(APIKey).filter(APIKey.key == hashed_key).first()

    if not api_key_obj:
        record_api_key_usage(api_key_id="unknown", valid=False)
        raise HTTPException(401, "Invalid API key")

    if not api_key_obj.is_active:
        record_api_key_usage(api_key_id=api_key_obj.agent_id, valid=False)
        raise HTTPException(403, "Inactive API key")

    # 记录使用
    record_api_key_usage(api_key_id=api_key_obj.agent_id, valid=True)
    api_key_obj.last_used_at = datetime.now(UTC)
    db.commit()

    # 获取 Agent
    agent = db.query(Agent).filter(Agent.agent_id == api_key_obj.agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")

    return agent
```

---

## 📊 进度跟踪

### 本周目标 (2026-03-02 至 2026-03-08)

| 任务 | 状态 | 负责人 | 进度 | 备注 |
|------|------|--------|------|------|
| P0-1: CAPTCHA 验证 | 🔴 待开始 | - | 0% | 需要 reCAPTCHA 密钥 |
| P0-2: OAuth State | 🔴 待开始 | - | 0% | 依赖 Redis |
| P0-3: API Key 哈希 | 🔴 待开始 | - | 0% | 需要数据迁移 |

### 下周目标 (2026-03-09 至 2026-03-15)

| 任务 | 状态 | 负责人 | 进度 | 备注 |
|------|------|--------|------|------|
| P1-1: 钱包管理 | 🟠 计划中 | - | 0% | 等待 P0 完成 |
| P1-2: 监控告警 | 🟠 计划中 | - | 0% | 等待 P0 完成 |

---

## 🔔 通知和沟通

### 需要通知的人员

- [ ] 项目负责人
- [ ] 开发团队
- [ ] 运维团队
- [ ] 安全团队

### 沟通内容

1. **P0 问题严重性**: 需要立即修复
2. **修复时间表**: 本周内完成
3. **资源需求**: 开发人员、测试环境
4. **风险评估**: 不修复的后果
5. **修复计划**: 详细步骤和时间表

---

## 📞 联系方式

**安全审计师**: 安全审计师 Agent
**报告日期**: 2026-03-02
**下次更新**: 2026-03-05 (3天后)

**紧急联系**: security@nautilus.example.com

---

*此清单将持续更新，直到所有问题修复完成。*
