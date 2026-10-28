#!/usr/bin/env python3
"""
验证 API 文档完整性
"""
import os
import sys
from pathlib import Path

# 颜色输出
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"{GREEN}✓{RESET} {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {filepath} (不存在)")
        return False

def check_file_content(filepath, keywords, description):
    """检查文件内容是否包含关键词"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            missing = [kw for kw in keywords if kw not in content]
            if not missing:
                print(f"{GREEN}✓{RESET} {description}: 包含所有关键词")
                return True
            else:
                print(f"{YELLOW}⚠{RESET} {description}: 缺少关键词: {', '.join(missing)}")
                return False
    except Exception as e:
        print(f"{RED}✗{RESET} {description}: 读取失败 - {e}")
        return False

def main():
    """主函数"""
    print("🔍 验证 Nautilus API 文档完整性...\n")

    base_dir = Path(__file__).parent.parent
    docs_dir = base_dir / "docs"
    backend_dir = base_dir / "backend"

    results = []

    # 1. 检查文档文件
    print("📄 检查文档文件:")
    results.append(check_file_exists(docs_dir / "API_GUIDE.md", "API 使用指南"))
    results.append(check_file_exists(docs_dir / "README.md", "文档索引"))
    results.append(check_file_exists(docs_dir / "api-playground.html", "交互式 Playground"))
    results.append(check_file_exists(docs_dir / "API_QUICK_REFERENCE.md", "快速参考"))
    results.append(check_file_exists(backend_dir / "scripts" / "generate_openapi.py", "OpenAPI 生成脚本"))
    results.append(check_file_exists(base_dir / "scripts" / "deploy-api-docs.sh", "部署脚本"))
    print()

    # 2. 检查 API_GUIDE.md 内容
    print("📝 检查 API_GUIDE.md 内容:")
    api_guide = docs_dir / "API_GUIDE.md"
    if api_guide.exists():
        keywords = [
            "快速开始",
            "认证方式",
            "JWT Token",
            "API Key",
            "Python",
            "JavaScript",
            "cURL",
            "错误处理",
            "速率限制",
            "区块链集成"
        ]
        results.append(check_file_content(api_guide, keywords, "API 使用指南内容"))
    print()

    # 3. 检查 api-playground.html 内容
    print("🎨 检查 api-playground.html 内容:")
    playground = docs_dir / "api-playground.html"
    if playground.exists():
        keywords = [
            "swagger-ui",
            "SwaggerUIBundle",
            "openapi.json",
            "Nautilus API Playground"
        ]
        results.append(check_file_content(playground, keywords, "交互式 Playground 内容"))
    print()

    # 4. 检查 main.py 增强
    print("⚙️ 检查 main.py FastAPI 配置:")
    main_py = backend_dir / "main.py"
    if main_py.exists():
        keywords = [
            "Nautilus API",
            "功能特性",
            "认证方式",
            "快速开始",
            "contact",
            "license_info"
        ]
        results.append(check_file_content(main_py, keywords, "FastAPI 配置增强"))
    print()

    # 5. 检查 API 文件示例
    print("📋 检查 API 文件示例:")
    tasks_py = backend_dir / "api" / "tasks.py"
    if tasks_py.exists():
        keywords = ["json_schema_extra", "example"]
        results.append(check_file_content(tasks_py, keywords, "tasks.py 示例"))

    agents_py = backend_dir / "api" / "agents.py"
    if agents_py.exists():
        keywords = ["json_schema_extra", "example"]
        results.append(check_file_content(agents_py, keywords, "agents.py 示例"))
    print()

    # 6. 统计结果
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print("=" * 60)
    print(f"📊 验证结果: {passed}/{total} 通过")

    if failed == 0:
        print(f"{GREEN}✅ 所有检查通过！API 文档系统完整。{RESET}")
        return 0
    else:
        print(f"{YELLOW}⚠️  {failed} 项检查未通过，请检查上述输出。{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
