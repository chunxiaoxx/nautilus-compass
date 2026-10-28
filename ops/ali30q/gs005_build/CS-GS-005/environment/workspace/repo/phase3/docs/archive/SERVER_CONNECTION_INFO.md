# 🔧 Nautilus 服务器连接信息

**更新时间**: 2026-03-04

---

## 📡 服务器信息

### 基本信息
- **服务器IP**: 43.160.239.61
- **SSH端口**: 24860 ⚠️ (非默认端口)
- **用户名**: ubuntu
- **密码**: DRKcx30190310@@

### SSH连接命令

```bash
# 正确的SSH连接命令
ssh -p 24860 ubuntu@43.160.239.61

# 或使用完整格式
ssh ubuntu@43.160.239.61 -p 24860
```

### SCP文件传输

```bash
# 上传文件到服务器
scp -P 24860 local_file ubuntu@43.160.239.61:/remote/path/

# 从服务器下载文件
scp -P 24860 ubuntu@43.160.239.61:/remote/path/file ./local/path/

# 上传整个目录
scp -P 24860 -r local_dir ubuntu@43.160.239.61:/remote/path/
```

---

## 🚀 快速修复 P0 问题

### 1. 修复生产环境配置 (30分钟)

```bash
# 连接到服务器
ssh -p 24860 ubuntu@43.160.239.61

# 进入项目目录
cd /var/www/nautilus-core/phase3/backend

# 备份当前配置
cp .env .env.backup.$(date +%Y%m%d)

# 修改配置
sudo nano .env

# 修改以下内容:
DEBUG=false
ENVIRONMENT=production
TESTING=false

# 保存后重启服务
pm2 restart nautilus-backend

# 验证配置
pm2 logs nautilus-backend --lines 50

# 检查服务状态
curl http://localhost:8000/health
```

### 2. 启用防火墙

```bash
# 启用UFW防火墙
sudo ufw enable
# 允许SSH端口（重要！）
sudo ufw allow 24860/tcp

# 允许HTTP和HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 检查防火墙状态
sudo ufw status verbose
```

### 3. 轮换密钥 (1小时)

```bash
# 生成新的JWT和CSRF密钥
openssl rand -hex 32  # 用于JWT_SECRET_KEY
openssl rand -hex 32  # 用于CSRF_SECRET_KEY

# 编辑.env文件
sudo nano /var/www/nautilus-core/phase3/backend/.env

# 更新密钥后重启
pm2 restart nautilus-backend
```

---

## 📊 服务状态检查

### 检查所有服务

```bash
# 连接服务器
ssh -p 24860 ubuntu@43.160.239.61

# 检查PM2进程
pm2 list

# 检查Nginx状态
sudo systemctl status nginx

# 检查PostgreSQL
sudo systemctl status postgresql

# 检查Redis
sudo systemctl status redis

# 检查磁盘空间
df -h

# 检查内存使用
free -h

# 检查端口监听
sudo netstat -tlnp | grep -E ':(80|443|8000|3000|5432|6379|9090|3001)'
```

### 查看日志

```bash
# 后端日志
pm2 logs nautilus-backend --lines 100

# Nginx访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 系统日志
sudo journalctl -u nginx -f
```

---

## 🔄 部署前端

### 从本地部署

```bash
# 在本地构建前端
cd C:\Users\chunx\Projects\nautilus-core\phase3\frontend
npm run build

# 上传到服务器
scp -P 24860 -r dist/* ubuntu@43.160.239.61:/var/www/nautilus-core/phase3/frontend/dist/

# 或使用rsync（更高效）
rsync -avz -e "ssh -p 24860" dist/ ubuntu@43.160.239.61:/var/www/nautilus-core/phase3/frontend/dist/
```

### 在服务器上构建

```bash
# 连接服务器
ssh -p 24860 ubuntu@43.160.239.61

# 进入前端目录
cd /var/www/nautilus-core/phase3/frontend

# 拉取最新代码
git pull origin master

# 安装依赖（如果需要）
npm install

# 构建
npm run build

# 重启Nginx
sudo systemctl reload nginx
```

---

## 🔍 故障排查

### 前端无法访问

```bash
# 检查Nginx配置
sudo nginx -t

# 查看Nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 检查文件权限
ls -la /var/www/nautilus-core/phase3/frontend/dist/

# 确保Nginx可以读取
sudo chown -R www-data:www-data /var/www/nautilus-core/phase3/frontend/dist/
```

### 后端API错误

```bash
# 查看后端日志
pm2 logs nautilus-backend --lines 200

# 检查环境变量
pm2 env 0  # 0是进程ID

# 重启后端
pm2 restart nautilus-backend

# 如果需要完全重启
pm2 delete nautilus-backend
cd /var/www/nautilus-core/phase3/backend
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name nautilus-backend
```

### 数据库连接问题

```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 测试数据库连接
psql -h localhost -U nautilus_user -d nautilus

# 检查数据库配置
cat /var/www/nautilus-core/phase3/backend/.env | grep DATABASE
```

---

## 🔐 安全注意事项

### ⚠️ 重要提醒

1. **立即更改密码**
   ```bash
   # 连接服务器后
   passwd
   # 输入新密码
   ```

2. **轮换SSH密钥**
   ```bash
   # 在本地生成新密钥
   ssh-keygen -t ed25519 -C "your_email@example.com"

   # 上传公钥到服务器
   ssh-copy-id -p 24860 -i ~/.ssh/id_ed25519.pub ubuntu@43.160.239.61

   # 禁用密码登录（可选，但推荐）
   sudo nano /etc/ssh/sshd_config
   # 设置: PasswordAuthentication no
   sudo systemctl restart sshd
   ```

3. **配置Fail2Ban**
   ```bash
   # 安装Fail2Ban
   sudo apt install fail2ban

   # 配置SSH保护
   sudo nano /etc/fail2ban/jail.local

   # 添加:
   [sshd]
   enabled = true
   port = 24860
   maxretry = 3
   bantime = 3600
   # 启动服务
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

---

## 📝 快速命令参考

### 一键检查脚本

```bash
# 创建检查脚本
cat > ~/check-nautilus.sh << 'EOF'
#!/bin/bash
echo "=== Nautilus 服务状态检查 ==="
echo "
echo "1. PM2 进程:"
pm2 list
echo ""
echo "2. Nginx 状态:"
sudo systemctl status nginx --no-pager
echo ""
echo "3. 磁盘空间:"
df -h | grep -E '(Filesystem|/$)'
echo ""
echo "4. 内存使用:"
free -h
echo ""
echo "5. 最近的错误日志:"
pm2 logs nautilus-backend --lines 10 --nostream
EOF

chmod +x ~/check-nautilus.sh

# 运行检查
~/check-nautilus.sh
```

### 常用命令别名

```bash
# 添加到 ~/.bashrc
cat >> ~/.bashrc << 'EOF'

# Nautilus 快捷命令
alias ncd='cd /var/www/nautilus-core/phase3'
alias nlog='pm2 logs nautilus-backend'
alias nrestart='pm2 restart nautilus-backend'
alias nstatus='pm2 list && sudo systemctl status nginx --no-pager'
alias ncheck='~/check-nautilus.sh'

EOF

# 重新加载配置
source ~/.bashrc
```

---

## 🎯 下一步行动

### 立即执行（使用正确的端口）

```bash
# 1. 连接服务器
ssh -p 24860 ubuntu@43.160.239.61

# 2. 修复生产配置
cd /var/www/nautilus-core/phase3/backend
sudo nano .env
# 修改: DEBUG=false, ENVIRONMENT=production

# 3. 重启服务
pm2 restart nautilus-backend

# 4. 验证
curl http://localhost:8000/health
```

---

**更新说明**:
- ✅ SSH端口已更正为 24860
- ✅ 所有命令已更新
- ✅ 添加了安全建议
- ✅ 提供了快速检查脚本

**安全提醒**:
- 🔴 服务器密码已暴露，请立即更改
- 🔴 建议配置SSH密钥认证
- 🔴 建议安装Fail2Ban防止暴力破解
