#!/usr/bin/env python3
"""
种子数据导入脚本
用于填充Nautilus数据库的示例数据
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 导入嵌入服务
from memory.embedding_service import EmbeddingService


class SeedDataLoader:
    """种子数据加载器"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.embedding_service = EmbeddingService()
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

    async def clear_existing_data(self):
        """清除现有数据（可选）"""
        print("\n🔄 清除现有数据...")
        async with self.pool.acquire() as conn:
            # 按依赖顺序删除
            await conn.execute("DELETE FROM agent_memories")
            await conn.execute("DELETE FROM agent_reflections")
            await conn.execute("DELETE FROM agent_skills")
            await conn.execute("DELETE FROM task_assignments")
            await conn.execute("DELETE FROM tasks")
            await conn.execute("DELETE FROM agents")
            await conn.execute("DELETE FROM users")
        print("✅ 现有数据已清除")

    async def seed_users(self):
        """导入用户数据"""
        print("\n🔄 导入用户数据...")
        users = self.load_json('seed_users.json')

        async with self.pool.acquire() as conn:
            for user in users:
                # 将role转换为is_admin
                is_admin = user['role'] == 'admin'
                # 使用默认密码hash（实际应用中不应这样做）
                default_password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qvQu6'  # "password123"

                await conn.execute("""
                    INSERT INTO users (wallet_address, username, email, hashed_password, is_active, is_admin, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
                    ON CONFLICT (wallet_address) DO NOTHING
                """, user['walletAddress'], user['username'], user['email'],
                    default_password_hash, user['isActive'], is_admin, user['createdAt'])

        print(f"✅ 导入了 {len(users)} 个用户")

    async def seed_agents(self):
        """导入代理数据"""
        print("\n🔄 导入代理数据...")
        agents = self.load_json('seed_agents.json')

        async with self.pool.acquire() as conn:
            for agent in agents:
                # 插入代理基本信息
                agent_id = await conn.fetchval("""
                    INSERT INTO agents (
                        wallet_address, name, bio, experience_level,
                        reputation, completed_tasks, success_rate,
                        average_rating, hourly_rate, availability,
                        created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
                    ON CONFLICT (wallet_address) DO UPDATE
                    SET name = EXCLUDED.name
                    RETURNING id
                """, agent['walletAddress'], agent['name'], agent['bio'],
                    agent['experienceLevel'], agent['reputation'],
                    agent['completedTasks'], agent['successRate'],
                    agent['averageRating'], agent['hourlyRate'],
                    agent['availability'])

                # 插入技能数据
                for skill in agent['skills']:
                    # 根据经验等级设置技能等级
                    skill_level = {
                        'Expert': 5,
                        'Advanced': 4,
                        'Intermediate': 3,
                        'Beginner': 2
                    }.get(agent['experienceLevel'], 3)

                    await conn.execute("""
                        INSERT INTO agent_skills (
                            agent_id, skill_name, skill_level,
                            experience, success_count, created_at
                        )
                        VALUES ($1, $2, $3, $4, $5, NOW())
                        ON CONFLICT (agent_id, skill_name) DO NOTHING
                    """, agent_id, skill, skill_level,
                        agent['completedTasks'] * 10,
                        int(agent['completedTasks'] * agent['successRate']))

        print(f"✅ 导入了 {len(agents)} 个代理")

    async def seed_tasks(self):
        """导入任务数据"""
        print("\n🔄 导入任务数据...")
        tasks = self.load_json('seed_tasks.json')

        async with self.pool.acquire() as conn:
            for task in tasks:
                # 插入任务
                task_id = await conn.fetchval("""
                    INSERT INTO tasks (
                        title, description, type, status, reward,
                        difficulty, estimated_time, requirements,
                        created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                    RETURNING id
                """, task['title'], task['description'], task['type'],
                    task['status'], task['reward'], task['difficulty'],
                    task['estimatedTime'], json.dumps(task['requirements']))

                # 插入任务技能要求
                for skill in task['requiredSkills']:
                    await conn.execute("""
                        INSERT INTO task_skills (task_id, skill_name)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """, task_id, skill)

        print(f"✅ 导入了 {len(tasks)} 个任务")

    async def generate_task_memories(self):
        """为已完成的任务生成记忆数据"""
        print("\n🔄 生成任务记忆数据...")

        async with self.pool.acquire() as conn:
            # 获取已完成的任务
            completed_tasks = await conn.fetch("""
                SELECT id, title, description, type
                FROM tasks
                WHERE status = 'Completed'
            """)

            if not completed_tasks:
                print("⚠️  没有已完成的任务，跳过记忆生成")
                return

            # 获取代理
            agents = await conn.fetch("SELECT id, name FROM agents LIMIT 3")

            memory_count = 0
            for task in completed_tasks:
                for agent in agents:
                    # 创建记忆文本
                    memory_text = f"""
                    Task: {task['title']}
                    Type: {task['type']}
                    Description: {task['description']}
                    Result: Successfully completed with high quality
                    """

                    # 生成嵌入向量
                    print(f"  生成嵌入向量: Agent {agent['name']} - Task {task['title'][:30]}...")
                    embedding = await self.embedding_service.embed(memory_text)

                    # 存储记忆
                    await conn.execute("""
                        INSERT INTO agent_memories (
                            agent_id, task_id, memory_type, content,
                            embedding, created_at
                        )
                        VALUES ($1, $2, $3, $4, $5, NOW())
                    """, agent['id'], task['id'], 'task_execution',
                        json.dumps({
                            'task_title': task['title'],
                            'task_type': task['type'],
                            'result': 'success',
                            'quality_score': 0.9
                        }), embedding)

                    memory_count += 1

        print(f"✅ 生成了 {memory_count} 条记忆数据")

    async def generate_reflections(self):
        """生成反思数据"""
        print("\n🔄 生成反思数据...")

        async with self.pool.acquire() as conn:
            # 获取已完成的任务
            completed_tasks = await conn.fetch("""
                SELECT id, title, type
                FROM tasks
                WHERE status = 'Completed'
            """)

            if not completed_tasks:
                print("⚠️  没有已完成的任务，跳过反思生成")
                return

            # 获取代理
            agents = await conn.fetch("SELECT id, name FROM agents LIMIT 2")

            reflection_count = 0
            for task in completed_tasks:
                for agent in agents:
                    reflection_text = f"""
                    Reflection on completing {task['title']}:

                    What went well:
                    - Successfully delivered high-quality solution
                    - Met all requirements and deadlines
                    - Applied best practices effectively

                    What could be improved:
                    - Could optimize performance further
                    - Better documentation needed

                    Key learnings:
                    - Improved understanding of {task['type']} domain
                    - Learned new optimization techniques
                    """

                    await conn.execute("""
                        INSERT INTO agent_reflections (
                            agent_id, task_id, reflection_text,
                            insights, importance_score, created_at
                        )
                        VALUES ($1, $2, $3, $4, $5, NOW())
                    """, agent['id'], task['id'], reflection_text,
                        json.dumps({
                            'strengths': ['quality', 'timeliness'],
                            'improvements': ['optimization', 'documentation'],
                            'learnings': ['domain knowledge', 'techniques']
                        }), 0.8)

                    reflection_count += 1

        print(f"✅ 生成了 {reflection_count} 条反思数据")

    async def create_task_assignments(self):
        """创建任务分配"""
        print("\n🔄 创建任务分配...")

        async with self.pool.acquire() as conn:
            # 为进行中的任务分配代理
            in_progress_tasks = await conn.fetch("""
                SELECT id FROM tasks WHERE status = 'In Progress'
            """)

            agents = await conn.fetch("SELECT id FROM agents LIMIT 3")

            assignment_count = 0
            for i, task in enumerate(in_progress_tasks):
                agent = agents[i % len(agents)]
                await conn.execute("""
                    INSERT INTO task_assignments (
                        task_id, agent_id, status, assigned_at
                    )
                    VALUES ($1, $2, 'in_progress', NOW())
                    ON CONFLICT DO NOTHING
                """, task['id'], agent['id'])
                assignment_count += 1

        print(f"✅ 创建了 {assignment_count} 个任务分配")

    async def verify_data(self):
        """验证导入的数据"""
        print("\n🔄 验证数据...")

        async with self.pool.acquire() as conn:
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            agent_count = await conn.fetchval("SELECT COUNT(*) FROM agents")
            task_count = await conn.fetchval("SELECT COUNT(*) FROM tasks")
            skill_count = await conn.fetchval("SELECT COUNT(*) FROM agent_skills")
            memory_count = await conn.fetchval("SELECT COUNT(*) FROM agent_memories")
            reflection_count = await conn.fetchval("SELECT COUNT(*) FROM agent_reflections")

            print(f"\n📊 数据统计:")
            print(f"  用户: {user_count}")
            print(f"  代理: {agent_count}")
            print(f"  任务: {task_count}")
            print(f"  技能: {skill_count}")
            print(f"  记忆: {memory_count}")
            print(f"  反思: {reflection_count}")

            # 验证外键关系
            print(f"\n🔍 验证外键关系...")

            # 检查孤立的技能记录
            orphan_skills = await conn.fetchval("""
                SELECT COUNT(*) FROM agent_skills
                WHERE agent_id NOT IN (SELECT id FROM agents)
            """)

            if orphan_skills > 0:
                print(f"  ⚠️  发现 {orphan_skills} 条孤立的技能记录")
            else:
                print(f"  ✅ 所有技能记录都有对应的代理")

            # 检查孤立的记忆记录
            orphan_memories = await conn.fetchval("""
                SELECT COUNT(*) FROM agent_memories
                WHERE agent_id NOT IN (SELECT id FROM agents)
            """)

            if orphan_memories > 0:
                print(f"  ⚠️  发现 {orphan_memories} 条孤立的记忆记录")
            else:
                print(f"  ✅ 所有记忆记录都有对应的代理")

        print("\n✅ 数据验证完成")

    async def run(self, clear_existing: bool = False):
        """运行完整的种子数据导入流程"""
        try:
            await self.connect()

            if clear_existing:
                await self.clear_existing_data()

            # 按依赖顺序导入
            await self.seed_users()
            await self.seed_agents()
            await self.seed_tasks()
            await self.create_task_assignments()

            # 生成记忆和反思数据
            await self.generate_task_memories()
            await self.generate_reflections()

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
    print("🌱 Nautilus 种子数据导入工具")
    print("="*70)

    # 询问是否清除现有数据
    clear_existing = input("\n是否清除现有数据? (y/N): ").lower() == 'y'

    loader = SeedDataLoader(database_url)
    await loader.run(clear_existing=clear_existing)


if __name__ == '__main__':
    asyncio.run(main())
