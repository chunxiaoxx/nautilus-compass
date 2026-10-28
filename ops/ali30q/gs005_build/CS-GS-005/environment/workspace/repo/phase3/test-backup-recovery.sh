#!/bin/bash
# Nautilus 备份恢复测试脚本
# 用途：验证备份和恢复流程是否正常工作

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
BACKUP_DIR="/backup"
TEST_BACKUP_DIR="/tmp/nautilus-backup-test"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================="
echo "Nautilus 备份恢复测试"
echo "测试时间: $(date)"
echo "========================================="
echo ""

# 创建测试目录
mkdir -p $TEST_BACKUP_DIR/{database,redis,config}

# ============================================
# 测试 1: PostgreSQL 备份和恢复
# ============================================
echo -e "${YELLOW}[测试 1/5] PostgreSQL 备份测试${NC}"

# 1.1 创建测试数据
echo "  → 创建测试数据..."
docker exec nautilus-postgres psql -U nautilus_user -d nautilus_production -c \
  "CREATE TABLE IF NOT EXISTS backup_test (id SERIAL PRIMARY KEY, test_data VARCHAR(100), created_at TIMESTAMP DEFAULT NOW());"

docker exec nautilus-postgres psql -U nautilus_user -d nautilus_production -c \
  "INSERT INTO backup_test (test_data) VALUES ('Test data for backup at $TIMESTAMP');"

TEST_DATA_COUNT=$(docker exec nautilus-postgres psql -U nautilus_user -d nautilus_production -t -c \
  "SELECT COUNT(*) FROM backup_test;")

echo "  → 测试数据已创建，记录数: $TEST_DATA_COUNT"

# 1.2 执行备份
echo "  → 执行 PostgreSQL 备份..."
docker exec nautilus-postgres pg_dump -U nautilus_user nautilus_production > $TEST_BACKUP_DIR/database/test_backup_$TIMESTAMP.sql

if [ -f "$TEST_BACKUP_DIR/database/test_backup_$TIMESTAMP.sql" ]; then
    BACKUP_SIZE=$(du -h $TEST_BACKUP_DIR/database/test_backup_$TIMESTAMP.sql | cut -f1)
    echo -e "  ${GREEN}✓ 备份成功，文件大小: $BACKUP_SIZE${NC}"
else
    echo -e "  ${RED}✗ 备份失败${NC}"
    exit 1
fi

# 1.3 删除测试数据
echo "  → 删除测试数据..."
docker exec nautilus-postgres psql -U nautilus_user -d nautilus_production -c \
  "DELETE FROM backup_test WHERE test_data LIKE '%$TIMESTAMP%';"

# 1.4 恢复测试
echo "  → 测试恢复..."
cat $TEST_BACKUP_DIR/database/test_backup_$TIMESTAMP.sql | \
  docker exec -i nautilus-postgres psql -U nautilus_user -d nautilus_production > /dev/null 2>&1

RESTORED_COUNT=$(docker exec nautilus-postgres psql -U nautilus_user -d nautilus_production -t -c \
  "SELECT COUNT(*) FROM backup_test WHERE test_data LIKE '%$TIMESTAMP%';")

if [ "$RESTORED_COUNT" -gt 0 ]; then
    echo -e "  ${GREEN}✓ 恢复成功，恢复记录数: $RESTORED_COUNT${NC}"
else
    echo -e "  ${RED}✗ 恢复失败${NC}"
    exit 1
fi

# 清理测试数据
docker exec nautilus-postgres psql -U nautilus_user -d nautilus_production -c \
  "DROP TABLE IF EXISTS backup_test;" > /dev/null 2>&1

echo ""

# ============================================
# 测试 2: Redis 备份和恢复
# ============================================
echo -e "${YELLOW}[测试 2/5] Redis 备份测试${NC}"

# 2.1 创建测试数据
echo "  → 创建测试数据..."
docker exec nautilus-redis redis-cli -a nautilus2024 SET "backup_test:$TIMESTAMP" "Test data for Redis backup" > /dev/null

TEST_VALUE=$(docker exec nautilus-redis redis-cli -a nautilus2024 GET "backup_test:$TIMESTAMP" 2>/dev/null)
echo "  → 测试数据已创建: $TEST_VALUE"

# 2.2 执行备份
echo "  → 执行 Redis 备份..."
docker exec nautilus-redis redis-cli -a nautilus2024 SAVE > /dev/null 2>&1
docker cp nautilus-redis:/data/dump.rdb $TEST_BACKUP_DIR/redis/test_backup_$TIMESTAMP.rdb

if [ -f "$TEST_BACKUP_DIR/redis/test_backup_$TIMESTAMP.rdb" ]; then
    BACKUP_SIZE=$(du -h $TEST_BACKUP_DIR/redis/test_backup_$TIMESTAMP.rdb | cut -f1)
    echo -e "  ${GREEN}✓ 备份成功，文件大小: $BACKUP_SIZE${NC}"
else
    echo -e "  ${RED}✗ 备份失败${NC}"
    exit 1
fi

# 2.3 删除测试数据
echo "  → 删除测试数据..."
docker exec nautilus-redis redis-cli -a nautilus2024 DEL "backup_test:$TIMESTAMP" > /dev/null 2>&1

# 2.4 恢复测试（注意：Redis 恢复需要重启容器）
echo "  → 测试恢复（模拟）..."
echo -e "  ${GREEN}✓ Redis 备份文件可用，实际恢复需要停止容器并替换 dump.rdb${NC}"

# 清理测试数据
docker exec nautilus-redis redis-cli -a nautilus2024 DEL "backup_test:$TIMESTAMP" > /dev/null 2>&1

echo ""

# ============================================
# 测试 3: 配置文件备份
# ============================================
echo -e "${YELLOW}[测试 3/5] 配置文件备份测试${NC}"

echo "  → 备份配置文件..."
tar -czf $TEST_BACKUP_DIR/config/test_config_$TIMESTAMP.tar.gz \
  -C /home/ubuntu/nautilus-mvp/phase3/backend .env 2>/dev/null || true

if [ -f "$TEST_BACKUP_DIR/config/test_config_$TIMESTAMP.tar.gz" ]; then
    BACKUP_SIZE=$(du -h $TEST_BACKUP_DIR/config/test_config_$TIMESTAMP.tar.gz | cut -f1)
    echo -e "  ${GREEN}✓ 配置备份成功，文件大小: $BACKUP_SIZE${NC}"

    # 测试解压
    tar -tzf $TEST_BACKUP_DIR/config/test_config_$TIMESTAMP.tar.gz > /dev/null 2>&1
    echo -e "  ${GREEN}✓ 配置文件可以正常解压${NC}"
else
    echo -e "  ${RED}✗ 配置备份失败${NC}"
    exit 1
fi

echo ""

# ============================================
# 测试 4: 自动备份脚本验证
# ============================================
echo -e "${YELLOW}[测试 4/5] 自动备份脚本验证${NC}"

# 检查备份脚本是否存在
BACKUP_SCRIPTS=(
    "/home/ubuntu/backup-database.sh"
    "/home/ubuntu/backup-redis.sh"
    "/home/ubuntu/backup-config.sh"
    "/home/ubuntu/backup-all.sh"
)

for script in "${BACKUP_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "  ${GREEN}✓ $script 存在且可执行${NC}"
        else
            echo -e "  ${YELLOW}⚠ $script 存在但不可执行${NC}"
        fi
    else
        echo -e "  ${RED}✗ $script 不存在${NC}"
    fi
done

# 检查 Cron 任务
echo "  → 检查 Cron 任务..."
if crontab -l 2>/dev/null | grep -q "backup-all.sh"; then
    echo -e "  ${GREEN}✓ Cron 任务已配置${NC}"
    crontab -l | grep backup-all.sh
else
    echo -e "  ${YELLOW}⚠ Cron 任务未配置${NC}"
fi

echo ""

# ============================================
# 测试 5: 恢复脚本验证
# ============================================
echo -e "${YELLOW}[测试 5/5] 恢复脚本验证${NC}"

RESTORE_SCRIPTS=(
    "/home/ubuntu/restore-database.sh"
    "/home/ubuntu/restore-redis.sh"
)

for script in "${RESTORE_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "  ${GREEN}✓ $script 存在且可执行${NC}"
        else
            echo -e "  ${YELLOW}⚠ $script 存在但不可执行${NC}"
        fi
    else
        echo -e "  ${RED}✗ $script 不存在${NC}"
    fi
done

echo ""

# ============================================
# 测试总结
# ============================================
echo "========================================="
echo -e "${GREEN}测试完成！${NC}"
echo "========================================="
echo ""
echo "测试结果摘要:"
echo "  ✓ PostgreSQL 备份和恢复: 通过"
echo "  ✓ Redis 备份: 通过"
echo "  ✓ 配置文件备份: 通过"
echo "  ✓ 备份脚本验证: 完成"
echo "  ✓ 恢复脚本验证: 完成"
echo ""
echo "测试备份文件位置: $TEST_BACKUP_DIR"
echo ""
echo "建议:"
echo "  1. 定期执行此测试脚本验证备份系统"
echo "  2. 每月至少进行一次完整恢复演练"
echo "  3. 确保备份文件异地存储"
echo "  4. 监控备份任务执行状态"
echo ""
echo "清理测试文件:"
echo "  rm -rf $TEST_BACKUP_DIR"
echo ""
