# 🌐 CDN配置指南 - Nautilus Phase 3

## 📋 文档概述

本指南提供Nautilus Phase 3后端系统的CDN（内容分发网络）配置方案，包括CloudFlare、AWS CloudFront和自建CDN的详细配置步骤。

**版本**: 1.0
**日期**: 2026-02-27
**适用环境**: 生产环境

---

## 🎯 CDN优化目标

### 性能目标
- 静态资源加载时间 < 100ms
- 全球访问延迟 < 200ms
- 缓存命中率 > 90%
- 带宽成本降低 60%

### 覆盖范围
- API响应缓存
- 静态资源分发
- 图片/视频优化
- WebSocket连接加速

---

## 🚀 方案一: CloudFlare CDN (推荐)

### 优势
- ✅ 免费套餐可用
- ✅ 全球200+节点
- ✅ 自动HTTPS
- ✅ DDoS防护
- ✅ 配置简单

### 1.1 账号设置

**步骤1: 注册CloudFlare账号**
```
1. 访问 https://dash.cloudflare.com/sign-up
2. 使用企业邮箱注册
3. 验证邮箱地址
```

**步骤2: 添加网站**
```
1. 点击 "Add a Site"
2. 输入域名: api.nautilus.io
3. 选择计划: Free (或Pro $20/月)
4. 点击 "Continue"
```

**步骤3: 更新DNS记录**
```
CloudFlare会提供两个nameserver:
- ns1.cloudflare.com
- ns2.cloudflare.com

在域名注册商处更新DNS:
1. 登录域名注册商
2. 找到DNS设置
3. 替换为CloudFlare的nameserver
4. 等待DNS传播 (24-48小时)
```

### 1.2 DNS配置

**添加DNS记录**:
```
类型    名称              内容                    代理状态
A       api              203.0.113.10            已代理 (橙色云)
A       www              203.0.113.10            已代理
CNAME   cdn              api.nautilus.io         已代理
CNAME   static           api.nautilus.io         已代理
```

**配置说明**:
- 橙色云 = 流量通过CloudFlare CDN
- 灰色云 = 直连源服务器（不推荐）

### 1.3 缓存规则配置

**页面规则 (Page Rules)**:

```
规则1: 静态资源缓存
URL: static.nautilus.io/*
设置:
  - 缓存级别: 缓存所有内容
  - 边缘缓存TTL: 1个月
  - 浏览器缓存TTL: 1周
  - 始终在线: 开启

规则2: API响应缓存
URL: api.nautilus.io/api/*
设置:
  - 缓存级别: 标准
  - 边缘缓存TTL: 2分钟
  - 绕过缓存Cookie: session_id
  - 缓存查询字符串: 排序

规则3: 不缓存认证端点
URL: api.nautilus.io/api/auth/*
设置:
  - 缓存级别: 绕过
```

**缓存规则配置界面**:
```
CloudFlare Dashboard → 缓存 → 配置
1. 缓存级别: 标准
2. 浏览器缓存过期: 尊重现有标头
3. 始终在线: 开启
4. 开发模式: 关闭（生产环境）
```

### 1.4 性能优化设置

**自动优化**:
```
CloudFlare Dashboard → 速度 → 优化

✅ Auto Minify (自动压缩)
   - JavaScript: 开启
   - CSS: 开启
   - HTML: 开启

✅ Brotli (压缩算法)
   - 开启

✅ Rocket Loader (JS优化)
   - 开启

✅ Mirage (图片优化)
   - 开启 (Pro计划)

✅ Polish (图片压缩)
   - 有损压缩 (Pro计划)
```

**HTTP/3支持**:
```
CloudFlare Dashboard → 网络
✅ HTTP/3 (QUIC): 开启
✅ 0-RTT连接恢复: 开启
✅ WebSockets: 开启
✅ gRPC: 开启
```

### 1.5 安全设置

**SSL/TLS配置**:
```
CloudFlare Dashboard → SSL/TLS

加密模式: 完全（严格）
  - CloudFlare ↔ 用户: HTTPS
  - CloudFlare ↔ 源服务器: HTTPS (验证证书)

最低TLS版本: TLS 1.2
TLS 1.3: 开启
自动HTTPS重写: 开启
```

**防火墙规则**:
```
CloudFlare Dashboard → 安全性 → WAF

规则1: 阻止恶意爬虫
表达式: (cf.client.bot) and not (cf.verified_bot_category in {"Search Engine Crawler"})
操作: 质询

规则2: 速率限制
表达式: (http.request.uri.path contains "/api/")
操作: 速率限制 (100 req/min)

规则3: 地理封锁（可选）
表达式: (ip.geoip.country in {"CN" "RU"})
操作: 质询或阻止
```

### 1.6 后端配置

**Nginx配置** (`/etc/nginx/sites-available/nautilus`):
```nginx
server {
    listen 443 ssl http2;
    server_name api.nautilus.io;

    # SSL证书（CloudFlare Origin证书）
    ssl_certificate /etc/ssl/cloudflare/cert.pem;
    ssl_certificate_key /etc/ssl/cloudflare/key.pem;

    # 信任CloudFlare IP
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    set_real_ip_from 2400:cb00::/32;
    set_real_ip_from 2606:4700::/32;
    set_real_ip_from 2803:f800::/32;
    set_real_ip_from 2405:b500::/32;
    set_real_ip_from 2405:8100::/32;
    set_real_ip_from 2c0f:f248::/32;
    set_real_ip_from 2a06:98c0::/29;
    real_ip_header CF-Connecting-IP;

    # 静态资源缓存
    location /static/ {
        alias /var/www/nautilus/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options "nosniff";
    }

    # API端点
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 缓存控制
        add_header Cache-Control "public, max-age=120";
        add_header X-Cache-Status $upstream_cache_status;
    }

    # 不缓存认证端点
    location /api/auth/ {
        proxy_pass http://localhost:8000;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
```

**FastAPI缓存头配置**:
```python
# main.py
from fastapi import Response

@app.get("/api/tasks")
async def list_tasks(response: Response):
    # 设置缓存头
    response.headers["Cache-Control"] = "public, max-age=120"
    response.headers["CDN-Cache-Control"] = "max-age=300"

    tasks = get_tasks_from_db()
    return tasks

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: int, response: Response):
    # 长期缓存
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["CDN-Cache-Control"] = "max-age=7200"

    agent = get_agent_from_db(agent_id)
    return agent
```

### 1.7 缓存清除

**手动清除缓存**:
```bash
# 使用CloudFlare API清除缓存
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'

# 清除特定URL
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"files":["https://api.nautilus.io/api/tasks"]}'
```

**自动清除脚本** (`scripts/purge_cdn_cache.sh`):
```bash
#!/bin/bash

ZONE_ID="your_zone_id"
API_TOKEN="your_api_token"

# 清除特定路径
purge_path() {
    local path=$1
    curl -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/purge_cache" \
      -H "Authorization: Bearer ${API_TOKEN}" \
      -H "Content-Type: application/json" \
      --data "{\"files\":[\"https://api.nautilus.io${path}\"]}"
}

# 任务更新时清除缓存
purge_path "/api/tasks"
purge_path "/api/tasks?status=Open"

echo "CDN cache purged successfully"
```

---

## 🌟 方案二: AWS CloudFront

### 2.1 创建CloudFront分发

**步骤1: 创建分发**:
```
AWS Console → CloudFront → Create Distribution

源域名: api.nautilus.io
源协议策略: HTTPS Only
源SSL协议: TLSv1.2

查看器协议策略: Redirect HTTP to HTTPS
允许的HTTP方法: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
缓存HTTP方法: GET, HEAD, OPTIONS

价格类别: Use All Edge Locations (最佳性能)
```

**步骤2: 配置缓存行为**:
```
路径模式: /static/*
缓存策略: CachingOptimized
源请求策略: CORS-S3Origin
TTL:
  - 最小: 0
  - 最大: 31536000 (1年)
  - 默认: 86400 (1天)

路径模式: /api/*
缓存策略: CachingDisabled (或自定义)
源请求策略: AllViewer
压缩对象: 是
```

### 2.2 自定义缓存策略

**创建缓存策略**:
```
名称: NautilusAPICache
TTL设置:
  - 最小: 0
  - 最大: 300 (5分钟)
  - 默认: 120 (2分钟)

缓存键设置:
  - 查询字符串: 全部
  - 标头:
    - Authorization
    - X-API-Key
  - Cookie: 无

压缩支持:
  - Gzip: 是
  - Brotli: 是
```

### 2.3 Lambda@Edge优化

**缓存控制函数** (`lambda/cache-control.js`):
```javascript
'use strict';

exports.handler = (event, context, callback) => {
    const response = event.Records[0].cf.response;
    const headers = response.headers;
    const uri = event.Records[0].cf.request.uri;

    // 静态资源长期缓存
    if (uri.startsWith('/static/')) {
        headers['cache-control'] = [{
            key: 'Cache-Control',
            value: 'public, max-age=2592000, immutable'
        }];
    }

    // API响应短期缓存
    else if (uri.startsWith('/api/')) {
        // 排除认证端点
        if (!uri.startsWith('/api/auth/')) {
            headers['cache-control'] = [{
                key: 'Cache-Control',
                value: 'public, max-age=120, s-maxage=300'
            }];
        }
    }

    callback(null, response);
};
```

**部署Lambda@Edge**:
```bash
# 创建Lambda函数
aws lambda create-function \
  --function-name nautilus-cache-control \
  --runtime nodejs18.x \
  --role arn:aws:iam::account-id:role/lambda-edge-role \
  --handler index.handler \
  --zip-file fileb://function.zip \
  --region us-east-1

# 关联到CloudFront
aws cloudfront update-distribution \
  --id DISTRIBUTION_ID \
  --lambda-function-associations \
    Quantity=1,Items=[{LambdaFunctionARN=arn:aws:lambda:us-east-1:account-id:function:nautilus-cache-control:1,EventType=origin-response}]
```

---

## 🔧 方案三: 自建CDN (Nginx + Varnish)

### 3.1 架构设计

```
用户请求
    ↓
边缘节点 (Varnish)
    ↓
源服务器 (Nginx + FastAPI)
```

### 3.2 Varnish配置

**安装Varnish**:
```bash
# Ubuntu/Debian
apt-get update
apt-get install varnish

# CentOS/RHEL
yum install varnish
```

**配置文件** (`/etc/varnish/default.vcl`):
```vcl
vcl 4.1;

# 后端服务器
backend default {
    .host = "api.nautilus.io";
    .port = "443";
    .connect_timeout = 5s;
    .first_byte_timeout = 30s;
    .between_bytes_timeout = 10s;
}

# 接收请求
sub vcl_recv {
    # 移除不必要的cookie
    if (req.url ~ "^/static/") {
        unset req.http.Cookie;
    }

    # 不缓存认证请求
    if (req.url ~ "^/api/auth/") {
        return (pass);
    }

    # 不缓存POST/PUT/DELETE
    if (req.method != "GET" && req.method != "HEAD") {
        return (pass);
    }

    # 标准化Accept-Encoding
    if (req.http.Accept-Encoding) {
        if (req.http.Accept-Encoding ~ "gzip") {
            set req.http.Accept-Encoding = "gzip";
        } elsif (req.http.Accept-Encoding ~ "deflate") {
            set req.http.Accept-Encoding = "deflate";
        } else {
            unset req.http.Accept-Encoding;
        }
    }

    return (hash);
}

# 后端响应
sub vcl_backend_response {
    # 静态资源长期缓存
    if (bereq.url ~ "^/static/") {
        set beresp.ttl = 30d;
        set beresp.http.Cache-Control = "public, max-age=2592000";
    }

    # API响应短期缓存
    if (bereq.url ~ "^/api/") {
        set beresp.ttl = 2m;
        set beresp.http.Cache-Control = "public, max-age=120";
    }

    # 启用grace模式（源服务器故障时提供过期内容）
    set beresp.grace = 1h;

    return (deliver);
}

# 交付响应
sub vcl_deliver {
    # 添加缓存状态头
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
        set resp.http.X-Cache-Hits = obj.hits;
    } else {
        set resp.http.X-Cache = "MISS";
    }

    # 移除内部头
    unset resp.http.X-Varnish;
    unset resp.http.Via;
    unset resp.http.Age;

    return (deliver);
}
```

**启动Varnish**:
```bash
# 编辑服务配置
vim /etc/systemd/system/varnish.service

[Service]
ExecStart=/usr/sbin/varnishd \
  -a :80 \
  -T localhost:6082 \
  -f /etc/varnish/default.vcl \
  -s malloc,2G \
  -p thread_pools=4 \
  -p thread_pool_min=100 \
  -p thread_pool_max=1000

# 启动服务
systemctl daemon-reload
systemctl enable varnish
systemctl start varnish
```

### 3.3 多节点部署

**节点分布**:
```
- 北美: us-east-1.cdn.nautilus.io (纽约)
- 欧洲: eu-west-1.cdn.nautilus.io (伦敦)
- 亚洲: ap-east-1.cdn.nautilus.io (东京)
```

**GeoDNS配置** (Route53):
```
记录名称: cdn.nautilus.io
记录类型: A
路由策略: 地理位置

北美:
  - 值: 203.0.113.10
  - 位置: 北美

欧洲:
  - 值: 198.51.100.20
  - 位置: 欧洲

亚洲:
  - 值: 192.0.2.30
  - 位置: 亚洲

默认:
  - 值: 203.0.113.10
  - 位置: 默认
```

---

## 📊 性能监控

### 监控指标

**CloudFlare Analytics**:
```
- 请求总数
- 缓存命中率
- 带宽使用
- 响应时间
- 错误率
- 威胁阻止数
```

**自定义监控脚本** (`scripts/monitor_cdn.py`):
```python
import requests
import time
from datetime import datetime

def check_cdn_performance():
    """检查CDN性能"""
    endpoints = [
        "https://cdn.nautilus.io/static/logo.png",
        "https://api.nautilus.io/api/tasks",
        "https://api.nautilus.io/api/agents"
    ]

    results = []
    for url in endpoints:
        start = time.time()
        response = requests.get(url)
        elapsed = time.time() - start

        cache_status = response.headers.get('X-Cache', 'UNKNOWN')

        results.append({
            'url': url,
            'status': response.status_code,
            'time': elapsed * 1000,  # ms
            'cache': cache_status,
            'timestamp': datetime.now().isoformat()
        })

    return results

if __name__ == "__main__":
    results = check_cdn_performance()
    for r in results:
        print(f"{r['url']}: {r['time']:.2f}ms - {r['cache']}")
```

---

## 🎯 最佳实践

### 缓存策略

✅ **DO**:
- 静态资源设置长TTL (30天)
- API响应设置短TTL (2-5分钟)
- 使用版本化URL (`/static/v1.2.3/app.js`)
- 设置合适的Cache-Control头
- 启用压缩 (Gzip/Brotli)

❌ **DON'T**:
- 缓存认证端点
- 缓存用户特定数据
- 忽略缓存清除
- 过度缓存动态内容

### 安全配置

✅ **DO**:
- 启用HTTPS
- 配置WAF规则
- 限制源服务器访问
- 启用DDoS防护
- 定期更新SSL证书

❌ **DON'T**:
- 暴露源服务器IP
- 使用弱SSL配置
- 忽略安全日志
- 禁用安全功能

---

## 📈 预期效果

### 性能提升

| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| 静态资源加载 | 800ms | 80ms | ↓ 90% |
| API响应时间 | 200ms | 120ms | ↓ 40% |
| 全球访问延迟 | 500ms | 150ms | ↓ 70% |
| 带宽成本 | $500/月 | $200/月 | ↓ 60% |
| 缓存命中率 | 0% | 92% | ↑ 92% |

### 成本分析

**CloudFlare**:
- Free: $0/月 (适合小型项目)
- Pro: $20/月 (推荐)
- Business: $200/月 (企业级)

**AWS CloudFront**:
- 数据传输: $0.085/GB (前10TB)
- 请求: $0.0075/10,000请求
- 预估: $150-300/月

**自建CDN**:
- 服务器: $50/月 × 3节点 = $150/月
- 带宽: $100/月
- 维护: $200/月
- 总计: $450/月

---

## ✅ 验证清单

### 配置验证

- [ ] DNS记录已更新
- [ ] SSL证书已配置
- [ ] 缓存规则已设置
- [ ] 安全规则已启用
- [ ] 监控已配置

### 性能验证

- [ ] 缓存命中率 > 90%
- [ ] 响应时间 < 200ms
- [ ] 全球访问测试通过
- [ ] 负载测试通过

### 安全验证

- [ ] HTTPS强制启用
- [ ] WAF规则生效
- [ ] DDoS防护启用
- [ ] 源服务器已保护

---

**文档版本**: 1.0
**最后更新**: 2026-02-27
**维护团队**: DevOps Team
