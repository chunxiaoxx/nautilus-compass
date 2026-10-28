#!/bin/bash

################################################################################
# SSL 证书自动配置脚本
#
# 功能:
# - 自动安装 Certbot
# - 获取 Let's Encrypt SSL 证书
# - 配置 Nginx
# - 设置自动续期
#
# 使用方法:
#   sudo ./setup_ssl.sh -d yourdomain.com -e admin@yourdomain.com
#
# 版本: 1.0.0
# 创建日期: 2026-02-27
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 显示使用说明
show_usage() {
    cat << EOF
使用方法: $0 [选项]

选项:
    -d, --domain DOMAIN         域名（必需，可多次使用）
    -e, --email EMAIL           邮箱地址（必需）
    -w, --webroot PATH          Webroot 路径（默认: /var/www/html）
    -m, --method METHOD         验证方法: nginx|standalone|webroot|dns（默认: nginx）
    -s, --staging               使用 Let's Encrypt 测试环境
    -r, --redirect              自动配置 HTTP 到 HTTPS 重定向
    -h, --help                  显示此帮助信息

示例:
    # 使用 Nginx 插件自动配置
    sudo $0 -d example.com -d www.example.com -e admin@example.com

    # 使用 Webroot 方法
    sudo $0 -d example.com -e admin@example.com -m webroot -w /var/www/html

    # 使用测试环境（不计入速率限制）
    sudo $0 -d example.com -e admin@example.com -s

    # 获取通配符证书（需要 DNS 验证）
    sudo $0 -d example.com -d "*.example.com" -e admin@example.com -m dns

EOF
    exit 1
}

# 检查是否以 root 权限运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本必须以 root 权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi

    log_info "检测到操作系统: $OS $OS_VERSION"
}

# 安装 Certbot
install_certbot() {
    log_info "开始安装 Certbot..."

    case $OS in
        ubuntu|debian)
            log_info "更新软件包列表..."
            apt-get update -qq

            log_info "安装 Certbot 和 Nginx 插件..."
            apt-get install -y certbot python3-certbot-nginx
            ;;

        centos|rhel|fedora)
            log_info "安装 EPEL 仓库..."
            yum install -y epel-release

            log_info "安装 Certbot 和 Nginx 插件..."
            yum install -y certbot python3-certbot-nginx
            ;;

        *)
            log_warning "未识别的操作系统，尝试使用 Snap 安装..."
            install_certbot_snap
            return
            ;;
    esac

    # 验证安装
    if command -v certbot &> /dev/null; then
        CERTBOT_VERSION=$(certbot --version 2>&1 | grep -oP '\d+\.\d+\.\d+' | head -1)
        log_success "Certbot 安装成功 (版本: $CERTBOT_VERSION)"
    else
        log_error "Certbot 安装失败"
        exit 1
    fi
}

# 使用 Snap 安装 Certbot
install_certbot_snap() {
    log_info "使用 Snap 安装 Certbot..."

    # 安装 Snap
    if ! command -v snap &> /dev/null; then
        case $OS in
            ubuntu|debian)
                apt-get install -y snapd
                ;;
            centos|rhel|fedora)
                yum install -y snapd
                systemctl enable --now snapd.socket
                ;;
        esac
    fi

    # 安装 Certbot
    snap install --classic certbot
    ln -sf /snap/bin/certbot /usr/bin/certbot

    log_success "Certbot 通过 Snap 安装成功"
}

# 检查 Nginx 是否安装
check_nginx() {
    if ! command -v nginx &> /dev/null; then
        log_error "未检测到 Nginx，请先安装 Nginx"
        log_info "Ubuntu/Debian: sudo apt-get install nginx"
        log_info "CentOS/RHEL: sudo yum install nginx"
        exit 1
    fi

    NGINX_VERSION=$(nginx -v 2>&1 | grep -oP '\d+\.\d+\.\d+')
    log_success "检测到 Nginx (版本: $NGINX_VERSION)"
}

# 检查域名解析
check_dns() {
    local domain=$1
    log_info "检查域名解析: $domain"

    # 获取域名 IP
    DOMAIN_IP=$(dig +short "$domain" A | tail -n1)

    if [[ -z "$DOMAIN_IP" ]]; then
        log_warning "域名 $domain 无法解析，请检查 DNS 配置"
        return 1
    fi

    # 获取服务器公网 IP
    SERVER_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || curl -s ipinfo.io/ip)

    if [[ "$DOMAIN_IP" == "$SERVER_IP" ]]; then
        log_success "域名解析正确: $domain -> $DOMAIN_IP"
        return 0
    else
        log_warning "域名解析不匹配: $domain -> $DOMAIN_IP (服务器 IP: $SERVER_IP)"
        log_warning "SSL 证书验证可能失败，建议等待 DNS 传播完成"
        return 1
    fi
}

# 检查端口是否开放
check_ports() {
    log_info "检查必需端口..."

    # 检查 80 端口
    if netstat -tuln | grep -q ':80 '; then
        log_success "端口 80 已开放"
    else
        log_warning "端口 80 未开放，可能影响证书验证"
    fi

    # 检查 443 端口
    if netstat -tuln | grep -q ':443 '; then
        log_success "端口 443 已开放"
    else
        log_warning "端口 443 未开放"
    fi
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙规则..."

    # UFW (Ubuntu/Debian)
    if command -v ufw &> /dev/null; then
        ufw allow 80/tcp comment 'HTTP for SSL verification'
        ufw allow 443/tcp comment 'HTTPS'
        log_success "UFW 防火墙规则已配置"
    fi

    # Firewalld (CentOS/RHEL)
    if command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        log_success "Firewalld 防火墙规则已配置"
    fi
}

# 获取 SSL 证书
obtain_certificate() {
    log_info "开始获取 SSL 证书..."

    # 构建域名参数
    local domain_args=""
    for domain in "${DOMAINS[@]}"; do
        domain_args="$domain_args -d $domain"
    done

    # 构建 Certbot 命令
    local certbot_cmd="certbot"

    # 选择验证方法
    case $METHOD in
        nginx)
            certbot_cmd="$certbot_cmd --nginx"
            ;;
        standalone)
            log_info "停止 Nginx 服务..."
            systemctl stop nginx
            certbot_cmd="$certbot_cmd certonly --standalone"
            ;;
        webroot)
            certbot_cmd="$certbot_cmd certonly --webroot -w $WEBROOT"
            ;;
        dns)
            certbot_cmd="$certbot_cmd certonly --manual --preferred-challenges dns"
            log_warning "DNS 验证需要手动添加 TXT 记录"
            ;;
    esac

    # 添加域名
    certbot_cmd="$certbot_cmd $domain_args"

    # 添加邮箱
    certbot_cmd="$certbot_cmd --email $EMAIL --agree-tos --no-eff-email"

    # 测试环境
    if [[ "$STAGING" == "true" ]]; then
        certbot_cmd="$certbot_cmd --staging"
        log_warning "使用 Let's Encrypt 测试环境"
    fi

    # HTTP 重定向
    if [[ "$REDIRECT" == "true" && "$METHOD" == "nginx" ]]; then
        certbot_cmd="$certbot_cmd --redirect"
    else
        certbot_cmd="$certbot_cmd --no-redirect"
    fi

    # 非交互模式
    certbot_cmd="$certbot_cmd --non-interactive"

    log_info "执行命令: $certbot_cmd"

    # 执行 Certbot
    if eval $certbot_cmd; then
        log_success "SSL 证书获取成功！"

        # 如果使用 standalone 模式，重启 Nginx
        if [[ "$METHOD" == "standalone" ]]; then
            log_info "启动 Nginx 服务..."
            systemctl start nginx
        fi

        return 0
    else
        log_error "SSL 证书获取失败"

        # 如果使用 standalone 模式，确保 Nginx 重启
        if [[ "$METHOD" == "standalone" ]]; then
            systemctl start nginx
        fi

        return 1
    fi
}

# 验证证书
verify_certificate() {
    local domain=${DOMAINS[0]}
    log_info "验证证书: $domain"

    # 检查证书文件
    local cert_path="/etc/letsencrypt/live/$domain"

    if [[ ! -d "$cert_path" ]]; then
        log_error "证书目录不存在: $cert_path"
        return 1
    fi

    # 检查证书文件
    local files=("fullchain.pem" "privkey.pem" "chain.pem" "cert.pem")
    for file in "${files[@]}"; do
        if [[ -f "$cert_path/$file" ]]; then
            log_success "证书文件存在: $file"
        else
            log_error "证书文件缺失: $file"
            return 1
        fi
    done

    # 显示证书信息
    log_info "证书信息:"
    certbot certificates -d "$domain"

    return 0
}

# 测试 Nginx 配置
test_nginx_config() {
    log_info "测试 Nginx 配置..."

    if nginx -t; then
        log_success "Nginx 配置测试通过"
        return 0
    else
        log_error "Nginx 配置测试失败"
        return 1
    fi
}

# 重载 Nginx
reload_nginx() {
    log_info "重载 Nginx 配置..."

    if systemctl reload nginx; then
        log_success "Nginx 重载成功"
        return 0
    else
        log_error "Nginx 重载失败"
        return 1
    fi
}

# 配置自动续期
setup_auto_renewal() {
    log_info "配置自动续期..."

    # 检查是否已有自动续期任务
    if systemctl list-timers | grep -q certbot; then
        log_success "Certbot 自动续期已配置（systemd timer）"
    elif [[ -f /etc/cron.d/certbot ]]; then
        log_success "Certbot 自动续期已配置（cron）"
    else
        log_info "创建自动续期 cron 任务..."

        # 创建续期脚本
        cat > /etc/cron.d/certbot << 'EOF'
# 每天凌晨 2:30 检查证书续期
30 2 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

        chmod 644 /etc/cron.d/certbot
        log_success "自动续期 cron 任务已创建"
    fi

    # 测试续期
    log_info "测试自动续期..."
    if certbot renew --dry-run; then
        log_success "自动续期测试通过"
    else
        log_warning "自动续期测试失败，请检查配置"
    fi
}

# 创建续期钩子
create_renewal_hooks() {
    log_info "创建续期钩子..."

    # 创建 post-hook 目录
    mkdir -p /etc/letsencrypt/renewal-hooks/post

    # 创建 Nginx 重载脚本
    cat > /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh << 'EOF'
#!/bin/bash
# 证书续期后重载 Nginx
systemctl reload nginx
EOF

    chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
    log_success "续期钩子已创建"
}

# 生成 DH 参数
generate_dhparam() {
    local dhparam_file="/etc/nginx/ssl/dhparam.pem"

    if [[ -f "$dhparam_file" ]]; then
        log_info "DH 参数文件已存在，跳过生成"
        return 0
    fi

    log_info "生成 DH 参数（这可能需要几分钟）..."
    mkdir -p /etc/nginx/ssl

    if openssl dhparam -out "$dhparam_file" 4096; then
        chmod 644 "$dhparam_file"
        log_success "DH 参数生成成功"
    else
        log_warning "DH 参数生成失败，将使用默认参数"
    fi
}

# 显示证书信息
show_certificate_info() {
    local domain=${DOMAINS[0]}

    echo ""
    log_success "=========================================="
    log_success "SSL 证书配置完成！"
    log_success "=========================================="
    echo ""
    log_info "证书位置:"
    log_info "  证书: /etc/letsencrypt/live/$domain/fullchain.pem"
    log_info "  私钥: /etc/letsencrypt/live/$domain/privkey.pem"
    log_info "  链: /etc/letsencrypt/live/$domain/chain.pem"
    echo ""
    log_info "证书有效期: 90 天"
    log_info "自动续期: 已配置（每天检查）"
    echo ""
    log_info "测试 HTTPS 访问:"
    for domain in "${DOMAINS[@]}"; do
        log_info "  https://$domain"
    done
    echo ""
    log_info "在线测试 SSL 配置:"
    log_info "  https://www.ssllabs.com/ssltest/analyze.html?d=${DOMAINS[0]}"
    echo ""
    log_info "手动续期命令:"
    log_info "  sudo certbot renew"
    echo ""
    log_info "查看证书信息:"
    log_info "  sudo certbot certificates"
    echo ""
}

# 主函数
main() {
    # 默认值
    DOMAINS=()
    EMAIL=""
    WEBROOT="/var/www/html"
    METHOD="nginx"
    STAGING="false"
    REDIRECT="false"

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--domain)
                DOMAINS+=("$2")
                shift 2
                ;;
            -e|--email)
                EMAIL="$2"
                shift 2
                ;;
            -w|--webroot)
                WEBROOT="$2"
                shift 2
                ;;
            -m|--method)
                METHOD="$2"
                shift 2
                ;;
            -s|--staging)
                STAGING="true"
                shift
                ;;
            -r|--redirect)
                REDIRECT="true"
                shift
                ;;
            -h|--help)
                show_usage
                ;;
            *)
                log_error "未知参数: $1"
                show_usage
                ;;
        esac
    done

    # 验证必需参数
    if [[ ${#DOMAINS[@]} -eq 0 ]]; then
        log_error "缺少域名参数"
        show_usage
    fi

    if [[ -z "$EMAIL" ]]; then
        log_error "缺少邮箱参数"
        show_usage
    fi

    # 显示配置信息
    echo ""
    log_info "=========================================="
    log_info "SSL 证书自动配置脚本"
    log_info "=========================================="
    log_info "域名: ${DOMAINS[*]}"
    log_info "邮箱: $EMAIL"
    log_info "验证方法: $METHOD"
    log_info "测试环境: $STAGING"
    log_info "HTTP 重定向: $REDIRECT"
    echo ""

    # 执行配置步骤
    check_root
    detect_os

    # 检查并安装 Certbot
    if ! command -v certbot &> /dev/null; then
        install_certbot
    else
        log_success "Certbot 已安装"
    fi

    # 检查 Nginx
    if [[ "$METHOD" == "nginx" || "$METHOD" == "webroot" ]]; then
        check_nginx
    fi

    # 检查域名解析
    for domain in "${DOMAINS[@]}"; do
        check_dns "$domain" || true
    done

    # 检查端口
    check_ports

    # 配置防火墙
    configure_firewall

    # 获取证书
    if obtain_certificate; then
        # 验证证书
        verify_certificate

        # 测试 Nginx 配置
        if [[ "$METHOD" == "nginx" ]]; then
            test_nginx_config && reload_nginx
        fi

        # 配置自动续期
        setup_auto_renewal

        # 创建续期钩子
        create_renewal_hooks

        # 生成 DH 参数
        generate_dhparam

        # 显示证书信息
        show_certificate_info

        exit 0
    else
        log_error "SSL 证书配置失败"
        exit 1
    fi
}

# 运行主函数
main "$@"
