"""
日志中间件
记录所有HTTP请求和响应，包括性能指标和错误信息
"""
import time
import uuid
import json
from typing import Callable
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
import logging

# 上下文变量，用于在请求处理过程中传递信息
request_id_var: ContextVar[str] = ContextVar('request_id', default=None)
user_id_var: ContextVar[str] = ContextVar('user_id', default=None)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志中间件

    功能：
    1. 为每个请求生成唯一ID
    2. 记录请求信息（方法、路径、参数、头部）
    3. 记录响应信息（状态码、响应时间）
    4. 记录性能指标
    5. 记录错误和异常
    """

    def __init__(
        self,
        app: FastAPI,
        logger_name: str = "access",
        log_request_body: bool = False,
        log_response_body: bool = False,
        slow_request_threshold: float = 1.0,
        exclude_paths: list = None
    ):
        """
        初始化日志中间件

        Args:
            app: FastAPI应用实例
            logger_name: 日志记录器名称
            log_request_body: 是否记录请求体
            log_response_body: 是否记录响应体
            slow_request_threshold: 慢请求阈值（秒）
            exclude_paths: 排除的路径列表
        """
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.slow_request_threshold = slow_request_threshold
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 检查是否需要排除此路径
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # 生成请求ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

        # 记录开始时间
        start_time = time.time()

        # 提取用户信息（如果存在）
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
            user_id_var.set(user_id)

        # 获取客户端IP
        client_ip = self._get_client_ip(request)

        # 记录请求信息
        request_log = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "user_id": user_id
        }

        # 记录请求体（如果启用）
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_log["request_body"] = body.decode("utf-8")[:1000]  # 限制长度
            except Exception as e:
                request_log["request_body_error"] = str(e)

        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "ip_address": client_ip,
                "user_id": user_id,
                "extra_fields": request_log
            }
        )

        # 处理请求
        response = None
        error = None
        try:
            response = await call_next(request)
        except Exception as e:
            error = e
            self.logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "ip_address": client_ip,
                    "user_id": user_id,
                    "extra_fields": {
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                }
            )
            raise

        # 计算响应时间
        duration = time.time() - start_time
        duration_ms = duration * 1000

        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request_id

        # 记录响应信息
        response_log = {
            "request_id": request_id,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "duration_seconds": round(duration, 3)
        }

        # 判断是否为慢请求
        is_slow = duration > self.slow_request_threshold

        # 选择日志级别
        if response.status_code >= 500:
            log_level = logging.ERROR
            log_message = f"Request failed: {request.method} {request.url.path} - {response.status_code}"
        elif response.status_code >= 400:
            log_level = logging.WARNING
            log_message = f"Request error: {request.method} {request.url.path} - {response.status_code}"
        elif is_slow:
            log_level = logging.WARNING
            log_message = f"Slow request: {request.method} {request.url.path} - {duration_ms:.2f}ms"
        else:
            log_level = logging.INFO
            log_message = f"Request completed: {request.method} {request.url.path} - {response.status_code}"

        # 记录响应日志
        self.logger.log(
            log_level,
            log_message,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "ip_address": client_ip,
                "user_id": user_id,
                "extra_fields": response_log
            }
        )

        # 记录性能指标
        if is_slow:
            self._log_performance_warning(request, response, duration_ms, request_id)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 尝试从代理头获取真实IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 返回直接连接的IP
        if request.client:
            return request.client.host

        return "unknown"

    def _log_performance_warning(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        request_id: str
    ):
        """记录性能警告"""
        perf_logger = logging.getLogger("performance")
        perf_logger.warning(
            f"Slow request detected: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "extra_fields": {
                    "threshold_ms": self.slow_request_threshold * 1000,
                    "exceeded_by_ms": round(duration_ms - (self.slow_request_threshold * 1000), 2)
                }
            }
        )


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    错误日志中间件
    专门用于捕获和记录未处理的异常
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.logger = logging.getLogger("error")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # 获取请求ID
            request_id = request_id_var.get() or "unknown"

            # 记录详细的错误信息
            self.logger.exception(
                f"Unhandled exception: {type(e).__name__}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "extra_fields": {
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                        "query_params": dict(request.query_params),
                        "headers": dict(request.headers)
                    }
                }
            )

            # 重新抛出异常，让FastAPI的异常处理器处理
            raise


def get_request_id() -> str:
    """获取当前请求ID"""
    return request_id_var.get()


def get_user_id() -> str:
    """获取当前用户ID"""
    return user_id_var.get()


def set_user_id(user_id: str):
    """设置当前用户ID"""
    user_id_var.set(user_id)
