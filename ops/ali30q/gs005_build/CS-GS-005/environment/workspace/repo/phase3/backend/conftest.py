"""
Pytest配置文件
确保测试隔离和指标重置
"""
import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture(scope="function", autouse=True)
def reset_metrics():
    """每个测试前重置Prometheus指标"""
    from utils.metrics_registry import reset_metrics
    reset_metrics()
    yield
    # 测试后清理
    reset_metrics()


@pytest.fixture(scope="session")
def test_db():
    """测试数据库配置"""
    # 使用内存数据库进行测试
    return "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session(test_db):
    """创建测试数据库会话"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models.database import Base

    engine = create_engine(test_db)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def client():
    """创建测试客户端"""
    from fastapi.testclient import TestClient
    from main import app

    return TestClient(app)
