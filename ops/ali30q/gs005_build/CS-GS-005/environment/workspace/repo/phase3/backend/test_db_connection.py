"""
测试数据库连接和配置
"""
import os
from dotenv import load_dotenv
import psycopg2

# 加载环境变量
load_dotenv('.env.production')

# 获取数据库配置
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'nautilus_phase3')
db_user = os.getenv('DB_USER', 'nautilus_user')
db_password = os.getenv('DB_PASSWORD', 'nautilus_pass')

print(f"数据库配置:")
print(f"  Host: {db_host}")
print(f"  Port: {db_port}")
print(f"  Database: {db_name}")
print(f"  User: {db_user}")
print(f"  Password: {'*' * len(db_password)}")
print()

# 测试连接到postgres数据库（默认数据库）
print("1. 测试连接到postgres数据库...")
try:
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database='postgres',
        user='postgres',
        password='postgres'
    )
    print("✅ 成功连接到postgres数据库")

    # 检查nautilus_phase3数据库是否存在
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    exists = cur.fetchone()
    if exists:
        print(f"✅ 数据库 {db_name} 已存在")
    else:
        print(f"❌ 数据库 {db_name} 不存在")

    # 检查nautilus_user用户是否存在
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (db_user,))
    exists = cur.fetchone()
    if exists:
        print(f"✅ 用户 {db_user} 已存在")
    else:
        print(f"❌ 用户 {db_user} 不存在")

    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ 连接postgres数据库失败: {e}")
    print()

# 测试连接到nautilus_phase3数据库
print()
print("2. 测试连接到nautilus_phase3数据库...")
try:
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    print(f"✅ 成功连接到 {db_name} 数据库")
    conn.close()
except Exception as e:
    print(f"❌ 连接失败: {e}")
