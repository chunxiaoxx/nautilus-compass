"""
创建PostgreSQL测试数据库
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 连接参数
conn_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432
}

try:
    # 连接到postgres数据库
    conn = psycopg2.connect(**conn_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # 检查数据库是否存在
    cur.execute("SELECT 1 FROM pg_database WHERE datname='nautilus'")
    exists = cur.fetchone()

    if not exists:
        cur.execute('CREATE DATABASE nautilus')
        print("✅ 数据库 'nautilus' 创建成功")
    else:
        print("ℹ️  数据库 'nautilus' 已存在")

    # 创建测试数据库
    cur.execute("SELECT 1 FROM pg_database WHERE datname='nautilus_test'")
    exists = cur.fetchone()

    if not exists:
        cur.execute('CREATE DATABASE nautilus_test')
        print("✅ 数据库 'nautilus_test' 创建成功")
    else:
        print("ℹ️  数据库 'nautilus_test' 已存在")

    cur.close()
    conn.close()
    print("\n✅ 数据库准备完成！")

except psycopg2.OperationalError as e:
    print(f"❌ 连接失败: {e}")
    print("\n可能的原因:")
    print("1. PostgreSQL服务未运行")
    print("2. 密码不正确")
    print("3. pg_hba.conf配置问题")
except Exception as e:
    print(f"❌ 错误: {e}")
