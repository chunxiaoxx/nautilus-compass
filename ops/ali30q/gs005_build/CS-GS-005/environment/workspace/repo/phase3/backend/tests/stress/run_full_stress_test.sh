#!/bin/bash
# 生产环境压力测试完整流程脚本
#
# 此脚本自动化执行完整的压力测试流程：
# 1. 启动资源监控
# 2. 执行压力测试
# 3. 分析测试结果
# 4. 生成综合报告
#
# 使用方式:
#   ./run_full_stress_test.sh light
#   ./run_full_stress_test.sh medium
#   ./run_full_stress_test.sh heavy

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 默认参数
TEST_LEVEL="${1:-light}"
API_HOST="${2:-http://localhost:8000}"

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."

    if ! command -v python &> /dev/null; then
        print_error "Python未安装"
        exit 1
    fi

    if ! python -c "import locust" 2>/dev/null; then
        print_error "Locust未安装，请运行: pip install locust"
        exit 1
    fi

    if ! python -c "import psutil" 2>/dev/null; then
        print_warn "psutil未安装，资源监控将被跳过"
        SKIP_MONITORING=true
    fi

    print_info "依赖检查完成"
}

# 检查服务器状态
check_server() {
    print_info "检查服务器状态: $API_HOST"

    if curl -s -f "$API_HOST/health" > /dev/null 2>&1; then
        print_info "服务器运行正常"
    else
        print_error "无法连接到服务器: $API_HOST"
        print_error "请确保服务器正在运行"
        exit 1
    fi
}

# 启动资源监控
start_monitoring() {
    if [ "$SKIP_MONITORING" = true ]; then
        print_warn "跳过资源监控"
        return
    fi

    print_info "启动资源监控..."

    # 根据测试级别确定监控时长
    case $TEST_LEVEL in
        light)
            MONITOR_DURATION=600  # 10分钟
            ;;
        medium)
            MONITOR_DURATION=900  # 15分钟
            ;;
        heavy)
            MONITOR_DURATION=1200 # 20分钟
            ;;
        peak)
            MONITOR_DURATION=900  # 15分钟
            ;;
        endurance)
            MONITOR_DURATION=3600 # 60分钟
            ;;
        *)
            MONITOR_DURATION=600
            ;;
    esac

    python "$SCRIPT_DIR/monitor_resources.py" \
        --duration $MONITOR_DURATION \
        --interval 5 \
        --api-url "$API_HOST" \
        > "$RESULTS_DIR/monitor_${TEST_LEVEL}_${TIMESTAMP}.log" 2>&1 &

    MONITOR_PID=$!
    print_info "资源监控已启动 (PID: $MONITOR_PID)"

    # 等待监控启动
    sleep 2
}

# 运行压力测试
run_stress_test() {
    print_info "运行压力测试: $TEST_LEVEL"
    print_info "目标主机: $API_HOST"

    cd "$BACKEND_DIR"

    python "$SCRIPT_DIR/run_production_tests.py" \
        --level "$TEST_LEVEL" \
        --host "$API_HOST"

    TEST_EXIT_CODE=$?

    if [ $TEST_EXIT_CODE -eq 0 ]; then
        print_info "压力测试完成"
    else
        print_error "压力测试失败 (退出码: $TEST_EXIT_CODE)"
        return $TEST_EXIT_CODE
    fi
}

# 等待监控完成
wait_monitoring() {
    if [ "$SKIP_MONITORING" = true ] || [ -z "$MONITOR_PID" ]; then
        return
    fi

    print_info "等待资源监控完成..."

    # 等待监控进程结束
    wait $MONITOR_PID 2>/dev/null || true

    print_info "资源监控已完成"
}

# 分析测试结果
analyze_results() {
    print_info "分析测试结果..."

    # 查找最新的stats文件
    LATEST_STATS=$(ls -t "$RESULTS_DIR"/production_${TEST_LEVEL}_*_stats.csv 2>/dev/null | head -1)

    if [ -z "$LATEST_STATS" ]; then
        print_warn "未找到测试结果文件"
        return
    fi

    print_info "分析文件: $LATEST_STATS"

    python "$SCRIPT_DIR/analyze_test_results.py" \
        --csv "$LATEST_STATS"

    print_info "结果分析完成"
}

# 生成综合报告
generate_summary() {
    print_info "生成测试摘要..."

    SUMMARY_FILE="$RESULTS_DIR/summary_${TEST_LEVEL}_${TIMESTAMP}.txt"

    cat > "$SUMMARY_FILE" << EOF
================================================================================
生产环境压力测试摘要
================================================================================
测试时间: $(date '+%Y-%m-%d %H:%M:%S')
测试级别: $TEST_LEVEL
目标主机: $API_HOST
================================================================================

测试文件:
EOF

    # 列出相关文件
    ls -lh "$RESULTS_DIR"/production_${TEST_LEVEL}_*${TIMESTAMP}* 2>/dev/null >> "$SUMMARY_FILE" || true
    ls -lh "$RESULTS_DIR"/monitor_${TEST_LEVEL}_${TIMESTAMP}* 2>/dev/null >> "$SUMMARY_FILE" || true

    cat >> "$SUMMARY_FILE" << EOF

================================================================================
查看详细报告:
  HTML报告: $(ls "$RESULTS_DIR"/production_${TEST_LEVEL}_*${TIMESTAMP}.html 2>/dev/null | head -1)
  CSV统计: $(ls "$RESULTS_DIR"/production_${TEST_LEVEL}_*${TIMESTAMP}_stats.csv 2>/dev/null | head -1)
  分析报告: $(ls "$RESULTS_DIR"/production_${TEST_LEVEL}_*${TIMESTAMP}_stats_analysis.json 2>/dev/null | head -1)
  监控日志: $(ls "$RESULTS_DIR"/monitor_${TEST_LEVEL}_${TIMESTAMP}.log 2>/dev/null | head -1)
================================================================================
EOF

    print_info "摘要已保存到: $SUMMARY_FILE"
    cat "$SUMMARY_FILE"
}

# 清理函数
cleanup() {
    print_info "清理资源..."

    # 如果监控进程还在运行，终止它
    if [ ! -z "$MONITOR_PID" ]; then
        kill $MONITOR_PID 2>/dev/null || true
    fi
}

# 主函数
main() {
    echo "================================================================================"
    echo "生产环境压力测试完整流程"
    echo "================================================================================"
    echo "测试级别: $TEST_LEVEL"
    echo "目标主机: $API_HOST"
    echo "时间戳: $TIMESTAMP"
    echo "================================================================================"
    echo

    # 设置清理陷阱
    trap cleanup EXIT INT TERM

    # 创建结果目录
    mkdir -p "$RESULTS_DIR"

    # 执行测试流程
    check_dependencies
    check_server
    start_monitoring
    run_stress_test
    wait_monitoring
    analyze_results
    generate_summary

    echo
    print_info "测试流程完成！"
    echo
}

# 显示帮助
show_help() {
    cat << EOF
使用方式: $0 [TEST_LEVEL] [API_HOST]

参数:
  TEST_LEVEL    测试级别 (light|medium|heavy|peak|endurance)
                默认: light
  API_HOST      API服务器地址
                默认: http://localhost:8000

示例:
  $0 light
  $0 medium http://localhost:8000
  $0 heavy http://staging.example.com

测试级别说明:
  light      - 100并发用户，10分钟
  medium     - 500并发用户，15分钟
  heavy      - 1000并发用户，20分钟
  peak       - 2000并发用户，15分钟
  endurance  - 200并发用户，60分钟
EOF
}

# 检查帮助参数
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# 运行主函数
main
