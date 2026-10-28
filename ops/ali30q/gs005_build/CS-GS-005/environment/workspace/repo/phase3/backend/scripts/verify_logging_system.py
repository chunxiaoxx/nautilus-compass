#!/usr/bin/env python3
"""
日志系统验证脚本
验证所有日志组件是否正常工作
"""
import sys
import json
from pathlib import Path


def check_files():
    """检查所有必需文件是否存在"""
    print("="*60)
    print("检查文件...")
    print("="*60)

    required_files = [
        "utils/logging_config.py",
        "middleware/logging_middleware.py",
        "middleware/__init__.py",
        "scripts/analyze_logs.py",
        "scripts/logging_examples.py",
        "scripts/start_logging_stack.py",
        "scripts/test_logging_system.sh",
        "config/logging/promtail.yml",
        "config/logging/filebeat.yml",
        "config/logging/grafana-datasources.yml",
        "config/logging/docker-compose.logging.yml",
        "config/logging/.env.logging.example",
        "config/logging/README.md",
        "tests/test_logging_system.py",
        "LOGGING_GUIDE.md",
        "LOGGING_SYSTEM_SUMMARY.md"
    ]

    missing_files = []
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (缺失)")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n警告: {len(missing_files)} 个文件缺失")
        return False
    else:
        print(f"\n所有 {len(required_files)} 个文件都存在")
        return True


def test_logging_import():
    """测试日志模块导入"""
    print("\n" + "="*60)
    print("测试模块导入...")
    print("="*60)

    try:
        from utils.logging_config import (
            setup_structured_logging,
            get_logger,
            StructuredLogger,
            get_blockchain_logger
        )
        print("✓ utils.logging_config 导入成功")
    except Exception as e:
        print(f"✗ utils.logging_config 导入失败: {e}")
        return False

    try:
        from middleware.logging_middleware import (
            LoggingMiddleware,
            ErrorLoggingMiddleware,
            get_request_id,
            set_user_id
        )
        print("✓ middleware.logging_middleware 导入成功")
    except Exception as e:
        print(f"✗ middleware.logging_middleware 导入失败: {e}")
        return False

    return True


def test_logging_functionality():
    """测试日志功能"""
    print("\n" + "="*60)
    print("测试日志功能...")
    print("="*60)

    try:
        from utils.logging_config import setup_structured_logging, get_logger, StructuredLogger

        # 初始化日志系统
        setup_structured_logging(
            log_level="debug",
            service_name="test-service",
            environment="test",
            enable_console=False,
            enable_json_file=True,
            enable_text_file=True
        )
        print("✓ 日志系统初始化成功")

        # 测试基础日志
        logger = get_logger("test")
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        print("✓ 基础日志记录成功")

        # 测试结构化日志
        structured_logger = StructuredLogger(logger)
        structured_logger.info(
            "Structured log test",
            user_id="user123",
            action="test",
            count=42
        )
        print("✓ 结构化日志记录成功")

        # 测试异常日志
        try:
            raise ValueError("Test exception")
        except Exception:
            logger.exception("Exception test")
        print("✓ 异常日志记录成功")

        return True

    except Exception as e:
        print(f"✗ 日志功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_log_files():
    """验证日志文件"""
    print("\n" + "="*60)
    print("验证日志文件...")
    print("="*60)

    log_files = [
        "logs/nautilus.json.log",
        "logs/nautilus.log",
        "logs/nautilus.error.json.log"
    ]

    all_exist = True
    for log_file in log_files:
        path = Path(log_file)
        if path.exists():
            size = path.stat().st_size
            print(f"✓ {log_file} ({size} bytes)")

            # 验证JSON格式
            if log_file.endswith('.json.log'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                json.loads(line)
                    print(f"  └─ JSON格式验证通过")
                except json.JSONDecodeError as e:
                    print(f"  └─ JSON格式错误: {e}")
                    all_exist = False
        else:
            print(f"✗ {log_file} (不存在)")
            all_exist = False

    return all_exist


def verify_json_structure():
    """验证JSON日志结构"""
    print("\n" + "="*60)
    print("验证JSON日志结构...")
    print("="*60)

    json_log = Path("logs/nautilus.json.log")
    if not json_log.exists():
        print("✗ JSON日志文件不存在")
        return False

    required_fields = [
        "timestamp",
        "level",
        "logger",
        "message",
        "service",
        "environment",
        "hostname",
        "process",
        "thread",
        "source"
    ]

    try:
        with open(json_log, 'r', encoding='utf-8') as f:
            line = f.readline()
            if not line.strip():
                print("✗ 日志文件为空")
                return False

            log_entry = json.loads(line)

            missing_fields = []
            for field in required_fields:
                if field not in log_entry:
                    missing_fields.append(field)

            if missing_fields:
                print(f"✗ 缺少必需字段: {', '.join(missing_fields)}")
                return False

            print("✓ 所有必需字段都存在")
            print(f"  字段: {', '.join(required_fields)}")

            # 显示示例日志
            print("\n示例日志条目:")
            print(json.dumps(log_entry, indent=2, ensure_ascii=False)[:500] + "...")

            return True

    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False


def print_summary(results):
    """打印总结"""
    print("\n" + "="*60)
    print("验证总结")
    print("="*60)

    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {test_name}")

    print(f"\n总计: {passed}/{total} 通过")

    if failed == 0:
        print("\n🎉 所有验证通过！日志系统已成功完善。")
        return True
    else:
        print(f"\n⚠️  {failed} 个验证失败，请检查上述错误。")
        return False


def main():
    """主函数"""
    print("\n日志系统验证")
    print("="*60)

    results = {}

    # 运行所有验证
    results["文件检查"] = check_files()
    results["模块导入"] = test_logging_import()
    results["日志功能"] = test_logging_functionality()
    results["日志文件"] = verify_log_files()
    results["JSON结构"] = verify_json_structure()

    # 打印总结
    success = print_summary(results)

    # 清理测试日志
    print("\n清理测试日志...")
    import shutil
    if Path("logs").exists():
        try:
            shutil.rmtree("logs")
            print("✓ 测试日志已清理")
        except Exception as e:
            print(f"⚠️  清理失败: {e}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
