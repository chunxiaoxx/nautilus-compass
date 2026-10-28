# 密钥管理快速参考

## 🚀 快速开始

### 1. 生成新密钥
```bash
python tools/key_manager_cli.py generate \
  --output keys/blockchain_key.json \
  --password "YourSecurePassword"
```

### 2. 配置环境变量
在 `.env` 文件中添加：
```env
KEY_SOURCE=encrypted_file
KEY_FILE_PATH=./keys/blockchain_key.json
KEY_ENCRYPTION_PASSWORD=YourSecurePassword
KEY_ROTATION_ENABLED=true
KEY_ROTATION_DAYS=90
```

### 3. 验证配置
```bash
python tests/test_key_manager.py
```

---

## 📋 常用命令

### 查看密钥信息
```bash
python tools/key_manager_cli.py info \
  --source encrypted_file \
  --input keys/blockchain_key.json \
  --password "YourPassword"
```

### 轮换密钥
```bash
python tools/key_manager_cli.py rotate \
  --input keys/blockchain_key.json \
  --password "YourPassword"
```

### 验证密钥格式
```bash
python tools/key_manager_cli.py validate \
  --key "0x1234567890abcdef..."
```

### 加密现有密钥
```bash
python tools/key_manager_cli.py encrypt \
  --key "0x1234567890abcdef..." \
  --password "YourPassword" \
  --output keys/blockchain_key.json
```

### 解密查看密钥
```bash
python tools/key_manager_cli.py decrypt \
  --input keys/blockchain_key.json \
  --password "YourPassword"
```

### 迁移密钥
```bash
# 从环境变量迁移到加密文件
export BLOCKCHAIN_PRIVATE_KEY="0x..."
python tools/key_manager_cli.py migrate \
  --output keys/blockchain_key.json \
  --password "YourPassword"
```

---

## 💻 代码使用

### 基本使用
```python
from blockchain.key_manager import get_key_manager

# 获取密钥管理器（单例）
manager = get_key_manager()

# 获取私钥
private_key = manager.get_private_key()

# 获取区块链地址
address = manager.get_public_address()

# 验证密钥
is_valid = manager.validate_key()
```

### 获取元数据
```python
metadata = manager.get_metadata()
print(f"密钥ID: {metadata.key_id}")
print(f"创建时间: {metadata.created_at}")
print(f"轮换次数: {metadata.rotation_count}")
print(f"上次轮换: {metadata.last_rotated}")
```

### 密钥遮蔽
```python
# 安全显示密钥（遮蔽中间部分）
masked_key = manager.mask_key(private_key)
print(f"密钥: {masked_key}")  # 输出: 0xabcd...ef12
```

---

## 🔐 密钥源配置

### 1. 加密文件（推荐开发/测试）
```env
KEY_SOURCE=encrypted_file
KEY_FILE_PATH=./keys/blockchain_key.json
KEY_ENCRYPTION_PASSWORD=YourPassword
```

### 2. 环境变量（简单但不安全）
```env
KEY_SOURCE=environment
BLOCKCHAIN_PRIVATE_KEY=0x1234567890abcdef...
```

### 3. AWS KMS（推荐生产）
```env
KEY_SOURCE=aws_kms
AWS_KMS_KEY_ID=arn:aws:kms:region:account:key/key-id
AWS_REGION=us-east-1
BLOCKCHAIN_PRIVATE_KEY_ENCRYPTED=base64_encrypted_key
```

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

---

## ⚙️ 轮换策略配置

```env
# 启用自动轮换
KEY_ROTATION_ENABLED=true

# 轮换周期（天）
KEY_ROTATION_DAYS=90

# 警告提前天数
KEY_ROTATION_WARNING_DAYS=7
```

---

## 🛡️ 安全检查清单

### 开发环境
- [ ] 使用加密文件存储密钥
- [ ] 使用强密码（至少16字符）
- [ ] 密钥文件已添加到 .gitignore
- [ ] 不使用生产环境密钥
- [ ] 定期清理测试密钥

### 生产环境
- [ ] 使用 KMS 或 Key Vault
- [ ] 启用多因素认证
- [ ] 配置访问审计日志
- [ ] 启用自动密钥轮换
- [ ] 配置告警监控
- [ ] 制定密钥泄露应急预案

---

## 🔧 故障排查

### 问题：密钥文件不存在
```bash
# 检查文件是否存在
ls -l keys/blockchain_key.json

# 重新生成密钥
python tools/key_manager_cli.py generate \
  --output keys/blockchain_key.json \
  --password "YourPassword"
```

### 问题：密码错误
```bash
# 确认密码正确
echo $KEY_ENCRYPTION_PASSWORD

# 如果忘记密码，需要重新生成密钥
```

### 问题：密钥格式无效
```bash
# 验证密钥格式
python tools/key_manager_cli.py validate --key "0x..."

# 密钥应为64位十六进制（可选0x前缀）
```

### 问题：权限不足
```bash
# 设置正确的文件权限
chmod 600 keys/blockchain_key.json
chmod 700 keys/
```

---

## 📊 测试命令

### 运行完整测试套件
```bash
python tests/test_key_manager.py
```

### 运行特定测试
```bash
python -m pytest tests/test_key_manager.py::test_encrypted_file -v
```

### 验证密钥加载
```bash
python -c "from blockchain.key_manager import get_key_manager; \
  m = get_key_manager(); \
  print('Address:', m.get_public_address())"
```

---

## 📁 文件位置

```
backend/
├── blockchain/
│   └── key_manager.py              # 核心模块
├── tools/
│   └── key_manager_cli.py          # CLI工具
├── tests/
│   └── test_key_manager.py         # 测试套件
├── keys/
│   ├── blockchain_key.json         # 密钥文件
│   └── config_info.json            # 配置信息
├── .env                            # 环境变量
├── .gitignore                      # Git忽略
├── setup_key_management.py         # 配置脚本
├── KEY_SETUP_GUIDE.md             # 详细指南
├── KEY_MANAGEMENT_SETUP_REPORT.md # 配置报告
└── KEY_QUICK_REFERENCE.md         # 本文档
```

---

## 🔗 相关文档

- **详细配置指南：** `KEY_SETUP_GUIDE.md`
- **完整配置报告：** `KEY_MANAGEMENT_SETUP_REPORT.md`
- **配置完成总结：** `KEY_MANAGEMENT_COMPLETION_SUMMARY.md`

---

## ⚠️ 重要提醒

1. **不要在生产环境使用示例密码**
2. **密钥文件必须添加到 .gitignore**
3. **定期轮换密钥（建议90天）**
4. **使用密码管理器存储密码**
5. **生产环境建议使用 KMS**

---

**最后更新：** 2026-02-26
**版本：** 1.0
