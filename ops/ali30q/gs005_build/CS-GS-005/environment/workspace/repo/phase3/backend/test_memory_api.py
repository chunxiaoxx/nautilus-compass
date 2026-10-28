#!/usr/bin/env python3
import requests
import json

BASE_URL = 'http://localhost:8000'

print('=== 测试 Memory API 端点 ===\n')

# 测试端点列表
endpoints = [
    '/api/memory/memories',
    '/api/memory/memories/search',
    '/api/memory/memories/stats',
    '/api/memory/reflections',
    '/api/memory/skills'
]

for endpoint in endpoints:
    url = f'{BASE_URL}{endpoint}'
    try:
        response = requests.get(url, timeout=5)
        status = '✅' if response.status_code in [200, 401, 403] else '❌'
        print(f'{status} {endpoint}')
        print(f'   Status: {response.status_code}')
        print(f'   Response: {response.text[:100]}')
        print()
    except Exception as e:
        print(f'❌ {endpoint}')
        print(f'   Error: {e}')
        print()

print('=== 测试完成 ===')
