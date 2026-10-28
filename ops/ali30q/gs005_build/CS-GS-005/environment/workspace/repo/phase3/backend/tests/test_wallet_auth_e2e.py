"""
端到端测试：钱包认证完整流程
测试钱包注册、登录、Token验证等完整流程
"""
import pytest
import requests
import time
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

# 配置
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

# 测试钱包
def create_test_wallet():
    """创建测试钱包"""
    account = Account.create()
    return {
        "address": account.address,
        "private_key": account.key.hex()
    }

class TestWalletAuthE2E:
    """钱包认证端到端测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.wallet = create_test_wallet()
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        yield
        self.session.close()

    def test_01_get_nonce_success(self):
        """测试1: 获取nonce成功"""
        print(f"\n[测试1] 获取nonce - 钱包地址: {self.wallet['address']}")

        response = self.session.get(
            f"{self.base_url}/api/auth/nonce",
            params={"wallet_address": self.wallet['address']},
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200, f"状态码错误: {response.status_code}"
        data = response.json()

        assert "nonce" in data, "响应缺少nonce字段"
        assert "message" in data, "响应缺少message字段"
        assert len(data["nonce"]) == 64, f"nonce长度错误: {len(data['nonce'])}"
        assert "Sign this message to authenticate with Nautilus:" in data["message"]

        self.nonce = data["nonce"]
        self.message = data["message"]

        print(f"✅ Nonce获取成功: {self.nonce[:16]}...")
        print(f"✅ Message: {self.message}")

    def test_02_wallet_register_success(self):
        """测试2: 钱包注册成功"""
        print(f"\n[测试2] 钱包注册")

        # 获取nonce
        response = self.session.get(
            f"{self.base_url}/api/auth/nonce",
            params={"wallet_address": self.wallet['address']},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        message = data["message"]

        # 签名
        w3 = Web3()
        message_hash = encode_defunct(text=message)
        signed_message = w3.eth.account.sign_message(
            message_hash,
            private_key=self.wallet['private_key']
        )
        signature = signed_message.signature.hex()

        print(f"✅ 签名生成: {signature[:32]}...")

        # 注册
        register_data = {
            "wallet_address": self.wallet['address'],
            "signature": signature,
            "message": message,
            "username": f"test_user_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com"
        }

        response = self.session.post(
            f"{self.base_url}/api/auth/wallet-register",
            json=register_data,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200, f"注册失败: {response.text}"
        data = response.json()

        assert "access_token" in data, "响应缺少access_token"
        assert "token_type" in data, "响应缺少token_type"
        assert data["token_type"] == "bearer"

        self.access_token = data["access_token"]

        print(f"✅ 注册成功")
        print(f"✅ Token: {self.access_token[:32]}...")

    def test_03_verify_token_and_get_user_info(self):
        """测试3: 验证Token并获取用户信息"""
        print(f"\n[测试3] 验证Token")

        # 先注册获取token
        self.test_02_wallet_register_success()

        # 使用token获取用户信息
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.get(
            f"{self.base_url}/api/auth/me",
            headers=headers,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200, f"获取用户信息失败: {response.text}"
        user_data = response.json()

        assert "id" in user_data
        assert "username" in user_data
        assert "wallet_address" in user_data
        assert user_data["wallet_address"].lower() == self.wallet['address'].lower()

        print(f"✅ Token验证成功")
        print(f"✅ 用户ID: {user_data['id']}")
        print(f"✅ 用户名: {user_data['username']}")
        print(f"✅ 钱包地址: {user_data['wallet_address']}")

    def test_04_wallet_login_success(self):
        """测试4: 钱包登录成功"""
        print(f"\n[测试4] 钱包登录")

        # 先注册
        self.test_02_wallet_register_success()

        # 获取新的nonce
        response = self.session.get(
            f"{self.base_url}/api/auth/nonce",
            params={"wallet_address": self.wallet['address']},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        message = data["message"]

        # 签名
        w3 = Web3()
        message_hash = encode_defunct(text=message)
        signed_message = w3.eth.account.sign_message(
            message_hash,
            private_key=self.wallet['private_key']
        )
        signature = signed_message.signature.hex()

        # 登录
        login_data = {
            "wallet_address": self.wallet['address'],
            "signature": signature,
            "message": message
        }

        response = self.session.post(
            f"{self.base_url}/api/auth/wallet-login",
            json=login_data,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200, f"登录失败: {response.text}"
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data

        print(f"✅ 登录成功")
        print(f"✅ Token: {data['access_token'][:32]}...")

    def test_05_error_invalid_signature(self):
        """测试5: 错误场景 - 无效签名"""
        print(f"\n[测试5] 错误场景 - 无效签名")

        # 获取nonce
        response = self.session.get(
            f"{self.base_url}/api/auth/nonce",
            params={"wallet_address": self.wallet['address']},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        message = data["message"]

        # 使用错误的签名
        invalid_signature = "0x" + "0" * 130

        register_data = {
            "wallet_address": self.wallet['address'],
            "signature": invalid_signature,
            "message": message
        }

        response = self.session.post(
            f"{self.base_url}/api/auth/wallet-register",
            json=register_data,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code in [400, 401], f"应该返回错误状态码"

        print(f"✅ 无效签名被正确拒绝")

    def test_06_error_wallet_not_registered(self):
        """测试6: 错误场景 - 钱包未注册"""
        print(f"\n[测试6] 错误场景 - 钱包未注册")

        # 创建新钱包（未注册）
        new_wallet = create_test_wallet()

        # 获取nonce
        response = self.session.get(
            f"{self.base_url}/api/auth/nonce",
            params={"wallet_address": new_wallet['address']},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        message = data["message"]

        # 签名
        w3 = Web3()
        message_hash = encode_defunct(text=message)
        signed_message = w3.eth.account.sign_message(
            message_hash,
            private_key=new_wallet['private_key']
        )
        signature = signed_message.signature.hex()

        # 尝试登录（未注册）
        login_data = {
            "wallet_address": new_wallet['address'],
            "signature": signature,
            "message": message
        }

        response = self.session.post(
            f"{self.base_url}/api/auth/wallet-login",
            json=login_data,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 404, f"应该返回404"

        print(f"✅ 未注册钱包登录被正确拒绝")

    def test_07_error_invalid_token(self):
        """测试7: 错误场景 - 无效Token"""
        print(f"\n[测试7] 错误场景 - 无效Token")

        invalid_token = "invalid_token_12345"
        headers = {"Authorization": f"Bearer {invalid_token}"}

        response = self.session.get(
            f"{self.base_url}/api/auth/me",
            headers=headers,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 401, f"应该返回401"

        print(f"✅ 无效Token被正确拒绝")

    def test_08_complete_flow(self):
        """测试8: 完整流程测试"""
        print(f"\n[测试8] 完整流程测试")

        # 1. 获取nonce
        print("步骤1: 获取nonce...")
        response = self.session.get(
            f"{self.base_url}/api/auth/nonce",
            params={"wallet_address": self.wallet['address']},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        nonce_data = response.json()
        print(f"✅ Nonce: {nonce_data['nonce'][:16]}...")

        # 2. 签名
        print("步骤2: 生成签名...")
        w3 = Web3()
        message_hash = encode_defunct(text=nonce_data['message'])
        signed_message = w3.eth.account.sign_message(
            message_hash,
            private_key=self.wallet['private_key']
        )
        signature = signed_message.signature.hex()
        print(f"✅ 签名: {signature[:32]}...")

        # 3. 注册
        print("步骤3: 注册...")
        register_data = {
            "wallet_address": self.wallet['address'],
            "signature": signature,
            "message": nonce_data['message'],
            "username": f"e2e_test_{int(time.time())}",
            "email": f"e2e_{int(time.time())}@example.com"
        }
        response = self.session.post(
            f"{self.base_url}/api/auth/wallet-register",
            json=register_data,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        register_result = response.json()
        token = register_result['access_token']
        print(f"✅ 注册成功，Token: {token[:32]}...")

        # 4. 验证Token
        print("步骤4: 验证Token...")
        headers = {"Authorization": f"Bearer {token}"}
        response = self.session.get(
            f"{self.base_url}/api/auth/me",
            headers=headers,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        user_info = response.json()
        print(f"✅ 用户信息: {user_info['username']}")

        # 5. 登出（清除token）
        print("步骤5: 登出...")
        # 前端清除token即可
        print(f"✅ 登出成功")

        # 6. 重新登录
        print("步骤6: 重新登录...")
        response = self.session.get(
            f"{self.base_url}/api/auth/nonce",
            params={"wallet_address": self.wallet['address']},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        new_nonce_data = response.json()

        message_hash = encode_defunct(text=new_nonce_data['message'])
        signed_message = w3.eth.account.sign_message(
            message_hash,
            private_key=self.wallet['private_key']
        )
        new_signature = signed_message.signature.hex()

        login_data = {
            "wallet_address": self.wallet['address'],
            "signature": new_signature,
            "message": new_nonce_data['message']
        }
        response = self.session.post(
            f"{self.base_url}/api/auth/wallet-login",
            json=login_data,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        login_result = response.json()
        print(f"✅ 重新登录成功，Token: {login_result['access_token'][:32]}...")

        print(f"\n✅ 完整流程测试通过！")


if __name__ == "__main__":
    print("=" * 60)
    print("钱包认证端到端测试")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s"])
