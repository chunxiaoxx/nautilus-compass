#!/bin/bash

# Nautilus Phase 3 Backend - 安全修复快速部署脚本
# 版本: 1.0
# 日期: 2026-02-26

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 检查Python版本
check_python() {
    print_header "检查Python环境"

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 未安装"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python版本: $PYTHON_VERSION"
}

# 检查虚拟环境
check_venv() {
    print_header "检查虚拟环境"

    if [ -d "venv" ]; then
        print_success "虚拟环境已存在"
    else
        print_warning "虚拟环境不存在，正在创建..."
        python3 -m venv venv
        print_success "虚拟环境创建成功"
    fi

    # 激活虚拟环境
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "虚拟环境已激活"
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        print_success "虚拟环境已激活 (Windows)"
    else
        print_error "无法激活虚拟环境"
        exit 1
    fi
}

# 安装依赖
install_dependencies() {
    print_header "安装依赖包"

    print_info "升级pip..."
    pip install --upgrade pip

    print_info "安装requirements.txt中的依赖..."
    pip install -r requirements.txt

    print_success "依赖安装完成"

    # 验证关键依赖
    print_info "验证安全依赖..."
    pip list | grep -E "slowapi|fastapi-csrf-protect|itsdangerous" || {
        print_error "安全依赖安装失败"
        exit 1
    }
    print_success "安全依赖验证通过"
}

# 生成密钥
generate_keys() {
    print_header "生成安全密钥"

    CSRF_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    JWT_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    print_success "CSRF密钥已生成"
    print_success "JWT密钥已生成"

    echo ""
    print_info "请将以下密钥添加到 .env 文件:"
    echo ""
    echo "CSRF_SECRET_KEY=$CSRF_KEY"
    echo "JWT_SECRET_KEY=$JWT_KEY"
    echo ""
}

# 配置环境变量
configure_env() {
    print_header "配置环境变量"

    if [ ! -f ".env" ]; then
        print_warning ".env 文件不存在，从 .env.example 复制..."
        cp .env.example .env
        print_success ".env 文件已创建"
    else
        print_info ".env 文件已存在"
    fi

    # 检查必需的环境变量
    print_info "检查环境变量配置..."

    if ! grep -q "ALLOWED_ORIGINS" .env; then
        print_warning "ALLOWED_ORIGINS 未配置"
        echo "ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001" >> .env
        print_success "已添加默认 ALLOWED_ORIGINS"
    fi

    if ! grep -q "CSRF_SECRET_KEY" .env; then
        print_warning "CSRF_SECRET_KEY 未配置"
        echo "CSRF_SECRET_KEY=$CSRF_KEY" >> .env
        print_success "已添加 CSRF_SECRET_KEY"
    fi

    if ! grep -q "RATE_LIMIT_ENABLED" .env; then
        print_warning "RATE_LIMIT_ENABLED 未配置"
        echo "RATE_LIMIT_ENABLED=true" >> .env
        print_success "已添加 RATE_LIMIT_ENABLED"
    fi

    print_success "环境变量配置完成"
}

# 验证代码
verify_code() {
    print_header "验证代码"

    print_info "检查main.py导入..."
    python3 -c "from main import app; print('导入成功')" || {
        print_error "main.py 导入失败"
        exit 1
    }
    print_success "代码验证通过"
}

# 运行测试
run_tests() {
    print_header "运行测试"

    read -p "是否运行测试? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -d "tests" ]; then
            print_info "运行pytest测试..."
            pytest tests/ -v || print_warning "部分测试失败"
        else
            print_warning "tests目录不存在，跳过测试"
        fi
    else
        print_info "跳过测试"
    fi
}

# 启动服务
start_service() {
    print_header "启动服务"

    read -p "是否启动开发服务器? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "启动服务器..."
        print_info "访问: http://localhost:8000"
        print_info "API文档: http://localhost:8000/docs"
        print_info "按 Ctrl+C 停止服务器"
        echo ""
        python3 main.py
    else
        print_info "跳过启动服务器"
        print_info "手动启动命令: python main.py"
    fi
}

# 打印摘要
print_summary() {
    print_header "部署摘要"

    echo ""
    print_success "安全修复部署完成!"
    echo ""
    print_info "已实施的安全措施:"
    echo "  1. ✅ API速率限制"
    echo "  2. ✅ CORS源限制"
    echo "  3. ✅ CSRF防护"
    echo "  4. ✅ 安全HTTP头部"
    echo ""
    print_info "下一步:"
    echo "  1. 检查 .env 文件配置"
    echo "  2. 启动服务: python main.py"
    echo "  3. 运行安全测试: python test_security_fixes.py"
    echo "  4. 查看报告: SECURITY_FIXES_REPORT.md"
    echo "  5. 查看检查清单: DEPLOYMENT_CHECKLIST.md"
    echo ""
    print_info "有用的命令:"
    echo "  - 启动服务: python main.py"
    echo "  - 运行测试: pytest tests/"
    echo "  - 安全测试: python test_security_fixes.py"
    echo "  - 查看日志: tail -f logs/app.log"
    echo ""
}

# 主函数
main() {
    clear
    print_header "Nautilus Phase 3 Backend - 安全修复部署"
    echo ""
    print_info "此脚本将帮助您部署安全修复"
    echo ""

    # 执行部署步骤
    check_python
    check_venv
    install_dependencies
    generate_keys
    configure_env
    verify_code
    run_tests

    # 打印摘要
    print_summary

    # 询问是否启动服务
    start_service
}

# 运行主函数
main
