# Nautilus Social DNS 配置状态

**日期**: 2026-02-22
**域名**: nautilus.social

---

## ✅ DNS 解析状态

### 主域名
```
域名: nautilus.social
状态: ✅ 已解析
```

### 需要配置的DNS记录

请在你的域名注册商（Namecheap/GoDaddy/Cloudflare等）添加以下DNS记录：

```
类型    主机记录    记录值              TTL
A       @          43.160.239.61       600
A       www        43.160.239.61       600
A       api        43.160.239.61       600
```

---

## 📋 配置步骤

### 1. 登录域名管理面板

根据你注册域名的服务商，登录对应的管理面板：

**Namecheap**:
1. 登录 https://www.namecheap.com
2. 点击 "Domain List"
3. 找到 nautilus.social，点击 "Manage"
4. 点击 "Advanced DNS" 标签

**GoDaddy**:
1. 登录 https://www.godaddy.com
2. 点击 "My Products"
3. 找到 nautilus.social，点击 "DNS"

**Cloudflare**:
1. 登录 https://dash.cloudflare.com
2. 选择 nautilus.social
3. 点击 "DNS" 标签

### 2. 添加DNS记录

添加以下3条A记录：

#### 记录1: 主域名
```
类型: A
名称/主机: @ (或留空)
值/指向: 43.160.239.61
TTL: 600 (或 Automatic)
```

#### 记录2: WWW子域名
```
类型: A
名称/主机: www
值/指向: 43.160.239.61
TTL: 600 (或 Automatic)
```

#### 记录3: API子域名
```
类型: A
名称/主机: api
值/指向: 43.160.239.61
TTL: 600 (或 Automatic)
```

### 3. 保存配置

点击 "Save" 或 "Add Record" 保存所有记录。

---

## ⏱️ 等待DNS生效

DNS记录通常需要 **5-30分钟** 生效，最长可能需要24小时。

### 验证DNS是否生效

在Windows PowerShell或CMD中执行：

```powershell
# 检查主域名
nslookup nautilus.social 8.8.8.8

# 检查WWW
nslookup www.nautilus.social 8.8.8.8

# 检查API
nslookup api.nautilus.social 8.8.8.8
```

**期望结果**:
```
Server:  dns.google
Address:  8.8.8.8

Name:    nautilus.social
Address:  43.160.239.61
```

如果看到 `Address: 43.160.239.61`，说明DNS已生效！

---

## 🚀 DNS生效后的下一步

### 自动部署（推荐）

DNS生效后，执行以下命令开始自动部署：

```bash
# SSH登录服务器
ssh ubuntu@43.160.239.61

# 执行部署脚本
sudo /tmp/deploy-nautilus-social.sh
```

部署脚本会自动：
1. ✅ 检查DNS解析
2. ✅ 安装certbot和nginx
3. ✅ 获取SSL证书
4. ✅ 配置Nginx
5. ✅ 重启服务

### 预计时间

- DNS配置: 5分钟
- DNS生效: 5-30分钟
- 自动部署: 5-10分钟
- **总计**: 15-45分钟

---

## 📊 当前状态

- [x] 域名已注册: nautilus.social
- [x] 主域名DNS已解析
- [ ] WWW子域名DNS配置（待添加）
- [ ] API子域名DNS配置（待添加）
- [ ] DNS完全生效（待验证）
- [ ] SSL证书获取（待执行）
- [ ] Nginx配置（待执行）
- [ ] HTTPS部署（待完成）

---

## 🎯 立即行动

**现在请执行**:

1. **登录域名管理面板**
2. **添加3条A记录**（@, www, api → 43.160.239.61）
3. **保存配置**
4. **等待5-30分钟**
5. **验证DNS**: `nslookup www.nautilus.social 8.8.8.8`
6. **通知我DNS已生效**，我将立即执行部署

---

**配置DNS后，我们就可以立即部署HTTPS了！** 🚀
