#!/bin/bash

################################################################################
# Nautilus 生产环境配置准备脚本
################################################################################

set -e

echo "🚀 Nautilus 生产环境配置准备"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置文件路径
ENV_FILE=".env.production"
ENV_TEMPLATE=".env.production.template"

# 检查是否存在配置文件
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗${NC} 配置文件不存在: $ENV_FILE"
    if [ -f "$ENV_TEMPLATE" ]; then
        echo -e "${BLUE}ℹ${NC} 从模板创建配置文件..."
        cp "$ENV_TEMPLATE" "$ENV_FILE"
        echo -e "${GREEN}✓${NC} 已创建配置文件"
    else
        echo -e "${RED}✗${NC} 模板文件也不存在: $ENV_TEMPLATE"
        exit 1
    fi
fi

echo -e "${BLUE}ℹ${NC} 检查生产环境配置..."
echo ""

# 生成强密钥的函数
generate_key() {
    openssl rand -base64 32 | tr -d '\n'
}

# 检查并生成缺失的密钥
echo "🔑 检查密钥配置..."

# 检查 SECRET_KEY
if grep -q "SECRET_KEY=your-secret-key-change-in-production" "$ENV_FILE" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} SECRET_KEY 使用默认值，正在生成新密钥..."
    NEW_KEY=$(generate_key)
    sed -i "s|SECRET_KEY=your-secret-key-change-in-production|SECRET_KEY=$NEW_KEY|g" "$ENV_FILE"
    echo -e "${GREEN}✓${NC} SECRET_KEY 已更新"
else
    echo -e "${GREEN}✓${NC} SECRET_KEY 已配置"
fi

# 检查 JWT_SECRET_KEY
if grep -q "JWT_SECRET_KEY=your-jwt-secret-key-here" "$ENV_FILE" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} JWT_SECRET_KEY 使用默认值，正在生成新密钥..."
    NEW_KEY=$(generate_key)
    sed -i "s|JWT_SECRET_KEY=your-jwt-secret-key-here|JWT_SECRET_KEY=$NEW_KEY|g" "$ENV_FILE"
    echo -e "${GREEN}✓${NC} JWT_SECRET_KEY 已更新"
else
    echo -e "${GREEN}✓${NC} JWT_SECRET_KEY 已配置"
fi

# 添加缺失的环境变量
echo ""
echo "📝 检查必需的环境变量..."

# 添加 ENVIRONMENT
if ! grep -q "^ENVIRONMENT=" "$ENV_FILE"; then
    echo "ENVIRONMENT=production" >> "$ENV_FILE"
    echo -e "${GREEN}✓${NC} 已添加 ENVIRONMENT=production"
else
    # 确保设置为 production
    sed -i 's/^ENVIRONMENT=.*/ENVIRONMENT=production/' "$ENV_FILE"
    echo -e "${GREEN}✓${NC} ENVIRONMENT 已设置为 production"
fi

# 添加 DEBUG
if ! grep -q "^DEBUG=" "$ENV_FILE"; then
    echo "DEBUG=false" >> "$ENV_FILE"
    echo -e "${GREEN}✓${NC} 已添加 DEBUG=false"
else
    sed -i 's/^DEBUG=.*/DEBUG=false/' "$ENV_FILE"
    echo -e "${GREEN}✓${NC} DEBUG 已设置为 false"
fi

# 添加 CSRF_SECRET_KEY
if ! grep -q "^CSRF_SECRET_KEY=" "$ENV_FILE"; then
    CSRF_KEY=$(generate_key)
    echo "CSRF_SECRET_KEY=$CSRF_KEY" >> "$ENV_FILE"
    echo -e "${GREEN}✓${NC} 已添加 CSRF_SECRET_KEY"
else
    echo -e "${GREEN}✓${NC} CSRF_SECRET_KEY 已存在"
fi

# 添加 BLOCKCHAIN_NETWORK
if ! grep -q "^BLOCKCHAIN_NETWORK=" "$ENV_FILE"; then
    echo "BLOCKCHAIN_NETWORK=sepolia" >> "$ENV_FILE"
    echo -e "${GREEN}✓${NC} 已添加 BLOCKCHAIN_NETWORK=sepolia"
else
    echo -e "${GREEN}✓${NC} BLOCKCHAIN_NETWORK 已存在"
fi

# 添加 BLOCKCHAIN_RPC_URL (使用已有的 SEPOLIA_RPC_URL)
if ! grep -q "^BLOCKCHAIN_RPC_URL=" "$ENV_FILE"; then
    if grep -q "^SEPOLIA_RPC_URL=" "$ENV_FILE"; then
        RPC_URL=$(grep "^SEPOLIA_RPC_URL=" "$ENV_FILE" | cut -d'=' -f2-)
        echo "BLOCKCHAIN_RPC_URL=$RPC_URL" >> "$ENV_FILE"
        echo -e "${GREEN}✓${NC} 已添加 BLOCKCHAIN_RPC_URL"
    else
        echo -e "${YELLOW}⚠${NC} 需要手动配置 BLOCKCHAIN_RPC_URL"
    fi
else
    echo -e "${GREEN}✓${NC} BLOCKCHAIN_RPC_URL 已存在"
fi

# 添加 CORS_ORIGINS
if ! grep -q "^CORS_ORIGINS=" "$ENV_FILE"; then
    echo 'CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]' >> "$ENV_FILE"
    echo -e "${YELLOW}⚠${NC} 已添加默认 CORS_ORIGINS，请根据实际域名修改"
else
    echo -e "${GREEN}✓${NC} CORS_ORIGINS 已存在"
fi

echo ""
echo "✅ 配置准备完成！"
echo ""
echo "📋 下一步操作："
echo "1. 检查 $ENV_FILE 中的配置"
echo "2. 更新以下配置为实际值："
echo "   - DATABASE_URL (生产数据库)"
echo "   - REDIS_URL (生产Redis)"
echo "   - CORS_ORIGINS (实际前端域名)"
echo "   - BLOCKCHAIN_PRIVATE_KEY (如需要)"
echo "3. 运行验证: bash scripts/deploy/validate_config.sh $ENV_FILE"
echo ""
