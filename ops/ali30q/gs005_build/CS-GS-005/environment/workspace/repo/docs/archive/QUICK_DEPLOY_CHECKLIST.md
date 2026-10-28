# Nautilus Social - 快速部署清单

**域名**: nautilus.social ✅ 已注册
**服务器**: 43.160.239.61
**状态**: 等待DNS配置

---

## 📋 第一步：DNS配置（5分钟）

### 在你的域名注册商后台添加以下记录：

| 类型 | 主机记录 | 记录值 | TTL |
|------|---------|--------|-----|
| A | @ | 43.160.239.61 | 600 |
| A | www | 43.160.239.61 | 600 |
| A | api | 43.160.239.61 | 600 |

### 验证DNS（10-30分钟后）：
```bash
nslookup nautilus.social
```

---

## 🚀 第二步：一键部署（DNS生效后）

### 复制粘贴以下命令到服务器：

```bash
# SSH登录
ssh ubuntu@43.160.239.61

# 下载并执行部署脚本
curl -o /tmp/nginx-config.conf https://raw.githubusercontent.com/chunxiaoxx/nautilus-core/master/nginx-nautilus-social.conf && \
curl -o /tmp/deploy.sh https://raw.githubusercontent.com/chunxiaoxx/nautilus-core/master/deploy-nautilus-social.sh && \
chmod +x /tmp/deploy.sh && \
sudo /tmp/deploy.sh
```

---

## ✅ 第三步：验证部署

### 浏览器访问：
- https://nautilus.social
- https://www.nautilus.social
- https://api.nautilus.social/docs

---

## 📞 完成后通知

DNS配置完成后，告诉我：
- "DNS已配置" 或
- "继续部署"

---

**Nautilus Social · 智涌** 🚀
