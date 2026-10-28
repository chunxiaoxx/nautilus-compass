#!/bin/bash

# Locust压力测试快速启动脚本
# 用于快速运行不同的负载测试场景

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Locust是否安装
check_locust() {
    if ! command -v locust &> /dev/null; then
        print_error "Locust未安装"
        print_info "请运行: pip install locust"
        exit 1
    fi
    print_success "Locust已安装: $(locust --version)"
}

# 检查后端服务是否运行
check_backend() {
    local host=$1
    print_info "检查后端服务: $host"

    if curl -s -f "$host/health" > /dev/null 2>&1; then
        print_success "后端服务正常运行"
        return 0
    else
        print_warning "无法连接到后端服务: $host"
        print_info "请确保后端服务正在运行"
        read -p "是否继续? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 显示使用说明
show_usage() {
    echo "用法: $0 [scenario] [options]"
    echo ""
    echo "场景:"
    echo "  light      - 轻负载测试 (10用户, 5分钟)"
    echo "  medium     - 中负载测试 (50用户, 10分钟)"
    echo "  heavy      - 重负载测试 (100用户, 15分钟)"
    echo "  peak       - 峰值负载测试 (200用户, 10分钟)"
    echo "  stress     - 压力测试 (500用户, 20分钟)"
    echo "  spike      - 尖峰测试 (300用户, 5分钟)"
    echo "  endurance  - 耐久测试 (30用户, 60分钟)"
    echo "  custom     - 自定义测试"
    echo ""
    echo "选项:"
    echo "  --host URL        - 目标主机 (默认: http://localhost:8000)"
    echo "  --web             - 使用Web界面模式"
    echo "  --no-report       - 不生成HTML报告"
    echo "  --help            - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 light"
    echo "  $0 medium --host http://staging.example.com"
    echo "  $0 heavy --web"
}

# 运行测试
run_test() {
    local scenario=$1
    local host=$2
    local web_mode=$3
    local generate_report=$4

    local users spawn_rate run_time

    # 根据场景设置参数
    case $scenario in
        light)
            users=10
            spawn_rate=2
            run_time="5m"
            ;;
        medium)
            users=50
            spawn_rate=5
            run_time="10m"
            ;;
        heavy)
            users=100
            spawn_rate=10
            run_time="15m"
            ;;
        peak)
            users=200
            spawn_rate=20
            run_time="10m"
            ;;
        stress)
            users=500
            spawn_rate=50
            run_time="20m"
            ;;
        spike)
            users=300
            spawn_rate=100
            run_time="5m"
            ;;
        endurance)
            users=30
            spawn_rate=3
            run_time="60m"
            ;;
        custom)
            read -p "并发用户数: " users
            read -p "启动速率 (用户/秒): " spawn_rate
            read -p "运行时间 (如: 10m, 1h): " run_time
            ;;
        *)
            print_error "未知场景: $scenario"
            show_usage
            exit 1
            ;;
    esac

    # 显示测试信息
    echo ""
    print_info "=========================================="
    print_info "场景: $scenario"
    print_info "目标主机: $host"
    print_info "并发用户数: $users"
    print_info "启动速率: $spawn_rate 用户/秒"
    print_info "运行时间: $run_time"
    print_info "=========================================="
    echo ""

    # 构建命令
    local cmd="locust -f locustfile.py --host=$host"

    if [ "$web_mode" = true ]; then
        # Web界面模式
        print_info "启动Web界面模式..."
        print_info "请访问: http://localhost:8089"
        $cmd
    else
        # 无头模式
        cmd="$cmd --users $users --spawn-rate $spawn_rate --run-time $run_time --headless"

        # 生成报告
        if [ "$generate_report" = true ]; then
            local timestamp=$(date +%Y%m%d_%H%M%S)
            local report_name="load_test_${scenario}_${timestamp}"
            cmd="$cmd --csv results/${report_name} --html results/${report_name}.html"

            # 创建results目录
            mkdir -p results

            print_info "报告将保存到: results/${report_name}.html"
        fi

        print_info "运行命令: $cmd"
        echo ""

        # 运行测试
        if eval $cmd; then
            print_success "测试完成！"
            if [ "$generate_report" = true ]; then
                print_success "报告已保存: results/${report_name}.html"
            fi
        else
            print_error "测试失败"
            exit 1
        fi
    fi
}

# 主函数
main() {
    # 默认参数
    local scenario=""
    local host="http://localhost:8000"
    local web_mode=false
    local generate_report=true

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --host)
                host="$2"
                shift 2
                ;;
            --web)
                web_mode=true
                shift
                ;;
            --no-report)
                generate_report=false
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                if [ -z "$scenario" ]; then
                    scenario="$1"
                else
                    print_error "未知参数: $1"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # 检查场景参数
    if [ -z "$scenario" ]; then
        print_error "请指定测试场景"
        show_usage
        exit 1
    fi

    # 检查依赖
    check_locust

    # 检查后端服务
    check_backend "$host"

    # 运行测试
    run_test "$scenario" "$host" "$web_mode" "$generate_report"
}

# 执行主函数
main "$@"
