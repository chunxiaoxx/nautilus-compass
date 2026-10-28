"""
创建测试Agent数据

服务器: cloud -p 24860
数据库: nautilus_production

创建3-5个示例Agent:
- 不同专业（Python开发、数据分析、机器学习等）
- 不同声誉等级（50-95分）
- 关联到已创建的用户
"""
import sys
import pymysql
from datetime import datetime
import json

# 数据库连接配置
DB_CONFIG = {
    'host': 'cloud',
    'port': 24860,
    'user': 'root',
    'password': '',  # 需要输入密码
    'database': 'nautilus_production',
    'charset': 'utf8mb4'
}

# 测试Agent数据
TEST_AGENTS = [
    {
        'agent_id': 1001,
        'owner': '0x1234567890123456789012345678901234567890',
        'name': 'PythonMaster',
        'description': '专业的Python开发Agent，擅长Web开发、数据处理和自动化脚本',
        'reputation': 95,
        'specialties': json.dumps(['Python', 'Django', 'FastAPI', 'Data Processing', 'Automation']),
        'current_tasks': 2,
        'completed_tasks': 156,
        'failed_tasks': 4,
        'total_earnings': 15600000000000000000,  # 15.6 ETH in Wei
        'blockchain_registered': True,
        'blockchain_tx_hash': '0xabc123def456789012345678901234567890123456789012345678901234567890',
        'blockchain_address': '0x1234567890123456789012345678901234567890'
    },
    {
        'agent_id': 1002,
        'owner': '0x2345678901234567890123456789012345678901',
        'name': 'DataAnalyst',
        'description': '数据分析专家，精通数据清洗、可视化和统计分析',
        'reputation': 88,
        'specialties': json.dumps(['Data Analysis', 'Pandas', 'NumPy', 'Matplotlib', 'Statistics']),
        'current_tasks': 1,
        'completed_tasks': 92,
        'failed_tasks': 8,
        'total_earnings': 9200000000000000000,  # 9.2 ETH in Wei
        'blockchain_registered': True,
        'blockchain_tx_hash': '0xdef456abc789012345678901234567890123456789012345678901234567890123',
        'blockchain_address': '0x2345678901234567890123456789012345678901'
    },
    {
        'agent_id': 1003,
        'owner': '0x3456789012345678901234567890123456789012',
        'name': 'MLEngineer',
        'description': '机器学习工程师，专注于深度学习、NLP和计算机视觉',
        'reputation': 92,
        'specialties': json.dumps(['Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'NLP', 'Computer Vision']),
        'current_tasks': 3,
        'completed_tasks': 78,
        'failed_tasks': 2,
        'total_earnings': 18500000000000000000,  # 18.5 ETH in Wei
        'blockchain_registered': True,
        'blockchain_tx_hash': '0x789012def456abc345678901234567890123456789012345678901234567890456',
        'blockchain_address': '0x3456789012345678901234567890123456789012'
    },
    {
        'agent_id': 1004,
        'owner': '0x4567890123456789012345678901234567890123',
        'name': 'DevOpsBot',
        'description': 'DevOps自动化Agent，擅长CI/CD、容器化和云基础设施',
        'reputation': 75,
        'specialties': json.dumps(['DevOps', 'Docker', 'Kubernetes', 'CI/CD', 'AWS', 'Terraform']),
        'current_tasks': 1,
        'completed_tasks': 45,
        'failed_tasks': 5,
        'total_earnings': 5800000000000000000,  # 5.8 ETH in Wei
        'blockchain_registered': True,
        'blockchain_tx_hash': '0x456789abc012def567890123456789012345678901234567890123456789012789',
        'blockchain_address': '0x4567890123456789012345678901234567890123'
    },
    {
        'agent_id': 1005,
        'owner': '0x5678901234567890123456789012345678901234',
        'name': 'WebScraper',
        'description': '网络爬虫专家，精通数据采集、反爬虫和数据提取',
        'reputation': 68,
        'specialties': json.dumps(['Web Scraping', 'Selenium', 'BeautifulSoup', 'Scrapy', 'Data Extraction']),
        'current_tasks': 0,
        'completed_tasks': 34,
        'failed_tasks': 6,
        'total_earnings': 3200000000000000000,  # 3.2 ETH in Wei
        'blockchain_registered': True,
        'blockchain_tx_hash': '0x567890def123abc678901234567890123456789012345678901234567890123abc',
        'blockchain_address': '0x5678901234567890123456789012345678901234'
    }
]


def create_agents():
    """创建测试Agent数据"""
    try:
        # 连接数据库
        print("正在连接数据库...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        print(f"✅ 成功连接到数据库: {DB_CONFIG['database']}")

        # 检查agents表是否存在
        cursor.execute("SHOW TABLES LIKE 'agents'")
        if not cursor.fetchone():
            print("❌ agents表不存在")
            return

        # 插入Agent数据
        insert_query = """
        INSERT INTO agents (
            agent_id, owner, name, description, reputation, specialties,
            current_tasks, completed_tasks, failed_tasks, total_earnings,
            blockchain_registered, blockchain_tx_hash, blockchain_address, created_at
        ) VALUES (
            %(agent_id)s, %(owner)s, %(name)s, %(description)s, %(reputation)s, %(specialties)s,
            %(current_tasks)s, %(completed_tasks)s, %(failed_tasks)s, %(total_earnings)s,
            %(blockchain_registered)s, %(blockchain_tx_hash)s, %(blockchain_address)s, %(created_at)s
        )
        """

        created_count = 0
        skipped_count = 0

        for agent_data in TEST_AGENTS:
            # 检查agent_id是否已存在
            cursor.execute("SELECT agent_id FROM agents WHERE agent_id = %s", (agent_data['agent_id'],))
            if cursor.fetchone():
                print(f"⚠️  Agent {agent_data['agent_id']} ({agent_data['name']}) 已存在，跳过")
                skipped_count += 1
                continue

            # 添加创建时间
            agent_data['created_at'] = datetime.now(timezone.utc)

            # 插入数据
            cursor.execute(insert_query, agent_data)
            created_count += 1
            print(f"✅ 创建Agent: {agent_data['name']} (ID: {agent_data['agent_id']}, 声誉: {agent_data['reputation']})")

        # 提交事务
        connection.commit()

        print(f"\n{'='*60}")
        print(f"Agent数据创建完成！")
        print(f"{'='*60}")
        print(f"创建数量: {created_count}")
        print(f"跳过数量: {skipped_count}")
        print(f"总计: {len(TEST_AGENTS)}")

        # 显示创建的Agent统计
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                AVG(reputation) as avg_reputation,
                SUM(completed_tasks) as total_completed,
                SUM(total_earnings) as total_earnings
            FROM agents
            WHERE agent_id >= 1001 AND agent_id <= 1005
        """)
        stats = cursor.fetchone()

        if stats and stats[0] > 0:
            print(f"\n统计信息:")
            print(f"- 总Agent数: {stats[0]}")
            print(f"- 平均声誉: {stats[1]:.2f}")
            print(f"- 总完成任务: {stats[2]}")
            print(f"- 总收益: {stats[3] / 1e18:.2f} ETH")

        cursor.close()
        connection.close()

    except pymysql.err.OperationalError as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n可能的原因:")
        print("1. 数据库服务未运行")
        print("2. 主机地址或端口不正确")
        print("3. 用户名或密码不正确")
        print("4. 数据库不存在")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("="*60)
    print("创建测试Agent数据")
    print("="*60)
    print(f"数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"将创建 {len(TEST_AGENTS)} 个测试Agent")
    print("="*60)

    # 提示输入密码
    if not DB_CONFIG['password']:
        import getpass
        DB_CONFIG['password'] = getpass.getpass("请输入数据库密码: ")

    create_agents()
