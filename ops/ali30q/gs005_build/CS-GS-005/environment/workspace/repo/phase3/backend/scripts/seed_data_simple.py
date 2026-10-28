#!/usr/bin/env python3
"""
种子数据导入脚本 - 简化版
适配现有数据库表结构
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg


class SimpleSeedDataLoader:
    """简化的种子数据加载器"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None

    async def connect(self):
        """连接数据库"""
        print("🔄 连接数据库...")
        self.pool = await asyncpg.create_pool(self.database_url)
        print("✅ 数据库连接成功")

    async def close(self):
        """关闭连接"""
        if self.pool:
            await self.pool.close()
            print("✅ 数据库连接已关闭")

    def load_json(self, filename: str):
        """加载JSON文件"""
        filepath = Path(__file__).parent / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def seed_users(self):
        """导入用户数据"""
        print("\n🔄 导入用户数据...")
        users = self.load_json('seed_users.json')

        async with self.pool.acquire() as conn:
            count = 0
            for user in users:
                # 将role转换为is_admin
                is_admin = user['role'] == 'admin'
                # 使用默认密码hash
                default_password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qvQu6'

                # 转换日期格式 - 移除时区信息
                created_at = datetime.fromisoformat(user['createdAt'].replace('Z', '+00:00')).replace(tzinfo=None)

                try:
                    await conn.execute("""
                        INSERT INTO users (wallet_address, username, email, hashed_password, is_active, is_admin, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
                        ON CONFLICT (wallet_address) DO NOTHING
                    """, user['walletAddress'], user['username'], user['email'],
                        default_password_hash, user['isActive'], is_admin, created_at)
                    count += 1
                except Exception as e:
                    print(f"  ⚠️  跳过用户 {user['username']}: {e}")

        print(f"✅ 导入了 {count} 个用户")

    async def seed_agents(self):
        """导入代理数据"""
        print("\n🔄 导入代理数据...")
        agents = self.load_json('seed_agents.json')

        async with self.pool.acquire() as conn:
            count = 0
            for i, agent in enumerate(agents, start=1):
                try:
                    # 将技能列表转换为字符串
                    specialties = ', '.join(agent['skills'])

                    await conn.execute("""
                        INSERT INTO agents (
                            agent_id, owner, name, description, reputation,
                            specialties, current_tasks, completed_tasks, failed_tasks,
                            total_earnings, created_at, blockchain_registered
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), false)
                        ON CONFLICT (agent_id) DO NOTHING
                    """, i, agent['walletAddress'], agent['name'], agent['bio'],
                        agent['reputation'], specialties, 0, agent['completedTasks'],
                        0, 0)
                    count += 1
                except Exception as e:
                    print(f"  ⚠️  跳过代理 {agent['name']}: {e}")

        print(f"✅ 导入了 {count} 个代理")

    async def seed_tasks(self):
        """导入任务数据"""
        print("\n🔄 导入任务数据...")
        tasks = self.load_json('seed_tasks.json')

        # 任务类型映射 - 使用正确的枚举值
        type_mapping = {
            'AI/ML': 'CODE',
            'Blockchain': 'CODE',
            'Frontend': 'CODE',
            'Backend': 'CODE',
            'DevOps': 'CODE',
            'Mobile': 'CODE',
            'Security': 'RESEARCH',  # 改为RESEARCH
            'Data': 'DATA'
        }

        # 状态映射 - 使用正确的枚举值（大写）
        status_mapping = {
            'Open': 'OPEN',
            'In Progress': 'ACCEPTED',
            'Completed': 'COMPLETED'
        }

        async with self.pool.acquire() as conn:
            count = 0
            for task in tasks:
                try:
                    task_type = type_mapping.get(task['type'], 'CODE')
                    status = status_mapping.get(task['status'], 'OPEN')

                    # 生成唯一的task_id
                    task_id = f"0x{task['id']:064x}"

                    # 使用第一个用户作为publisher
                    publisher = "0x8901234567890123456789012345678901234567"

                    await conn.execute("""
                        INSERT INTO tasks (
                            task_id, publisher, description, reward,
                            task_type, status, timeout, created_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, 86400, NOW())
                        ON CONFLICT (task_id) DO NOTHING
                    """, task_id, publisher, task['description'],
                        task['reward'], task_type, status)
                    count += 1
                except Exception as e:
                    print(f"  ⚠️  跳过任务 {task['title']}: {e}")

        print(f"✅ 导入了 {count} 个任务")

    async def verify_data(self):
        """验证导入的数据"""
        print("\n🔄 验证数据...")

        async with self.pool.acquire() as conn:
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            agent_count = await conn.fetchval("SELECT COUNT(*) FROM agents")
            task_count = await conn.fetchval("SELECT COUNT(*) FROM tasks")

            print(f"\n📊 数据统计:")
            print(f"  用户: {user_count}")
            print(f"  代理: {agent_count}")
            print(f"  任务: {task_count}")

        print("\n✅ 数据验证完成")

    async def run(self):
        """运行完整的种子数据导入流程"""
        try:
            await self.connect()

            # 按依赖顺序导入
            await self.seed_users()
            await self.seed_agents()
            await self.seed_tasks()

            # 验证数据
            await self.verify_data()

            print("\n🎉 种子数据导入完成！")

        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await self.close()


async def main():
    """主函数"""
    # 从环境变量获取数据库URL
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://nautilus:nautilus_staging_2024@localhost:5432/nautilus_staging'
    )

    print("="*70)
    print("🌱 Nautilus 种子数据导入工具 (简化版)")
    print("="*70)
    print("\n适配现有数据库表结构")
    print("将导入: 用户、代理、任务")
    print("\n开始导入...\n")

    loader = SimpleSeedDataLoader(database_url)
    await loader.run()


if __name__ == '__main__':
    asyncio.run(main())
