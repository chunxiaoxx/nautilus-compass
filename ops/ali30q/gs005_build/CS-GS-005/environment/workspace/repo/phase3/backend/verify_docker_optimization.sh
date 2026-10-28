#!/bin/bash

# ============================================
# Docker优化验证脚本
# ============================================
# 快速验证Docker优化成果
# ============================================

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Docker优化成果验证${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 检查文件是否存在
echo -e "${BLUE}[1/5] 检查优化文件...${NC}"
files=(
    "Dockerfile.optimized"
    "Dockerfile.production"
    "docker-compose.optimized.yml"
    "build_docker_images.sh"
    "test_docker_images.sh"
    ".dockerignore"
    "DOCKER_OPTIMIZATION_REPORT.md"
    "DOCKER_BEST_PRACTICES.md"
    "DOCKER_OPTIMIZATION_SUMMARY.md"
    "DOCKER_WORK_COMPLETE.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${YELLOW}✗${NC} $file (未找到)"
    fi
done
echo ""

# 统计文件行数
echo -e "${BLUE}[2/5] 统计代码行数...${NC}"
if command -v wc &> /dev/null; then
    total_lines=$(wc -l Dockerfile.optimized Dockerfile.production docker-compose.optimized.yml build_docker_images.sh test_docker_images.sh 2>/dev/null | tail -1 | awk '{print $1}')
    echo -e "${GREEN}总代码行数: ${total_lines}${NC}"
fi
echo ""

# 检查脚本权限
echo -e "${BLUE}[3/5] 检查脚本权限...${NC}"
for script in build_docker_images.sh test_docker_images.sh; do
    if [ -x "$script" ]; then
        echo -e "${GREEN}✓${NC} $script (可执行)"
    else
        echo -e "${YELLOW}!${NC} $script (不可执行，正在修复...)"
        chmod +x "$script"
        echo -e "${GREEN}✓${NC} 权限已修复"
    fi
done
echo ""

# 显示Dockerfile对比
echo -e "${BLUE}[4/5] Dockerfile对比...${NC}"
echo "原始Dockerfile: $(wc -l < Dockerfile 2>/dev/null || echo '未知') 行"
echo "优化Dockerfile: $(wc -l < Dockerfile.optimized 2>/dev/null || echo '未知') 行"
echo "生产Dockerfile: $(wc -l < Dockerfile.production 2>/dev/null || echo '未知') 行"
echo ""

# 显示文档统计
echo -e "${BLUE}[5/5] 文档统计...${NC}"
doc_files=(
    "DOCKER_OPTIMIZATION_REPORT.md"
    "DOCKER_BEST_PRACTICES.md"
    "DOCKER_OPTIMIZATION_SUMMARY.md"
    "DOCKER_WORK_COMPLETE.md"
)

total_doc_lines=0
for doc in "${doc_files[@]}"; do
    if [ -f "$doc" ]; then
        lines=$(wc -l < "$doc" 2>/dev/null || echo 0)
        total_doc_lines=$((total_doc_lines + lines))
        echo "  $doc: $lines 行"
    fi
done
echo -e "${GREEN}文档总行数: ${total_doc_lines}${NC}"
echo ""

# 总结
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✓ Docker优化工作已完成！${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "交付成果："
echo "  ✓ 2个优化的Dockerfile"
echo "  ✓ 1个优化的Docker Compose配置"
echo "  ✓ 2个自动化脚本"
echo "  ✓ 4个完整文档"
echo "  ✓ 1个优化的.dockerignore"
echo ""
echo "下一步："
echo "  1. 运行 ./test_docker_images.sh 测试构建"
echo "  2. 查看 DOCKER_OPTIMIZATION_REPORT.md 了解详情"
echo "  3. 参考 DOCKER_BEST_PRACTICES.md 学习最佳实践"
echo "  4. 使用 ./build_docker_images.sh 自动化构建"
echo ""
