#!/usr/bin/env python3
"""
Generate OpenAPI schema and SDK for Nautilus API.
"""
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from fastapi.openapi.utils import get_openapi


def generate_openapi_schema():
    """Generate OpenAPI schema from FastAPI app."""
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info
    )

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'openapi.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"✅ OpenAPI schema generated: {output_path}")
    return schema


def generate_sdk_instructions():
    """Generate SDK generation instructions."""
    instructions = """
# SDK 生成指南

## 安装 OpenAPI Generator

```bash
npm install @openapitools/openapi-generator-cli -g
```

## 生成 Python SDK

```bash
openapi-generator-cli generate \\
  -i docs/openapi.json \\
  -g python \\
  -o sdk/python \\
  --additional-properties=packageName=nautilus_sdk,projectName=nautilus-sdk
```

## 生成 JavaScript/TypeScript SDK

```bash
openapi-generator-cli generate \\
  -i docs/openapi.json \\
  -g typescript-axios \\
  -o sdk/typescript \\
  --additional-properties=npmName=@nautilus/sdk,supportsES6=true
```

## 生成 Go SDK

```bash
openapi-generator-cli generate \\
  -i docs/openapi.json \\
  -g go \\
  -o sdk/go \\
  --additional-properties=packageName=nautilus
```

## 生成 Java SDK

```bash
openapi-generator-cli generate \\
  -i docs/openapi.json \\
  -g java \\
  -o sdk/java \\
  --additional-properties=groupId=com.nautilus,artifactId=nautilus-sdk
```

## 使用生成的 SDK

### Python

```python
from nautilus_sdk import ApiClient, Configuration, TasksApi

# 配置
config = Configuration()
config.host = "https://api.nautilus.social"
config.access_token = "your_jwt_token"

# 创建客户端
client = ApiClient(config)
tasks_api = TasksApi(client)

# 发布任务
task = tasks_api.create_task({
    "description": "开发任务",
    "reward": 1000000000000000000,
    "task_type": "CODE",
    "timeout": 86400
})
print(f"任务已创建: {task.task_id}")
```

### TypeScript

```typescript
import { Configuration, TasksApi } from '@nautilus/sdk';

// 配置
const config = new Configuration({
  basePath: 'https://api.nautilus.social',
  accessToken: 'your_jwt_token'
});

// 创建客户端
const tasksApi = new TasksApi(config);

// 发布任务
const task = await tasksApi.createTask({
  description: '开发任务',
  reward: '1000000000000000000',
  task_type: 'CODE',
  timeout: 86400
});
console.log(`任务已创建: ${task.task_id}`);
```

## 自定义 SDK

如果需要自定义 SDK，可以修改 OpenAPI schema 或使用模板：

```bash
openapi-generator-cli generate \\
  -i docs/openapi.json \\
  -g python \\
  -o sdk/python \\
  -t templates/python
```
"""

    output_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'SDK_GENERATION.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(instructions)

    print(f"✅ SDK generation instructions: {output_path}")


if __name__ == "__main__":
    print("🚀 Generating OpenAPI schema and SDK instructions...")
    generate_openapi_schema()
    generate_sdk_instructions()
    print("✅ Done!")
