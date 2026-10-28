#!/bin/bash

# Nautilus Website 部署脚本 - 带版本管理
# 使用方法: ./deploy.sh

set -e

echo "🚀 开始部署 Nautilus Website..."

# 1. 构建
echo "📦 构建项目..."
npm run build

# 2. 创建版本标识
VERSION=$(date +%Y%m%d_%H%M%S)
echo "📌 版本号: $VERSION"

# 3. 打包
echo "📦 打包文件..."
tar -czf dist.tar.gz -C dist .

# 4. 上传到服务器
echo "⬆️  上传到服务器..."
scp dist.tar.gz cloud:/tmp/

# 5. 在服务器上部署
echo "🔄 服务器端部署..."
ssh cloud << EOF
  set -e

  # 备份当前版本
  if [ -d /var/www/nautilus/current ]; then
    echo "💾 备份当前版本..."
    sudo mkdir -p /var/www/nautilus/versions
    sudo cp -r /var/www/nautilus/current /var/www/nautilus/versions/backup_$VERSION
    echo "✅ 备份完成: /var/www/nautilus/versions/backup_$VERSION"
  fi

  # 清理当前目录
  echo "🧹 清理当前目录..."
  sudo rm -rf /var/www/nautilus/current/*

  # 解压新版本
  echo "📂 解压新版本..."
  cd /tmp
  sudo tar -xzf dist.tar.gz -C /var/www/nautilus/current/

  # 设置权限
  echo "🔐 设置权限..."
  sudo chown -R www-data:www-data /var/www/nautilus/current/

  # 清理临时文件
  rm dist.tar.gz

  # 只保留最近5个版本
  echo "🗑️  清理旧版本..."
  cd /var/www/nautilus/versions
  sudo ls -t | tail -n +6 | xargs -r sudo rm -rf

  echo "✅ 服务器端部署完成"
EOF

# 6. 验证部署
echo "🔍 验证部署..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://www.nautilus.social/)
DOC_PAGE=$(curl -s -o /dev/null -w "%{http_code}" https://www.nautilus.social/docs/fde-phase3)
if [ "$HTTP_CODE" = "200" ] && [ "$DOC_PAGE" = "200" ]; then
  echo "✅ 部署成功！版本: $VERSION"
  echo "🌐 网站: https://www.nautilus.social/"
  echo "📘 三期文档页面: https://www.nautilus.social/docs/fde-phase3"
  if [ -n "${FDE_HOST:-}" ]; then
    FDE_DOC_PAGE=$(curl -s -o /dev/null -w "%{http_code}" ${FDE_HOST}/docs/fde-phase3)
    echo "🧪 fde 子域: ${FDE_HOST}/docs/fde-phase3 (${FDE_DOC_PAGE})"
  fi
  echo "💾 备份位置: /var/www/nautilus/versions/backup_$VERSION"
else
  echo "❌ 部署可能有问题，首页代码: $HTTP_CODE，三期页代码: $DOC_PAGE"
  exit 1
fi
# 7. 清理本地临时文件
rm dist.tar.gz

echo "🎉 部署完成！"

