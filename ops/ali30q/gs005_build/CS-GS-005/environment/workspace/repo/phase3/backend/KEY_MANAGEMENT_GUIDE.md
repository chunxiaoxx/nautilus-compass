# 密钥管理指南

## 概述

本指南介绍 Nautilus Phase 3 Backend 的私钥管理系统，包括多种密钥存储方案、安全最佳实践和迁移指南。

## 目录

1. [密钥管理方案对比](#密钥管理方案对比)
2. [快速开始](#快速开始)
3. [配置方式](#配置方式)
4. [密钥轮换](#密钥轮换)
5. [迁移指南](#迁移指南)
6. [安全最佳实践](#安全最佳实践)
7. [故障排查](#故障排查)

---

## 密钥管理方案对比

### 方案评估

| 方案 | 安全等级 | 复杂度 | 成本 | 推荐场景 |
|------|---------|--------|------|---------|
| 环境变量 | ⭐⭐ | 低 | 免费 | 开发环境 |
| 加密文件 | ⭐⭐⭐ | 中 | 免费 | 小型生产环境 |
| AWS KMS | ⭐⭐⭐⭐⭐ | 中 | 付费 | AWS 生产环境 |
| Azure Key Vault | ⭐⭐⭐⭐⭐ | 中 | 付费 | Azure 生产环境 |
| HashiCorp Vault | ⭐⭐⭐⭐⭐ | 高 | 免费/付费 | 企业级多云环境 |

### 方案详细对比

#### 1. 环境变量（默认）
**优点：**
- 简单易用，无需额外配置
- 向后兼容现有系统
- 适合快速开发和测试

**缺点：**
- 安全性较低
- 容易泄露到日志或进程列表
- 无密钥轮换机制

**适用场景：** 开发环境、测试环境

#### 2. 加密文件存储
**优点：**
- 密钥加密存储，提高安全性
- 无需外部服务，部署简单
- 支持密钥轮换和备份

**缺点：**
- 需要管理加密密码
- 文件权限管理复杂
- 不适合分布式环境

**适用场景：** 小型生产环境、单机部署

#### 3. AWS KMS
**优点：**
- 企业级安全性
- 自动密钥轮换
- 审计日志完整
- 与 AWS 服务深度集成

**缺点：**
- 需要 AWS 账户
- 有使用成本
- 依赖 AWS 服务可用性

**适用场景：** AWS 云环境生产部署

#### 4. Azure Key Vault
**优点：**
- 企业级安全性
- 支持 HSM 硬件加密
- 与 Azure 服务集成
- 细粒度访问控制

**缺点：**
- 需要 Azure 账户
- 有使用成本
- 依赖 Azure 服务可用性

**适用场景：** Azure 云环境生产部署

#### 5. HashiCorp Vault
**优点：**
- 多云支持，不绑定特定云平台
- 功能强大，支持动态密钥
- 开源版本免费
- 企业级安全特性

**缺点：**
- 部署和维护复杂
- 需要额外的基础设施
- 学习曲线较陡

**适用场景：** 企业级多云环境、混合云部署

---

## 快速开始

### 方式 1: 环境变量（默认）

最简单的方式，适合开发环境：

```bash
# .env 文件
BLOCKCHAIN_PRIVATE_KEY=0x1234567890abcdef...
```

### 方式 2: 加密文件存储

推荐用于生产环境的简单方案：

```bash
# 1. 生成加密密钥文件
python -c "
from blockchain.key_manager import KeyManager, KeySource
import os

manager = KeyManager(
    key_source=KeySource.ENCRYPTED_FILE,
    key_file_path='./keys/blockchain_key.json',
    encryption_password='your-strong-password'
)

private_key = os.getenv('BLOCKCHAIN_PRIVATE_KEY')
manager.save_encrypted_key(private_key, './keys/blockchain_key.json')
print('✅ Encrypted key saved')
"

# 2. 配置环境变量
# .env 文件
KEY_SOURCE=encrypted_file
KEY_FILE_PATH=/path/to/keys/blockchain_key.json
KEY_ENCRYPTION_PASSWORD=your-strong-password
```

### 方式 3: AWS KMS

适合 AWS 云环境：

```bash
# 1. 在 AWS KMS 中创建密钥
aws kms create-key --description "Nautilus Blockchain Key"

# 2. 加密私钥
aws kms encrypt \
  --key-id alias/nautilus-blockchain \
  --plaintext "0x1234567890abcdef..." \
  --output text \
  --query CiphertextBlob

# 3. 配置环境变量
# .env 文件
KEY_SOURCE=aws_kms
AWS_KMS_KEY_ID=alias/nautilus-blockchain
AWS_REGION=us-east-1
BLOCKCHAIN_PRIVATE_KEY_ENCRYPTED=<base64-encoded-ciphertext>
```

---

## 配置方式

### 环境变量配置

所有配置都通过 `.env` 文件或环境变量设置：

```bash
# 密钥源类型
# 可选值: environment, encrypted_file, aws_kms, azure_key_vault, hashicorp_vault
KEY_SOURCE=environment

# 加密文件配置（当 KEY_SOURCE=encrypted_file 时）
KEY_FILE_PATH=/path/to/encrypted_key.json
KEY_ENCRYPTION_PASSWORD=your-encryption-password

# AWS KMS 配置（当 KEY_SOURCE=aws_kms 时）
AWS_KMS_KEY_ID=your-kms-key-id
AWS_REGION=us-east-1
BLOCKCHAIN_PRIVATE_KEY_ENCRYPTED=base64-encoded-encrypted-key

# Azure Key Vault 配置（当 KEY_SOURCE=azure_key_vault 时）
AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/
AZURE_KEY_VAULT_SECRET_NAME=blockchain-private-key

# HashiCorp Vault 配置（当 KEY_SOURCE=hashicorp_vault 时）
VAULT_ADDR=https://vault.example.com:8200
VAULT_TOKEN=your-vault-token
VAULT_SECRET_PATH=secret/blockchain/private-key

# 密钥轮换策略
KEY_ROTATION_ENABLED=false
KEY_ROTATION_DAYS=90
KEY_ROTATION_WARNING_DAYS=7
```

### 代码中使用

```python
from blockchain.key_manager import get_key_manager

# 获取密钥管理器（自动从环境变量读取配置）
manager = get_key_manager()

# 获取私钥
private_key = manager.get_private_key()

# 获取公钥地址
address = manager.get_public_address()

# 验证密钥
is_valid = manager.validate_key()

# 获取元数据
metadata = manager.get_metadata()
print(f"Key ID: {metadata.key_id}")
print(f"Created: {metadata.created_at}")
print(f"Last Rotated: {metadata.last_rotated}")
```

---

## 密钥轮换

### 为什么需要密钥轮换？

- **降低风险：** 定期更换密钥可以限制密钥泄露的影响范围
- **合规要求：** 许多安全标准要求定期轮换密钥
- **最佳实践：** 密钥轮换是安全管理的基本要求

### 配置密钥轮换

```bash
# .env 文件
KEY_ROTATION_ENABLED=true
KEY_ROTATION_DAYS=90          # 每 90 天轮换一次
KEY_ROTATION_WARNING_DAYS=7   # 提前 7 天警告
```

### 手动轮换密钥

```python
from blockchain.key_manager import get_key_manager

# 获取密钥管理器
manager = get_key_manager()

# 生成新的私钥
import secrets
new_private_key = "0x" + secrets.token_hex(32)

# 轮换密钥
manager.rotate_key(new_private_key)

print("✅ Key rotated successfully")
```

### 自动轮换提醒

系统会在以下情况发出警告：

1. **轮换警告：** 距离上次轮换超过 `KEY_ROTATION_DAYS - KEY_ROTATION_WARNING_DAYS` 天
2. **轮换要求：** 距离上次轮换超过 `KEY_ROTATION_DAYS` 天

警告会记录在日志中：

```
WARNING: Key rotation recommended. Last rotated 83 days ago
WARNING: Key rotation required! Last rotated 90 days ago
```

---

## 迁移指南

### 从环境变量迁移到加密文件

#### 步骤 1: 创建加密密钥文件

```bash
# 运行迁移脚本
python -c "
from blockchain.key_manager import KeyManager, KeySource
import os

# 从环境变量读取当前私钥
current_key = os.getenv('BLOCKCHAIN_PRIVATE_KEY')

if not current_key:
    print('❌ BLOCKCHAIN_PRIVATE_KEY not set')
    exit(1)

# 创建密钥管理器
manager = KeyManager(
    key_source=KeySource.ENCRYPTED_FILE,
    key_file_path='./keys/blockchain_key.json',
    encryption_password=os.getenv('KEY_ENCRYPTION_PASSWORD')
)

# 保存加密密钥
manager.save_encrypted_key(current_key, './keys/blockchain_key.json')
print('✅ Key migrated to encrypted file')
"
```

#### 步骤 2: 更新配置

```bash
# 更新 .env 文件
KEY_SOURCE=encrypted_file
KEY_FILE_PATH=/path/to/keys/blockchain_key.json
KEY_ENCRYPTION_PASSWORD=your-strong-password

# 可选：删除旧的环境变量（确保新配置工作后）
# BLOCKCHAIN_PRIVATE_KEY=...
```

#### 步骤 3: 测试新配置

```bash
# 测试密钥加载
python -c "
from blockchain.key_manager import get_key_manager

manager = get_key_manager()
if manager.get_private_key():
    print('✅ Key loaded successfully')
    print(f'✅ Address: {manager.get_public_address()}')
else:
    print('❌ Failed to load key')
"
```

#### 步骤 4: 设置文件权限

```bash
# 限制密钥文件访问权限
chmod 600 ./keys/blockchain_key.json
chown app_user:app_group ./keys/blockchain_key.json
```

### 从环境变量迁移到 AWS KMS

#### 步骤 1: 创建 KMS 密钥

```bash
# 创建 KMS 密钥
aws kms create-key \
  --description "Nautilus Blockchain Private Key" \
  --key-usage ENCRYPT_DECRYPT

# 创建别名
aws kms create-alias \
  --alias-name alias/nautilus-blockchain \
  --target-key-id <key-id>
```

#### 步骤 2: 加密私钥

```bash
# 从环境变量读取私钥并加密
PRIVATE_KEY=$(grep BLOCKCHAIN_PRIVATE_KEY .env | cut -d '=' -f2)

aws kms encrypt \
  --key-id alias/nautilus-blockchain \
  --plaintext "$PRIVATE_KEY" \
  --output text \
  --query CiphertextBlob > encrypted_key.txt
```

#### 步骤 3: 更新配置

```bash
# 更新 .env 文件
KEY_SOURCE=aws_kms
AWS_KMS_KEY_ID=alias/nautilus-blockchain
AWS_REGION=us-east-1
BLOCKCHAIN_PRIVATE_KEY_ENCRYPTED=$(cat encrypted_key.txt)

# 删除明文私钥
# BLOCKCHAIN_PRIVATE_KEY=...
```

#### 步骤 4: 配置 IAM 权限

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:123456789012:key/*"
    }
  ]
}
```

---

## 安全最佳实践

### 1. 密钥生成

```python
# ✅ 使用安全的随机数生成器
import secrets
private_key = "0x" + secrets.token_hex(32)

# ❌ 不要使用弱随机数生成器
import random
private_key = "0x" + ''.join(random.choices('0123456789abcdef', k=64))  # 不安全！
```

### 2. 密钥存储

- **永远不要** 将私钥硬编码在代码中
- **永远不要** 将私钥提交到版本控制系统
- **永远不要** 在日志中输出完整私钥
- **始终** 使用加密存储或密钥管理服务
- **始终** 限制密钥文件的访问权限（chmod 600）

### 3. 密钥使用

```python
# ✅ 使用 KeyManager
from blockchain.key_manager import get_key_manager

manager = get_key_manager()
private_key = manager.get_private_key()

# ✅ 日志中遮蔽密钥
logger.info(f"Using key: {manager.mask_key(private_key)}")
# 输出: Using key: 0x1234...abcd

# ❌ 不要在日志中输出完整密钥
logger.info(f"Using key: {private_key}")  # 危险！
```

### 4. 密钥轮换

- 定期轮换密钥（建议 90 天）
- 保留旧密钥的备份（用于恢复历史交易）
- 记录密钥轮换历史
- 测试新密钥后再删除旧密钥

### 5. 访问控制

- 使用最小权限原则
- 限制密钥访问的 IP 地址
- 启用多因素认证（MFA）
- 定期审计密钥访问日志

### 6. 备份和恢复

```bash
# 备份加密密钥文件
cp keys/blockchain_key.json keys/blockchain_key.json.backup.$(date +%Y%m%d)

# 加密备份
tar czf - keys/ | gpg --symmetric --cipher-algo AES256 > keys_backup.tar.gz.gpg

# 恢复备份
gpg --decrypt keys_backup.tar.gz.gpg | tar xzf -
```

### 7. 环境隔离

```bash
# 开发环境
KEY_SOURCE=environment
BLOCKCHAIN_PRIVATE_KEY=0x...  # 测试网私钥

# 生产环境
KEY_SOURCE=aws_kms
AWS_KMS_KEY_ID=alias/nautilus-blockchain-prod
```

### 8. 监控和告警

- 监控密钥使用频率
- 设置异常访问告警
- 记录所有密钥操作
- 定期审查访问日志

---

## 故障排查

### 问题 1: 密钥加载失败

**症状：**
```
ERROR: Failed to load key: ...
WARNING: Private key not loaded
```

**解决方案：**

1. 检查环境变量配置：
```bash
# 检查 KEY_SOURCE 是否正确
echo $KEY_SOURCE

# 检查私钥是否设置
echo $BLOCKCHAIN_PRIVATE_KEY | head -c 10
```

2. 验证文件路径和权限：
```bash
# 检查文件是否存在
ls -la $KEY_FILE_PATH

# 检查文件权限
stat $KEY_FILE_PATH
```

3. 测试密钥解密：
```python
from blockchain.key_manager import KeyManager, KeySource

manager = KeyManager(
    key_source=KeySource.ENCRYPTED_FILE,
    key_file_path='./keys/blockchain_key.json',
    encryption_password='your-password'
)

try:
    key = manager.get_private_key()
    print(f"✅ Key loaded: {manager.mask_key(key)}")
except Exception as e:
    print(f"❌ Error: {e}")
```

### 问题 2: 密钥验证失败

**症状：**
```
WARNING: Invalid private key format
```

**解决方案：**

1. 检查密钥格式：
```python
from blockchain.key_manager import get_key_manager

manager = get_key_manager()
is_valid = manager.validate_key()

if not is_valid:
    print("❌ Invalid key format")
    print("Key should be 64 hex characters with optional 0x prefix")
```

2. 修复密钥格式：
```python
# 添加 0x 前缀
if not private_key.startswith('0x'):
    private_key = '0x' + private_key

# 验证长度
if len(private_key) != 66:
    print(f"❌ Invalid length: {len(private_key)} (expected 66)")
```

### 问题 3: KMS 访问被拒绝

**症状：**
```
ERROR: AWS KMS error: AccessDeniedException
```

**解决方案：**

1. 检查 IAM 权限：
```bash
# 测试 KMS 访问
aws kms describe-key --key-id alias/nautilus-blockchain
```

2. 验证 IAM 角色：
```bash
# 检查当前身份
aws sts get-caller-identity

# 检查附加的策略
aws iam list-attached-role-policies --role-name YourRoleName
```

3. 添加必要权限：
```json
{
  "Effect": "Allow",
  "Action": [
    "kms:Decrypt",
    "kms:DescribeKey"
  ],
  "Resource": "arn:aws:kms:*:*:key/*"
}
```

### 问题 4: 密钥轮换失败

**症状：**
```
ERROR: Failed to rotate key: ...
```

**解决方案：**

1. 检查备份：
```bash
# 查看备份文件
ls -la keys/*.backup.*
```

2. 手动恢复：
```bash
# 恢复最新备份
cp keys/blockchain_key.json.backup.20260226 keys/blockchain_key.json
```

3. 验证新密钥：
```python
from blockchain.key_manager import get_key_manager

manager = get_key_manager()

# 验证密钥
if manager.validate_key():
    print("✅ Key is valid")

# 测试签名
address = manager.get_public_address()
print(f"✅ Address: {address}")
```

### 问题 5: 加密密码错误

**症状：**
```
ERROR: Failed to decrypt key: Invalid token
```

**解决方案：**

1. 验证密码：
```bash
# 检查环境变量
echo $KEY_ENCRYPTION_PASSWORD
```

2. 重置密码（需要原始私钥）：
```python
from blockchain.key_manager import KeyManager, KeySource

# 使用新密码重新加密
manager = KeyManager(
    key_source=KeySource.ENCRYPTED_FILE,
    key_file_path='./keys/blockchain_key.json',
    encryption_password='new-password'
)

# 保存（需要原始私钥）
original_key = "0x..."  # 从备份或其他来源获取
manager.save_encrypted_key(original_key, './keys/blockchain_key.json')
```

---

## 附录

### A. 依赖库安装

```bash
# 基础依赖（已包含在 requirements.txt）
pip install web3 cryptography

# AWS KMS 支持
pip install boto3

# Azure Key Vault 支持
pip install azure-keyvault-secrets azure-identity

# HashiCorp Vault 支持
pip install hvac
```

### B. 密钥管理工具脚本

创建 `tools/key_manager_cli.py`：

```python
#!/usr/bin/env python3
"""密钥管理命令行工具"""
import sys
import argparse
from blockchain.key_manager import KeyManager, KeySource

def main():
    parser = argparse.ArgumentParser(description='Key Manager CLI')
    subparsers = parser.add_subparsers(dest='command')

    # encrypt 命令
    encrypt_parser = subparsers.add_parser('encrypt', help='Encrypt a private key')
    encrypt_parser.add_argument('--key', required=True, help='Private key to encrypt')
    encrypt_parser.add_argument('--password', required=True, help='Encryption password')
    encrypt_parser.add_argument('--output', required=True, help='Output file path')

    # decrypt 命令
    decrypt_parser = subparsers.add_parser('decrypt', help='Decrypt a private key')
    decrypt_parser.add_argument('--input', required=True, help='Input file path')
    decrypt_parser.add_argument('--password', required=True, help='Decryption password')

    # validate 命令
    validate_parser = subparsers.add_parser('validate', help='Validate a private key')
    validate_parser.add_argument('--key', required=True, help='Private key to validate')

    args = parser.parse_args()

    if args.command == 'encrypt':
        manager = KeyManager(
            key_source=KeySource.ENCRYPTED_FILE,
            key_file_path=args.output,
            encryption_password=args.password
        )
        manager.save_encrypted_key(args.key, args.output)
        print(f'✅ Key encrypted and saved to {args.output}')

    elif args.command == 'decrypt':
        manager = KeyManager(
            key_source=KeySource.ENCRYPTED_FILE,
            key_file_path=args.input,
            encryption_password=args.password
        )
        key = manager.get_private_key()
        print(f'✅ Decrypted key: {manager.mask_key(key)}')

    elif args.command == 'validate':
        manager = KeyManager(key_source=KeySource.ENVIRONMENT)
        manager._private_key = args.key
        if manager.validate_key():
            print('✅ Key is valid')
            print(f'✅ Address: {manager.get_public_address()}')
        else:
            print('❌ Key is invalid')
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
```

### C. 安全检查清单

- [ ] 私钥已加密存储
- [ ] 密钥文件权限设置为 600
- [ ] 启用密钥轮换策略
- [ ] 配置密钥访问审计
- [ ] 设置密钥备份计划
- [ ] 限制密钥访问 IP
- [ ] 启用多因素认证
- [ ] 定期审查访问日志
- [ ] 测试密钥恢复流程
- [ ] 文档化密钥管理流程

---

## 支持

如有问题或建议，请联系：

- 技术支持：support@nautilus.example.com
- 文档：https://docs.nautilus.example.com
- GitHub Issues：https://github.com/nautilus/issues

---

**最后更新：** 2026-02-26
**版本：** 1.0.0
