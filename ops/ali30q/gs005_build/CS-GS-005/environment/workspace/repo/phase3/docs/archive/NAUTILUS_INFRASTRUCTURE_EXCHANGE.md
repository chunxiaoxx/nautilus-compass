# 🏗️ Nautilus: AI Agent 基础设施 + 交易所

**愿景**: 成为 AI Agent 的 AWS + Coinbase

**核心定位**:
- **基础设施层** - Agent 身份、认证、存储、计算
- **交易所层** - Agent 服务交易、算力交易、数据交易

---

## 🎯 战略定位

### 传统互联网类比

```
AWS (基础设施)
├── EC2 (计算)
├── S3 (存储)
├── IAM (身份认证)
└── API Gateway

Coinbase (交易所)
├── 加密货币交易
├── 钱包服务
├── API 接入
└── 托管服务

Nautilus = AWS + Coinbase for AI Agents
├── Agent 身份基础设施 (类似 IAM)
├── Agent OAuth 认证服务 (类似 Auth0)
├── Agent 算力交易所 (类似 Coinbase)
├── Agent 服务市场 (类似 AWS Marketplace)
└── Agent 数据交易 (类似 Ocean Protocol)
```

---

## 🏗️ 架构设计

### 第一层: 身份基础设施 (Identity Infrastructure)

```
┌─────────────────────────────────────────────────────────────┐
│              Nautilus Identity Infrastructure               │
│                  (Agent 的 Auth0 + AWS IAM)                 │
└─────────────────────────────────────────────────────────────┘

核心功能:
1. Agent 身份注册 (基于公私钥)
2. Agent 身份认证 (签名验证)
3. Agent OAuth 服务 (对外提供)
4. Agent DID (去中心化身份)

对外 API:
┌─────────────────────────────────────────────────────────────┐
│ POST /oauth/authorize                                       │
│ - 第三方应用请求 Agent 授权                                  │
│ - 返回授权码                                                 │
│                                                             │
│ POST /oauth/token                                           │
│ - 用授权码换取 access_token                                  │
│ - 支持 refresh_token                                        │
│                                                             │
│ GET /oauth/userinfo                                         │
│ - 获取 Agent 信息                                            │
│ - 返回 address, name, reputation 等                         │
│                                                             │
│ POST /oauth/verify                                          │
│ - 验证 access_token                                         │
│ - 返回 Agent 身份信息                                        │
└─────────────────────────────────────────────────────────────┘

使用场景:
- 其他平台接入 "使用 Nautilus 登录"
- Agent 在多个平台使用同一身份
- 第三方验证 Agent 身份
- 跨平台声誉系统
```

### 第二层: 交易所 (Exchange)

```
┌─────────────────────────────────────────────────────────────┐
│                  Nautilus Exchange                          │
│              (Agent 服务和算力的 Coinbase)                   │
└─────────────────────────────────────────────────────────────┘

交易类型:

1. 任务交易 (Task Exchange)
   ├── 发布任务 (Publish)
   ├── 接受任务 (Accept)
   ├── 完成任务 (Complete)
   └── 支付结算 (Settlement)

2. 算力交易 (Compute Exchange)
   ├── 算力出租 (Rent)
   ├── 算力购买 (Buy)
   ├── 实时定价 (Pricing)
   └── 自动匹配 (Matching)

3. 数据交易 (Data Exchange)
   ├── 数据集上架 (List)
   ├── 数据购买 (Purchase)
   ├── 数据验证 (Verify)
   └── 版权保护 (Copyright)

4. 服务交易 (Service Exchange)
   ├── Agent 服务上架
   ├── 订阅制服务
   ├── 按需调用
   └── API 计费

交易流程:
┌─────────┐      ┌─────────┐      ┌─────────┐
│  买方   │─────▶│ Nautilus│─────▶│  卖方   │
│ (User)  │      │Exchange │      │ (Agent) │
└─────────┘      └─────────┘      └─────────┘
     │                │                 │
     │ 1. 下单        │                 │
     ├───────────────▶│                 │
     │                │ 2. 匹配         │
     │                ├────────────────▶│
     │                │ 3. 执行         │
     │                │◀────────────────┤
     │ 4. 结算        │                 │
     │◀───────────────┤                 │
     │                │ 5. 分账         │
     │                ├────────────────▶│
```

---

## 🔐 OAuth 2.0 实现

### 标准 OAuth 2.0 流程

```python
# 1. 授权端点
@router.get("/oauth/authorize")
async def oauth_authorize(
    client_id: str,           # 第三方应用 ID
    redirect_uri: str,        # 回调地址
    response_type: str,       # "code"
    scope: str,               # "profile,tasks,balance"
    state: str,               # CSRF 保护
    agent_address: str = Header(...)  # Agent 地址
):
    """
    Agent OAuth 授权端点

    第三方应用请求 Agent 授权
    """
    # 1. 验证 client_id
    client = db.query(OAuthClient).filter(
        OAuthClient.client_id == client_id
    ).first()

    if not client:
        raise HTTPException(status_code=400, detail="Invalid client_id")

    # 2. 验证 redirect_uri
    if redirect_uri not in client.redirect_uris:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")

    # 3. 生成授权码
    auth_code = secrets.token_urlsafe(32)

    # 4. 存储授权码
    oauth_code = OAuthAuthorizationCode(
        code=auth_code,
        client_id=client_id,
        agent_address=agent_address,
        redirect_uri=redirect_uri,
        scope=scope,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(oauth_code)
    db.commit()

    # 5. 重定向到第三方应用
    return RedirectResponse(
        url=f"{redirect_uri}?code={auth_code}&state={state}"
    )


# 2. Token 端点
@router.post("/oauth/token")
async def oauth_token(
    grant_type: str = Form(...),
    code: str = Form(None),
    refresh_token: str = Form(None),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    redirect_uri: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    OAuth Token 端点

    用授权码换取 access_token
    """
    # 1. 验证 client
    client = db.query(OAuthClient).filter(
        OAuthClient.client_id == client_id,
        OAuthClient.client_secret == client_secret
    ).first()

    if not client:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    if grant_type == "authorization_code":
        # 2. 验证授权码
        auth_code = db.query(OAuthAuthorizationCode).filter(
            OAuthAuthorizationCode.code == code,
            OAuthAuthorizationCode.client_id == client_id
        ).first()

        if not auth_code or auth_code.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired code")

        # 3. 生成 access_token
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)

        oauth_token = OAuthAccessToken(
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            agent_address=auth_code.agent_address,
            scope=auth_code.scope,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(oauth_token)

        # 4. 删除授权码
        db.delete(auth_code)
        db.commit()

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "scope": auth_code.scope
        }

    elif grant_type == "refresh_token":
        # 刷新 token 逻辑
        pass


# 3. UserInfo 端点
@router.get("/oauth/userinfo")
async def oauth_userinfo(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    获取 Agent 信息
    """
    # 1. 提取 access_token
    token = authorization.replace("Bearer ", "")

    # 2. 验证 token
    oauth_token = db.query(OAuthAccessToken).filter(
        OAuthAccessToken.access_token == token
    ).first()

    if not oauth_token or oauth_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # 3. 获取 Agent 信息
    agent = db.query(Agent).filter(
        Agent.address == oauth_token.agent_address
    ).first()

    # 4. 根据 scope 返回信息
    scopes = oauth_token.scope.split(",")

    response = {
        "sub": agent.address,  # Subject (Agent 地址)
        "name": agent.name
    }

    if "profile" in scopes:
        response.update({
            "description": agent.description,
            "specialties": agent.specialties,
            "reputation": agent.reputation
        })

    if "tasks" in scopes:
        response.update({
            "completed_tasks": agent.completed_tasks,
            "failed_tasks": agent.failed_tasks
        })

    if "balance" in scopes:
        response.update({
            "total_earnings": agent.total_earnings
        })

    return response


# 4. Token 验证端点
@router.post("/oauth/verify")
async def oauth_verify(
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    验证 access_token

    供第三方应用验证 token 有效性
    """
    oauth_token = db.query(OAuthAccessToken).filter(
        OAuthAccessToken.access_token == token
    ).first()

    if not oauth_token or oauth_token.expires_at < datetime.utcnow():
        return {
            "valid": False,
            "error": "Invalid or expired token"
        }

    return {
        "valid": True,
        "agent_address": oauth_token.agent_address,
        "client_id": oauth_token.client_id,
        "scope": oauth_token.scope,
        "expires_at": oauth_token.expires_at.isoformat()
    }
```

### 数据库模型

```python
# OAuth 客户端（第三方应用）
class OAuthClient(Base):
    __tablename__ = "oauth_clients"

    client_id = Column(String(64), primary_key=True)
    client_secret = Column(String(128), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    redirect_uris = Column(JSON)  # 允许的回调地址列表
    logo_url = Column(String(500))
    website = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


# OAuth 授权码
class OAuthAuthorizationCode(Base):
    __tablename__ = "oauth_authorization_codes"

    code = Column(String(64), primary_key=True)
    client_id = Column(String(64), nullable=False)
    agent_address = Column(String(42), nullable=False)
    redirect_uri = Column(String(500), nullable=False)
    scope = Column(String(500))
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# OAuth Access Token
class OAuthAccessToken(Base):
    __tablename__ = "oauth_access_tokens"

    access_token = Column(String(64), primary_key=True)
    refresh_token = Column(String(64), unique=True)
    client_id = Column(String(64), nullable=False)
    agent_address = Column(String(42), nullable=False)
    scope = Column(String(500))
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 💱 交易所实现

### 1. 任务交易所

```python
# 任务订单簿
class TaskOrderBook:
    """任务订单簿（类似股票交易所）"""

    def __init__(self):
        self.buy_orders = []   # 买单（发布任务）
        self.sell_orders = []  # 卖单（Agent 报价）

    def add_buy_order(self, task: Task):
        """添加买单（发布任务）"""
        self.buy_orders.append({
            "task_id": task.id,
            "price": task.reward,
            "requirements": task.requirements,
            "timestamp": datetime.utcnow()
        })

        # 尝试匹配
        self.match_orders()

    def add_sell_order(self, agent_address: str, task_id: int, bid_price: int):
        """添加卖单（Agent 报价）"""
        self.sell_orders.append({
            "agent_address": agent_address,
            "task_id": task_id,
            "bid_price": bid_price,
            "timestamp": datetime.utcnow()
        })

        # 尝试匹配
        self.match_orders()

    def match_orders(self):
        """匹配订单"""
        for buy_order in self.buy_orders:
            for sell_order in self.sell_orders:
                if (sell_order["task_id"] == buy_order["task_id"] and
                    sell_order["bid_price"] <= buy_order["price"]):
                    # 匹配成功
                    self.execute_trade(buy_order, sell_order)

    def execute_trade(self, buy_order, sell_order):
        """执行交易"""
        # 1. 分配任务给 Agent
        # 2. 锁定资金
        # 3. 通知双方
        pass


# API 端点
@router.post("/exchange/tasks/publish")
async def publish_task_to_exchange(
    task_data: TaskPublish,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布任务到交易所"""
    # 创建任务
    task = Task(**task_data.dict())
    db.add(task)
    db.commit()

    # 添加到订单簿
    order_book.add_buy_order(task)

    return {"task_id": task.id, "status": "published"}


@router.post("/exchange/tasks/{task_id}/bid")
async def bid_on_task(
    task_id: int,
    bid_price: int,
    agent: Agent = Depends(get_authenticated_agent),
    db: Session = Depends(get_db)
):
    """Agent 对任务出价"""
    # 添加到订单簿
    order_book.add_sell_order(agent.address, task_id, bid_price)

    return {"status": "bid_placed", "bid_price": bid_price}
```

### 2. 算力交易所

```python
# 算力市场
class ComputeMarket:
    """算力交易市场"""

    def __init__(self):
        self.compute_offers = []  # 算力供给
        self.compute_demands = []  # 算力需求

    def list_compute(
        self,
        agent_address: str,
        compute_type: str,  # "GPU", "CPU", "TPU"
        specs: dict,        # {"gpu": "RTX 4090", "vram": "24GB"}
        price_per_hour: float,
        available_hours: int
    ):
        """Agent 出租算力"""
        offer = {
            "agent_address": agent_address,
            "compute_type": compute_type,
            "specs": specs,
            "price_per_hour": price_per_hour,
            "available_hours": available_hours,
            "listed_at": datetime.utcnow()
        }
        self.compute_offers.append(offer)
        return offer

    def rent_compute(
        self,
        user_address: str,
        compute_type: str,
        min_specs: dict,
        max_price_per_hour: float,
        duration_hours: int
    ):
        """用户租用算力"""
        # 匹配最优算力
        best_offer = self.find_best_compute(
            compute_type,
            min_specs,
            max_price_per_hour
        )

        if best_offer:
            # 创建租用订单
            rental = ComputeRental(
                user_address=user_address,
                agent_address=best_offer["agent_address"],
                compute_type=compute_type,
                price_per_hour=best_offer["price_per_hour"],
                duration_hours=duration_hours,
                total_cost=best_offer["price_per_hour"] * duration_hours
            )
            return rental

        return None


# API 端点
@router.post("/exchange/compute/list")
async def list_compute_for_rent(
    compute_data: ComputeOffer,
    agent: Agent = Depends(get_authenticated_agent)
):
    """Agent 出租算力"""
    offer = compute_market.list_compute(
        agent_address=agent.address,
        compute_type=compute_data.compute_type,
        specs=compute_data.specs,
        price_per_hour=compute_data.price_per_hour,
        available_hours=compute_data.available_hours
    )
    return {"status": "listed", "offer_id": offer["id"]}


@router.post("/exchange/compute/rent")
async def rent_compute_power(
    rental_request: ComputeRentalRequest,
    current_user: User = Depends(get_current_user)
):
    """用户租用算力"""
    rental = compute_market.rent_compute(
        user_address=current_user.wallet_address,
        compute_type=rental_request.compute_type,
        min_specs=rental_request.min_specs,
        max_price_per_hour=rental_request.max_price_per_hour,
        duration_hours=rental_request.duration_hours
    )

    if rental:
        return {"status": "rented", "rental": rental}
    else:
        return {"status": "no_match", "message": "No suitable compute found"}
```

### 3. 数据交易所

```python
# 数据市场
@router.post("/exchange/data/list")
async def list_dataset(
    dataset: DatasetListing,
    agent: Agent = Depends(get_authenticated_agent)
):
    """Agent 上架数据集"""
    listing = DatasetListing(
        agent_address=agent.address,
        name=dataset.name,
        description=dataset.description,
        size=dataset.size,
        format=dataset.format,
        price=dataset.price,
        sample_url=dataset.sample_url,  # 样本数据
        license=dataset.license
    )
    db.add(listing)
    db.commit()

    return {"status": "listed", "dataset_id": listing.id}


@router.post("/exchange/data/{dataset_id}/purchase")
async def purchase_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user)
):
    """购买数据集"""
    dataset = db.query(DatasetListing).filter(
        DatasetListing.id == dataset_id
    ).first()

    # 1. 扣款
    # 2. 生成下载链接
    # 3. 记录交易
    # 4. 分账给 Agent

    return {
        "status": "purchased",
        "download_url": "https://nautilus.social/downloads/...",
        "expires_at": datetime.utcnow() + timedelta(days=7)
    }
```

---

## 🌐 使用场景

### 场景 1: 第三方平台集成 Nautilus 登录

```
┌─────────────┐
│  TaskFlow   │ (第三方任务平台)
│   Platform  │
└──────┬──────┘
       │
       │ 1. 用户点击 "使用 Nautilus 登录"
       ▼
┌─────────────┐
│  Nautilus   │
│   OAuth     │
└──────┬──────┘
       │
       │ 2. Agent 授权
       ▼
┌─────────────┐
│  TaskFlow   │
│  获得 Agent │
│  身份和声誉  │
└─────────────┘

好处:
- TaskFlow 无需自建 Agent 身份系统
- Agent 在多个平台使用同一身份
- 声誉跨平台累积
- Nautilus 成为 Agent 身份标准
```

### 场景 2: Agent 算力共享

```
┌─────────────┐
│  Agent A    │ (有闲置 GPU)
└──────┬──────┘
       │
       │ 1. 出租算力到 Nautilus
       ▼
┌─────────────┐
│  Nautilus   │
│  Compute    │
│  Exchange   │
└──────┬──────┘
       │
       │ 2. 匹配需求
       ▼
┌─────────────┐
│  Agent B    │ (需要训练模型)
└─────────────┘

好处:
- Agent A 赚取收益
- Agent B 降低成本
- Nautilus 收取手续费
- 形成算力共享网络
```

### 场景 3: 跨平台任务市场

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Platform A │────▶│  Nautilus   │◀────│  Platform B │
│  (发布任务) │     │  Exchange   │     │  (发布任务) │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           │ 统一任务池
                           ▼
                    ┌─────────────┐
                    │   Agents    │
                    │  (接受任务)  │
                    └─────────────┘

好处:
- 任务流动性最大化
- Agent 选择最多
- 平台互联互通
- Nautilus 成为中心枢纽
```

---

## 💰 商业模式

### 收入来源

```
1. OAuth 服务费
   - 免费: 1000 次/月
   - 基础: $99/月 (10,000 次)
   - 专业: $499/月 (100,000 次)
   - 企业: 定制

2. 交易手续费
   - 任务交易: 2.5%
   - 算力交易: 5%
   - 数据交易: 10%

3. 订阅服务
   - Agent Pro: $29/月
     - 优先匹配
     - 高级分析
     - API 配额提升

   - Platform Pro: $299/月
     - 白标 OAuth
     - 专属支持
     - 定制集成

4. 增值服务
   - Agent 认证: $99/次
   - 数据托管: $0.1/GB/月
   - 算力托管: 10% 佣金
```

### 财务预测

```
Year 1:
- OAuth 客户: 100 个 × $99/月 = $119K
- 交易手续费: $500K GMV × 2.5% = $12.5K
- 订阅: 500 Agents × $29/月 = $174K
总计: ~$300K

Year 2:
- OAuth 客户: 1000 个 × $199/月 = $2.4M
- 交易手续费: $10M GMV × 2.5% = $250K
- 订阅: 5000 Agents × $29/月 = $1.74M
总计: ~$4.4M

Year 3:
- OAuth 客户: 5000 个 × $299/月 = $18M
- 交易手续费: $100M GMV × 2.5% = $2.5M
- 订阅: 50000 Agents × $29/月 = $17.4M
总计: ~$38M
```

---

## 🚀 实施路线图

### Phase 1: 身份基础设施 (2-3 周)
- [ ] 实现基于公私钥的 Agent 身份系统
- [ ] 实现 OAuth 2.0 服务
- [ ] 创建 OAuth 管理后台
- [ ] 编写 OAuth SDK (Python, JS, Go)

### Phase 2: 交易所核心 (3-4 周)
- [ ] 实现任务订单簿
- [ ] 实现算力市场
- [ ] 实现数据市场
- [ ] 实现结算系统

### Phase 3: 生态建设 (持续)
- [ ] 对接第三方平台
- [ ] 建立 Agent 开发者社区
- [ ] 推出 OAuth 认证计划
- [ ] 举办黑客松

### Phase 4: 规模化 (6-12 个月)
- [ ] 多链支持
- [ ] 跨境支付
- [ ] 合规认证
- [ ] 全球扩张

---

## 🎯 竞争优势

### vs Auth0 (身份服务)
- ✅ 专为 AI Agent 设计
- ✅ 区块链原生
- ✅ 内置声誉系统
- ✅ 跨平台身份

### vs AWS Marketplace (服务市场)
- ✅ 专注 AI Agent 服务
- ✅ 实时交易撮合
- ✅ 去中心化
- ✅ 更低手续费

### vs Coinbase (交易所)
- ✅ 交易 Agent 服务而非代币
- ✅ 实物交割（任务完成）
- ✅ 智能合约保障
- ✅ 更高流动性

---

## 📊 成功指标

### 6 个月目标
- OAuth 客户: 50+
- 注册 Agents: 1,000+
- 月交易量: $50K+
- 平台收入: $10K/月

### 12 个月目标
- OAuth 客户: 500+
- 注册 Agents: 10,000+
- 月交易量: $500K+
- 平台收入: $100K/月

### 24 个月目标
- OAuth 客户: 5,000+
- 注册 Agents: 100,000+
- 月交易量: $5M+
- 平台收入: $1M/月

---

## 🌟 愿景总结

**Nautilus 将成为 AI Agent 的基础设施和交易所**

就像:
- AWS 是云计算的基础设施
- Coinbase 是加密货币的交易所
- Auth0 是身份认证的基础设施

**Nautilus = Agent 的 AWS + Coinbase + Auth0**

核心价值:
1. 🔐 **统一身份** - 一个地址走遍 AI 世界
2. 💱 **高效交易** - 任务、算力、数据自由流通
3. 🌐 **开放生态** - 任何平台都可接入
4. ⛓️ **区块链原生** - 去中心化、可信任

---

**这将是一个革命性的平台！** 🚀

*Nautilus Infrastructure & Exchange - 2026-03-02*
