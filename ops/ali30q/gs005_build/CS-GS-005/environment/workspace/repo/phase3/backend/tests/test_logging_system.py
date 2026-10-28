"""
日志系统单元测试
"""
import unittest
import json
import logging
import tempfile
import shutil
from pathlib import Path
from utils.logging_config import (
    setup_structured_logging,
    get_logger,
    StructuredLogger,
    StructuredFormatter
)


class TestStructuredLogging(unittest.TestCase):
    """结构化日志测试"""

    def setUp(self):
        """测试前设置"""
        # 创建临时日志目录
        self.temp_dir = tempfile.mkdtemp()
        self.original_log_dir = Path("logs")

        # 临时替换日志目录
        import utils.logging_config as logging_config
        logging_config.LOG_DIR = Path(self.temp_dir)

        # 初始化日志系统
        setup_structured_logging(
            log_level="debug",
            service_name="test-service",
            environment="test",
            enable_console=False,
            enable_json_file=True,
            enable_text_file=True
        )

        self.logger = get_logger("test")
        self.structured_logger = StructuredLogger(self.logger)

    def tearDown(self):
        """测试后清理"""
        # 清理日志处理器
        logging.getLogger().handlers.clear()

        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_json_log_format(self):
        """测试JSON日志格式"""
        self.logger.info("Test message")

        # 读取JSON日志文件
        json_log_file = Path(self.temp_dir) / "nautilus.json.log"
        self.assertTrue(json_log_file.exists(), "JSON日志文件应该存在")

        with open(json_log_file, 'r') as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)

            # 验证必需字段
            self.assertIn("timestamp", log_entry)
            self.assertIn("level", log_entry)
            self.assertIn("logger", log_entry)
            self.assertIn("message", log_entry)
            self.assertIn("service", log_entry)
            self.assertIn("environment", log_entry)

            # 验证值
            self.assertEqual(log_entry["level"], "INFO")
            self.assertEqual(log_entry["message"], "Test message")
            self.assertEqual(log_entry["service"], "test-service")
            self.assertEqual(log_entry["environment"], "test")

    def test_structured_logger(self):
        """测试结构化日志记录器"""
        self.structured_logger.info(
            "Structured message",
            user_id="user123",
            action="test"
        )

        # 读取JSON日志
        json_log_file = Path(self.temp_dir) / "nautilus.json.log"
        with open(json_log_file, 'r') as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)

            # 验证自定义字段
            self.assertIn("extra", log_entry)
            self.assertEqual(log_entry["extra"]["user_id"], "user123")
            self.assertEqual(log_entry["extra"]["action"], "test")

    def test_exception_logging(self):
        """测试异常日志"""
        try:
            raise ValueError("Test exception")
        except Exception:
            self.logger.exception("Exception occurred")

        # 读取错误日志
        error_log_file = Path(self.temp_dir) / "nautilus.error.json.log"
        self.assertTrue(error_log_file.exists(), "错误日志文件应该存在")

        with open(error_log_file, 'r') as f:
            log_line = f.readline()
            log_entry = json.loads(log_line)

            # 验证异常信息
            self.assertIn("exception", log_entry)
            self.assertEqual(log_entry["exception"]["type"], "ValueError")
            self.assertIn("Test exception", log_entry["exception"]["message"])
            self.assertIn("stacktrace", log_entry["exception"])

    def test_log_levels(self):
        """测试不同日志级别"""
        levels = ["debug", "info", "warning", "error", "critical"]

        for level in levels:
            method = getattr(self.logger, level)
            method(f"Test {level} message")

        # 验证所有级别都被记录
        json_log_file = Path(self.temp_dir) / "nautilus.json.log"
        with open(json_log_file, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 5, "应该有5条日志记录")

            for i, level in enumerate(levels):
                log_entry = json.loads(lines[i])
                self.assertEqual(log_entry["level"], level.upper())

    def test_text_log_format(self):
        """测试文本日志格式"""
        self.logger.info("Text log test")

        # 验证文本日志文件
        text_log_file = Path(self.temp_dir) / "nautilus.log"
        self.assertTrue(text_log_file.exists(), "文本日志文件应该存在")

        with open(text_log_file, 'r') as f:
            log_line = f.readline()
            self.assertIn("INFO", log_line)
            self.assertIn("Text log test", log_line)


class TestStructuredFormatter(unittest.TestCase):
    """结构化格式化器测试"""

    def test_formatter_basic(self):
        """测试基础格式化"""
        formatter = StructuredFormatter("test-service", "test")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        log_entry = json.loads(formatted)

        self.assertEqual(log_entry["level"], "INFO")
        self.assertEqual(log_entry["message"], "Test message")
        self.assertEqual(log_entry["service"], "test-service")
        self.assertEqual(log_entry["environment"], "test")

    def test_formatter_with_exception(self):
        """测试异常格式化"""
        formatter = StructuredFormatter("test-service", "test")

        try:
            raise ValueError("Test error")
        except Exception:
            import sys
            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="/test/file.py",
                lineno=10,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )

            formatted = formatter.format(record)
            log_entry = json.loads(formatted)

            self.assertIn("exception", log_entry)
            self.assertEqual(log_entry["exception"]["type"], "ValueError")
            self.assertIn("Test error", log_entry["exception"]["message"])


class TestLoggingMiddleware(unittest.TestCase):
    """日志中间件测试"""

    def test_request_id_generation(self):
        """测试请求ID生成"""
        from middleware.logging_middleware import request_id_var
        import uuid

        # 设置请求ID
        test_id = str(uuid.uuid4())
        request_id_var.set(test_id)

        # 验证
        self.assertEqual(request_id_var.get(), test_id)

    def test_user_id_context(self):
        """测试用户ID上下文"""
        from middleware.logging_middleware import user_id_var, set_user_id, get_user_id

        # 设置用户ID
        set_user_id("user123")

        # 验证
        self.assertEqual(get_user_id(), "user123")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestStructuredLogging))
    suite.addTests(loader.loadTestsFromTestCase(TestStructuredFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestLoggingMiddleware))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
