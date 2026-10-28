# Nautilus Social - DNS 配置指南

**域名**: nautilus.social ✅ 已注册
**日期**: 2026-02-22

---

## 🎯 第一步：配置DNS（最重要）

### 请在你的域名注册商后台配置以下DNS记录：

```
记录类型    主机记录    记录值              TTL
A          @          43.160.239.61       600
A          www        43.160.239.61       600
A          api        43.160.239.61       600
```

### 详细说明：

| 字段 | 值 | 说明 |
|------|-----|------|
| **记录类型** | A | A记录（将域名指向IP地址） |
| **主机记录 @** | @ | 根域名 nautilus.social |
| **主机记录 www** | www | www.nautilus.social |
| **主机记录 api** | api | api.nautilus.social |
| **记录值** | 43.160.239.61 | 你的服务器IP地址 |
| **TTL** | 600 | 10分钟（600秒） |

---

## 📝 常见域名注册商配置方法

### Namecheap
1. 登录 Namecheap 账户
2. 进入 Domain List
3. 点击域名旁边的 "Manage"
4. 选择 "Advanced DNS" 标签
5. 点击 "Add New Record"
6. 添加上述3条A记录

### GoDaddy
1. 登录 GoDaddy 账户
2. 进入 My Products
3. 点击域名旁边的 "DNS"
4. 点击 "Add" 添加记录
5. 添加上述3条A记录

### Cloudflare
1. 登录 Cloudflare 账户
2. 选择你的域名
3. 进入 "DNS" 标签
4. 点击 "Add record"
5. 添加上述3条A记录
6. **重要**: 关闭橙色云朵（Proxy status）或等待SSL证书获取后再开启

### 阿里云（万网）
1. 登录阿里云控制台
2. 进入域名控制台
3. 点击域名后的 "解析"
4. 点击 "添加记录"
5. 添加上述3条A记录

### 腾讯云（DNSPod）
1. 登录腾讯云控制台
2. 进入域名解析
3. 选择域名
4. 点击 "添加记录"
5. 添加上述3条A记录

---

## ✅ 验证DNS是否生效

### 方法1: 使用 nslookup（Windows）
```cmd
nslookup nautilus.social
nslookup www.nautilus.social
nslookup api.nautilus.social
```

**成功示例**:
```
Server:  dns.google
Address:  8.8.8.8

Non-authoritative answer:
Name:    nautilus.social
Address:  43.160.239.61
```

### 方法2: 使用 dig（Linux/Mac）
```bash
dig nautilus.social
dig www.nautilus.social
dig api.nautilus.social
```

### 方法3: 在线工具
- https://dnschecker.org
- https://www.whatsmydns.net
- 输入域名，查看全球DNS传播状态

---

## ⏱️ DNS生效时间

- **最快**: 5-10分钟
- **通常**: 10-30分钟
- **最长**: 24-48小时（极少情况）

**建议**: 配置完成后等待30分钟，然后验证DNS是否生效。

---

## 🚀 DNS生效后的下一步

### 快速部署命令

```bash
# 1. SSH登录服务器
ssh ubuntu@43.160.239.61

# 2. 下载并执行部署脚本
curl -o /tmp/deploy.sh https://raw.githubusercontent.com/chunxiaoxx/nautilus-core/master/deploy-nautilus-social.sh
curl -o /tmp/nginx-config.conf https://raw.githubusercontent.com/chunxiaoxx/nautilus-core/master/nginx-nautilus-social.conf
chmod +x /tmp/deploy.sh
sudo /tmp/deploy.sh
```

---

## 📊 配置检查清单

- [ ] 已在域名注册商后台添加 @ 记录（指向 43.160.239.61）
- [ ] 已在域名注册商后台添加 www 记录（指向 43.160.239.61）
- [ ] 已在域名注册商后台添加 api 记录（指向 43.160.239.61）
- [ ] 已等待至少10分钟
- [ ] 使用 nslookup 验证 nautilus.social 解析成功
- [ ] 使用 nslookup 验证 www.nautilus.social 解析成功
- [ ] 使用 nslookup 验证 api.nautilus.social 解析成功

---

## 🐛 常见问题

### Q1: DNS配置后立即验证，显示未生效？
**A**: 这是正常的，DNS传播需要时间。请等待10-30分钟后再验证。

### Q2: 等待很久DNS还是未生效？
**A**: 检查以下几点：
- 确认记录类型是 "A" 而不是 "CNAME"
- 确认记录值是 "43.160.239.61" 而不是其他
- 确认没有其他冲突的记录
- 尝试清除本地DNS缓存：`ipconfig /flushdns`（Windows）

### Q3: 如何清除本地DNS缓存？
**A**:
- Windows: `ipconfig /flushdns`
- Mac: `sudo dscacheutil -flushcache`
- Linux: `sudo systemd-resolve --flush-caches`

### Q4: Cloudflare的橙色云朵要不要开启？
**A**:
- 初次部署时建议**关闭**（灰色云朵）
- 等SSL证书获取成功后，可以开启（橙色云朵）
- 开启后可以享受Cloudflare的CDN和DDoS防护

---

## 📞 配置完成后通知我

DNS配置完成并生效后，请告诉我：
1. "DNS已配置"
2. 或直接说 "继续部署"

我将立即帮你执行部署脚本！

---

**Nautilus Social · 智涌 - 智能如潮，螺旋向上！** 🚀
