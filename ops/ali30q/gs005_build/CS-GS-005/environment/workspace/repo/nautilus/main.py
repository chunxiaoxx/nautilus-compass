"""
Nautilus 主程序入口
基于 V7.1 的模块化版本
"""
import asyncio
import logging

from nautilus.pool import Pool
from nautilus.mind import Mind
from nautilus.body import Body
from nautilus.models import Task

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("nautilus")


async def main():
    """主程序"""
    pool = Pool()
    mind = Mind()
    body = Body(pool, mind)

    logger.info("🚀 Nautilus V7.1 (Modular) 启动")
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

    # 执行
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
