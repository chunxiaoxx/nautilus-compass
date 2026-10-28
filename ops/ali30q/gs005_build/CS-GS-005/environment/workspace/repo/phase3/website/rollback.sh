#!/bin/bash

# Nautilus Website 版本回滚脚本
# 使用方法: ./rollback.sh [版本号]
# 示例: ./rollback.sh backup_20260316_135530

set -e

if [ -z "$1" ]; then
  echo "❌ 请指定要回滚的版本号"
  echo "📋 可用版本列表:"
  ssh cloud "ls -lt /var/www/nautilus/versions/ | grep backup"
  echo ""
  echo "使用方法: ./rollback.sh backup_20260316_135530"
  exit 1
fi

VERSION=$1

echo "🔄 开始回滚到版本: $VERSION"

# 在服务器上执行回滚
ssh cloud << EOF
  set -e

  # 检查版本是否存在
  if [ ! -d /var/www/nautilus/versions/$VERSION ]; then
    echo "❌ 版本不存在: $VERSION"
    echo "📋 可用版本:"
    ls -lt /var/www/nautilus/versions/
    exit 1
  fi

  # 备份当前版本（以防回滚失败）
  ROLLBACK_BACKUP="rollback_backup_\$(date +%Y%m%d_%H%M%S)"
  echo "💾 备份当前版本为: \$ROLLBACK_BACKUP"
  sudo cp -r /var/www/nautilus/current /var/www/nautilus/versions/\$ROLLBACK_BACKUP

  # 清理当前目录
  echo "🧹 清理当前目录..."
  sudo rm -rf /var/www/nautilus/current/*

  # 恢复指定版本
  echo "📂 恢复版本: $VERSION"
  sudo cp -r /var/www/nautilus/versions/$VERSION/* /var/www/nautilus/current/

  # 设置权限
  echo "🔐 设置权限..."
  sudo chown -R www-data:www-data /var/www/nautilus/current/

  echo "✅ 回滚完成"
EOF

# 验证
echo "🔍 验证回滚..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://www.nautilus.social/)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ 回滚成功！当前版本: $VERSION"
  echo "🌐 网站: https://www.nautilus.social/"
else
  echo "❌ 回滚可能有问题，HTTP状态码: $HTTP_CODE"
  exit 1
fi

echo "🎉 回滚完成！"
