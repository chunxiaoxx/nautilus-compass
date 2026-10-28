"""
Gas费用API端点测试
测试Gas费用查询和任务完成时的Gas计算
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from main import app
from models.database import Base, Task, TaskStatus, TaskType, User, Agent
from utils.database import get_db
from utils.auth import create_access_token


# 测试数据库设置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_gas_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(setup_database):
    """Create test user"""
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        wallet_address="0x1234567890123456789012345678901234567890",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.close()


@pytest.fixture
def test_agent(setup_database, test_user):
    """Create test agent"""
    db = TestingSessionLocal()
    agent = Agent(
        agent_id=1,
        owner=test_user.wallet_address,
        name="Test Agent",
        description="Test agent description",
        reputation=100,
        blockchain_registered=True
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    yield agent
    db.close()


@pytest.fixture
def test_task(setup_database, test_user, test_agent):
    """Create test task with blockchain transactions"""
    db = TestingSessionLocal()
    task = Task(
        task_id="task_test_123",
        publisher=test_user.wallet_address,
        description="Test task",
        reward=10000000000000000,  # 0.01 ETH
        task_type=TaskType.CODE,
        status=TaskStatus.SUBMITTED,
        agent=test_agent.owner,
        timeout=3600,
        blockchain_tx_hash="0xpublish123",
        blockchain_accept_tx="0xaccept456",
        blockchain_submit_tx="0xsubmit789",
        blockchain_status="submitted"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    yield task
    db.close()


@pytest.fixture
def auth_token(test_user):
    """Create authentication token"""
    return create_access_token(data={"sub": test_user.username})


class TestGasInfoEndpoint:
    """测试Gas信息查询端点"""

    def test_get_gas_info_not_completed(self, test_task):
        """测试获取未完成任务的Gas信息"""
        response = client.get(f"/api/tasks/{test_task.id}/gas")

        assert response.status_code == 200
        data = response.json()

        assert data["task_id"] == test_task.id
        assert data["gas_used"] is None
        assert data["gas_cost"] is None
        assert data["gas_split"] is None
        assert data["reward"] == test_task.reward
        assert data["actual_reward"] is None
        assert len(data["transactions"]) == 4

    def test_get_gas_info_completed_with_gas(self, test_task):
        """测试获取已完成任务的Gas信息"""
        # Update task with gas information
        db = TestingSessionLocal()
        task = db.query(Task).filter(Task.id == test_task.id).first()
        task.status = TaskStatus.COMPLETED
        task.blockchain_complete_tx = "0xcomplete999"
        task.gas_used = 225000
        task.gas_cost = 4500000000000000  # 0.0045 ETH
        task.gas_split = 2250000000000000  # 0.00225 ETH
        db.commit()
        db.close()

        response = client.get(f"/api/tasks/{test_task.id}/gas")

        assert response.status_code == 200
        data = response.json()

        assert data["task_id"] == test_task.id
        assert data["gas_used"] == 225000
        assert data["gas_cost"] == 4500000000000000
        assert data["gas_split"] == 2250000000000000
        assert data["reward"] == 10000000000000000
        assert data["actual_reward"] == 7750000000000000  # 0.01 - 0.00225 = 0.00775 ETH

    def test_get_gas_info_task_not_found(self, setup_database):
        """测试查询不存在的任务"""
        response = client.get("/api/tasks/99999/gas")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_gas_info_transactions_list(self, test_task):
        """测试Gas信息中的交易列表"""
        response = client.get(f"/api/tasks/{test_task.id}/gas")

        assert response.status_code == 200
        data = response.json()

        transactions = data["transactions"]
        assert len(transactions) == 4

        # Check transaction types
        tx_types = [tx["type"] for tx in transactions]
        assert "publish" in tx_types
        assert "accept" in tx_types
        assert "submit" in tx_types
        assert "complete" in tx_types

        # Check transaction hashes
        publish_tx = next(tx for tx in transactions if tx["type"] == "publish")
        assert publish_tx["tx_hash"] == "0xpublish123"


class TestTaskCompletionWithGas:
    """测试任务完成时的Gas计算"""

    @patch('blockchain.blockchain_service.BlockchainService.complete_task_on_chain')
    @patch('blockchain.blockchain_service.BlockchainService.calculate_task_total_gas')
    def test_complete_task_with_gas_calculation(
        self,
        mock_calculate_gas,
        mock_complete_task,
        test_task,
        auth_token
    ):
        """测试完成任务时计算Gas费用"""
        # Mock blockchain responses
        mock_complete_task.return_value = "0xcomplete999"
        mock_calculate_gas.return_value = {
            'total_gas_used': 225000,
            'total_gas_cost': 4500000000000000,
            'gas_split': 2250000000000000
        }

        response = client.post(
            f"/api/tasks/{test_task.id}/complete",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "Completed"
        assert data["gas_used"] == 225000
        assert data["gas_cost"] == 4500000000000000
        assert data["gas_split"] == 2250000000000000
        assert data["blockchain_complete_tx"] == "0xcomplete999"

    @patch('blockchain.blockchain_service.BlockchainService.complete_task_on_chain')
    @patch('blockchain.blockchain_service.BlockchainService.calculate_task_total_gas')
    def test_complete_task_gas_calculation_failure(
        self,
        mock_calculate_gas,
        mock_complete_task,
        test_task,
        auth_token
    ):
        """测试Gas计算失败的情况"""
        # Mock blockchain responses
        mock_complete_task.return_value = "0xcomplete999"
        mock_calculate_gas.return_value = None  # Gas calculation failed

        response = client.post(
            f"/api/tasks/{test_task.id}/complete",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Task should still be completed even if gas calculation fails
        assert data["status"] == "Completed"
        assert data["gas_used"] is None
        assert data["gas_cost"] is None
        assert data["gas_split"] is None

    @patch('blockchain.blockchain_service.BlockchainService.complete_task_on_chain')
    def test_complete_task_blockchain_failure(
        self,
        mock_complete_task,
        test_task,
        auth_token
    ):
        """测试区块链完成失败的情况"""
        # Mock blockchain failure
        mock_complete_task.return_value = None

        response = client.post(
            f"/api/tasks/{test_task.id}/complete",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Task should still be marked as completed in database
        assert data["status"] == "Completed"
        assert data["blockchain_complete_tx"] is None
        assert data["gas_used"] is None

    def test_complete_task_unauthorized(self, test_task):
        """测试未授权完成任务"""
        response = client.post(f"/api/tasks/{test_task.id}/complete")

        assert response.status_code == 401

    def test_complete_task_wrong_publisher(self, test_task, setup_database):
        """测试非发布者完成任务"""
        # Create another user
        db = TestingSessionLocal()
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed_password",
            wallet_address="0x9999999999999999999999999999999999999999",
            is_active=True
        )
        db.add(other_user)
        db.commit()
        db.close()

        other_token = create_access_token(data={"sub": "otheruser"})

        response = client.post(
            f"/api/tasks/{test_task.id}/complete",
            headers={"Authorization": f"Bearer {other_token}"}
        )

        assert response.status_code == 403
        assert "publisher" in response.json()["detail"].lower()


class TestGasFeeScenarios:
    """测试各种Gas费用场景"""

    def test_high_gas_low_reward_scenario(self, test_task):
        """测试高Gas费用低奖励场景"""
        db = TestingSessionLocal()
        task = db.query(Task).filter(Task.id == test_task.id).first()
        task.reward = 1000000000000000  # 0.001 ETH (low reward)
        task.gas_cost = 3000000000000000  # 0.003 ETH (high gas)
        task.gas_split = 1500000000000000  # 0.0015 ETH (50%)
        db.commit()
        db.close()

        response = client.get(f"/api/tasks/{test_task.id}/gas")

        assert response.status_code == 200
        data = response.json()

        # Agent would lose money in this scenario
        assert data["actual_reward"] < 0
        assert data["actual_reward"] == -500000000000000

    def test_zero_gas_scenario(self, test_task):
        """测试零Gas费用场景（理论情况）"""
        db = TestingSessionLocal()
        task = db.query(Task).filter(Task.id == test_task.id).first()
        task.gas_used = 0
        task.gas_cost = 0
        task.gas_split = 0
        db.commit()
        db.close()

        response = client.get(f"/api/tasks/{test_task.id}/gas")

        assert response.status_code == 200
        data = response.json()

        # Full reward goes to agent
        assert data["actual_reward"] == data["reward"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
