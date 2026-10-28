"""
Nautilus V7.1 演示程序
基于模块化架构的示例
"""
import asyncio
import logging
from nautilus import Pool, Body, Mind, Task
from nautilus.utils import setup_logging

# 配置日志
setup_logging(level="INFO")
logger = logging.getLogger("nautilus.demo")


async def main():
    """主程序"""
    # 初始化核心组件
    pool = Pool()
    mind = Mind()
    body = Body(pool, mind)

    logger.info("🚀 Nautilus V7.1 启动（模块化版本）")
    logger.info(f"Body: {body.node_id[:8]}")

    # 提交任务
    tasks = [
        Task(task_id="", desc="你好", user_id="u1"),
        Task(task_id="", desc="帮我分析一下人工智能的发展趋势和未来方向", user_id="u1"),
        Task(task_id="", desc="写一个Python快速排序算法", user_id="u1"),
        Task(task_id="", desc="创作一首关于春天的诗", user_id="u1"),
    ]

    for t in tasks:
        pool.submit(t)

    # 执行任务
    await body.work(max_tasks=4)

    # 检查离线
    pool.check_offline()

    # 排行榜
    print("\n" + "="*60)
    print("📊 排行榜")
    print("="*60)
    for i, e in enumerate(pool.leaderboard(), 1):
        print(f"{i}. {e['node']} | {e['points']}pts | {e['meme']:.2f}MEME | "
              f"{e['tasks']}tasks | HP:{e['hp']} | ROI:{e['roi']:.2f} | Cost:{e['total_cost']:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
