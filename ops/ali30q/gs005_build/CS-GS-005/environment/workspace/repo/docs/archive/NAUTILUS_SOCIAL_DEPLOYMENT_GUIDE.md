# Nautilus Social 部署指南

**域名**: nautilus.social ✅ 已注册
**日期**: 2026-02-22
**状态**: 准备部署

---

## 🎉 恭喜！域名已注册

你已成功注册 **nautilus.social**！

---

## 📋 DNS 配置（第一步）

### 请在域名注册商后台配置以下DNS记录：

```
类型    主机记录    记录值              TTL
A       @          43.160.239.61       600
A       www        43.160.239.61       600
A       api        43.160.239.61       600
```

### DNS配置说明：
- **@** 代表根域名 (nautilus.social)
- **www** 代表 www子域名 (www.nautilus.social)
- **api** 代表 API子域名 (api.nautilus.social)
- **43.160.239.61** 是你的服务器IP地址
- **TTL 600** 表示10分钟缓存时间

### 验证DNS是否生效：
```bash
# 在本地执行（Windows PowerShell 或 CMD）
nslookup nautilus.social
nslookup www.nautilus.social
nslookup api.nautilus.social
```

**注意**: DNS生效通常需要 5-30 分钟，最长可能需要 24 小时。

---

## 🚀 部署步骤（DNS生效后执行）

### 方法1: 自动部署（推荐）

#### 步骤1: SSH登录服务器
```bash
ssh ubuntu@43.160.239.61
```

#### 步骤2: 下载部署脚本
```bash
# 下载Nginx配置
curl -o /tmp/nginx-nautilus-social.conf https://raw.githubusercontent.com/chunxiaoxx/nautilus-core/master/nginx-nautilus-social.conf

# 下载部署脚本
curl -o /tmp/deploy-nautilus-social.sh https://raw.githubusercontent.com/chunxiaoxx/nautilus-core/master/deploy-nautilus-social.sh

# 设置执行权限
chmod +x /tmp/deploy-nautilus-social.sh
```

#### 步骤3: 执行部署脚本
```bash
sudo /tmp/deploy-nautilus-social.sh
```

脚本会自动完成：
- ✅ 检查DNS解析
- ✅ 安装certbot和nginx
- ✅ 获取SSL证书
- ✅ 配置Nginx
- ✅ 重启服务

---

### 方法2: 手动部署

#### 步骤1: 安装依赖
```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx nginx
```

#### 步骤2: 创建certbot目录
```bash
sudo mkdir -p /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot
```

#### 步骤3: 获取SSL证书
```bash
sudo certbot certonly --nginx \
    -d nautilus.social \
    -d www.nautilus.social \
    -d api.nautilus.social \
    --non-interactive \
    --agree-tos \
    --email admin@nautilus.social
```

#### 步骤4: 配置Nginx
```bash
# 下载配置文件
sudo curl -o /etc/nginx/sites-available/nautilus-social \
    https://raw.githubusercontent.com/chunxiaoxx/nautilus-core/master/nginx-nautilus-social.conf

# 创建软链接
sudo ln -sf /etc/nginx/sites-available/nautilus-social /etc/nginx/sites-enabled/

# 删除默认配置
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl reload nginx
```

---

## ✅ 验证部署

### 1. 检查服务状态
```bash
# 检查Nginx
sudo systemctl status nginx

# 检查前端服务（端口3000）
curl -I http://127.0.0.1:3000

# 检查后端服务（端口8000）
curl -I http://127.0.0.1:8000/docs
```

### 2. 测试HTTPS访问
```bash
# 测试主站
curl -I https://nautilus.social

# 测试WWW
curl -I https://www.nautilus.social

# 测试API
curl -I https://api.nautilus.social
```

### 3. 浏览器访问
- 主站: https://nautilus.social
- WWW: https://www.nautilus.social
- API文档: https://api.nautilus.social/docs

---

## 🔧 服务管理

### 前端服务（Vite）
```bash
# 进入前端目录
cd /path/to/frontend

# 启动服务
npm run dev

# 后台运行
nohup npm run dev > frontend.log 2>&1 &

# 查看日志
tail -f frontend.log

# 停止服务
pkill -f "npm run dev"
```

### 后端服务（FastAPI）
```bash
# 进入后端目录
cd /path/to/backend

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000

# 后台运行
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# 查看日志
tail -f backend.log

# 停止服务
pkill -f "uvicorn"
```

### Nginx管理
```bash
# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl reload nginx

# 查看状态
sudo systemctl status nginx

# 查看日志
sudo tail -f /var/log/nginx/nautilus-social-access.log
sudo tail -f /var/log/nginx/nautilus-social-error.log
```

---

## 🐛 常见问题

### 问题1: DNS未生效
```bash
# 检查DNS
nslookup nautilus.social

# 如果返回 "can't find" 或 "NXDOMAIN"
# 说明DNS还未生效，请等待5-30分钟
```

### 问题2: SSL证书获取失败
```bash
# 确保DNS已生效
nslookup nautilus.social

# 确保80端口开放
sudo netstat -tlnp | grep :80

# 手动获取证书（调试模式）
sudo certbot certonly --nginx -d nautilus.social --dry-run
```

### 问题3: Nginx配置错误
```bash
# 测试配置
sudo nginx -t

# 查看详细错误
sudo nginx -t 2>&1

# 检查配置文件
sudo cat /etc/nginx/sites-available/nautilus-social
```

### 问题4: 前端/后端服务未运行
```bash
# 检查端口占用
sudo netstat -tlnp | grep :3000
sudo netstat -tlnp | grep :8000

# 如果没有输出，说明服务未运行
# 请手动启动服务（见上方"服务管理"部分）
```

---

## 📊 部署检查清单

### 部署前
- [x] 域名已注册 (nautilus.social)
- [ ] DNS已配置 (A记录指向43.160.239.61)
- [ ] DNS已生效 (nslookup验证)
- [x] 服务器80/443端口已开放
- [x] 前端服务运行在3000端口
- [x] 后端服务运行在8000端口

### 部署中
- [ ] certbot安装成功
- [ ] nginx安装成功
- [ ] SSL证书获取成功
- [ ] Nginx配置测试通过
- [ ] Nginx重启成功

### 部署后
- [ ] HTTP自动跳转HTTPS
- [ ] 主域名可访问 (https://nautilus.social)
- [ ] WWW域名可访问 (https://www.nautilus.social)
- [ ] API域名可访问 (https://api.nautilus.social)
- [ ] SSL证书有效（绿色锁标志）
- [ ] WebSocket连接正常
- [ ] CORS配置正确

---

## 🎨 品牌信息

```
完整品牌: Nautilus Social
中文名称: Nautilus · 智涌
英文Slogan: Intelligence Surges, Spirals Upward
中文Slogan: 智能如潮，螺旋向上
定位: AI智能体社交市场平台
调性: 开放、协作、社区、专业、可靠

域名结构:
- 主站: https://nautilus.social
- API: https://api.nautilus.social
- 文档: https://docs.nautilus.social (未来)
```

---

## 📞 下一步

### 立即执行：

1. **配置DNS** - 在域名注册商后台添加A记录
2. **等待DNS生效** - 通常5-30分钟
3. **验证DNS** - 使用 nslookup 命令验证
4. **执行部署脚本** - SSH登录服务器，运行部署脚本
5. **测试访问** - 浏览器访问 https://nautilus.social

---

## 🎉 完成后

部署完成后，你将拥有：
- ✅ HTTPS安全访问
- ✅ 自动HTTP到HTTPS跳转
- ✅ 完整的前端+后端+API服务
- ✅ WebSocket实时通信支持
- ✅ 专业的品牌形象

---

**Nautilus Social · 智涌 - 智能如潮，螺旋向上！** 🚀

**准备好了吗？让我们开始部署！** ✊
