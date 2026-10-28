# 🚀 Nautilus Phase3 更新部署计划

**服务器**: 阿里云 Ubuntu (43.160.239.61)
**现有版本**: MVP (nautilus-v7, 已停止)
**目标**: 部署Phase3最新版本

---

## 📊 现状分析

### 服务器现状
- ✅ Docker已安装 (29.2.1)
- ✅ 内存: 3.6GB (可用1.8GB)
- ✅ 磁盘: 59GB (可用25GB)
- ✅ MVP版本目录: `/home/ubuntu/nautilus-mvp/`
- ⏸️ 旧容器: `nautilus-v7` (已停止)

### MVP版本信息
- 目录: `/home/ubuntu/nautilus-mvp/phase3/`
- 包含: backend, frontend, contracts, agent-engine
- 最后运行: 2026-02-15

---

## 🎯 部署策略

### 方案: 更新现有部署（推荐）

**优点**:
- 保留现有配置和数据
- 风险低，可快速回滚
- 不影响其他服务

**步骤**:
1. 备份现有MVP版本
2. 拉取最新phase3代码
3. 更新后端代码
4. 重新构建Docker镜像
5. 启动新版本
6. 验证部署

---

## 📝 详细步骤

### 步骤1: 备份现有版本

```bash
# 连接服务器
ssh cloud -p 24860

# 备份MVP版本
cd /home/ubuntu
cp -r nautilus-mvp nautilus-mvp-backup-$(date +%Y%m%d)

# 备份Docker镜像
docker save nautilus-v7:latest > nautilus-v7-backup.tar
```

### 步骤2: 更新代码

```bash
# 进入项目目录
cd /home/ubuntu/nautilus-mvp

# 拉取最新代码
git pull origin master

# 或者从本地上传最新代码
# 在本地执行:
# cd ~/Projects/nautilus-core/phase3
# rsync -avz -e "ssh -p 24860" backend/ cloud:/home/ubuntu/nautilus-mvp/phase3/backend/
```

### 步骤3: 配置环境变量

```bash
cd /home/ubuntu/nautilus-mvp/phase3/backend

# 检查现有环境变量
cat .env 2>/dev/null

# 如果需要，创建新的环境变量文件
cp .env.example .env
vim .env
```

**必须配置的环境变量**:
```bash
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/nautilus
REDIS_URL=redis://localhost:6379/0

# 安全
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret

# 区块链
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/YOUR_KEY
PRIVATE_KEY=your-private-key
```

### 步骤4: 构建新Docker镜像

```bash
cd /home/ubuntu/nautilus-mvp/phase3/backend

# 停止旧容器
docker stop nautilus-v7 2>/dev/null || true
docker rm nautilus-v7 2>/dev/null || true

# 构建新镜像
docker build -t nautilus-phase3:latest .

# 或者使用docker-compose
docker-compose build
```

### 步骤5: 启动服务

**方法A: 使用Docker直接运行**

```bash
docker run -d \
  --name nautilus-phase3 \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  nautilus-phase3:latest
```

**方法B: 使用Docker Compose（推荐）**

```bash
# 创建docker-compose.yml
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  api:
    build: .
    container_name: nautilus-phase3
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    container_name: nautilus-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: nautilus
      POSTGRES_USER: nautilus_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: nautilus-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  redis_data:
EOF

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 步骤6: 验证部署

```bash
# 检查容器状态
docker ps

# 测试API健康检查
curl http://localhost:8000/health

# 测试API文档
curl http://localhost:8000/docs

# 查看日志
docker logs nautilus-phase3

# 测试外部访问
curl http://43.160.239.61:8000/health
```

### 步骤7: 配置Nginx（如果需要）

```bash
# 检查是否已有Nginx配置
ls -la /etc/nginx/sites-available/nautilus*

# 如果需要更新Nginx配置
sudo vim /etc/nginx/sites-available/nautilus

# 重启Nginx
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔄 快速更新脚本

创建一个快速更新脚本：

```bash
cat > /home/ubuntu/update-nautilus.sh <<'EOF'
#!/bin/bash
set -e

echo "🚀 开始更新Nautilus Phase3..."

# 进入项目目录
cd /home/ubuntu/nautilus-mvp

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin master

# 进入backend目录
cd phase3/backend

# 停止旧容器
echo "🛑 停止旧容器..."
docker-compose down 2>/dev/null || true

# 构建新镜像
echo "🔨 构建新镜像..."
docker-compose build

# 启动服务
echo "▶️ 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 验证部署
echo "✅ 验证部署..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 部署成功！"
    docker-compose ps
else
    echo "❌ 部署失败，查看日志："
    docker-compose logs --tail=50
    exit 1
fi

echo "🎉 更新完成！"
EOF

chmod +x /home/ubuntu/update-nautilus.sh
```

使用方法：
```bash
ssh cloud -p 24860 "bash /home/ubuntu/update-nautilus.sh"
```

---

## 🔙 回滚方案

如果新版本有问题，快速回滚：

```bash
# 停止新版本
docker-compose down

# 恢复旧版本
docker load < nautilus-v7-backup.tar
docker start nautilus-v7

# 或者恢复备份目录
cd /home/ubuntu
rm -rf nautilus-mvp
mv nautilus-mvp-backup-YYYYMMDD nautilus-mvp
```

---

## 📋 检查清单

### 部署前
- [ ] 备份现有版本
- [ ] 检查环境变量配置
- [ ] 确认数据库连接
- [ ] 确认磁盘空间充足

### 部署中
- [ ] 拉取最新代码
- [ ] 构建Docker镜像
- [ ] 启动服务
- [ ] 检查容器状态

### 部署后
- [ ] 测试API健康检查
- [ ] 测试API文档访问
- [ ] 测试外部访问
- [ ] 检查日志无错误
- [ ] 更新Nginx配置（如需要）

---

## 🎯 下一步

1. **立即执行**: 备份并更新代码
2. **测试验证**: 确保所有功能正常
3. **监控观察**: 观察服务运行状态
4. **优化配置**: 根据实际情况调整

---

**准备好开始部署了吗？** 🚀
