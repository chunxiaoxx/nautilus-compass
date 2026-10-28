"""
Locust压力测试脚本 - Nautilus Backend API

测试关键API端点的性能和稳定性。

运行方式:
    locust -f locustfile.py --host=http://localhost:8000

或使用Web界面:
    locust -f locustfile.py --host=http://localhost:8000 --web-host=0.0.0.0 --web-port=8089
"""

from locust import HttpUser, task, between, SequentialTaskSet
import random
import json
import logging

logger = logging.getLogger(__name__)


class UserBehavior(SequentialTaskSet):
    """模拟真实用户行为的任务序列"""

    def on_start(self):
        """初始化：注册用户并获取token"""
        self.username = f"loadtest_user_{random.randint(1000, 9999)}"
        self.password = "TestPassword123!"
        self.email = f"{self.username}@loadtest.com"
        self.wallet_address = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
        self.token = None
        self.agent_id = None
        self.api_key = None
        self.task_id = None

        # 注册用户
        self.register_user()

        # 注册Agent
        self.register_agent()

    def register_user(self):
        """注册新用户"""
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": self.username,
                "email": self.email,
                "password": self.password,
                "wallet_address": self.wallet_address
            },
            name="/api/auth/register"
        )

        if response.status_code == 201:
            data = response.json()
            self.token = data.get("access_token")
            logger.info(f"User registered: {self.username}")
        else:
            logger.error(f"Failed to register user: {response.status_code}")

    def register_agent(self):
        """注册Agent"""
        if not self.token:
            return

        response = self.client.post(
            "/api/agents",
            json={
                "name": f"Agent_{self.username}",
                "description": "Load test agent",
                "specialties": ["data_processing", "computation"]
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/agents"
        )

        if response.status_code == 201:
            data = response.json()
            self.agent_id = data.get("agent", {}).get("agent_id")
            self.api_key = data.get("api_key")
            logger.info(f"Agent registered: {self.agent_id}")
        else:
            logger.error(f"Failed to register agent: {response.status_code}")

    @task(1)
    def view_tasks(self):
        """查看任务列表"""
        self.client.get(
            "/api/tasks",
            params={"limit": 20},
            name="/api/tasks (list)"
        )

    @task(2)
    def view_agents(self):
        """查看Agent列表"""
        self.client.get(
            "/api/agents",
            params={"limit": 20},
            name="/api/agents (list)"
        )

    @task(3)
    def create_task(self):
        """创建新任务"""
        if not self.token:
            return

        response = self.client.post(
            "/api/tasks",
            json={
                "description": f"Load test task {random.randint(1000, 9999)}",
                "input_data": "Test input data",
                "expected_output": "Test expected output",
                "reward": random.randint(1000000, 10000000),  # Wei
                "task_type": random.choice(["data_processing", "computation", "verification"]),
                "timeout": 3600
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/tasks (create)"
        )

        if response.status_code == 201:
            data = response.json()
            self.task_id = data.get("id")
            logger.info(f"Task created: {self.task_id}")

    @task(2)
    def view_task_detail(self):
        """查看任务详情"""
        if not self.task_id:
            # 获取一个随机任务
            response = self.client.get("/api/tasks", params={"limit": 1})
            if response.status_code == 200:
                tasks = response.json()
                if tasks:
                    self.task_id = tasks[0].get("id")

        if self.task_id:
            self.client.get(
                f"/api/tasks/{self.task_id}",
                name="/api/tasks/{id} (detail)"
            )

    @task(1)
    def check_reward_balance(self):
        """查看奖励余额"""
        if not self.api_key:
            return

        self.client.get(
            "/api/rewards/balance",
            headers={"X-API-Key": self.api_key},
            name="/api/rewards/balance"
        )

    @task(1)
    def view_reward_history(self):
        """查看奖励历史"""
        if not self.api_key:
            return

        self.client.get(
            "/api/rewards/history",
            params={"limit": 20},
            headers={"X-API-Key": self.api_key},
            name="/api/rewards/history"
        )

    @task(1)
    def view_agent_detail(self):
        """查看Agent详情"""
        if not self.agent_id:
            # 获取一个随机Agent
            response = self.client.get("/api/agents", params={"limit": 1})
            if response.status_code == 200:
                agents = response.json()
                if agents:
                    self.agent_id = agents[0].get("agent_id")

        if self.agent_id:
            self.client.get(
                f"/api/agents/{self.agent_id}",
                name="/api/agents/{id} (detail)"
            )

    @task(1)
    def view_current_user(self):
        """查看当前用户信息"""
        if not self.token:
            return

        self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/auth/me"
        )


class AgentBehavior(SequentialTaskSet):
    """模拟Agent行为的任务序列"""

    def on_start(self):
        """初始化：创建用户和Agent"""
        self.username = f"agent_user_{random.randint(1000, 9999)}"
        self.password = "TestPassword123!"
        self.email = f"{self.username}@loadtest.com"
        self.wallet_address = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
        self.token = None
        self.agent_id = None
        self.api_key = None
        self.accepted_task_id = None

        # 注册并获取API Key
        self.setup_agent()

    def setup_agent(self):
        """设置Agent"""
        # 注册用户
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": self.username,
                "email": self.email,
                "password": self.password,
                "wallet_address": self.wallet_address
            }
        )

        if response.status_code == 201:
            self.token = response.json().get("access_token")

            # 注册Agent
            response = self.client.post(
                "/api/agents",
                json={
                    "name": f"Agent_{self.username}",
                    "description": "Load test agent",
                    "specialties": ["data_processing"]
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 201:
                data = response.json()
                self.agent_id = data.get("agent", {}).get("agent_id")
                self.api_key = data.get("api_key")

    @task(3)
    def find_open_tasks(self):
        """查找开放任务"""
        self.client.get(
            "/api/tasks",
            params={"status": "open", "limit": 10},
            name="/api/tasks (find open)"
        )

    @task(1)
    def accept_task(self):
        """接受任务"""
        if not self.api_key:
            return

        # 获取一个开放任务
        response = self.client.get(
            "/api/tasks",
            params={"status": "open", "limit": 1}
        )

        if response.status_code == 200:
            tasks = response.json()
            if tasks:
                task_id = tasks[0].get("id")

                # 接受任务
                response = self.client.post(
                    f"/api/tasks/{task_id}/accept",
                    headers={"X-API-Key": self.api_key},
                    name="/api/tasks/{id}/accept"
                )

                if response.status_code == 200:
                    self.accepted_task_id = task_id
                    logger.info(f"Task accepted: {task_id}")

    @task(1)
    def submit_task(self):
        """提交任务结果"""
        if not self.api_key or not self.accepted_task_id:
            return

        self.client.post(
            f"/api/tasks/{self.accepted_task_id}/submit",
            json={"result": f"Task result {random.randint(1000, 9999)}"},
            headers={"X-API-Key": self.api_key},
            name="/api/tasks/{id}/submit"
        )

        self.accepted_task_id = None

    @task(2)
    def check_balance(self):
        """检查余额"""
        if not self.api_key:
            return

        self.client.get(
            "/api/rewards/balance",
            headers={"X-API-Key": self.api_key},
            name="/api/rewards/balance (agent)"
        )


class NautilusUser(HttpUser):
    """普通用户"""
    tasks = [UserBehavior]
    wait_time = between(1, 3)  # 用户操作间隔1-3秒
    weight = 3  # 权重：普通用户占75%


class NautilusAgent(HttpUser):
    """Agent用户"""
    tasks = [AgentBehavior]
    wait_time = between(2, 5)  # Agent操作间隔2-5秒
    weight = 1  # 权重：Agent占25%
