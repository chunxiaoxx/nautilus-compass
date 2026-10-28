# Nautilus 域名部署实施手册

**日期**: 2026-02-21
**状态**: 准备就绪

---

## 📋 准备工作清单

### ✅ 已完成
- [x] 创建两套完整的Nginx配置文件
- [x] 创建两套一键部署脚本
- [x] 准备DNS配置说明
- [x] 准备SSL证书获取流程
- [x] 前端服务运行在端口3000
- [x] 后端服务运行在端口8000

### ⏳ 待完成
- [ ] 选择最终域名（nautilus.social 或 nautilusx.ai）
- [ ] 注册域名
- [ ] 配置DNS解析
- [ ] 执行部署脚本

---

## 🎯 两个方案对比

| 项目 | nautilus.social | nautilusx.ai |
|------|----------------|--------------|
| **配置文件** | nginx-nautilus-social.conf | nginx-nautilusx-ai.conf |
| **部署脚本** | deploy-nautilus-social.sh | deploy-nautilusx-ai.sh |
| **主域名** | nautilus.social | nautilusx.ai |
| **API域名** | api.nautilus.social | api.nautilusx.ai |
| **WWW域名** | www.nautilus.social | www.nautilusx.ai |
| **年费** | $50/年 | $150/年 |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 📝 方案A: nautilus.social 部署流程

### 步骤1: 注册域名

**推荐注册商**:
- Namecheap: https://www.namecheap.com
- GoDaddy: https://www.godaddy.com
- Cloudflare: https://www.cloudflare.com

**注册信息**:
```
域名: nautilus.social
年费: 约 $50
续费: 自动续费（建议）
```

### 步骤2: 配置DNS解析

登录域名注册商的DNS管理面板，添加以下记录：

```
类型    主机记录    记录值              TTL
A       @          43.160.239.61       600
A       www        43.160.239.61       600
A       api        43.160.239.61       600
```

**验证DNS解析**:
```bash
# 等待5-30分钟后执行
nslookup nautilus.social
nslookup www.nautilus.social
nslookup api.nautilus.social
```

### 步骤3: 上传配置文件到服务器

```bash
# 在本地执行（Windows WSL）
cd /mnt/c/Users/chunx/Projects/nautilus-core

# 上传Nginx配置
cat nginx-nautilus-social.conf | ssh ubuntu@43.160.239.61 'cat > /tmp/nginx-nautilus-social.conf'

# 上传部署脚本
cat deploy-nautilus-social.sh | ssh ubuntu@43.160.239.61 'cat > /tmp/deploy-nautilus-social.sh'

# 设置执行权限
ssh ubuntu@43.160.239.61 'chmod +x /tmp/deploy-nautilus-social.sh'
```

### 步骤4: 执行部署脚本

```bash
# SSH登录服务器
ssh ubuntu@43.160.239.61

# 执行部署脚本
sudo /tmp/deploy-nautilus-social.sh
```

**脚本会自动完成**:
1. ✅ 检查DNS解析
2. ✅ 安装certbot和nginx
3. ✅ 创建certbot目录
4. ✅ 获取SSL证书
5. ✅ 配置Nginx
6. ✅ 重启服务

### 步骤5: 验证部署

```bash
# 测试HTTPS访问
curl -I https://nautilus.social
curl -I https://www.nautilus.social
curl -I https://api.nautilus.social

# 检查SSL证书
openssl s_client -connect nautilus.social:443 -servername nautilus.social < /dev/null

# 查看日志
tail -f /var/log/nginx/nautilus-social-access.log
tail -f /var/log/nginx/nautilus-social-error.log
```

### 步骤6: 浏览器测试

访问以下地址：
- https://nautilus.social
- https://www.nautilus.social
- https://api.nautilus.social/docs

---

## 📝 方案B: nautilusx.ai 部署流程

### 步骤1: 注册域名

**推荐注册商**:
- Namecheap: https://www.namecheap.com
- GoDaddy: https://www.godaddy.com
- 101domain: https://www.101domain.com

**注册信息**:
```
域名: nautilusx.ai
年费: 约 $150
续费: 自动续费（建议）
```

### 步骤2: 配置DNS解析

登录域名注册商的DNS管理面板，添加以下记录：

```
类型    主机记录    记录值              TTL
A       @          43.160.239.61       600
A       www        43.160.239.61       600
A       api        43.160.239.61       600
```

**验证DNS解析**:
```bash
# 等待5-30分钟后执行
nslookup nautilusx.ai
nslookup www.nautilusx.ai
nslookup api.nautilusx.ai
```

### 步骤3: 上传配置文件到服务器

```bash
# 在本地执行（Windows WSL）
cd /mnt/c/Users/chunx/Projects/nautilus-core

# 上传Nginx配置
cat nginx-nautilusx-ai.conf | ssh ubuntu@43.160.239.61 'cat > /tmp/nginx-nautilusx-ai.conf'

# 上传部署脚本
cat deploy-nautilusx-ai.sh | ssh ubuntu@43.160.239.61 'cat > /tmp/deploy-nautilusx-ai.sh'

# 设置执行权限
ssh ubuntu@43.160.239.61 'chmod +x /tmp/deploy-nautilusx-ai.sh'
```

### 步骤4: 执行部署脚本

```bash
# SSH登录服务器
ssh ubuntu@43.160.239.61

# 执行部署脚本
sudo /tmp/deploy-nautilusx-ai.sh
```

**脚本会自动完成**:
1. ✅ 检查DNS解析
2. ✅ 安装certbot和nginx
3. ✅ 创建certbot目录
4. ✅ 获取SSL证书
5. ✅ 配置Nginx
6. ✅ 重启服务

### 步骤5: 验证部署

```bash
# 测试HTTPS访问
curl -I https://nautilusx.ai
curl -I https://www.nautilusx.ai
curl -I https://api.nautilusx.ai

# 检查SSL证书
openssl s_client -connect nautilusx.ai:443 -servername nautilusx.ai < /dev/null

# 查看日志
tail -f /var/log/nginx/nautilusx-ai-access.log
tail -f /var/log/nginx/nautilusx-ai-error.log
```

### 步骤6: 浏览器测试

访问以下地址：
- https://nautilusx.ai
- https://www.nautilusx.ai
- https://api.nautilusx.ai/docs

---

## 🔧 服务管理命令

### Nginx管理
```bash
# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl reload nginx

# 查看状态
sudo systemctl status nginx

# 查看错误日志
sudo tail -f /var/log/nginx/error.log
```

### SSL证书管理
```bash
# 查看证书信息
sudo certbot certificates

# 手动续期
sudo certbot renew

# 测试续期（不实际执行）
sudo certbot renew --dry-run
```

### 前端服务管理
```bash
# 启动前端（Vite）
cd /path/to/frontend
npm run dev

# 后台运行
nohup npm run dev > frontend.log 2>&1 &

# 查看日志
tail -f frontend.log
```

### 后端服务管理
```bash
# 启动后端（FastAPI）
cd /path/to/backend
uvicorn main:app --host 0.0.0.0 --port 8000

# 后台运行
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# 查看日志
tail -f backend.log
```

---

## 🐛 常见问题排查

### 问题1: DNS解析失败
```bash
# 检查DNS配置
nslookup your-domain.com

# 等待DNS传播（可能需要1-24小时）
# 使用在线工具检查: https://dnschecker.org
```

### 问题2: SSL证书获取失败
```bash
# 检查80端口是否开放
sudo netstat -tlnp | grep :80

# 检查防火墙
sudo ufw status

# 手动获取证书（调试模式）
sudo certbot certonly --nginx -d your-domain.com --dry-run
```

### 问题3: Nginx配置错误
```bash
# 测试配置
sudo nginx -t

# 查看详细错误
sudo nginx -t 2>&1

# 检查配置文件语法
sudo cat /etc/nginx/sites-available/your-config | grep -n "error"
```

### 问题4: 前端/后端服务无法访问
```bash
# 检查端口占用
sudo netstat -tlnp | grep :3000
sudo netstat -tlnp | grep :8000

# 检查进程
ps aux | grep node
ps aux | grep uvicorn

# 重启服务
pkill -f "npm run dev"
pkill -f "uvicorn"
```

### 问题5: CORS错误
```bash
# 检查Nginx CORS配置
sudo cat /etc/nginx/sites-available/your-config | grep -A 5 "Access-Control"

# 测试API访问
curl -H "Origin: https://your-domain.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://api.your-domain.com/endpoint
```

---

## 📊 部署检查清单

### 部署前检查
- [ ] 域名已注册
- [ ] DNS已配置（A记录指向43.160.239.61）
- [ ] DNS已生效（nslookup验证）
- [ ] 服务器80/443端口已开放
- [ ] 前端服务运行在3000端口
- [ ] 后端服务运行在8000端口

### 部署中检查
- [ ] certbot安装成功
- [ ] nginx安装成功
- [ ] SSL证书获取成功
- [ ] Nginx配置测试通过
- [ ] Nginx重启成功

### 部署后检查
- [ ] HTTP自动跳转HTTPS
- [ ] 主域名可访问（https://domain.com）
- [ ] WWW域名可访问（https://www.domain.com）
- [ ] API域名可访问（https://api.domain.com）
- [ ] SSL证书有效（绿色锁标志）
- [ ] WebSocket连接正常
- [ ] CORS配置正确

---

## 🎯 快速决策

### 如果选择 nautilus.social
```bash
# 执行以下命令开始部署
cd /mnt/c/Users/chunx/Projects/nautilus-core
cat deploy-nautilus-social.sh | ssh ubuntu@43.160.239.61 'cat > /tmp/deploy.sh && chmod +x /tmp/deploy.sh'
cat nginx-nautilus-social.conf | ssh ubuntu@43.160.239.61 'cat > /tmp/nginx-config.conf'
ssh ubuntu@43.160.239.61 'sudo /tmp/deploy.sh'
```

### 如果选择 nautilusx.ai
```bash
# 执行以下命令开始部署
cd /mnt/c/Users/chunx/Projects/nautilus-core
cat deploy-nautilusx-ai.sh | ssh ubuntu@43.160.239.61 'cat > /tmp/deploy.sh && chmod +x /tmp/deploy.sh'
cat nginx-nautilusx-ai.conf | ssh ubuntu@43.160.239.61 'cat > /tmp/nginx-config.conf'
ssh ubuntu@43.160.239.61 'sudo /tmp/deploy.sh'
```

---

## 📞 支持信息

**服务器信息**:
- IP: 43.160.239.61
- 用户: ubuntu
- 前端端口: 3000
- 后端端口: 8000

**文档位置**:
- 决策指南: DOMAIN_FINAL_DECISION_GUIDE.md
- 实施手册: DOMAIN_DEPLOYMENT_MANUAL.md（本文件）
- Nginx配置: nginx-nautilus-social.conf / nginx-nautilusx-ai.conf
- 部署脚本: deploy-nautilus-social.sh / deploy-nautilusx-ai.sh

---

**准备就绪，等待你的最终决策！**

**Nautilus · 智涌 - 智能如潮，螺旋向上！** 🚀
