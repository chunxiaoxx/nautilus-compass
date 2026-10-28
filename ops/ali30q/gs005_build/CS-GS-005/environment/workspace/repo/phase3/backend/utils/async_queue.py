"""
异步任务队列 - 用于处理耗时的后台任务
支持任务优先级、重试机制、任务监控等功能
"""
import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """
    异步任务

    Attributes:
        id: 任务ID
        name: 任务名称
        func: 任务函数
        args: 位置参数
        kwargs: 关键字参数
        priority: 优先级
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        timeout: 超时时间（秒）
        status: 任务状态
        result: 任务结果
        error: 错误信息
        created_at: 创建时间
        started_at: 开始时间
        completed_at: 完成时间
        retries: 已重试次数
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 5.0
    timeout: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int = 0

    def __lt__(self, other):
        """用于优先级队列排序"""
        return self.priority.value > other.priority.value


class AsyncTaskQueue:
    """
    异步任务队列

    功能:
    - 任务优先级管理
    - 并发控制
    - 自动重试
    - 超时控制
    - 任务监控
    """

    def __init__(
        self,
        max_workers: int = 5,
        max_queue_size: int = 1000,
        enable_monitoring: bool = True
    ):
        """
        初始化任务队列

        Args:
            max_workers: 最大工作线程数
            max_queue_size: 最大队列大小
            enable_monitoring: 是否启用监控
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.enable_monitoring = enable_monitoring

        # 任务队列（优先级队列）
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)

        # 任务存储
        self.tasks: Dict[str, Task] = {}

        # 工作线程
        self.workers: List[asyncio.Task] = []

        # 运行状态
        self.running = False

        # 统计信息
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'total_time': 0.0,
            'avg_time': 0.0
        }

        logger.info(f"AsyncTaskQueue initialized with {max_workers} workers")

    async def start(self):
        """启动任务队列"""
        if self.running:
            logger.warning("Task queue is already running")
            return

        self.running = True

        # 启动工作线程
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        logger.info(f"Task queue started with {self.max_workers} workers")

    async def stop(self, wait: bool = True):
        """
        停止任务队列

        Args:
            wait: 是否等待所有任务完成
        """
        if not self.running:
            return

        self.running = False

        if wait:
            # 等待队列清空
            await self.queue.join()

        # 取消所有工作线程
        for worker in self.workers:
            worker.cancel()

        # 等待工作线程结束
        await asyncio.gather(*self.workers, return_exceptions=True)

        self.workers.clear()

        logger.info("Task queue stopped")

    async def submit(
        self,
        func: Callable,
        *args,
        name: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        timeout: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        提交任务

        Args:
            func: 任务函数（可以是同步或异步函数）
            args: 位置参数
            name: 任务名称
            priority: 优先级
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            timeout: 超时时间（秒）
            kwargs: 关键字参数

        Returns:
            任务ID
        """
        if not self.running:
            raise RuntimeError("Task queue is not running")

        # 创建任务
        task = Task(
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout
        )

        # 存储任务
        self.tasks[task.id] = task

        # 加入队列
        await self.queue.put(task)

        self.stats['total_tasks'] += 1

        logger.debug(f"Task submitted: {task.name} (id={task.id}, priority={priority.name})")

        return task.id

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务对象
        """
        return self.tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            self.stats['cancelled_tasks'] += 1
            logger.info(f"Task cancelled: {task.name} (id={task_id})")
            return True
        return False

    async def _worker(self, worker_id: int):
        """
        工作线程

        Args:
            worker_id: 工作线程ID
        """
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # 获取任务（带超时）
                task = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )

                # 检查任务是否已取消
                if task.status == TaskStatus.CANCELLED:
                    self.queue.task_done()
                    continue

                # 执行任务
                await self._execute_task(task, worker_id)

                # 标记任务完成
                self.queue.task_done()

            except asyncio.TimeoutError:
                # 队列为空，继续等待
                continue
            except asyncio.CancelledError:
                # 工作线程被取消
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

        logger.info(f"Worker {worker_id} stopped")

    async def _execute_task(self, task: Task, worker_id: int):
        """
        执行任务

        Args:
            task: 任务对象
            worker_id: 工作线程ID
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        logger.debug(f"Worker {worker_id} executing task: {task.name} (id={task.id})")

        start_time = time.time()

        try:
            # 执行任务（带超时）
            if asyncio.iscoroutinefunction(task.func):
                # 异步函数
                if task.timeout:
                    task.result = await asyncio.wait_for(
                        task.func(*task.args, **task.kwargs),
                        timeout=task.timeout
                    )
                else:
                    task.result = await task.func(*task.args, **task.kwargs)
            else:
                # 同步函数，在线程池中执行
                loop = asyncio.get_event_loop()
                if task.timeout:
                    task.result = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: task.func(*task.args, **task.kwargs)
                        ),
                        timeout=task.timeout
                    )
                else:
                    task.result = await loop.run_in_executor(
                        None,
                        lambda: task.func(*task.args, **task.kwargs)
                    )

            # 任务成功
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

            elapsed = time.time() - start_time
            self.stats['completed_tasks'] += 1
            self.stats['total_time'] += elapsed
            self.stats['avg_time'] = self.stats['total_time'] / self.stats['completed_tasks']

            logger.info(
                f"Task completed: {task.name} (id={task.id}, time={elapsed:.3f}s)"
            )

        except asyncio.TimeoutError:
            # 任务超时
            task.error = f"Task timeout after {task.timeout}s"
            await self._handle_task_failure(task, worker_id)

        except Exception as e:
            # 任务失败
            task.error = str(e)
            await self._handle_task_failure(task, worker_id)

    async def _handle_task_failure(self, task: Task, worker_id: int):
        """
        处理任务失败

        Args:
            task: 任务对象
            worker_id: 工作线程ID
        """
        task.retries += 1

        logger.warning(
            f"Task failed: {task.name} (id={task.id}, "
            f"retries={task.retries}/{task.max_retries}, error={task.error})"
        )

        # 检查是否需要重试
        if task.retries < task.max_retries:
            task.status = TaskStatus.RETRYING

            # 延迟后重新加入队列
            await asyncio.sleep(task.retry_delay)
            await self.queue.put(task)

            logger.info(f"Task requeued for retry: {task.name} (id={task.id})")
        else:
            # 重试次数用尽，标记为失败
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            self.stats['failed_tasks'] += 1

            logger.error(
                f"Task failed permanently: {task.name} (id={task.id}, "
                f"error={task.error})"
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            **self.stats,
            'queue_size': self.queue.qsize(),
            'active_workers': len([w for w in self.workers if not w.done()]),
            'total_workers': len(self.workers),
            'running': self.running
        }

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        按状态获取任务

        Args:
            status: 任务状态

        Returns:
            任务列表
        """
        return [task for task in self.tasks.values() if task.status == status]

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Task:
        """
        等待任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            任务对象

        Raises:
            asyncio.TimeoutError: 等待超时
            KeyError: 任务不存在
        """
        task = self.tasks.get(task_id)
        if not task:
            raise KeyError(f"Task not found: {task_id}")

        start_time = time.time()

        while task.status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING]:
            if timeout and (time.time() - start_time) > timeout:
                raise asyncio.TimeoutError(f"Wait for task timeout: {task_id}")

            await asyncio.sleep(0.1)

        return task


# 全局任务队列实例
_task_queue: Optional[AsyncTaskQueue] = None


def get_task_queue() -> Optional[AsyncTaskQueue]:
    """获取全局任务队列"""
    return _task_queue


async def init_task_queue(
    max_workers: int = 5,
    max_queue_size: int = 1000,
    enable_monitoring: bool = True
) -> AsyncTaskQueue:
    """
    初始化全局任务队列

    Args:
        max_workers: 最大工作线程数
        max_queue_size: 最大队列大小
        enable_monitoring: 是否启用监控

    Returns:
        任务队列实例
    """
    global _task_queue
    _task_queue = AsyncTaskQueue(
        max_workers=max_workers,
        max_queue_size=max_queue_size,
        enable_monitoring=enable_monitoring
    )
    await _task_queue.start()
    return _task_queue


async def submit_task(
    func: Callable,
    *args,
    name: str = "",
    priority: TaskPriority = TaskPriority.NORMAL,
    max_retries: int = 3,
    retry_delay: float = 5.0,
    timeout: Optional[float] = None,
    **kwargs
) -> str:
    """
    提交任务到全局队列

    Args:
        func: 任务函数
        args: 位置参数
        name: 任务名称
        priority: 优先级
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        timeout: 超时时间（秒）
        kwargs: 关键字参数

    Returns:
        任务ID
    """
    queue = get_task_queue()
    if not queue:
        raise RuntimeError("Task queue not initialized")

    return await queue.submit(
        func,
        *args,
        name=name,
        priority=priority,
        max_retries=max_retries,
        retry_delay=retry_delay,
        timeout=timeout,
        **kwargs
    )


def background_task(
    name: str = "",
    priority: TaskPriority = TaskPriority.NORMAL,
    max_retries: int = 3,
    retry_delay: float = 5.0,
    timeout: Optional[float] = None
):
    """
    后台任务装饰器

    Args:
        name: 任务名称
        priority: 优先级
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        timeout: 超时时间（秒）

    Usage:
        @background_task(name="send_email", priority=TaskPriority.HIGH)
        async def send_email(to: str, subject: str, body: str):
            # 发送邮件逻辑
            pass

        # 调用时自动提交到后台队列
        task_id = await send_email("user@example.com", "Hello", "World")
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            return await submit_task(
                func,
                *args,
                name=name or func.__name__,
                priority=priority,
                max_retries=max_retries,
                retry_delay=retry_delay,
                timeout=timeout,
                **kwargs
            )
        return wrapper
    return decorator


# 导出
__all__ = [
    'TaskPriority',
    'TaskStatus',
    'Task',
    'AsyncTaskQueue',
    'get_task_queue',
    'init_task_queue',
    'submit_task',
    'background_task'
]
