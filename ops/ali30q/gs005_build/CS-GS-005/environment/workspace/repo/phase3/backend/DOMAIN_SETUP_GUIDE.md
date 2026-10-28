# 域名配置指南

## 文档信息
- **版本**: 1.0.0
- **创建日期**: 2026-02-27
- **适用环境**: 生产环境
- **维护团队**: 运维团队

---

## 1. 概述

本指南详细说明如何为 Nautilus Phase 3 Backend 配置域名和 DNS 记录，确保域名正确解析到服务器并支持 SSL 证书验证。

### 1.1 前置要求

- 已购买域名
- 拥有域名管理权限
- 服务器公网 IP 地址
- DNS 服务商账号（如 Cloudflare、阿里云、腾讯云等）

### 1.2 配置流程概览

```
购买域名 → 配置 DNS 解析 → 验证解析 → 配置 SSL 证书 → 测试访问
```

---

## 2. 域名选择和购买

### 2.1 域名选择建议

**域名命名原则**:
- 简短易记（建议 15 个字符以内）
- 与品牌相关
- 避免使用连字符和数字
- 选择合适的顶级域名（TLD）

**推荐的 TLD**:
| TLD | 适用场景 | 价格 | 推荐度 |
|-----|----------|------|--------|
| .com | 商业网站、国际业务 | 中 | ⭐⭐⭐⭐⭐ |
| .net | 网络服务、技术公司 | 中 | ⭐⭐⭐⭐ |
| .io | 科技创业公司 | 高 | ⭐⭐⭐⭐ |
| .cn | 中国市场 | 低 | ⭐⭐⭐ |
| .org | 非营利组织 | 中 | ⭐⭐⭐ |
| .app | 应用程序 | 中 | ⭐⭐⭐⭐ |

### 2.2 域名注册商推荐

**国际注册商**:
- **Namecheap**: 价格实惠，界面友好
- **GoDaddy**: 知名度高，服务完善
- **Google Domains**: 简洁易用，集成 Google 服务
- **Cloudflare Registrar**: 成本价注册，无加价

**国内注册商**:
- **阿里云（万网）**: 国内最大，服务稳定
- **腾讯云 DNSPod**: 解析速度快
- **华为云**: 企业级服务

### 2.3 域名购买步骤

1. **选择注册商**: 根据需求选择合适的注册商
2. **搜索域名**: 检查域名可用性
3. **添加到购物车**: 选择注册年限（建议 2-3 年）
4. **隐私保护**: 启用 WHOIS 隐私保护
5. **完成支付**: 使用信用卡或支付宝支付
6. **实名认证**: 国内域名需要实名认证（1-3 个工作日）

---

## 3. DNS 配置步骤

### 3.1 DNS 服务商选择

**推荐使用 Cloudflare**（免费且功能强大）:
- 全球 CDN 加速
- 免费 SSL 证书
- DDoS 防护
- DNS 解析速度快
- 提供 API 支持

**其他选择**:
- **阿里云 DNS**: 国内解析速度快
- **腾讯云 DNSPod**: 免费版功能丰富
- **AWS Route 53**: 企业级 DNS 服务
- **Google Cloud DNS**: 高可用性

### 3.2 将域名接入 Cloudflare

#### 步骤 1: 注册 Cloudflare 账号

1. 访问 https://dash.cloudflare.com/sign-up
2. 使用邮箱注册账号
3. 验证邮箱

#### 步骤 2: 添加站点

1. 登录 Cloudflare 控制台
2. 点击 "Add a Site"
3. 输入域名（例如: nautilus.com）
4. 选择免费计划（Free Plan）
5. 点击 "Add Site"

#### 步骤 3: 扫描 DNS 记录

Cloudflare 会自动扫描现有的 DNS 记录，确认无误后点击 "Continue"。

#### 步骤 4: 更改域名服务器

1. Cloudflare 会提供两个名称服务器（Nameservers）:
   ```
   例如:
   ns1.cloudflare.com
   ns2.cloudflare.com
   ```

2. 登录域名注册商控制台
3. 找到域名管理 → DNS 设置
4. 将默认的名称服务器替换为 Cloudflare 提供的名称服务器
5. 保存更改

#### 步骤 5: 等待生效

- DNS 更改通常需要 2-24 小时生效
- Cloudflare 会发送邮件通知激活成功

### 3.3 配置 DNS 记录

#### 3.3.1 A 记录配置（IPv4）

**用途**: 将域名指向服务器 IPv4 地址

**配置示例**:

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | 203.0.113.10 | Proxied | Auto |
| A | www | 203.0.113.10 | Proxied | Auto |
| A | api | 203.0.113.10 | Proxied | Auto |

**字段说明**:
- **Type**: 记录类型（A）
- **Name**:
  - `@` 表示根域名（nautilus.com）
  - `www` 表示 www 子域名（www.nautilus.com）
  - `api` 表示 API 子域名（api.nautilus.com）
- **Content**: 服务器公网 IPv4 地址
- **Proxy Status**:
  - `Proxied`（橙色云）: 流量经过 Cloudflare CDN
  - `DNS only`（灰色云）: 直接解析到服务器
- **TTL**: 生存时间（Auto 表示自动）

**Cloudflare 配置步骤**:
```bash
1. 登录 Cloudflare 控制台
2. 选择域名
3. 点击 "DNS" 标签
4. 点击 "Add record"
5. 选择类型: A
6. 输入名称: @
7. 输入 IPv4 地址: 203.0.113.10
8. 代理状态: Proxied（推荐）
9. 点击 "Save"
```

#### 3.3.2 AAAA 记录配置（IPv6）

**用途**: 将域名指向服务器 IPv6 地址（可选）

**配置示例**:

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| AAAA | @ | 2001:db8::1 | Proxied | Auto |
| AAAA | www | 2001:db8::1 | Proxied | Auto |

#### 3.3.3 CNAME 记录配置

**用途**: 创建域名别名

**配置示例**:

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| CNAME | blog | nautilus.com | Proxied | Auto |
| CNAME | docs | nautilus.com | Proxied | Auto |
| CNAME | status | status.example.com | DNS only | Auto |

**使用场景**:
- 将多个子域名指向同一个主域名
- 指向第三方服务（如 GitHub Pages）
- CDN 配置

**注意事项**:
- CNAME 记录不能与其他记录类型共存于同一名称
- 根域名（@）通常不使用 CNAME，而使用 A 记录

#### 3.3.4 MX 记录配置（邮件服务器）

**用途**: 配置邮件服务器（可选）

**配置示例**:

| Type | Name | Content | Priority | TTL |
|------|------|---------|----------|-----|
| MX | @ | mail.nautilus.com | 10 | Auto |
| MX | @ | mail2.nautilus.com | 20 | Auto |

#### 3.3.5 TXT 记录配置

**用途**:
- SPF 记录（防止邮件伪造）
- DKIM 记录（邮件签名）
- 域名验证（SSL 证书、Google Search Console）

**配置示例**:

| Type | Name | Content | TTL |
|------|------|---------|-----|
| TXT | @ | v=spf1 include:_spf.google.com ~all | Auto |
| TXT | _dmarc | v=DMARC1; p=quarantine; rua=mailto:admin@nautilus.com | Auto |
| TXT | @ | google-site-verification=xxxxx | Auto |

#### 3.3.6 CAA 记录配置（证书颁发机构授权）

**用途**: 指定哪些 CA 可以为域名颁发证书

**配置示例**:

| Type | Name | Content | TTL |
|------|------|---------|-----|
| CAA | @ | 0 issue "letsencrypt.org" | Auto |
| CAA | @ | 0 issuewild "letsencrypt.org" | Auto |
| CAA | @ | 0 iodef "mailto:security@nautilus.com" | Auto |

**字段说明**:
- `0 issue`: 允许颁发普通证书
- `0 issuewild`: 允许颁发通配符证书
- `0 iodef`: 违规通知邮箱

---

## 4. DNS 解析验证

### 4.1 使用命令行工具验证

#### 验证 A 记录

```bash
# 使用 dig 命令
dig nautilus.com A +short
dig www.nautilus.com A +short

# 使用 nslookup 命令
nslookup nautilus.com
nslookup www.nautilus.com

# 使用 host 命令
host nautilus.com
host www.nautilus.com
```

**预期输出**:
```
203.0.113.10
```

#### 验证 CNAME 记录

```bash
dig blog.nautilus.com CNAME +short
```

**预期输出**:
```
nautilus.com.
```

#### 验证 MX 记录

```bash
dig nautilus.com MX +short
```

**预期输出**:
```
10 mail.nautilus.com.
20 mail2.nautilus.com.
```

#### 验证 TXT 记录

```bash
dig nautilus.com TXT +short
```

#### 验证 CAA 记录

```bash
dig nautilus.com CAA +short
```

### 4.2 使用在线工具验证

**推荐工具**:
- **DNS Checker**: https://dnschecker.org/
  - 全球多地 DNS 解析检查
  - 支持所有记录类型

- **What's My DNS**: https://www.whatsmydns.net/
  - 可视化全球 DNS 传播状态

- **MX Toolbox**: https://mxtoolbox.com/
  - 全面的 DNS 诊断工具
  - 支持 DNS 健康检查

- **IntoDNS**: https://intodns.com/
  - 详细的 DNS 配置报告
  - 发现配置问题

### 4.3 验证 DNS 传播

DNS 更改需要时间传播到全球，通常：
- **本地 ISP**: 几分钟到几小时
- **全球传播**: 24-48 小时
- **完全生效**: 最多 72 小时

**加速传播方法**:
1. 降低 TTL 值（提前 24 小时）
2. 使用 Cloudflare（传播速度快）
3. 清除本地 DNS 缓存

**清除本地 DNS 缓存**:

```bash
# Windows
ipconfig /flushdns

# macOS
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# Linux
sudo systemd-resolve --flush-caches
# 或
sudo /etc/init.d/nscd restart
```

---

## 5. 子域名配置

### 5.1 常用子域名规划

| 子域名 | 用途 | 示例 |
|--------|------|------|
| www | 主网站 | www.nautilus.com |
| api | API 服务 | api.nautilus.com |
| admin | 管理后台 | admin.nautilus.com |
| app | Web 应用 | app.nautilus.com |
| blog | 博客 | blog.nautilus.com |
| docs | 文档 | docs.nautilus.com |
| status | 状态页面 | status.nautilus.com |
| cdn | CDN 资源 | cdn.nautilus.com |
| static | 静态资源 | static.nautilus.com |
| dev | 开发环境 | dev.nautilus.com |
| staging | 预发布环境 | staging.nautilus.com |

### 5.2 通配符子域名

**用途**: 匹配所有未定义的子域名

**配置示例**:

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | * | 203.0.113.10 | DNS only | Auto |

**注意事项**:
- 通配符记录优先级低于具体记录
- 需要通配符 SSL 证书支持
- 可能增加安全风险

---

## 6. Cloudflare 高级配置

### 6.1 SSL/TLS 设置

1. 登录 Cloudflare 控制台
2. 选择域名 → SSL/TLS
3. 选择加密模式:
   - **Off**: 不加密（不推荐）
   - **Flexible**: Cloudflare 到客户端加密，Cloudflare 到源服务器不加密
   - **Full**: 端到端加密，但不验证源服务器证书
   - **Full (strict)**: 端到端加密，验证源服务器证书（推荐）

**推荐配置**: Full (strict)

### 6.2 页面规则（Page Rules）

**用途**: 为特定 URL 设置自定义规则

**示例规则**:

1. **强制 HTTPS**:
   ```
   URL: http://*nautilus.com/*
   设置: Always Use HTTPS
   ```

2. **缓存所有内容**:
   ```
   URL: *nautilus.com/static/*
   设置: Cache Level = Cache Everything
   ```

3. **绕过缓存**:
   ```
   URL: *nautilus.com/api/*
   设置: Cache Level = Bypass
   ```

### 6.3 防火墙规则

**用途**: 保护网站免受恶意流量攻击

**示例规则**:

1. **阻止特定国家**:
   ```
   字段: Country
   运算符: equals
   值: CN
   操作: Block
   ```

2. **限制 API 访问频率**:
   ```
   字段: URI Path
   运算符: contains
   值: /api/
   操作: Rate Limit (100 requests per minute)
   ```

3. **阻止恶意 User-Agent**:
   ```
   字段: User Agent
   运算符: contains
   值: bot
   操作: Challenge (CAPTCHA)
   ```

### 6.4 缓存配置

1. 选择域名 → Caching
2. 配置选项:
   - **Caching Level**: Standard
   - **Browser Cache TTL**: 4 hours
   - **Always Online**: On（离线时显示缓存页面）
   - **Development Mode**: Off（开发时可临时启用）

---

## 7. 域名安全配置

### 7.1 启用域名锁定

**用途**: 防止域名被恶意转移

**配置步骤**:
1. 登录域名注册商控制台
2. 找到域名管理 → 安全设置
3. 启用 "域名锁定" 或 "Transfer Lock"
4. 保存更改

### 7.2 启用两步验证

**用途**: 保护域名管理账号

**配置步骤**:
1. 登录域名注册商账号
2. 账号设置 → 安全
3. 启用两步验证（2FA）
4. 使用 Google Authenticator 或短信验证

### 7.3 WHOIS 隐私保护

**用途**: 隐藏域名所有者信息

**配置步骤**:
1. 登录域名注册商控制台
2. 域名管理 → WHOIS 隐私
3. 启用隐私保护
4. 验证 WHOIS 信息已隐藏

### 7.4 DNSSEC 配置

**用途**: 防止 DNS 劫持和欺骗

**Cloudflare 配置步骤**:
1. 登录 Cloudflare 控制台
2. 选择域名 → DNS → DNSSEC
3. 点击 "Enable DNSSEC"
4. 复制 DS 记录信息
5. 登录域名注册商控制台
6. 添加 DS 记录
7. 等待验证完成

---

## 8. 故障排查

### 8.1 常见问题

#### 问题 1: 域名无法解析

**症状**: ping 域名返回 "unknown host"

**排查步骤**:
```bash
# 1. 检查 DNS 记录是否配置
dig nautilus.com A +short

# 2. 检查名称服务器是否正确
dig nautilus.com NS +short

# 3. 检查 DNS 传播状态
# 访问 https://dnschecker.org/

# 4. 清除本地 DNS 缓存
ipconfig /flushdns  # Windows
```

**解决方案**:
- 确认 DNS 记录已正确配置
- 等待 DNS 传播完成（最多 48 小时）
- 检查名称服务器是否已更新

#### 问题 2: SSL 证书验证失败

**症状**: Let's Encrypt 验证失败

**排查步骤**:
```bash
# 1. 检查域名是否解析到正确的服务器
dig nautilus.com A +short

# 2. 检查 80 端口是否开放
telnet nautilus.com 80

# 3. 检查防火墙规则
sudo ufw status

# 4. 检查 Nginx 配置
sudo nginx -t
```

**解决方案**:
- 确保域名已解析到服务器
- 开放 80 和 443 端口
- 检查 .well-known 目录权限

#### 问题 3: Cloudflare 错误

**常见错误代码**:
- **Error 521**: 源服务器拒绝连接
  - 检查源服务器是否运行
  - 检查防火墙是否允许 Cloudflare IP

- **Error 522**: 连接超时
  - 检查源服务器响应时间
  - 增加超时设置

- **Error 525**: SSL 握手失败
  - 检查源服务器 SSL 证书
  - 使用 Full (strict) 模式需要有效证书

#### 问题 4: DNS 传播缓慢

**解决方案**:
1. 提前降低 TTL 值（24 小时前）
2. 使用 Cloudflare 加速传播
3. 清除本地和 ISP DNS 缓存
4. 使用公共 DNS（8.8.8.8, 1.1.1.1）

---

## 9. 最佳实践

### 9.1 DNS 配置建议

1. **使用 Cloudflare**: 免费 CDN + SSL + DDoS 防护
2. **配置 CAA 记录**: 限制证书颁发机构
3. **启用 DNSSEC**: 防止 DNS 劫持
4. **合理设置 TTL**:
   - 稳定环境: 3600-86400 秒
   - 迁移期间: 300-600 秒
5. **配置冗余 DNS**: 使用多个名称服务器

### 9.2 安全建议

1. **启用域名锁定**: 防止恶意转移
2. **启用两步验证**: 保护管理账号
3. **定期检查 DNS 记录**: 防止被篡改
4. **使用强密码**: 域名管理账号使用复杂密码
5. **备份 DNS 配置**: 定期导出 DNS 记录

### 9.3 性能优化

1. **使用 CDN**: Cloudflare 或其他 CDN 服务
2. **启用 HTTP/2**: 提高传输效率
3. **配置缓存规则**: 减少源服务器负载
4. **使用 Anycast DNS**: 提高解析速度
5. **优化 TTL 值**: 平衡更新速度和缓存效率

---

## 10. 配置检查清单

### 10.1 DNS 配置检查

- [ ] A 记录已配置（@ 和 www）
- [ ] AAAA 记录已配置（如果支持 IPv6）
- [ ] CNAME 记录已配置（子域名）
- [ ] MX 记录已配置（如果需要邮件服务）
- [ ] TXT 记录已配置（SPF、DKIM、验证记录）
- [ ] CAA 记录已配置
- [ ] DNS 解析验证通过
- [ ] 全球 DNS 传播完成

### 10.2 安全配置检查

- [ ] 域名锁定已启用
- [ ] 两步验证已启用
- [ ] WHOIS 隐私保护已启用
- [ ] DNSSEC 已配置
- [ ] SSL/TLS 设置为 Full (strict)
- [ ] 防火墙规则已配置
- [ ] 强制 HTTPS 已启用

### 10.3 Cloudflare 配置检查

- [ ] 域名已添加到 Cloudflare
- [ ] 名称服务器已更新
- [ ] SSL/TLS 模式已设置
- [ ] 页面规则已配置
- [ ] 缓存规则已配置
- [ ] 防火墙规则已配置
- [ ] Always Online 已启用

---

## 11. 参考资源

### 11.1 官方文档

- [Cloudflare 文档](https://developers.cloudflare.com/)
- [阿里云 DNS 文档](https://help.aliyun.com/product/29697.html)
- [腾讯云 DNSPod 文档](https://docs.dnspod.cn/)
- [AWS Route 53 文档](https://docs.aws.amazon.com/route53/)

### 11.2 工具和资源

- [DNS Checker](https://dnschecker.org/)
- [What's My DNS](https://www.whatsmydns.net/)
- [MX Toolbox](https://mxtoolbox.com/)
- [SSL Labs](https://www.ssllabs.com/ssltest/)

### 11.3 相关文档

- [SSL 证书配置指南](SSL_CERTIFICATE_GUIDE.md)
- [Nginx 生产环境配置](config/nginx.production.conf)
- [生产环境部署指南](PRODUCTION_DEPLOYMENT_GUIDE.md)

---

**文档结束**
