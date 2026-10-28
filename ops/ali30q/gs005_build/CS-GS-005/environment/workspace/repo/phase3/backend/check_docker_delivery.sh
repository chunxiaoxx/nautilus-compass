#!/bin/bash

# ============================================
# Docker优化项目 - 完整性检查脚本
# ============================================
# 检查所有交付文件是否完整
# ============================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}Docker优化项目 - 完整性检查${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# 统计变量
total_files=0
found_files=0
missing_files=0

# 检查文件函数
check_file() {
    local file=$1
    local description=$2

    total_files=$((total_files + 1))

    if [ -f "$file" ]; then
        local size=$(ls -lh "$file" | awk '{print $5}')
        local lines=$(wc -l < "$file" 2>/dev/null || echo "N/A")
        echo -e "${GREEN}✓${NC} $file"
        echo -e "  ${BLUE}描述:${NC} $description"
        echo -e "  ${BLUE}大小:${NC} $size  ${BLUE}行数:${NC} $lines"
        found_files=$((found_files + 1))
    else
        echo -e "${RED}✗${NC} $file"
        echo -e "  ${YELLOW}状态:${NC} 文件不存在"
        missing_files=$((missing_files + 1))
    fi
    echo ""
}

# ============================================
# 检查Dockerfile
# ============================================
echo -e "${BLUE}[1/6] 检查Dockerfile文件...${NC}"
echo ""

check_file "Dockerfile" "原始Dockerfile（保留）"
check_file "Dockerfile.optimized" "优化版Dockerfile（开发/测试）"
check_file "Dockerfile.production" "生产版Dockerfile（生产环境）"

# ============================================
# 检查Docker Compose
# ============================================
echo -e "${BLUE}[2/6] 检查Docker Compose文件...${NC}"
echo ""

check_file "docker-compose.yml" "原始Docker Compose（保留）"
check_file "docker-compose.optimized.yml" "优化版Docker Compose（推荐）"

# ============================================
# 检查配置文件
# ============================================
echo -e "${BLUE}[3/6] 检查配置文件...${NC}"
echo ""

check_file ".dockerignore" "优化的dockerignore配置"

# ============================================
# 检查脚本文件
# ============================================
echo -e "${BLUE}[4/6] 检查脚本文件...${NC}"
echo ""

check_file "build_docker_images.sh" "自动化构建脚本"
check_file "test_docker_images.sh" "测试验证脚本"
check_file "verify_docker_optimization.sh" "快速验证脚本"

# ============================================
# 检查文档文件
# ============================================
echo -e "${BLUE}[5/6] 检查文档文件...${NC}"
echo ""

check_file "DOCKER_README.md" "项目README"
check_file "DOCKER_INDEX.md" "文档索引"
check_file "DOCKER_QUICK_REFERENCE.md" "快速参考"
check_file "DOCKER_FINAL_REPORT.md" "最终报告"
check_file "DOCKER_OPTIMIZATION_REPORT.md" "详细优化报告"
check_file "DOCKER_BEST_PRACTICES.md" "最佳实践指南"
check_file "DOCKER_OPTIMIZATION_SUMMARY.md" "项目总结"
check_file "DOCKER_WORK_COMPLETE.md" "完成报告"
check_file "DOCKER_DELIVERY_CHECKLIST.md" "交付清单"

# ============================================
# 检查脚本权限
# ============================================
echo -e "${BLUE}[6/6] 检查脚本权限...${NC}"
echo ""

scripts=(
    "build_docker_images.sh"
    "test_docker_images.sh"
    "verify_docker_optimization.sh"
)

for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "${GREEN}✓${NC} $script (可执行)"
        else
            echo -e "${YELLOW}!${NC} $script (不可执行，正在修复...)"
            chmod +x "$script"
            echo -e "${GREEN}✓${NC} 权限已修复"
        fi
    fi
done
echo ""

# ============================================
# 统计总结
# ============================================
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}检查结果统计${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

echo -e "${BLUE}总文件数:${NC} $total_files"
echo -e "${GREEN}已找到:${NC} $found_files"
echo -e "${RED}缺失:${NC} $missing_files"
echo ""

# 计算完成率
completion_rate=$((found_files * 100 / total_files))
echo -e "${BLUE}完成率:${NC} ${completion_rate}%"
echo ""

# ============================================
# 文件大小统计
# ============================================
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}文件大小统计${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

if command -v du &> /dev/null; then
    echo -e "${BLUE}Dockerfile总大小:${NC}"
    du -ch Dockerfile* 2>/dev/null | tail -1 || echo "无法计算"

    echo ""
    echo -e "${BLUE}Docker Compose总大小:${NC}"
    du -ch docker-compose*.yml 2>/dev/null | tail -1 || echo "无法计算"

    echo ""
    echo -e "${BLUE}脚本总大小:${NC}"
    du -ch build_docker_images.sh test_docker_images.sh verify_docker_optimization.sh 2>/dev/null | tail -1 || echo "无法计算"

    echo ""
    echo -e "${BLUE}文档总大小:${NC}"
    du -ch DOCKER_*.md 2>/dev/null | tail -1 || echo "无法计算"
fi
echo ""

# ============================================
# 最终结果
# ============================================
echo -e "${CYAN}============================================${NC}"

if [ $missing_files -eq 0 ]; then
    echo -e "${GREEN}✓ 所有文件检查完成！${NC}"
    echo -e "${GREEN}✓ Docker优化项目交付完整！${NC}"
    echo -e "${CYAN}============================================${NC}"
    echo ""
    echo -e "${BLUE}下一步:${NC}"
    echo "  1. 查看 DOCKER_INDEX.md 了解文档结构"
    echo "  2. 阅读 DOCKER_README.md 快速开始"
    echo "  3. 运行 ./test_docker_images.sh 测试构建"
    echo "  4. 参考 DOCKER_QUICK_REFERENCE.md 使用"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠ 发现 ${missing_files} 个文件缺失${NC}"
    echo -e "${CYAN}============================================${NC}"
    echo ""
    echo -e "${YELLOW}请检查缺失的文件${NC}"
    echo ""
    exit 1
fi
