#!/bin/bash
# Nexus Server Docker 部署脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# 检查Docker是否安装
check_docker() {
    print_info "检查Docker安装..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    print_info "Docker版本: $(docker --version)"
}

# 检查Docker Compose是否安装
check_docker_compose() {
    print_info "检查Docker Compose安装..."
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    print_info "Docker Compose版本: $(docker-compose --version)"
}

# 构建镜像
build_image() {
    print_info "构建Docker镜像..."
    docker-compose build --no-cache
    print_info "镜像构建完成"
}

# 启动服务
start_service() {
    print_info "启动Nexus服务..."
    docker-compose up -d
    print_info "服务启动完成"
}

# 检查服务状态
check_service() {
    print_info "检查服务状态..."
    sleep 5
    docker-compose ps

    print_info "检查健康状态..."
    for i in {1..30}; do
        if curl -f http://localhost:8001/health &> /dev/null; then
            print_info "服务健康检查通过"
            return 0
        fi
        echo -n "."
        sleep 1
    done

    print_error "服务健康检查失败"
    return 1
}

# 显示日志
show_logs() {
    print_info "显示服务日志..."
    docker-compose logs --tail=50
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    docker-compose down
    print_info "服务已停止"
}

# 清理资源
cleanup() {
    print_info "清理Docker资源..."
    docker-compose down -v
    docker system prune -f
    print_info "清理完成"
}

# 主菜单
show_menu() {
    echo ""
    echo "================================"
    echo "  Nexus Server Docker 部署工具"
    echo "================================"
    echo "1. 构建镜像"
    echo "2. 启动服务"
    echo "3. 停止服务"
    echo "4. 重启服务"
    echo "5. 查看日志"
    echo "6. 查看状态"
    echo "7. 健康检查"
    echo "8. 完整部署（构建+启动+检查）"
    echo "9. 清理资源"
    echo "0. 退出"
    echo "================================"
}

# 主函数
main() {
    check_docker
    check_docker_compose

    while true; do
        show_menu
        read -p "请选择操作 [0-9]: " choice

        case $choice in
            1)
                build_image
                ;;
            2)
                start_service
                ;;
            3)
                stop_service
                ;;
            4)
                stop_service
                start_service
                ;;
            5)
                show_logs
                ;;
            6)
                docker-compose ps
                ;;
            7)
                check_service
                ;;
            8)
                build_image
                start_service
                check_service
                ;;
            9)
                cleanup
                ;;
            0)
                print_info "退出部署工具"
                exit 0
                ;;
            *)
                print_error "无效选择，请重试"
                ;;
        esac

        echo ""
        read -p "按Enter继续..."
    done
}

# 如果有命令行参数，直接执行
if [ $# -gt 0 ]; then
    case $1 in
        build)
            build_image
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            stop_service
            start_service
            ;;
        logs)
            show_logs
            ;;
        status)
            docker-compose ps
            ;;
        health)
            check_service
            ;;
        deploy)
            build_image
            start_service
            check_service
            ;;
        cleanup)
            cleanup
            ;;
        *)
            echo "用法: $0 {build|start|stop|restart|logs|status|health|deploy|cleanup}"
            exit 1
            ;;
    esac
else
    main
fi
