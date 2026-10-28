#!/bin/bash
# 云DB直查通道(2026-10-27·SSH隧道故障期间的替代,验证可用)
# 用法: ./psql_cloud.sh "SQL语句" —— 经 ssh 在云内直连 PG(127.0.0.1:5432)
# 注意:云侧 psql 走云内 PATH;引号内勿用双引号嵌套(用单引号包SQL)
exec ssh -p 24860 -o ConnectTimeout=10 -o BatchMode=yes ubuntu@43.160.239.61 \
  "psql 'postgresql://nautilus_user:nautilus2024@127.0.0.1:5432/nautilus_production' -c \"$1\""
