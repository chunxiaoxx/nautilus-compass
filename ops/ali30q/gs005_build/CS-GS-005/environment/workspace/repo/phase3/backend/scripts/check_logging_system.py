#!/usr/bin/env python3
"""
日志系统完整性检查
快速检查所有日志系统组件是否就绪
"""
import sys
from pathlib import Path


def main():
    print("\n" + "="*70)
    print("日志系统完整性检查")
    print("="*70 + "\n")

    # 检查文件清单
    files = {
        "核心组件": [
            "utils/logging_config.py",
            "middleware/logging_middleware.py",
            "middleware/__init__.py",
        ],
        "日志聚合配置": [
            "config/logging/promtail.yml",
            "config/logging/filebeat.yml",
            "config/logging/grafana-datasources.yml",
            "config/logging/docker-compose.logging.yml",
            "config/logging/.env.logging.example",
            "config/logging/README.md",
        ],
        "脚本和工具": [
            "scripts/analyze_logs.py",
            "scripts/logging_examples.py",
            "scripts/start_logging_stack.py",
            "scripts/test_logging_system.sh",
            "scripts/verify_logging_system.py",
        ],
        "测试和文档": [
            "tests/test_logging_system.py",
            "LOGGING_GUIDE.md",
            "LOGGING_SYSTEM_SUMMARY.md",
            "LOGGING_QUICK_REFERENCE.md",
        ]
    }

    total_files = 0
    found_files = 0
    missing_files = []

    for category, file_list in files.items():
        print(f"📁 {category}")
        for file_path in file_list:
            total_files += 1
            if Path(file_path).exists():
                print(f"   ✅ {file_path}")
                found_files += 1
            else:
                print(f"   ❌ {file_path}")
                missing_files.append(file_path)
        print()

    # 统计
    print("="*70)
    print(f"统计: {found_files}/{total_files} 文件存在")

    if missing_files:
        print(f"\n⚠️  缺失 {len(missing_files)} 个文件:")
        for f in missing_files:
            print(f"   - {f}")
        print("\n状态: ❌ 不完整")
        return 1
    else:
        print("\n状态: ✅ 完整")
        print("\n🎉 日志系统已成功完善！")
        print("\n下一步:")
        print("   1. 运行验证: python scripts/verify_logging_system.py")
        print("   2. 查看示例: python scripts/logging_examples.py")
        print("   3. 启动日志栈: python scripts/start_logging_stack.py start")
        print("   4. 分析日志: python scripts/analyze_logs.py")
        print("   5. 阅读文档: LOGGING_GUIDE.md")
        return 0


if __name__ == "__main__":
    sys.exit(main())
