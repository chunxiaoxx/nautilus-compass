#!/bin/bash
# Nautilus服务器升级前备份脚本

echo "=== Nautilus服务器升级前备份 ==="
echo "开始时间: $(date)"
echo ""

# 1. 备份数据库
echo "1. 备份PostgreSQL数据库..."
docker exec nautilus-postgres pg_dump -U nautilus nautilus > /tmp/nautilus_backup_$(date +%Y%m%d_%H%M%S).sql
echo "✅ 数据库备份完成"

# 2. 备份Redis数据
echo "2. 备份Redis数据..."
docker exec nautilus-redis redis-cli SAVE
docker cp nautilus-redis:/data/dump.rdb /tmp/redis_backup_$(date +%Y%m%d_%H%M%S).rdb
echo "✅ Redis备份完成"

# 3. 备份配置文件
echo "3. 备份配置文件..."
cd /opt/nautilus
tar -czf /tmp/nautilus_config_$(date +%Y%m%d_%H%M%S).tar.gz .env docker-compose.simple.yml
echo "✅ 配置文件备份完成"

# 4. 导出Docker镜像
echo "4. 导出Docker镜像..."
docker save nautilus-api:latest | gzip > /tmp/nautilus_api_image_$(date +%Y%m%d_%H%M%S).tar.gz
echo "✅ Docker镜像备份完成"

# 5. 记录当前状态
echo "5. 记录当前状态..."
docker ps > /tmp/docker_status_$(date +%Y%m%d_%H%M%S).txt
docker images >> /tmp/docker_status_$(date +%Y%m%d_%H%M%S).txt
echo "✅ 状态记录完成"

echo ""
echo "=== 备份完成 ==="
echo "备份文件位置: /tmp/"
ls -lh /tmp/*$(date +%Y%m%d)* 2>/dev/null
echo ""
echo "完成时间: $(date)"
