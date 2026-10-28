#!/usr/bin/env bash
# bench.nautilus.social nginx+TLS 上线脚本(部署窗批次④ · 2026-10-08)
# 前置:DNS A 记录已生效(43.160.239.61 实测);用户批甲部署窗五件之④
# 纪律:acme.sh 签发(禁 certbot);sites-enabled 禁留 .bak;nginx -t 过才 reload;结尾 curl 三验
set -euo pipefail

CONF=/etc/nginx/sites-available/bench.nautilus.social
WEBROOT=/var/www/bench

mkdir -p "$WEBROOT"
# 先放占位(nginx 通判据=非 000;v5 V2.2 随后挂指纹件)
echo 'bench placeholder — V2.2 pending v5 mount' > "$WEBROOT/index.html"

# ① 80 先行(acme http-01 验证 + 跳转预留)
cat > "$CONF" <<'EOF'
server {
    listen 80;
    server_name bench.nautilus.social;
    root /var/www/bench;
    index index.html;
    location /.well-known/acme-challenge/ { root /var/www/bench; }
    location / { try_files $uri $uri/ =404; }
}
EOF
ln -sf "$CONF" /etc/nginx/sites-enabled/bench.nautilus.social
nginx -t && systemctl reload nginx
echo "[1/4] http-80 up"

# ② 签证书(acme.sh webroot;失败则停,不带病续)
~/.acme.sh/acme.sh --issue -d bench.nautilus.social -w "$WEBROOT" --server letsencrypt
echo "[2/4] cert issued"

# ③ 443(证书装到 nginx 可读路径)
CERTDIR=/etc/nginx/ssl/bench
mkdir -p "$CERTDIR"
~/.acme.sh/acme.sh --install-cert -d bench.nautilus.social \
  --key-file "$CERTDIR/key.pem" --fullchain-file "$CERTDIR/full.pem" \
  --reloadcmd "systemctl reload nginx"
cat > "$CONF" <<'EOF'
server {
    listen 80;
    server_name bench.nautilus.social;
    location /.well-known/acme-challenge/ { root /var/www/bench; }
    location / { return 301 https://$host$request_uri; }
}
server {
    listen 443 ssl;
    server_name bench.nautilus.social;
    root /var/www/bench;
    index index.html;
    ssl_certificate     /etc/nginx/ssl/bench/full.pem;
    ssl_certificate_key /etc/nginx/ssl/bench/key.pem;
    location / { try_files $uri $uri/ =404; }
}
EOF
nginx -t && systemctl reload nginx
echo "[3/4] https-443 up"

# ④ 三验
sleep 8
echo "[4/4] probes:"
curl -s -o /dev/null -m 10 -w "http:  %{http_code}\n" http://bench.nautilus.social/
curl -s -o /dev/null -m 10 -w "https: %{http_code}\n" https://bench.nautilus.social/
echo "DONE — 通知 v5 挂 V2.2(附指纹流程 #10418)"
