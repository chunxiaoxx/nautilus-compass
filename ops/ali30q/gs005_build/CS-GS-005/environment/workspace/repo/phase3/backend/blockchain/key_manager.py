"""
密钥管理模块
提供安全的私钥存储、加密和轮换功能
支持多种密钥源：环境变量、加密文件、KMS
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import hashlib
import secrets

logger = logging.getLogger(__name__)


class KeySource(Enum):
    """密钥源类型"""
    ENVIRONMENT = "environment"  # 环境变量
    ENCRYPTED_FILE = "encrypted_file"  # 加密文件
    AWS_KMS = "aws_kms"  # AWS KMS
    AZURE_KEY_VAULT = "azure_key_vault"  # Azure Key Vault
    HASHICORP_VAULT = "hashicorp_vault"  # HashiCorp Vault


class KeyRotationPolicy:
    """密钥轮换策略"""

    def __init__(
        self,
        enabled: bool = False,
        rotation_days: int = 90,
        warning_days: int = 7
    ):
        self.enabled = enabled
        self.rotation_days = rotation_days
        self.warning_days = warning_days


class KeyMetadata:
    """密钥元数据"""

    def __init__(
        self,
        key_id: str,
        created_at: datetime,
        last_rotated: Optional[datetime] = None,
        rotation_count: int = 0,
        source: KeySource = KeySource.ENVIRONMENT
    ):
        self.key_id = key_id
        self.created_at = created_at
        self.last_rotated = last_rotated or created_at
        self.rotation_count = rotation_count
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key_id": self.key_id,
            "created_at": self.created_at.isoformat(),
            "last_rotated": self.last_rotated.isoformat(),
            "rotation_count": self.rotation_count,
            "source": self.source.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyMetadata':
        """从字典创建"""
        return cls(
            key_id=data["key_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_rotated=datetime.fromisoformat(data["last_rotated"]),
            rotation_count=data["rotation_count"],
            source=KeySource(data["source"])
        )


class KeyEncryption:
    """密钥加密工具"""

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """从密码派生加密密钥"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

    @staticmethod
    def encrypt_key(private_key: str, password: str) -> Dict[str, str]:
        """
        加密私钥

        Args:
            private_key: 原始私钥
            password: 加密密码

        Returns:
            包含加密数据的字典
        """
        try:
            from cryptography.fernet import Fernet
            import base64

            # 生成盐值
            salt = secrets.token_bytes(32)

            # 派生密钥
            key = KeyEncryption.derive_key(password, salt)

            # 使用Fernet加密
            fernet_key = base64.urlsafe_b64encode(key)
            fernet = Fernet(fernet_key)

            # 加密私钥
            encrypted_data = fernet.encrypt(private_key.encode())

            return {
                "encrypted_key": base64.b64encode(encrypted_data).decode(),
                "salt": base64.b64encode(salt).decode(),
                "algorithm": "fernet-pbkdf2"
            }

        except ImportError:
            logger.error("cryptography library not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to encrypt key: {e}")
            raise

    @staticmethod
    def decrypt_key(encrypted_data: Dict[str, str], password: str) -> str:
        """
        解密私钥

        Args:
            encrypted_data: 加密数据字典
            password: 解密密码

        Returns:
            解密后的私钥
        """
        try:
            from cryptography.fernet import Fernet
            import base64

            # 解码数据
            encrypted_key = base64.b64decode(encrypted_data["encrypted_key"])
            salt = base64.b64decode(encrypted_data["salt"])

            # 派生密钥
            key = KeyEncryption.derive_key(password, salt)

            # 使用Fernet解密
            fernet_key = base64.urlsafe_b64encode(key)
            fernet = Fernet(fernet_key)

            # 解密私钥
            decrypted_data = fernet.decrypt(encrypted_key)

            return decrypted_data.decode()

        except Exception as e:
            logger.error(f"Failed to decrypt key: {e}")
            raise


class KeyManager:
    """密钥管理器"""

    def __init__(
        self,
        key_source: KeySource = KeySource.ENVIRONMENT,
        rotation_policy: Optional[KeyRotationPolicy] = None,
        key_file_path: Optional[str] = None,
        encryption_password: Optional[str] = None
    ):
        """
        初始化密钥管理器

        Args:
            key_source: 密钥源类型
            rotation_policy: 密钥轮换策略
            key_file_path: 密钥文件路径（用于加密文件源）
            encryption_password: 加密密码（用于加密文件源）
        """
        self.key_source = key_source
        self.rotation_policy = rotation_policy or KeyRotationPolicy()
        self.key_file_path = key_file_path
        self.encryption_password = encryption_password

        self._private_key: Optional[str] = None
        self._metadata: Optional[KeyMetadata] = None

        # 加载密钥
        self._load_key()

    def _load_key(self):
        """加载私钥"""
        try:
            if self.key_source == KeySource.ENVIRONMENT:
                self._load_from_environment()
            elif self.key_source == KeySource.ENCRYPTED_FILE:
                self._load_from_encrypted_file()
            elif self.key_source == KeySource.AWS_KMS:
                self._load_from_aws_kms()
            elif self.key_source == KeySource.AZURE_KEY_VAULT:
                self._load_from_azure_key_vault()
            elif self.key_source == KeySource.HASHICORP_VAULT:
                self._load_from_hashicorp_vault()
            else:
                raise ValueError(f"Unsupported key source: {self.key_source}")

            # 检查密钥轮换
            if self.rotation_policy.enabled:
                self._check_rotation_needed()

        except Exception as e:
            logger.error(f"Failed to load key: {e}")
            raise

    def _load_from_environment(self):
        """从环境变量加载密钥"""
        private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY", "")

        if not private_key:
            logger.warning("BLOCKCHAIN_PRIVATE_KEY not set in environment")
            return

        self._private_key = private_key

        # 创建元数据
        self._metadata = KeyMetadata(
            key_id="env_key",
            created_at=datetime.now(),
            source=KeySource.ENVIRONMENT
        )

        logger.info("Private key loaded from environment variable")

    def _load_from_encrypted_file(self):
        """从加密文件加载密钥"""
        if not self.key_file_path:
            raise ValueError("key_file_path is required for encrypted file source")

        if not self.encryption_password:
            raise ValueError("encryption_password is required for encrypted file source")

        key_path = Path(self.key_file_path)

        if not key_path.exists():
            logger.warning(f"Key file not found: {self.key_file_path}")
            return

        try:
            # 读取加密文件
            with open(key_path, 'r') as f:
                data = json.load(f)

            # 解密私钥
            self._private_key = KeyEncryption.decrypt_key(
                data["encrypted_key"],
                self.encryption_password
            )

            # 加载元数据
            if "metadata" in data:
                self._metadata = KeyMetadata.from_dict(data["metadata"])
            else:
                self._metadata = KeyMetadata(
                    key_id="file_key",
                    created_at=datetime.now(),
                    source=KeySource.ENCRYPTED_FILE
                )

            logger.info(f"Private key loaded from encrypted file: {self.key_file_path}")

        except Exception as e:
            logger.error(f"Failed to load key from encrypted file: {e}")
            raise

    def _load_from_aws_kms(self):
        """从AWS KMS加载密钥"""
        try:
            import boto3
            from botocore.exceptions import ClientError

            # 获取KMS配置
            kms_key_id = os.getenv("AWS_KMS_KEY_ID")
            region_name = os.getenv("AWS_REGION", "us-east-1")

            if not kms_key_id:
                raise ValueError("AWS_KMS_KEY_ID not set")

            # 创建KMS客户端
            kms_client = boto3.client('kms', region_name=region_name)

            # 从环境变量获取加密的私钥
            encrypted_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY_ENCRYPTED")

            if not encrypted_key:
                raise ValueError("BLOCKCHAIN_PRIVATE_KEY_ENCRYPTED not set")

            # 解密私钥
            import base64
            response = kms_client.decrypt(
                CiphertextBlob=base64.b64decode(encrypted_key),
                KeyId=kms_key_id
            )

            self._private_key = response['Plaintext'].decode()

            # 创建元数据
            self._metadata = KeyMetadata(
                key_id=kms_key_id,
                created_at=datetime.now(),
                source=KeySource.AWS_KMS
            )

            logger.info("Private key loaded from AWS KMS")

        except ImportError:
            logger.error("boto3 library not installed")
            raise
        except ClientError as e:
            logger.error(f"AWS KMS error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load key from AWS KMS: {e}")
            raise

    def _load_from_azure_key_vault(self):
        """从Azure Key Vault加载密钥"""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential

            # 获取Key Vault配置
            vault_url = os.getenv("AZURE_KEY_VAULT_URL")
            secret_name = os.getenv("AZURE_KEY_VAULT_SECRET_NAME", "blockchain-private-key")

            if not vault_url:
                raise ValueError("AZURE_KEY_VAULT_URL not set")

            # 创建客户端
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)

            # 获取密钥
            secret = client.get_secret(secret_name)
            self._private_key = secret.value

            # 创建元数据
            self._metadata = KeyMetadata(
                key_id=secret_name,
                created_at=datetime.now(),
                source=KeySource.AZURE_KEY_VAULT
            )

            logger.info("Private key loaded from Azure Key Vault")

        except ImportError:
            logger.error("azure-keyvault-secrets library not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to load key from Azure Key Vault: {e}")
            raise

    def _load_from_hashicorp_vault(self):
        """从HashiCorp Vault加载密钥"""
        try:
            import hvac

            # 获取Vault配置
            vault_url = os.getenv("VAULT_ADDR")
            vault_token = os.getenv("VAULT_TOKEN")
            secret_path = os.getenv("VAULT_SECRET_PATH", "secret/blockchain/private-key")

            if not vault_url:
                raise ValueError("VAULT_ADDR not set")

            if not vault_token:
                raise ValueError("VAULT_TOKEN not set")

            # 创建客户端
            client = hvac.Client(url=vault_url, token=vault_token)

            if not client.is_authenticated():
                raise ValueError("Failed to authenticate with Vault")

            # 读取密钥
            secret = client.secrets.kv.v2.read_secret_version(path=secret_path)
            self._private_key = secret['data']['data']['private_key']

            # 创建元数据
            self._metadata = KeyMetadata(
                key_id=secret_path,
                created_at=datetime.now(),
                source=KeySource.HASHICORP_VAULT
            )

            logger.info("Private key loaded from HashiCorp Vault")

        except ImportError:
            logger.error("hvac library not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to load key from HashiCorp Vault: {e}")
            raise

    def _check_rotation_needed(self):
        """检查是否需要轮换密钥"""
        if not self._metadata:
            return

        days_since_rotation = (datetime.now() - self._metadata.last_rotated).days

        if days_since_rotation >= self.rotation_policy.rotation_days:
            logger.warning(
                f"Key rotation required! Last rotated {days_since_rotation} days ago"
            )
        elif days_since_rotation >= (self.rotation_policy.rotation_days - self.rotation_policy.warning_days):
            logger.warning(
                f"Key rotation recommended. Last rotated {days_since_rotation} days ago"
            )

    def get_private_key(self) -> Optional[str]:
        """
        获取私钥

        Returns:
            私钥字符串，如果未加载返回None
        """
        if not self._private_key:
            logger.warning("Private key not loaded")
            return None

        return self._private_key

    def get_metadata(self) -> Optional[KeyMetadata]:
        """
        获取密钥元数据

        Returns:
            密钥元数据，如果未加载返回None
        """
        return self._metadata

    def save_encrypted_key(self, private_key: str, output_path: str):
        """
        保存加密的私钥到文件

        Args:
            private_key: 原始私钥
            output_path: 输出文件路径
        """
        if not self.encryption_password:
            raise ValueError("encryption_password is required")

        try:
            # 加密私钥
            encrypted_data = KeyEncryption.encrypt_key(private_key, self.encryption_password)

            # 创建元数据
            metadata = KeyMetadata(
                key_id="file_key",
                created_at=datetime.now(),
                source=KeySource.ENCRYPTED_FILE
            )

            # 保存到文件
            output = {
                "encrypted_key": encrypted_data,
                "metadata": metadata.to_dict()
            }

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w') as f:
                json.dump(output, f, indent=2)

            logger.info(f"Encrypted key saved to: {output_path}")

        except Exception as e:
            logger.error(f"Failed to save encrypted key: {e}")
            raise

    def rotate_key(self, new_private_key: str):
        """
        轮换密钥

        Args:
            new_private_key: 新的私钥
        """
        try:
            # 备份旧密钥（如果是文件源）
            if self.key_source == KeySource.ENCRYPTED_FILE and self.key_file_path:
                backup_path = f"{self.key_file_path}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                key_path = Path(self.key_file_path)
                if key_path.exists():
                    import shutil
                    shutil.copy2(key_path, backup_path)
                    logger.info(f"Old key backed up to: {backup_path}")

            # 更新私钥
            old_key = self._private_key
            self._private_key = new_private_key

            # 更新元数据
            if self._metadata:
                self._metadata.last_rotated = datetime.now()
                self._metadata.rotation_count += 1

            # 如果是文件源，保存新密钥
            if self.key_source == KeySource.ENCRYPTED_FILE and self.key_file_path:
                self.save_encrypted_key(new_private_key, self.key_file_path)

            logger.info("Key rotated successfully")

        except Exception as e:
            # 回滚
            self._private_key = old_key
            logger.error(f"Failed to rotate key: {e}")
            raise

    def validate_key(self) -> bool:
        """
        验证私钥格式

        Returns:
            是否有效
        """
        if not self._private_key:
            return False

        try:
            # 检查是否为有效的以太坊私钥
            if not self._private_key.startswith('0x'):
                test_key = '0x' + self._private_key
            else:
                test_key = self._private_key

            # 检查长度（64个十六进制字符 + 0x前缀）
            if len(test_key) != 66:
                return False

            # 尝试转换为整数（验证是否为有效的十六进制）
            int(test_key, 16)

            return True

        except (ValueError, TypeError):
            return False

    def get_public_address(self) -> Optional[str]:
        """
        从私钥获取公钥地址

        Returns:
            以太坊地址，如果失败返回None
        """
        if not self._private_key:
            return None

        try:
            from web3 import Web3

            # 确保私钥格式正确
            if not self._private_key.startswith('0x'):
                private_key = '0x' + self._private_key
            else:
                private_key = self._private_key

            # 从私钥获取账户
            account = Web3().eth.account.from_key(private_key)
            return account.address

        except Exception as e:
            logger.error(f"Failed to get public address: {e}")
            return None

    def mask_key(self, key: str) -> str:
        """
        遮蔽密钥用于日志输出

        Args:
            key: 原始密钥

        Returns:
            遮蔽后的密钥
        """
        if not key:
            return "None"

        if len(key) <= 10:
            return "***"

        return f"{key[:6]}...{key[-4:]}"


# 全局密钥管理器实例
_key_manager: Optional[KeyManager] = None


def get_key_manager(
    key_source: Optional[KeySource] = None,
    rotation_policy: Optional[KeyRotationPolicy] = None,
    key_file_path: Optional[str] = None,
    encryption_password: Optional[str] = None
) -> KeyManager:
    """
    获取密钥管理器实例（单例）

    Args:
        key_source: 密钥源类型
        rotation_policy: 密钥轮换策略
        key_file_path: 密钥文件路径
        encryption_password: 加密密码

    Returns:
        密钥管理器实例
    """
    global _key_manager

    if _key_manager is None:
        # 从环境变量读取配置
        if key_source is None:
            source_str = os.getenv("KEY_SOURCE", "environment")
            key_source = KeySource(source_str)

        if key_file_path is None:
            key_file_path = os.getenv("KEY_FILE_PATH")

        if encryption_password is None:
            encryption_password = os.getenv("KEY_ENCRYPTION_PASSWORD")

        # 创建轮换策略
        if rotation_policy is None:
            rotation_enabled = os.getenv("KEY_ROTATION_ENABLED", "false").lower() == "true"
            rotation_days = int(os.getenv("KEY_ROTATION_DAYS", "90"))
            warning_days = int(os.getenv("KEY_ROTATION_WARNING_DAYS", "7"))

            rotation_policy = KeyRotationPolicy(
                enabled=rotation_enabled,
                rotation_days=rotation_days,
                warning_days=warning_days
            )

        _key_manager = KeyManager(
            key_source=key_source,
            rotation_policy=rotation_policy,
            key_file_path=key_file_path,
            encryption_password=encryption_password
        )

    return _key_manager


def init_key_manager(**kwargs) -> KeyManager:
    """
    初始化密钥管理器

    Args:
        **kwargs: 传递给get_key_manager的参数

    Returns:
        密钥管理器实例
    """
    return get_key_manager(**kwargs)


if __name__ == "__main__":
    """测试密钥管理器"""
    print("🔐 Testing Key Manager...")

    try:
        # 测试环境变量源
        print("\n1. Testing environment variable source...")
        manager = KeyManager(key_source=KeySource.ENVIRONMENT)

        if manager.get_private_key():
            print(f"✅ Key loaded: {manager.mask_key(manager.get_private_key())}")
            print(f"✅ Valid: {manager.validate_key()}")

            address = manager.get_public_address()
            if address:
                print(f"✅ Address: {address}")
        else:
            print("⚠️ No key found in environment")

        # 测试加密文件保存
        print("\n2. Testing encrypted file save...")
        test_key = "0x" + secrets.token_hex(32)
        test_password = "test_password_123"

        file_manager = KeyManager(
            key_source=KeySource.ENCRYPTED_FILE,
            key_file_path="./test_key.json",
            encryption_password=test_password
        )

        file_manager.save_encrypted_key(test_key, "./test_key.json")
        print("✅ Encrypted key saved")

        # 测试加密文件加载
        print("\n3. Testing encrypted file load...")
        load_manager = KeyManager(
            key_source=KeySource.ENCRYPTED_FILE,
            key_file_path="./test_key.json",
            encryption_password=test_password
        )

        loaded_key = load_manager.get_private_key()
        if loaded_key == test_key:
            print("✅ Key loaded and verified")
        else:
            print("❌ Key mismatch")

        # 清理测试文件
        import os
        if os.path.exists("./test_key.json"):
            os.remove("./test_key.json")
            print("✅ Test file cleaned up")

        print("\n✅ Key Manager test successful!")

    except Exception as e:
        print(f"\n❌ Key Manager test failed: {e}")
        import traceback
        traceback.print_exc()
