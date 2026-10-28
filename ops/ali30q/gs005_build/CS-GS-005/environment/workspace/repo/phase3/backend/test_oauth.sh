#!/bin/bash
# 快速测试脚本 - 验证 OAuth 端点

echo "=========================================="
echo "OAuth 端点测试"
echo "=========================================="
echo ""

echo "测试 1: GitHub OAuth (GET 请求)"
echo "----------------------------------------"
GITHUB_GET=$(curl -s -o /dev/null -w "%{http_code}" -X GET https://api.nautilus.social/api/auth/github/login)
echo "HTTP 状态码: $GITHUB_GET"
if [ "$GITHUB_GET" = "307" ]; then
    echo "✅ GitHub OAuth 正常 (307 重定向)"
    curl -s -I -X GET https://api.nautilus.social/api/auth/github/login | grep -i location
else
    echo "❌ GitHub OAuth 异常"
fi
echo ""

echo "测试 2: GitHub OAuth (HEAD 请求)"
echo "----------------------------------------"
GITHUB_HEAD=$(curl -s -o /dev/null -w "%{http_code}" -I https://api.nautilus.social/api/auth/github/login)
echo "HTTP 状态码: $GITHUB_HEAD"
if [ "$GITHUB_HEAD" = "405" ]; then
    echo "✅ 返回 405 是正常的 (HEAD 方法不支持)"
    echo "   说明: OAuth 端点只支持 GET 方法"
else
    echo "⚠️  预期返回 405，实际返回 $GITHUB_HEAD"
fi
echo ""

echo "测试 3: Google OAuth (GET 请求)"
echo "----------------------------------------"
GOOGLE_GET=$(curl -s -o /dev/null -w "%{http_code}" -X GET https://api.nautilus.social/api/auth/google/login)
echo "HTTP 状态码: $GOOGLE_GET"
if [ "$GOOGLE_GET" = "307" ]; then
    echo "✅ Google OAuth 已配置并正常工作"
    curl -s -I -X GET https://api.nautilus.social/api/auth/google/login | grep -i location
elif [ "$GOOGLE_GET" = "500" ]; then
    echo "⚠️  Google OAuth 端点存在但未配置凭证"
    echo "   需要配置: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET"
elif [ "$GOOGLE_GET" = "404" ]; then
    echo "❌ Google OAuth 端点不存在 (需要部署)"
else
    echo "❌ Google OAuth 异常 (HTTP $GOOGLE_GET)"
fi
echo ""

echo "测试 4: 常规登录端点"
echo "----------------------------------------"
LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://api.nautilus.social/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}')
echo "HTTP 状态码: $LOGIN_STATUS"
if [ "$LOGIN_STATUS" = "401" ]; then
    echo "✅ 登录端点正常 (401 表示凭证错误，端点可用)"
else
    echo "⚠️  登录端点返回: $LOGIN_STATUS"
fi
echo ""

echo "测试 5: 健康检查"
echo "----------------------------------------"
HEALTH=$(curl -s https://api.nautilus.social/health)
STATUS=$(echo "$HEALTH" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
echo "服务状态: $STATUS"
if [ "$STATUS" = "healthy" ] || [ "$STATUS" = "degraded" ]; then
    echo "✅ 服务运行正常"
else
    echo "❌ 服务异常"
fi
echo ""

echo "=========================================="
echo "测试总结"
echo "=========================================="
echo ""
echo "GitHub OAuth:"
echo "  • GET 请求: $GITHUB_GET (预期: 307)"
echo "  • HEAD 请求: $GITHUB_HEAD (预期: 405)"
echo ""
echo "Google OAuth:"
echo "  • GET 请求: $GOOGLE_GET (预期: 307 或 500)"
echo ""
echo "服务状态: $STATUS"
echo ""

if [ "$GITHUB_GET" = "307" ] && [ "$GITHUB_HEAD" = "405" ]; then
    echo "✅ GitHub OAuth 完全正常"
else
    echo "⚠️  GitHub OAuth 需要检查"
fi

if [ "$GOOGLE_GET" = "307" ]; then
    echo "✅ Google OAuth 已配置并正常工作"
elif [ "$GOOGLE_GET" = "500" ]; then
    echo "⚠️  Google OAuth 需要配置凭证"
elif [ "$GOOGLE_GET" = "404" ]; then
    echo "❌ Google OAuth 需要部署"
fi
echo ""
