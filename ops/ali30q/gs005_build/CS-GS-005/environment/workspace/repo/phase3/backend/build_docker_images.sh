#!/bin/bash

# ============================================
# Docker镜像构建和管理脚本
# ============================================
# 功能：
# - 自动化构建多个Docker镜像
# - 版本标签管理
# - 镜像推送到仓库
# - 清理旧镜像
# - 构建缓存优化
# ============================================

set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时报错

# ============================================
# 配置变量
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="nautilus-backend"
REGISTRY="${DOCKER_REGISTRY:-docker.io}"
NAMESPACE="${DOCKER_NAMESPACE:-nautilus}"
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
VERSION="${VERSION:-latest}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# 辅助函数
# ============================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_separator() {
    echo "============================================"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "命令 '$1' 未找到，请先安装"
        exit 1
    fi
}

# 获取镜像大小
get_image_size() {
    docker images --format "{{.Size}}" "$1" 2>/dev/null || echo "unknown"
}

# 清理旧镜像
cleanup_old_images() {
    local image_name=$1
    local keep_count=${2:-3}

    log_info "清理旧镜像，保留最新 ${keep_count} 个版本..."

    # 获取所有镜像ID（按创建时间排序）
    local images=$(docker images "${image_name}" --format "{{.ID}}" | tail -n +$((keep_count + 1)))

    if [ -z "$images" ]; then
        log_info "没有需要清理的旧镜像"
        return
    fi

    for image_id in $images; do
        log_info "删除镜像: ${image_id}"
        docker rmi "$image_id" 2>/dev/null || log_warning "无法删除镜像 ${image_id}"
    done

    log_success "旧镜像清理完成"
}

# 构建镜像
build_image() {
    local dockerfile=$1
    local tag=$2
    local build_args=${3:-}

    log_info "开始构建镜像: ${tag}"
    log_info "使用 Dockerfile: ${dockerfile}"

    local start_time=$(date +%s)

    # 构建命令
    local build_cmd="docker build"
    build_cmd+=" --file ${dockerfile}"
    build_cmd+=" --tag ${tag}"
    build_cmd+=" --build-arg BUILD_DATE=${BUILD_DATE}"
    build_cmd+=" --build-arg VCS_REF=${VCS_REF}"
    build_cmd+=" --build-arg VERSION=${VERSION}"

    # 添加额外的构建参数
    if [ -n "$build_args" ]; then
        build_cmd+=" ${build_args}"
    fi

    # 启用BuildKit
    export DOCKER_BUILDKIT=1

    build_cmd+=" ."

    log_info "执行命令: ${build_cmd}"

    if eval "$build_cmd"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local image_size=$(get_image_size "${tag}")

        log_success "镜像构建成功！"
        log_info "构建时间: ${duration}秒"
        log_info "镜像大小: ${image_size}"

        return 0
    else
        log_error "镜像构建失败"
        return 1
    fi
}

# 标记镜像
tag_image() {
    local source_tag=$1
    local target_tag=$2

    log_info "标记镜像: ${source_tag} -> ${target_tag}"

    if docker tag "$source_tag" "$target_tag"; then
        log_success "镜像标记成功"
        return 0
    else
        log_error "镜像标记失败"
        return 1
    fi
}

# 推送镜像
push_image() {
    local tag=$1

    log_info "推送镜像到仓库: ${tag}"

    if docker push "$tag"; then
        log_success "镜像推送成功"
        return 0
    else
        log_error "镜像推送失败"
        return 1
    fi
}

# 测试镜像
test_image() {
    local tag=$1

    log_info "测试镜像: ${tag}"

    # 运行容器进行基本测试
    local container_id=$(docker run -d --rm -p 8001:8000 "$tag")

    if [ -z "$container_id" ]; then
        log_error "无法启动容器"
        return 1
    fi

    log_info "容器已启动: ${container_id}"

    # 等待容器启动
    sleep 10

    # 检查健康状态
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_id" 2>/dev/null || echo "none")

    if [ "$health_status" = "healthy" ] || [ "$health_status" = "none" ]; then
        log_success "镜像测试通过"
        docker stop "$container_id" > /dev/null
        return 0
    else
        log_error "镜像测试失败，健康状态: ${health_status}"
        docker logs "$container_id"
        docker stop "$container_id" > /dev/null
        return 1
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
Docker镜像构建和管理脚本

用法: $0 [选项]

选项:
    -h, --help              显示帮助信息
    -b, --build TYPE        构建指定类型的镜像 (optimized|production|all)
    -t, --tag TAG           指定镜像标签 (默认: latest)
    -p, --push              构建后推送到仓库
    -c, --cleanup           清理旧镜像
    -n, --no-cache          不使用缓存构建
    --test                  构建后测试镜像
    --registry REGISTRY     指定镜像仓库 (默认: docker.io)
    --namespace NAMESPACE   指定命名空间 (默认: nautilus)

示例:
    # 构建优化版本镜像
    $0 --build optimized

    # 构建生产版本并推送
    $0 --build production --tag v1.0.0 --push

    # 构建所有镜像并测试
    $0 --build all --test

    # 清理旧镜像
    $0 --cleanup

EOF
}

# ============================================
# 主函数
# ============================================

main() {
    # 检查必要的命令
    check_command docker
    check_command git

    # 解析命令行参数
    local build_type=""
    local should_push=false
    local should_cleanup=false
    local should_test=false
    local no_cache=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -b|--build)
                build_type="$2"
                shift 2
                ;;
            -t|--tag)
                VERSION="$2"
                shift 2
                ;;
            -p|--push)
                should_push=true
                shift
                ;;
            -c|--cleanup)
                should_cleanup=true
                shift
                ;;
            -n|--no-cache)
                no_cache="--no-cache"
                shift
                ;;
            --test)
                should_test=true
                shift
                ;;
            --registry)
                REGISTRY="$2"
                shift 2
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 切换到项目目录
    cd "$SCRIPT_DIR"

    print_separator
    log_info "Docker镜像构建脚本"
    log_info "项目: ${PROJECT_NAME}"
    log_info "版本: ${VERSION}"
    log_info "VCS引用: ${VCS_REF}"
    log_info "构建日期: ${BUILD_DATE}"
    print_separator

    # 构建镜像
    if [ -n "$build_type" ]; then
        case $build_type in
            optimized)
                local image_tag="${REGISTRY}/${NAMESPACE}/${PROJECT_NAME}:${VERSION}-optimized"
                build_image "Dockerfile.optimized" "$image_tag" "$no_cache" || exit 1

                if [ "$should_test" = true ]; then
                    test_image "$image_tag" || exit 1
                fi

                if [ "$should_push" = true ]; then
                    push_image "$image_tag" || exit 1
                fi
                ;;

            production)
                local image_tag="${REGISTRY}/${NAMESPACE}/${PROJECT_NAME}:${VERSION}"
                build_image "Dockerfile.production" "$image_tag" "$no_cache" || exit 1

                # 同时标记为production
                tag_image "$image_tag" "${REGISTRY}/${NAMESPACE}/${PROJECT_NAME}:${VERSION}-production"

                if [ "$should_test" = true ]; then
                    test_image "$image_tag" || exit 1
                fi

                if [ "$should_push" = true ]; then
                    push_image "$image_tag" || exit 1
                    push_image "${REGISTRY}/${NAMESPACE}/${PROJECT_NAME}:${VERSION}-production" || exit 1
                fi
                ;;

            all)
                # 构建优化版本
                local optimized_tag="${REGISTRY}/${NAMESPACE}/${PROJECT_NAME}:${VERSION}-optimized"
                build_image "Dockerfile.optimized" "$optimized_tag" "$no_cache" || exit 1

                # 构建生产版本
                local production_tag="${REGISTRY}/${NAMESPACE}/${PROJECT_NAME}:${VERSION}"
                build_image "Dockerfile.production" "$production_tag" "$no_cache" || exit 1

                if [ "$should_test" = true ]; then
                    test_image "$optimized_tag" || exit 1
                    test_image "$production_tag" || exit 1
                fi

                if [ "$should_push" = true ]; then
                    push_image "$optimized_tag" || exit 1
                    push_image "$production_tag" || exit 1
                fi
                ;;

            *)
                log_error "未知的构建类型: ${build_type}"
                log_info "支持的类型: optimized, production, all"
                exit 1
                ;;
        esac
    fi

    # 清理旧镜像
    if [ "$should_cleanup" = true ]; then
        print_separator
        cleanup_old_images "${REGISTRY}/${NAMESPACE}/${PROJECT_NAME}" 3

        # 清理悬空镜像
        log_info "清理悬空镜像..."
        docker image prune -f
    fi

    print_separator
    log_success "所有操作完成！"

    # 显示镜像列表
    log_info "当前镜像列表:"
    docker images "${REGISTRY}/${NAMESPACE}/${PROJECT_NAME}"
}

# 执行主函数
main "$@"
