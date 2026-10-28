# 安全修复使用指南

**Nautilus Phase 3 Backend - 安全增强版**

本文档提供安全修复的快速入门指南和使用说明。

---

## 快速开始

### 方式1: 使用自动部署脚本 (推荐)

#### Windows
```bash
deploy_security_fixes.bat
```

#### Linux/Mac
```bash
chmod +x deploy_security_fixes.sh
./deploy_security_fixes.sh
```

### 方式2: 手动部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env

# 3. 生成密钥
python -c "import secrets; print('CSRF_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# 4. 编辑 .env 文件，添加生成的密钥

# 5. 启动服务
python main.py
```

---

## 安全功能说明

### 1. API速率限制

**功能**: 防止暴力攻击和DDoS攻击

**配置**:
```bash
# .env
RATE_LIMIT_ENABLED=true
```

**限制规则**:
- 登录/注册: 5次/分钟
- 一般API: 100次/分钟
- 区块链交易: 10次/分钟

**响应示例**:
```json
// 超过限制时返回 429
{
  "error": "Rate limit exceeded",
  "detail": "5 per 1 minute"
}
```

**客户端处理**:
```javascript
// 检查速率限制
if (response.status === 429) {
  const retryAfter = response.headers.get('Retry-After');
  console.log(`请等待 ${retryAfter} 秒后重试`);
}
```

---

### 2. CORS源限制

**功能**: 限制跨域访问，只允许特定域名

**配置**:
```bash
# .env
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

**注意事项**:
- 必须包含协议 (http:// 或 https://)
- 多个域名用逗号分隔
- 不要使用通配符 (*)

**前端配置**:
```javascript
// 确保请求包含凭证
fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  credentials: 'include',  // 重要!
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({username, password})
});
```

---

### 3. CSRF防护

**功能**: 防止跨站请求伪造攻击

**配置**:
```bash
# .env
CSRF_SECRET_KEY=your-secret-key-here
```

**使用方法**:

#### 步骤1: 获取CSRF Token
```javascript
// 前端代码
const response = await fetch('http://localhost:8000/csrf-token', {
  credentials: 'include'
});
// CSRF token会自动设置在cookie中
```

#### 步骤2: 在请求中包含Token
```javascript
// 方式1: 从cookie读取并添加到请求头
const csrfToken = getCookie('fastapi-csrf-token');

fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrfToken
  },
  body: JSON.stringify({username, password})
});

// 辅助函数
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}
```

**注意**: GET请求通常不需要CSRF token，POST/PUT/DELETE请求需要。

---

### 4. 安全HTTP头部

**功能**: 增强浏览器安全防护

**自动添加的头部**:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Strict-Transport-Security: max-age=31536000; includeSubDomains (仅HTTPS)
```

**配置**:
```bash
# .env
FORCE_HTTPS=true  # 生产环境启用
HSTS_MAX_AGE=31536000  # 1年
```

---

## 环境配置

### 开发环境

```bash
# .env
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
FORCE_HTTPS=false
RATE_LIMIT_ENABLED=true
CSRF_SECRET_KEY=<生成的密钥>
JWT_SECRET_KEY=<生成的密钥>
```

### 生产环境

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FORCE_HTTPS=true
RATE_LIMIT_ENABLED=true
CSRF_SECRET_KEY=<强随机密钥>
JWT_SECRET_KEY=<强随机密钥>
HSTS_MAX_AGE=31536000
```

---

## 测试验证

### 运行安全测试
```bash
python test_security_fixes.py
```

### 手动测试

#### 测试速率限制
```bash
# 快速发送多个请求
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}'
  sleep 1
done
```

#### 测试CORS
```bash
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS http://localhost:8000/api/auth/login -v
```

#### 测试安全头部
```bash
curl -I http://localhost:8000/
```

---

## API使用示例

### 完整的前端集成示例

```javascript
class NautilusAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.csrfToken = null;
  }

  // 初始化: 获取CSRF token
  async init() {
    const response = await fetch(`${this.baseURL}/csrf-token`, {
      credentials: 'include'
    });

    // Token存储在cookie中
    this.csrfToken = this.getCookie('fastapi-csrf-token');
  }

  // 登录
  async login(username, password) {
    const response = await fetch(`${this.baseURL}/api/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': this.csrfToken
      },
      body: JSON.stringify({username, password})
    });

    if (response.status === 429) {
      throw new Error('请求过于频繁，请稍后再试');
    }

    if (!response.ok) {
      throw new Error('登录失败');
    }

    return await response.json();
  }

  // 获取用户信息
  async getCurrentUser(token) {
    const response = await fetch(`${this.baseURL}/api/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      credentials: 'include'
    });

    if (response.status === 429) {
      throw new Error('请求过于频繁，请稍后再试');
    }

    return await response.json();
  }

  // 辅助函数: 获取cookie
  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }
}

// 使用示例
const api = new NautilusAPI();

// 初始化
await api.init();

// 登录
try {
  const result = await api.login('username', 'password');
  console.log('登录成功:', result);

  // 保存token
  localStorage.setItem('token', result.access_token);

  // 获取用户信息
  const user = await api.getCurrentUser(result.access_token);
  console.log('用户信息:', user);
} catch (error) {
  console.error('错误:', error.message);
}
```

---

## 故障排查

### 问题1: 429 Too Many Requests

**原因**: 超过速率限制

**解决**:
- 检查请求频率
- 实现指数退避重试
- 增加请求间隔

```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429 && i < maxRetries - 1) {
        const delay = Math.pow(2, i) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error;
      }
    }
  }
}
```

### 问题2: CORS错误

**错误信息**:
```
Access to fetch at 'http://localhost:8000/api/auth/login' from origin
'http://localhost:3000' has been blocked by CORS policy
```

**解决**:
1. 检查 `ALLOWED_ORIGINS` 配置
2. 确保包含协议和端口
3. 前端请求添加 `credentials: 'include'`

### 问题3: CSRF验证失败

**错误信息**: `403 CSRF token validation failed`

**解决**:
1. 确保先调用 `/csrf-token` 获取token
2. 在POST/PUT/DELETE请求中包含token
3. 检查cookie是否正确设置

### 问题4: 速率限制配置不生效

**检查**:
```bash
# 检查环境变量
cat .env | grep RATE_LIMIT_ENABLED

# 检查日志
tail -f logs/app.log | grep "rate limit"
```

**解决**:
- 确保 `RATE_LIMIT_ENABLED=true`
- 重启服务
- 清除浏览器缓存

---

## 性能优化

### 使用Redis存储速率限制

```python
# 安装Redis
pip install redis

# 配置 (main.py)
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

### 配置CDN

对于静态资源和公共API，考虑使用CDN:
- Cloudflare
- AWS CloudFront
- Azure CDN

---

## 安全最佳实践

1. **定期轮换密钥**
   - CSRF密钥: 每90天
   - JWT密钥: 每90天

2. **监控异常活动**
   - 速率限制触发次数
   - CSRF验证失败次数
   - 异常IP地址

3. **日志审计**
   - 记录所有认证尝试
   - 记录速率限制事件
   - 记录安全事件

4. **定期更新依赖**
   ```bash
   pip list --outdated
   pip install --upgrade <package>
   ```

---

## 相关文档

- [安全修复报告](SECURITY_FIXES_REPORT.md) - 详细的修复说明
- [部署检查清单](DEPLOYMENT_CHECKLIST.md) - 完整的部署步骤
- [API文档](http://localhost:8000/docs) - 交互式API文档

---

## 支持

如有问题，请查看:
1. [故障排查](#故障排查)
2. [GitHub Issues](https://github.com/your-repo/issues)
3. 技术支持: support@nautilus.com

---

**版本**: 1.0
**最后更新**: 2026-02-26
