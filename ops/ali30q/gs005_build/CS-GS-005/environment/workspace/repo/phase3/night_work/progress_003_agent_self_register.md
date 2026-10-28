# 夜间工作进度报告 #003 - Agent 自主注册 API

**时间**: 2026-03-02 夜间
**任务**: 优先级 3 - 实现 Agent 自主注册 API

## 完成内容

### 1. API 端点实现 ✅

**端点**: `POST /api/agents/register`

**功能**: 允许 AI Agent 自主注册，无需人工干预

**特性**:
- ✅ 无需认证（公开端点）
- ✅ 自动生成用户账户
- ✅ 自动生成以太坊钱包地址
- ✅ 自动生成 API Key
- ✅ 生成移动监控链接
- ✅ 生成二维码（Base64 PNG）

### 2. 请求模型

```python
class AgentSelfRegister(BaseModel):
    name: str                      # Agent 名称（必填，最多100字符）
    email: EmailStr                # 联系邮箱（必填，唯一）
    description: Optional[str]     # 描述（可选）
    specialties: Optional[List[str]]  # 专长列表（可选）
```

### 3. 响应模型

```python
class AgentSelfRegisterResponse(BaseModel):
    success: bool                  # 注册状态
    agent_id: int                  # Agent ID
    username: str                  # 生成的用户名
    wallet_address: str            # 生成的钱包地址
    api_key: str                   # API Key
    monitoring_url: str            # 监控链接
    monitoring_qr_code: str        # QR码（Base64）
    message: str                   # 成功消息
```

### 4. 注册流程

```
1. 验证输入数据
   ├─ 检查名称长度
   ├─ 验证邮箱格式
   └─ 检查邮箱唯一性

2. 生成唯一用户名
   ├─ 从 Agent 名称生成基础用户名
   ├─ 添加随机后缀（4位十六进制）
   └─ 确保用户名唯一

3. 生成钱包地址
   ├─ 生成 20 字节随机数
   ├─ 转换为十六进制
   └─ 添加 0x 前缀

4. 创建用户账户
   ├─ 用户名
   ├─ 邮箱
   ├─ 随机密码（哈希）
   └─ 钱包地址

5. 创建 Agent 配置
   ├─ Agent ID（自增）
   ├─ 名称和描述
   ├─ 专长列表
   └─ 关联钱包地址

6. 生成 API Key
   ├─ 格式：nau_<32位十六进制>
   ├─ 存储到数据库
   └─ 关联到 Agent

7. 生成监控链接
   ├─ URL: https://nautilus.social/monitor/{agent_id}?token={token}
   └─ Token: 安全随机字符串

8. 生成 QR 码
   ├─ 编码监控链接
   ├─ 生成 PNG 图片
   └─ 转换为 Base64
```

### 5. 辅助函数

#### generate_wallet_address()
```python
def generate_wallet_address() -> str:
    """生成以太坊钱包地址"""
    random_bytes = secrets.token_bytes(20)
    address = "0x" + random_bytes.hex()
    return address
```

#### generate_qr_code()
```python
def generate_qr_code(data: str) -> str:
    """生成 QR 码并返回 Base64 PNG"""
    qr = qrcode.QRCode(...)
    qr.add_data(data)
    img = qr.make_image(...)
    # 转换为 Base64
    return f"data:image/png;base64,{img_str}"
```

### 6. 依赖更新 ✅

添加到 `requirements.txt`:
```
qrcode[pil]>=7.4.2
Pillow>=10.0.0
prometheus-client>=0.19.0
```

## 使用示例

### 请求示例

```bash
curl -X POST https://api.nautilus.social/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DataAnalyzer Pro",
    "email": "dataanalyzer@example.com",
    "description": "Specialized in data analysis",
    "specialties": ["Python", "Pandas", "ML"]
  }'
```

### 响应示例

```json
{
  "success": true,
  "agent_id": 42,
  "username": "dataanalyzer_pro_a3f2",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "api_key": "nau_1234567890abcdef1234567890abcdef",
  "monitoring_url": "https://nautilus.social/monitor/42?token=abc123",
  "monitoring_qr_code": "data:image/png;base64,iVBORw0KG...",
  "message": "Agent registered successfully! Use the API key..."
}
```

### Python 客户端示例

```python
import requests

response = requests.post(
    "https://api.nautilus.social/api/agents/register",
    json={
        "name": "My AI Agent",
        "email": "agent@example.com",
        "description": "Task automation agent",
        "specialties": ["automation", "data processing"]
    }
)

data = response.json()
print(f"Agent ID: {data['agent_id']}")
print(f"API Key: {data['api_key']}")
print(f"Monitoring: {data['monitoring_url']}")

# 保存 QR 码
import base64
qr_data = data['monitoring_qr_code'].split(',')[1]
with open('monitor_qr.png', 'wb') as f:
    f.write(base64.b64decode(qr_data))
```

## 安全特性

1. **邮箱唯一性** - 防止重复注册
2. **用户名唯一性** - 自动添加随机后缀
3. **钱包地址唯一性** - 检查碰撞（极低概率）
4. **API Key 安全** - 使用 secrets 模块生成
5. **监控 Token** - 防止未授权访问
6. **错误处理** - 完整的异常捕获和回滚

## 待完成

### 安装依赖 ⏳
```bash
cd /c/Users/chunx/Projects/nautilus-core/phase3/backend
pip install qrcode[pil] Pillow prometheus-client
```

### 测试端点 ⏳
```bash
# 启动服务后测试
curl -X POST http://localhost:8000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Agent","email":"test@example.com"}'
```

### 前端集成 ⏳
需要创建监控页面：
- `/monitor/{agent_id}` - 显示 Agent 状态
- 验证 token 参数
- 显示任务历史、收益等

### 区块链集成 ⏳
可选：将 Agent 注册到区块链
- 调用智能合约
- 记录交易哈希
- 更新 blockchain_registered 状态

## 文件修改

1. **backend/api/agents.py** - 添加自主注册端点
2. **backend/requirements.txt** - 添加 qrcode 和 Pillow 依赖

## 优势

1. **零门槛** - Agent 无需人工干预即可注册
2. **自动化** - 一次请求完成所有设置
3. **移动友好** - QR 码扫描即可监控
4. **安全** - 自动生成的凭证确保安全性
5. **可扩展** - 支持大规模 Agent 注册

## 下一步行动

1. **安装依赖** - pip install qrcode[pil] Pillow
2. **重启服务** - 应用新代码
3. **测试注册** - 验证完整流程
4. **创建监控页面** - 前端实现
5. **文档更新** - API 文档

## 状态

- ✅ API 端点实现完成
- ✅ 依赖配置完成
- ⏳ 等待依赖安装
- ⏳ 等待服务重启
- ⏳ 等待前端集成
- 📊 预计影响：Agent 可自主注册并获得监控能力

---

**下一个任务**: 优先级 4 - 完善任务详情页
