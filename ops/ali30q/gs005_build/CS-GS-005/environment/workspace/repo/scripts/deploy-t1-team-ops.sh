#!/usr/bin/env bash
set -euo pipefail

: "${T1_TEAM_USERNAME:?set T1_TEAM_USERNAME}"
: "${T1_TEAM_PASSWORD:?set T1_TEAM_PASSWORD}"

SOURCE="docs/business/phase3_expert_operations/t1_team_operations_portal.html"
HOST="cloud"
REMOTE_ROOT="/var/www/fde.nautilus.social/t1-team"
NGINX_SITE="/etc/nginx/sites-enabled/fde.nautilus.social"
NGINX_SNIPPET="/etc/nginx/snippets/fde-t1-team-auth.conf"
HTPASSWD_FILE="/etc/nginx/.htpasswd-fde-t1-team"
URL="https://fde.nautilus.social/t1-team/"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=15)

fail() { echo "[t1-team][FAIL] $*" >&2; exit 1; }
[[ -f "$SOURCE" ]] || fail "missing source: $SOURCE"
command -v openssl >/dev/null || fail "openssl is required to hash the password"

local_sha=$(sha256sum "$SOURCE" | awk '{print $1}')
password_hash=$(openssl passwd -apr1 "$T1_TEAM_PASSWORD")
htpasswd_line="${T1_TEAM_USERNAME}:${password_hash}"

read -r -d '' snippet <<'EOF' || true
location = /t1-team {
    return 301 /t1-team/;
}
location ^~ /t1-team/ {
    auth_basic "Nautilus T1 Team";
    auth_basic_user_file /etc/nginx/.htpasswd-fde-t1-team;
    root /var/www/fde.nautilus.social;
    index index.html;
    try_files $uri $uri/ =404;
    add_header Cache-Control "no-store, private" always;
    add_header X-Robots-Tag "noindex, nofollow, noarchive" always;
}
EOF

snippet_b64=$(printf '%s' "$snippet" | base64 | tr -d '\r\n')
htpasswd_b64=$(printf '%s\n' "$htpasswd_line" | base64 | tr -d '\r\n')
remote_session="/tmp/t1_team_publish_$(date +%s)"

echo "[t1-team] upload session: $remote_session"
scp "${SSH_OPTS[@]}" "$SOURCE" "${HOST}:${remote_session}/index.html" 2>/dev/null || {
  ssh "${SSH_OPTS[@]}" "$HOST" "mkdir -p '$remote_session'"
  scp "${SSH_OPTS[@]}" "$SOURCE" "${HOST}:${remote_session}/index.html"
}

ssh "${SSH_OPTS[@]}" "$HOST" "set -e
  sudo install -d -m 755 /etc/nginx/snippets
  printf '%s' '$snippet_b64' | base64 -d | sudo tee '$NGINX_SNIPPET' >/dev/null
  printf '%s' '$htpasswd_b64' | base64 -d | sudo tee '$HTPASSWD_FILE' >/dev/null
  sudo chmod 640 '$HTPASSWD_FILE'
  if ! sudo grep -Fqx '    include /etc/nginx/snippets/fde-t1-team-auth.conf;' '$NGINX_SITE'; then
    sudo sed -i '0,/^[[:space:]]*location \/api\//i\    include /etc/nginx/snippets/fde-t1-team-auth.conf;' '$NGINX_SITE'
  fi
  sudo nginx -t
  sudo systemctl reload nginx
  sudo install -d -m 755 '$REMOTE_ROOT'
  sudo mv '$remote_session/index.html' '$REMOTE_ROOT/index.html'
  rmdir '$remote_session' || true
  remote_sha=\$(sudo sha256sum '$REMOTE_ROOT/index.html' | awk '{print \$1}')
  test \"\$remote_sha\" = '$local_sha'
"

anonymous_status=$(curl -sk -o /dev/null -w '%{http_code}' "$URL")
[[ "$anonymous_status" == "401" ]] || fail "anonymous request was not challenged: $anonymous_status"
authorized_html=$(curl -skf --user "$T1_TEAM_USERNAME:$T1_TEAM_PASSWORD" "$URL") || fail "authorized request failed"
grep -Fq "T1 团队运营门户" <<<"$authorized_html" || fail "protected portal marker missing"
grep -Fq "内部受控资料" <<<"$authorized_html" || fail "protected portal boundary missing"
echo "[t1-team] deployed and access control verified"
