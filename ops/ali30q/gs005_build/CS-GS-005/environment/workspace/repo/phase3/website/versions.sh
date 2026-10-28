#!/bin/bash

# Nautilus Website 版本管理脚本
# 使用方法: ./versions.sh [list|clean]

set -e

case "$1" in
  list|"")
    echo "📋 已保存的版本列表:"
    echo ""
    ssh cloud "ls -lth /var/www/nautilus/versions/ | grep backup"
    echo ""
    echo "💡 使用 ./rollback.sh <版本号> 回滚到指定版本"
    ;;

  clean)
    echo "🗑️  清理旧版本（保留最近5个）..."
    ssh cloud << EOF
      cd /var/www/nautilus/versions
      sudo ls -t | tail -n +6 | xargs -r sudo rm -rf
      echo "✅ 清理完成"
      echo "📋 剩余版本:"
      ls -lth
EOF
    ;;

  *)
    echo "使用方法:"
    echo "  ./versions.sh list   - 列出所有版本"
    echo "  ./versions.sh clean  - 清理旧版本（保留最近5个）"
    ;;
esac
