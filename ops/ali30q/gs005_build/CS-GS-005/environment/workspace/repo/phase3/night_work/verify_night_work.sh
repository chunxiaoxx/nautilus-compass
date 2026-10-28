#!/bin/bash
# Nautilus 夜间工作验证脚本
# 用于快速验证所有夜间完成的工作

echo "=========================================="
echo "Nautilus 夜间工作验证脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 切换到后端目录
cd /c/Users/chunx/Projects/nautilus-core/phase3/backend

echo "步骤 1: 检查依赖安装"
echo "----------------------------------------"

# 检查 qrcode
if pip show qrcode > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} qrcode 已安装"
else
    echo -e "${YELLOW}⚠${NC} qrcode 未安装，正在安装..."
    pip install qrcode[pil]
fi

# 检查 Pillow
if pip show Pillow > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Pillow 已安装"
else
    echo -e "${YELLOW}⚠${NC} Pillow 未安装，正在安装..."
    pip install Pillow
fi

# 检查 prometheus-client
if pip show prometheus-client > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} prometheus-client 已安装"
else
    echo -e "${YELLOW}⚠${NC} prometheus-client 未安装，正在安装..."
    pip install prometheus-client
fi

echo ""
echo "步骤 2: 测试数据库健康检查"
echo "----------------------------------------"

python -c "
import asyncio
from monitoring_config import check_database_health

async def test():
    result = await check_database_health()
    if result['status'] == 'healthy':
        print('✓ 数据库健康检查: PASSED')
        print(f'  响应时间: {result.get(\"response_time\", \"N/A\")}s')
    else:
        print('✗ 数据库健康检查: FAILED')
        print(f'  错误: {result.get(\"error\", \"Unknown\")}')

asyncio.run(test())
"

echo ""
echo "步骤 3: 检查数据库迁移状态"
echo "----------------------------------------"

if [ -f "migrations/add_oauth_fields.py" ]; then
    echo -e "${GREEN}✓${NC} OAuth 迁移脚本已创建"
    echo "  运行迁移: python migrations/add_oauth_fields.py"
else
    echo -e "${RED}✗${NC} OAuth 迁移脚本未找到"
fi

echo ""
echo "步骤 4: 验证 API 端点代码"
echo "----------------------------------------"

# 检查 GitHub OAuth 端点
if grep -q "github/login" api/auth.py; then
    echo -e "${GREEN}✓${NC} GitHub OAuth 登录端点已实现"
else
    echo -e "${RED}✗${NC} GitHub OAuth 登录端点未找到"
fi

if grep -q "github/callback" api/auth.py; then
    echo -e "${GREEN}✓${NC} GitHub OAuth 回调端点已实现"
else
    echo -e "${RED}✗${NC} GitHub OAuth 回调端点未找到"
fi

# 检查 Agent 自主注册端点
if grep -q "agent_self_register" api/agents.py; then
    echo -e "${GREEN}✓${NC} Agent 自主注册端点已实现"
else
    echo -e "${RED}✗${NC} Agent 自主注册端点未找到"
fi

if grep -q "generate_qr_code" api/agents.py; then
    echo -e "${GREEN}✓${NC} QR 码生成功能已实现"
else
    echo -e "${RED}✗${NC} QR 码生成功能未找到"
fi

echo ""
echo "步骤 5: 检查环境变量配置"
echo "----------------------------------------"

if grep -q "GITHUB_CLIENT_ID" .env; then
    echo -e "${GREEN}✓${NC} GitHub OAuth 配置已添加"
else
    echo -e "${RED}✗${NC} GitHub OAuth 配置未找到"
fi

echo ""
echo "=========================================="
echo "验证完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 运行数据库迁移（如果 PostgreSQL 可用）："
echo "   python migrations/add_oauth_fields.py"
echo ""
echo "2. 启动后端服务："
echo "   python main.py"
echo ""
echo "3. 测试健康检查："
echo "   curl http://localhost:8000/health"
echo ""
echo "4. 测试 Agent 自主注册："
echo "   curl -X POST http://localhost:8000/api/agents/register \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"name\":\"Test Agent\",\"email\":\"test@example.com\"}'"
echo ""
echo "5. 测试 GitHub OAuth："
echo "   访问: http://localhost:8000/api/auth/github/login"
echo ""
echo "详细报告位于: ../night_work/"
echo ""
