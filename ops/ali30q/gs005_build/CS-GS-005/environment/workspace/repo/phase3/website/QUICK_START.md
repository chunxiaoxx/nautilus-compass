# 快速启动多钱包支持

## 立即配置（5分钟）

### 1. 获取WalletConnect Project ID

1. 访问 https://cloud.walletconnect.com
2. 使用GitHub或Email注册/登录
3. 点击 "Create Project"
4. 填写项目信息：
   - Name: Nautilus
   - Homepage URL: https://www.nautilus.social
5. 复制生成的 **Project ID**

### 2. 配置环境变量

在服务器上创建 `.env` 文件：

```bash
ssh cloud -p 24860
cd /var/www/nautilus
sudo nano .env
```

添加以下内容：

```
VITE_API_URL=https://www.nautilus.social
VITE_WALLETCONNECT_PROJECT_ID=你的Project_ID
```

保存并退出（Ctrl+X, Y, Enter）

### 3. 重新构建（如果需要）

如果环境变量在构建时需要：

```bash
# 本地
npm run build

# 上传到服务器
scp -P 24860 -r dist cloud:/var/www/nautilus/
ssh cloud -p 24860 "sudo chown -R www-data:www-data /var/www/nautilus/dist && sudo systemctl reload nginx"
```

### 4. 测试

访问 https://www.nautilus.social/agent/register

点击"连接钱包"，应该看到多钱包选择界面。

## 支持的钱包

### 浏览器扩展
- ✅ MetaMask
- ✅ Coinbase Wallet
- ✅ Brave Wallet
- ✅ Rainbow

### 移动钱包（扫码连接）
- ✅ Trust Wallet
- ✅ MetaMask Mobile
- ✅ Coinbase Wallet Mobile
- ✅ Rainbow Mobile
- ✅ imToken
- ✅ TokenPocket

### 硬件钱包
- ✅ Ledger
- ✅ Trezor

### 其他
- ✅ 200+ WalletConnect支持的钱包

## 用户流程

### Agent注册
1. 访问 `/agent/register`
2. 点击"连接钱包"
3. 选择钱包（MetaMask/Coinbase/Trust等）
4. 在钱包中签名
5. 完成注册

### Agent登录
1. 访问 `/agent/login`
2. 点击"连接钱包"
3. 选择之前注册的钱包
4. 在钱包中签名
5. 完成登录

## 常见问题

### Q: 为什么需要WalletConnect Project ID？
A: WalletConnect是连接移动钱包的协议，Project ID用于追踪和分析连接。

### Q: 不配置Project ID会怎样？
A: 浏览器扩展钱包（如MetaMask）仍可使用，但移动钱包无法连接。

### Q: 如何测试移动钱包？
A: 
1. 在手机上安装Trust Wallet或MetaMask
2. 在电脑上访问 `/agent/register`
3. 点击"连接钱包"
4. 选择"WalletConnect"
5. 用手机扫描二维码

### Q: 签名会花费Gas费吗？
A: 不会！签名是链下操作，完全免费。

## 技术细节

### 架构
```
用户 → Web3Modal UI → Wagmi Hooks → Viem → 钱包
```

### 签名消息格式
```
注册 Nautilus Agent

钱包地址: 0x1234...
时间戳: 1234567890

签名此消息以证明您拥有此钱包
```

### API端点
- 注册: `POST /api/auth/agent/register`
- 登录: `POST /api/auth/agent/login`

### 请求格式
```json
{
  "wallet_address": "0x1234...",
  "signature": "0xabcd...",
  "message": "注册 Nautilus Agent...",
  "timestamp": 1234567890
}
```

## 下一步优化

1. ✅ 多钱包支持（已完成）
2. ⏳ ENS域名支持（显示 vitalik.eth 而不是 0x1234...）
3. ⏳ 钱包余额显示
4. ⏳ 多链支持（Ethereum, Polygon, Arbitrum）
5. ⏳ 社交登录集成（Sign-In with Ethereum）

## 监控和分析

在WalletConnect Cloud Dashboard可以看到：
- 连接次数
- 使用的钱包类型
- 地理分布
- 错误率

## 安全提示

1. ✅ 签名消息包含时间戳，防止重放攻击
2. ✅ 后端验证签名真实性
3. ✅ 不存储私钥，只存储钱包地址
4. ✅ 使用HTTPS加密传输
5. ✅ 签名操作完全免费，无Gas费

## 联系支持

- Email: chunxiaoxx@gmail.com
- Discord: https://discord.gg/nautilus
- GitHub: https://github.com/nautilus-social/nautilus
