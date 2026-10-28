"""
日志系统集成示例
展示如何在应用中使用日志系统
"""
from fastapi import FastAPI, Request
from utils.logging_config import get_logger, StructuredLogger, get_blockchain_logger
from middleware.logging_middleware import get_request_id, set_user_id

# 获取日志记录器
logger = get_logger(__name__)
structured_logger = StructuredLogger(logger)
blockchain_logger = get_blockchain_logger()


# 示例1: 基础日志记录
def example_basic_logging():
    """基础日志记录示例"""
    logger.debug("调试信息")
    logger.info("一般信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    logger.critical("严重错误")


# 示例2: 结构化日志记录
def example_structured_logging():
    """结构化日志记录示例"""
    structured_logger.info(
        "用户登录成功",
        user_id="user_123",
        ip_address="192.168.1.100",
        login_method="password"
    )

    structured_logger.warning(
        "API调用频率过高",
        user_id="user_456",
        endpoint="/api/tasks",
        rate_limit=100,
        current_rate=150
    )


# 示例3: 异常日志记录
def example_exception_logging():
    """异常日志记录示例"""
    try:
        result = 1 / 0
    except Exception as e:
        logger.exception("计算错误")
        # 或者使用结构化日志
        structured_logger.error(
            "计算错误",
            operation="division",
            error_type=type(e).__name__,
            error_message=str(e)
        )


# 示例4: 区块链日志记录
def example_blockchain_logging():
    """区块链日志记录示例"""
    blockchain_logger.info(
        "交易已提交",
        extra={
            "extra_fields": {
                "tx_hash": "0x1234567890abcdef",
                "operation": "publish_task",
                "task_id": "task_123",
                "gas_used": 21000,
                "gas_price": 20000000000,
                "gas_cost": 420000000000000
            }
        }
    )


# 示例5: 在API端点中使用日志
async def example_api_endpoint(request: Request, user_id: str):
    """API端点日志记录示例"""
    # 设置用户ID到上下文
    set_user_id(user_id)

    # 获取请求ID
    request_id = get_request_id()

    # 记录操作开始
    structured_logger.info(
        "开始处理任务创建请求",
        user_id=user_id,
        request_id=request_id
    )

    try:
        # 业务逻辑
        task_id = "task_456"

        # 记录成功
        structured_logger.info(
            "任务创建成功",
            user_id=user_id,
            task_id=task_id,
            request_id=request_id
        )

        return {"task_id": task_id}

    except Exception as e:
        # 记录错误
        logger.exception(
            "任务创建失败",
            extra={
                "extra_fields": {
                    "user_id": user_id,
                    "request_id": request_id,
                    "error_type": type(e).__name__
                }
            }
        )
        raise


# 示例6: 性能日志记录
import time

def example_performance_logging():
    """性能日志记录示例"""
    start_time = time.time()

    # 执行操作
    time.sleep(0.5)

    duration_ms = (time.time() - start_time) * 1000

    if duration_ms > 1000:
        structured_logger.warning(
            "慢操作检测",
            operation="database_query",
            duration_ms=duration_ms,
            threshold_ms=1000
        )
    else:
        structured_logger.debug(
            "操作完成",
            operation="database_query",
            duration_ms=duration_ms
        )


# 示例7: 批量操作日志记录
def example_batch_logging():
    """批量操作日志记录示例"""
    items = ["item1", "item2", "item3"]

    structured_logger.info(
        "开始批量处理",
        total_items=len(items),
        operation="batch_update"
    )

    success_count = 0
    error_count = 0

    for item in items:
        try:
            # 处理项目
            success_count += 1
        except Exception as e:
            error_count += 1
            logger.error(
                f"处理项目失败: {item}",
                extra={
                    "extra_fields": {
                        "item": item,
                        "error": str(e)
                    }
                }
            )

    structured_logger.info(
        "批量处理完成",
        total_items=len(items),
        success_count=success_count,
        error_count=error_count,
        operation="batch_update"
    )


# 示例8: 条件日志记录
def example_conditional_logging(debug_mode: bool = False):
    """条件日志记录示例"""
    if debug_mode:
        logger.debug("详细调试信息")

    # 使用日志级别检查避免不必要的字符串格式化
    if logger.isEnabledFor(logging.DEBUG):
        expensive_data = generate_expensive_debug_data()
        logger.debug(f"调试数据: {expensive_data}")


def generate_expensive_debug_data():
    """生成昂贵的调试数据"""
    return {"key": "value"}


# 示例9: 上下文管理器日志记录
from contextlib import contextmanager

@contextmanager
def log_operation(operation_name: str):
    """操作日志上下文管理器"""
    start_time = time.time()
    structured_logger.info(f"开始操作: {operation_name}")

    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        structured_logger.info(
            f"操作完成: {operation_name}",
            duration_ms=duration_ms
        )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        structured_logger.error(
            f"操作失败: {operation_name}",
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise


def example_context_manager_logging():
    """使用上下文管理器记录日志"""
    with log_operation("数据库查询"):
        # 执行操作
        time.sleep(0.1)


# 示例10: 装饰器日志记录
from functools import wraps

def log_function_call(func):
    """函数调用日志装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        structured_logger.debug(
            f"调用函数: {func.__name__}",
            args=str(args)[:100],
            kwargs=str(kwargs)[:100]
        )

        try:
            result = func(*args, **kwargs)
            structured_logger.debug(f"函数返回: {func.__name__}")
            return result
        except Exception as e:
            structured_logger.error(
                f"函数异常: {func.__name__}",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise

    return wrapper


@log_function_call
def example_decorated_function(x: int, y: int) -> int:
    """使用装饰器记录日志的函数"""
    return x + y


if __name__ == "__main__":
    import logging
    from utils.logging_config import setup_structured_logging

    # 初始化日志系统
    setup_structured_logging(
        log_level="debug",
        service_name="nautilus-backend",
        environment="development"
    )

    print("运行日志示例...\n")

    print("1. 基础日志记录")
    example_basic_logging()

    print("\n2. 结构化日志记录")
    example_structured_logging()

    print("\n3. 异常日志记录")
    example_exception_logging()

    print("\n4. 区块链日志记录")
    example_blockchain_logging()

    print("\n5. 性能日志记录")
    example_performance_logging()

    print("\n6. 批量操作日志记录")
    example_batch_logging()

    print("\n7. 上下文管理器日志记录")
    example_context_manager_logging()

    print("\n8. 装饰器日志记录")
    result = example_decorated_function(10, 20)
    print(f"结果: {result}")

    print("\n日志文件已创建在 logs/ 目录")
