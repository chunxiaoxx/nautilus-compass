# 密钥管理配置指南

## 快速开始

### 1. 环境要求

- Python 3.8+
- cryptography 库
- web3 库

### 2. 安装依赖

```bash
pip install cryptography web3
```

### 3. 生成新密钥

使用命令行工具生成新的加密密钥：

```bash
# 生成新密钥并保存到加密文件
python tools/key_manager_cli.py generate \
  --output keys/blockchain_key.json \
  --password "YourSecurePassword123!@#"

# 查看生成的密钥信息（遮蔽显示）
python tools/key_manager_cli.py info \
  --source encrypted_file \
  --input keys/blockchain_key.json \
  --password "YourSecurePassword123!@#"
```

### 4. 配置环境变量

在 `.env` 文件中添加以下配置：

```env
# 密钥管理配置
KEY_SOURCE=encrypted_file
KEY_FILE_PATH=./keys/blockchain_key.json
KEY_ENCRYPTION_PASSWORD=YourSecurePassword123!@#
KEY_ROTATION_ENABLED=true
KEY_ROTATION_DAYS=90
```

### 5. 验证配置

```bash
# 运行测试验证配置
python tests/test_key_manager.py
```

## 环境变量配置详解

### 必需配置

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `KEY_SOURCE` | 密钥源类型 | `encrypted_file`, `environment`, `aws_kms` |
| `KEY_FILE_PATH` | 密钥文件路径（encrypted_file源） | `./keys/blockchain_key.json` |
| `KEY_ENCRYPTION_PASSWORD` | 加密密码（encrypted_file源） | `SecurePassword123!` |

### 可选配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `KEY_ROTATION_ENABLED` | 是否启用密钥轮换 | `false` |
| `KEY_ROTATION_DAYS` | 密钥轮换周期（天） | `90` |
| `KEY_ROTATION_WARNING_DAYS` | 轮换警告提前天数 | `7` |

## 密钥源类型

### 1. 加密文件（推荐用于开发/测试）

```env
KEY_SOURCE=encrypted_file
KEY_FILE_PATH=./keys/blockchain_key.json
KEY_ENCRYPTION_PASSWORD=YourSecurePassword
```

**优点：**
- 密钥加密存储
- 支持密钥轮换
- 自动备份
- 易于管理

**适用场景：**
- 开发环境
- 测试环境
- 小型部署

### 2. 环境变量（简单但不推荐生产环境）

```env
KEY_SOURCE=environment
BLOCKCHAIN_PRIVATE_KEY=0x1234567890abcdef...
```

**优点：**
- 配置简单
- 无需额外文件

**缺点：**
- 密钥明文存储
- 不支持轮换
- 安全性较低

**适用场景：**
- 快速测试
- 临时开发

### 3. AWS KMS（推荐用于生产环境）

```env
KEY_SOURCE=aws_kms
AWS_KMS_KEY_ID=arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
AWS_REGION=us-east-1
BLOCKCHAIN_PRIVATE_KEY_ENCRYPTED=base64_encrypted_key
```

**优点：**
- 企业级安全
- 集中管理
- 审计日志
- 自动轮换

**适用场景：**
- 生产环境
- 企业部署
- 合规要求

### 4. Azure Key Vault

```env
KEY_SOURCE=azure_key_vault
AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/
AZURE_KEY_VAULT_SECRET_NAME=blockchain-private-key
```

### 5. HashiCorp Vault

```env
KEY_SOURCE=hashicorp_vault
VAULT_ADDR=https://vault.example.com:8200
VAULT_TOKEN=your-vault-token
VAULT_SECRET_PATH=secret/blockchain/private-key
```

## 密钥管理操作

### 生成新密钥

```bash
# 生成并保存到加密文件
python tools/key_manager_cli.py generate \
  --output keys/blockchain_key.json \
  --password "SecurePassword123"

# 仅生成密钥（显示完整密钥，危险！）
python tools/key_manager_cli.py generate --show-full
```

### 加密现有密钥

```bash
python tools/key_manager_cli.py encrypt \
  --key "0x1234567890abcdef..." \
  --password "SecurePassword123" \
  --output keys/blockchain_key.json
```

### 解密密钥

```bash
# 遮蔽显示（安全）
python tools/key_manager_cli.py decrypt \
  --input keys/blockchain_key.json \
  --password "SecurePassword123"

# 完整显示（危险！）
python tools/key_manager_cli.py decrypt \
  --input keys/blockchain_key.json \
  --password "SecurePassword123" \
  --show-full
```

### 验证密钥

```bash
python tools/key_manager_cli.py validate \
  --key "0x1234567890abcdef..."
```

### 轮换密钥

```bash
# 自动生成新密钥
python tools/key_manager_cli.py rotate \
  --input keys/blockchain_key.json \
  --password "SecurePassword123"

# 使用指定的新密钥
python tools/key_manager_cli.py rotate \
  --input keys/blockchain_key.json \
  --password "SecurePassword123" \
  --new-key "0xnew_key_here..."
```

### 迁移密钥

从环境变量迁移到加密文件：

```bash
# 设置环境变量
export BLOCKCHAIN_PRIVATE_KEY="0x1234567890abcdef..."

# 迁移到加密文件
python tools/key_manager_cli.py migrate \
  --output keys/blockchain_key.json \
  --password "SecurePassword123"
```

### 查看密钥信息

```bash
# 查看加密文件中的密钥
python tools/key_manager_cli.py info \
  --source encrypted_file \
  --input keys/blockchain_key.json \
  --password "SecurePassword123"

# 查看环境变量中的密钥
python tools/key_manager_cli.py info \
  --source environment
```

## 安全建议

### 1. 密码管理

- ✅ 使用强密码（至少16字符，包含大小写字母、数字、特殊字符）
- ✅ 不要在代码中硬编码密码
- ✅ 使用密码管理器存储密码
- ✅ 定期更换密码
- ❌ 不要在日志中输出密码
- ❌ 不要通过邮件或聊天工具传输密码

### 2. 密钥文件管理

- ✅ 将密钥文件添加到 `.gitignore`
- ✅ 设置适当的文件权限（仅所有者可读写）
- ✅ 定期备份密钥文件
- ✅ 使用加密存储备份
- ❌ 不要将密钥文件提交到版本控制
- ❌ 不要在公共位置存储密钥文件

### 3. 密钥轮换

- ✅ 启用自动轮换策略
- ✅ 设置合理的轮换周期（建议90天）
- ✅ 在轮换前备份旧密钥
- ✅ 验证新密钥可用后再删除旧密钥
- ✅ 记录轮换历史

### 4. 访问控制

- ✅ 限制密钥访问权限
- ✅ 使用最小权限原则
- ✅ 启用审计日志
- ✅ 定期审查访问记录
- ❌ 不要共享密钥访问权限

### 5. 生产环境建议

- ✅ 使用 KMS 或 Key Vault
- ✅ 启用多因素认证
- ✅ 实施密钥分离（开发/测试/生产）
- ✅ 配置告警监控
- ✅ 制定密钥泄露应急预案

### 6. 开发环境建议

- ✅ 使用加密文件存储
- ✅ 不要使用生产密钥
- ✅ 定期清理测试密钥
- ✅ 使用独立的测试账户

## 故障排查

### 问题1：无法加载密钥

**症状：**
```
Failed to load key: [Errno 2] No such file or directory
```

**解决方案：**
1. 检查 `KEY_FILE_PATH` 是否正确
2. 确认密钥文件存在
3. 检查文件权限

### 问题2：解密失败

**症状：**
```
Failed to decrypt key: Invalid token
```

**解决方案：**
1. 确认 `KEY_ENCRYPTION_PASSWORD` 正确
2. 检查密钥文件是否损坏
3. 尝试从备份恢复

### 问题3：密钥验证失败

**症状：**
```
Key is invalid
```

**解决方案：**
1. 检查密钥格式（应为64位十六进制）
2. 确认是否包含 `0x` 前缀
3. 验证密钥长度

### 问题4：无法获取地址

**症状：**
```
Failed to get public address
```

**解决方案：**
1. 确认 web3 库已安装
2. 检查密钥格式是否正确
3. 验证密钥是否有效

### 问题5：轮换失败

**症状：**
```
Failed to rotate key
```

**解决方案：**
1. 检查文件写入权限
2. 确认磁盘空间充足
3. 验证新密钥格式正确
4. 从备份恢复旧密钥

## 最佳实践

### 开发流程

1. **初始化项目**
   ```bash
   # 生成开发密钥
   python tools/key_manager_cli.py generate \
     --output keys/dev_key.json \
     --password "DevPassword123"
   ```

2. **配置环境**
   ```bash
   # 复制环境变量模板
   cp .env.example .env

   # 编辑配置
   nano .env
   ```

3. **验证配置**
   ```bash
   # 运行测试
   python tests/test_key_manager.py
   ```

4. **开始开发**
   ```python
   from blockchain.key_manager import get_key_manager

   # 获取密钥管理器
   manager = get_key_manager()

   # 获取私钥
   private_key = manager.get_private_key()
   ```

### 部署流程

1. **准备生产密钥**
   - 使用 KMS 或 Key Vault
   - 配置访问权限
   - 启用审计日志

2. **配置生产环境**
   ```env
   KEY_SOURCE=aws_kms
   AWS_KMS_KEY_ID=your-kms-key-id
   KEY_ROTATION_ENABLED=true
   KEY_ROTATION_DAYS=90
   ```

3. **部署验证**
   - 验证密钥可访问
   - 测试密钥功能
   - 检查日志输出

4. **监控告警**
   - 配置密钥访问告警
   - 监控轮换状态
   - 定期审查日志

## 参考资料

- [密钥管理器源码](blockchain/key_manager.py)
- [命令行工具](tools/key_manager_cli.py)
- [测试套件](tests/test_key_manager.py)
- [环境变量示例](.env.example)

## 支持

如有问题，请查看：
- 故障排查章节
- 测试日志输出
- 系统日志文件
