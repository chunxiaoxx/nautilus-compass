# DNS 配置指南

## 文档信息
- **版本**: 1.0.0
- **创建日期**: 2026-02-26
- **适用环境**: 生产环境
- **维护团队**: 运维团队

---

## 1. 概述

本指南详细说明如何为 Nautilus Phase 3 Backend 配置 DNS 记录，包括基础记录、SSL 验证记录、负载均衡配置等。

### 1.1 DNS 基础知识

DNS (Domain Name System) 将人类可读的域名转换为 IP 地址。

**关键概念**:
- **域名**: yourdomain.com
- **子域名**: api.yourdomain.com, www.yourdomain.com
- **根域**: yourdomain.com (不带 www)
- **TTL**: Time To Live，DNS 记录缓存时间

### 1.2 DNS 记录类型

| 记录类型 | 用途 | 示例 |
|---------|------|------|
| A | 将域名指向 IPv4 地址 | yourdomain.com → 192.0.2.1 |
| AAAA | 将域名指向 IPv6 地址 | yourdomain.com → 2001:db8::1 |
| CNAME | 域名别名 | www → yourdomain.com |
| MX | 邮件服务器 | mail.yourdomain.com |
| TXT | 文本记录（验证、SPF等） | SPF, DKIM, 域名验证 |
| NS | 域名服务器 | ns1.nameserver.com |
| CAA | 证书颁发机构授权 | letsencrypt.org |
| SRV | 服务记录 | 特定服务的位置 |

---

## 2. 基础 DNS 配置

### 2.1 A 记录配置

A 记录将域名指向服务器的 IPv4 地址。

#### 2.1.1 单服务器配置

```
类型: A
主机: @
值: 203.0.113.10
TTL: 3600
```

**说明**:
- `@` 表示根域名 (yourdomain.com)
- `203.0.113.10` 是服务器的公网 IP
- `3600` 秒 = 1 小时缓存时间

#### 2.1.2 多子域名配置

```
# 根域名
类型: A
主机: @
值: 203.0.113.10
TTL: 3600

# www 子域名
类型: A
主机: www
值: 203.0.113.10
TTL: 3600

# API 子域名
类型: A
主机: api
值: 203.0.113.10
TTL: 3600

# 管理后台
类型: A
主机: admin
值: 203.0.113.11
TTL: 3600
```

#### 2.1.3 多服务器配置（轮询负载均衡）

```
# 主服务器
类型: A
主机: @
值: 203.0.113.10
TTL: 300

# 备用服务器
类型: A
主机: @
值: 203.0.113.11
TTL: 300
```

**注意**: DNS 轮询不是真正的负载均衡，建议使用专业负载均衡器。

### 2.2 AAAA 记录配置（IPv6）

如果服务器支持 IPv6，添加 AAAA 记录：

```
类型: AAAA
主机: @
值: 2001:db8:85a3::8a2e:370:7334
TTL: 3600

类型: AAAA
主机: www
值: 2001:db8:85a3::8a2e:370:7334
TTL: 3600
```

### 2.3 CNAME 记录配置

CNAME 创建域名别名，常用于 www 子域名。

```
类型: CNAME
主机: www
值: yourdomain.com
TTL: 3600
```

**重要限制**:
- CNAME 不能用于根域名 (@)
- CNAME 记录不能与其他记录类型共存

**推荐配置**:
```
# 方式1: 使用 A 记录（推荐）
类型: A
主机: @
值: 203.0.113.10

类型: A
主机: www
值: 203.0.113.10

# 方式2: 使用 CNAME（仅适用于子域名）
类型: A
主机: @
值: 203.0.113.10

类型: CNAME
主机: www
值: yourdomain.com
```

---

## 3. SSL 证书验证记录

### 3.1 HTTP 验证（推荐）

使用 HTTP 验证时，不需要添加 DNS 记录，只需确保：

```
# 确保域名解析正确
类型: A
主机: @
值: 203.0.113.10
TTL: 3600
```

Let's Encrypt 会访问：
```
http://yourdomain.com/.well-known/acme-challenge/验证文件
```

### 3.2 DNS TXT 记录验证

用于通配符证书或无法使用 HTTP 验证的情况。

```
类型: TXT
主机: _acme-challenge
值: "验证字符串由证书提供商提供"
TTL: 300
```

**示例**:
```
类型: TXT
主机: _acme-challenge
值: "xJ8fG3kL9mN2pQ5rS7tU1vW3xY5zA7bC9dE1fG3hI5jK7lM9nO1pQ3rS5tU7vW9x"
TTL: 300
```

**验证步骤**:
```bash
# 1. 添加 DNS 记录
# 2. 等待 DNS 传播（通常 1-5 分钟）
# 3. 验证记录是否生效
dig TXT _acme-challenge.yourdomain.com

# 4. 继续证书申请流程
```

### 3.3 CAA 记录（证书颁发机构授权）

CAA 记录指定哪些证书颁发机构可以为您的域名颁发证书。

```
# 允许 Let's Encrypt
类型: CAA
主机: @
值: 0 issue "letsencrypt.org"
TTL: 3600

# 允许通配符证书
类型: CAA
主机: @
值: 0 issuewild "letsencrypt.org"
TTL: 3600

# 违规通知邮箱
类型: CAA
主机: @
值: 0 iodef "mailto:security@yourdomain.com"
TTL: 3600
```

**多个 CA 配置**:
```
类型: CAA
主机: @
值: 0 issue "letsencrypt.org"

类型: CAA
主机: @
值: 0 issue "digicert.com"

类型: CAA
主机: @
值: 0 issue "sectigo.com"
```

---

## 4. 负载均衡配置

### 4.1 DNS 轮询（简单负载均衡）

```
# 服务器1
类型: A
主机: @
值: 203.0.113.10
TTL: 300

# 服务器2
类型: A
主机: @
值: 203.0.113.11
TTL: 300

# 服务器3
类型: A
主机: @
值: 203.0.113.12
TTL: 300
```

**优点**:
- 配置简单
- 无需额外成本

**缺点**:
- 无健康检查
- 无法控制流量分配
- 客户端可能缓存单个 IP

### 4.2 地理位置负载均衡

使用支持 GeoDNS 的 DNS 服务商（如 Cloudflare、Route53）。

**示例配置（Cloudflare）**:
```
# 亚洲用户
类型: A
主机: @
值: 203.0.113.10
地理位置: 亚洲
TTL: 300

# 欧洲用户
类型: A
主机: @
值: 198.51.100.10
地理位置: 欧洲
TTL: 300

# 美洲用户
类型: A
主机: @
值: 192.0.2.10
地理位置: 美洲
TTL: 300

# 默认（其他地区）
类型: A
主机: @
值: 203.0.113.10
地理位置: 默认
TTL: 300
```

### 4.3 故障转移配置

**主备模式**:
```
# 主服务器（优先级高）
类型: A
主机: @
值: 203.0.113.10
优先级: 1
健康检查: 启用
TTL: 60

# 备用服务器（优先级低）
类型: A
主机: @
值: 203.0.113.11
优先级: 2
健康检查: 启用
TTL: 60
```

### 4.4 CDN 配置

使用 CDN 时，通常使用 CNAME 指向 CDN 提供商。

**Cloudflare 示例**:
```
# 启用 Cloudflare 代理
类型: A
主机: @
值: 203.0.113.10
代理状态: 已代理（橙色云朵）
TTL: 自动

类型: A
主机: www
值: 203.0.113.10
代理状态: 已代理
TTL: 自动
```

**其他 CDN 示例**:
```
# AWS CloudFront
类型: CNAME
主机: www
值: d1234567890.cloudfront.net
TTL: 3600

# Fastly
类型: CNAME
主机: www
值: yourdomain.global.ssl.fastly.net
TTL: 3600
```

---

## 5. 高级配置

### 5.1 子域名配置

```
# API 服务
类型: A
主机: api
值: 203.0.113.10
TTL: 3600

# WebSocket 服务
类型: A
主机: ws
值: 203.0.113.11
TTL: 3600

# 静态资源
类型: CNAME
主机: static
值: cdn.yourdomain.com
TTL: 3600

# 管理后台
类型: A
主机: admin
值: 203.0.113.12
TTL: 3600

# 监控服务
类型: A
主机: monitoring
值: 203.0.113.13
TTL: 3600
```

### 5.2 邮件服务配置

```
# MX 记录（邮件服务器）
类型: MX
主机: @
值: mail.yourdomain.com
优先级: 10
TTL: 3600

# 邮件服务器 A 记录
类型: A
主机: mail
值: 203.0.113.20
TTL: 3600

# SPF 记录（防止邮件伪造）
类型: TXT
主机: @
值: "v=spf1 ip4:203.0.113.20 include:_spf.google.com ~all"
TTL: 3600

# DKIM 记录（邮件签名）
类型: TXT
主机: default._domainkey
值: "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA..."
TTL: 3600

# DMARC 记录（邮件策略）
类型: TXT
主机: _dmarc
值: "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com"
TTL: 3600
```

### 5.3 SRV 记录（服务发现）

```
# WebSocket 服务
类型: SRV
主机: _ws._tcp
值: 10 5 8001 ws.yourdomain.com
TTL: 3600

# 格式: 优先级 权重 端口 目标主机
```

### 5.4 通配符记录

```
# 通配符 A 记录
类型: A
主机: *
值: 203.0.113.10
TTL: 3600
```

**注意**: 通配符记录会匹配所有未明确定义的子域名。

---

## 6. DNS 服务商配置示例

### 6.1 Cloudflare 配置

**登录 Cloudflare Dashboard**:
1. 访问 https://dash.cloudflare.com
2. 选择域名
3. 点击 "DNS" 标签

**添加记录**:
```
类型: A
名称: @
IPv4地址: 203.0.113.10
代理状态: 已代理（推荐）
TTL: 自动

类型: A
名称: www
IPv4地址: 203.0.113.10
代理状态: 已代理
TTL: 自动

类型: A
名称: api
IPv4地址: 203.0.113.10
代理状态: 仅DNS（如果需要直连）
TTL: 自动
```

**Cloudflare 特殊功能**:
- **代理模式**: 隐藏真实 IP，提供 DDoS 防护
- **仅DNS模式**: 不经过 Cloudflare 代理
- **页面规则**: 自定义缓存、重定向等
- **防火墙规则**: IP 白名单/黑名单

### 6.2 AWS Route 53 配置

**使用 AWS CLI**:
```bash
# 创建托管区域
aws route53 create-hosted-zone \
  --name yourdomain.com \
  --caller-reference $(date +%s)

# 创建 A 记录
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "yourdomain.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "203.0.113.10"}]
      }
    }]
  }'
```

**使用 Terraform**:
```hcl
# route53.tf

resource "aws_route53_zone" "main" {
  name = "yourdomain.com"
}

resource "aws_route53_record" "root" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "yourdomain.com"
  type    = "A"
  ttl     = 300
  records = ["203.0.113.10"]
}

resource "aws_route53_record" "www" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "www.yourdomain.com"
  type    = "A"
  ttl     = 300
  records = ["203.0.113.10"]
}

resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.yourdomain.com"
  type    = "A"
  ttl     = 300
  records = ["203.0.113.10"]
}
```

### 6.3 阿里云 DNS 配置

**登录阿里云控制台**:
1. 访问 https://dns.console.aliyun.com
2. 选择域名
3. 点击 "解析设置"

**添加记录**:
```
记录类型: A
主机记录: @
解析线路: 默认
记录值: 203.0.113.10
TTL: 10分钟

记录类型: A
主机记录: www
解析线路: 默认
记录值: 203.0.113.10
TTL: 10分钟
```

**智能解析**（付费功能）:
```
# 境内用户
记录类型: A
主机记录: @
解析线路: 境内
记录值: 203.0.113.10

# 境外用户
记录类型: A
主机记录: @
解析线路: 境外
记录值: 198.51.100.10
```

### 6.4 腾讯云 DNSPod 配置

**登录 DNSPod 控制台**:
1. 访问 https://console.dnspod.cn
2. 选择域名
3. 点击 "添加记录"

**配置示例**:
```
主机记录: @
记录类型: A
线路类型: 默认
记录值: 203.0.113.10
TTL: 600

主机记录: www
记录类型: A
线路类型: 默认
记录值: 203.0.113.10
TTL: 600
```

---

## 7. DNS 验证和测试

### 7.1 使用 dig 命令

```bash
# 查询 A 记录
dig yourdomain.com A

# 查询特定 DNS 服务器
dig @8.8.8.8 yourdomain.com A

# 查询所有记录类型
dig yourdomain.com ANY

# 查询 TXT 记录
dig yourdomain.com TXT

# 查询 MX 记录
dig yourdomain.com MX

# 追踪 DNS 查询路径
dig +trace yourdomain.com
```

### 7.2 使用 nslookup 命令

```bash
# 基本查询
nslookup yourdomain.com

# 指定 DNS 服务器
nslookup yourdomain.com 8.8.8.8

# 查询特定记录类型
nslookup -type=MX yourdomain.com
nslookup -type=TXT yourdomain.com
```

### 7.3 使用 host 命令

```bash
# 基本查询
host yourdomain.com

# 查询所有记录
host -a yourdomain.com

# 查询特定类型
host -t A yourdomain.com
host -t MX yourdomain.com
```

### 7.4 在线测试工具

- **DNS Checker**: https://dnschecker.org
- **What's My DNS**: https://www.whatsmydns.net
- **DNS Propagation Checker**: https://www.whatsmydns.net
- **MX Toolbox**: https://mxtoolbox.com
- **IntoDNS**: https://intodns.com

### 7.5 验证 DNS 传播

```bash
#!/bin/bash
# check-dns-propagation.sh

DOMAIN="yourdomain.com"
EXPECTED_IP="203.0.113.10"

# 全球主要 DNS 服务器
DNS_SERVERS=(
    "8.8.8.8"          # Google
    "1.1.1.1"          # Cloudflare
    "208.67.222.222"   # OpenDNS
    "9.9.9.9"          # Quad9
    "114.114.114.114"  # 114DNS (中国)
    "223.5.5.5"        # 阿里DNS (中国)
)

echo "检查 DNS 传播状态: $DOMAIN"
echo "期望 IP: $EXPECTED_IP"
echo "-----------------------------------"

for dns in "${DNS_SERVERS[@]}"; do
    result=$(dig @$dns +short $DOMAIN A | head -n1)
    if [ "$result" == "$EXPECTED_IP" ]; then
        echo "✓ $dns: $result (正确)"
    else
        echo "✗ $dns: $result (不匹配)"
    fi
done
```

---

## 8. DNS 安全配置

### 8.1 DNSSEC（DNS 安全扩展）

DNSSEC 通过数字签名验证 DNS 响应的真实性。

**启用 DNSSEC**（以 Cloudflare 为例）:
1. 登录 Cloudflare Dashboard
2. 选择域名
3. 进入 "DNS" → "设置"
4. 启用 DNSSEC
5. 将 DS 记录添加到域名注册商

**验证 DNSSEC**:
```bash
# 检查 DNSSEC 状态
dig yourdomain.com +dnssec

# 验证 DNSSEC 签名
dig yourdomain.com +dnssec +multi
```

### 8.2 防止 DNS 劫持

**措施**:
1. **使用可信 DNS 服务商**: Cloudflare、Route53、DNSPod
2. **启用 DNSSEC**: 防止 DNS 欺骗
3. **启用两步验证**: 保护 DNS 管理账户
4. **监控 DNS 变更**: 设置变更通知
5. **锁定域名**: 防止未授权转移

### 8.3 DDoS 防护

**Cloudflare 配置**:
```
# 启用代理模式（橙色云朵）
类型: A
主机: @
值: 203.0.113.10
代理状态: 已代理

# 配置防火墙规则
安全 → WAF → 创建规则
- 速率限制: 100 请求/分钟
- 地理位置封锁: 封锁高风险国家
- IP 白名单: 允许可信 IP
```

---

## 9. DNS 性能优化

### 9.1 TTL 优化

**推荐 TTL 值**:
```
# 生产环境（稳定）
A 记录: 3600 (1小时)
CNAME 记录: 3600
MX 记录: 3600
TXT 记录: 3600

# 部署期间（频繁变更）
A 记录: 300 (5分钟)
CNAME 记录: 300

# 高可用场景（快速故障转移）
A 记录: 60 (1分钟)
```

**TTL 策略**:
- **部署前**: 降低 TTL 到 300 秒
- **部署中**: 保持低 TTL
- **部署后**: 24小时后恢复正常 TTL

### 9.2 使用 Anycast DNS

Anycast DNS 将 DNS 查询路由到最近的服务器。

**支持 Anycast 的 DNS 服务商**:
- Cloudflare
- AWS Route 53
- Google Cloud DNS
- Azure DNS

### 9.3 DNS 预取

在网页中添加 DNS 预取：

```html
<!-- 预取外部资源域名 -->
<link rel="dns-prefetch" href="//api.yourdomain.com">
<link rel="dns-prefetch" href="//cdn.yourdomain.com">
<link rel="dns-prefetch" href="//static.yourdomain.com">
```

---

## 10. 故障排查

### 10.1 常见问题

#### 问题1: DNS 记录不生效

**原因**:
- DNS 传播延迟（通常 5 分钟到 48 小时）
- 本地 DNS 缓存
- TTL 未过期

**解决方案**:
```bash
# 清除本地 DNS 缓存
# Windows
ipconfig /flushdns

# macOS
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# Linux
sudo systemd-resolve --flush-caches

# 使用不同 DNS 服务器测试
dig @8.8.8.8 yourdomain.com
dig @1.1.1.1 yourdomain.com
```

#### 问题2: CNAME 和 A 记录冲突

**错误配置**:
```
类型: A
主机: www
值: 203.0.113.10

类型: CNAME
主机: www
值: yourdomain.com
```

**正确配置**（选择其一）:
```
# 方式1: 仅使用 A 记录
类型: A
主机: www
值: 203.0.113.10

# 方式2: 仅使用 CNAME
类型: CNAME
主机: www
值: yourdomain.com
```

#### 问题3: SSL 证书验证失败

**检查 DNS 记录**:
```bash
# 验证 A 记录
dig yourdomain.com A

# 验证 TXT 记录（DNS 验证）
dig _acme-challenge.yourdomain.com TXT

# 等待 DNS 传播
# 使用多个 DNS 服务器测试
```

### 10.2 监控和告警

**DNS 监控脚本**:
```bash
#!/bin/bash
# monitor-dns.sh

DOMAIN="yourdomain.com"
EXPECTED_IP="203.0.113.10"

# 查询当前 IP
CURRENT_IP=$(dig +short $DOMAIN A | head -n1)

if [ "$CURRENT_IP" != "$EXPECTED_IP" ]; then
    echo "警告: DNS 记录异常！"
    echo "期望: $EXPECTED_IP"
    echo "当前: $CURRENT_IP"
    # 发送告警
    exit 1
else
    echo "DNS 记录正常"
    exit 0
fi
```

**添加到 crontab**:
```bash
# 每5分钟检查一次
*/5 * * * * /usr/local/bin/monitor-dns.sh
```

---

## 11. 部署检查清单

### 11.1 部署前检查

- [ ] 域名已注册
- [ ] DNS 服务商账户已创建
- [ ] 服务器 IP 地址已确认
- [ ] 子域名规划已完成
- [ ] TTL 已降低到 300 秒

### 11.2 DNS 记录配置

- [ ] A 记录已添加（根域名）
- [ ] A 记录已添加（www）
- [ ] A 记录已添加（api）
- [ ] AAAA 记录已添加（如果支持 IPv6）
- [ ] CAA 记录已添加
- [ ] TXT 记录已添加（如需 DNS 验证）

### 11.3 验证测试

- [ ] dig 命令验证通过
- [ ] 全球 DNS 传播检查通过
- [ ] SSL 证书验证通过
- [ ] 网站可通过域名访问
- [ ] API 可通过域名访问

### 11.4 部署后

- [ ] 监控已配置
- [ ] 告警已设置
- [ ] TTL 已恢复正常值（24小时后）
- [ ] 文档已更新

---

## 12. 参考资源

### 12.1 DNS 服务商

- **Cloudflare**: https://www.cloudflare.com
- **AWS Route 53**: https://aws.amazon.com/route53/
- **Google Cloud DNS**: https://cloud.google.com/dns
- **阿里云 DNS**: https://www.aliyun.com/product/dns
- **腾讯云 DNSPod**: https://www.dnspod.cn

### 12.2 测试工具

- **DNS Checker**: https://dnschecker.org
- **MX Toolbox**: https://mxtoolbox.com
- **IntoDNS**: https://intodns.com
- **DNSSEC Analyzer**: https://dnssec-debugger.verisignlabs.com

### 12.3 相关文档

- [生产环境部署计划](PRODUCTION_DEPLOYMENT_PLAN.md)
- [SSL证书配置指南](SSL_CERTIFICATE_GUIDE.md)
- [云服务部署指南](CLOUD_DEPLOYMENT_GUIDE.md)

---

**文档结束**
