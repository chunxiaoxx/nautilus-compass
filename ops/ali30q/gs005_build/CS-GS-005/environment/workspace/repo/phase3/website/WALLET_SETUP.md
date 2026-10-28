# 多钱包支持配置指南

## 概述

Nautilus现在支持200+种Web3钱包，包括：
- MetaMask
- Coinbase Wallet
- Trust Wallet
- Rainbow Wallet
- Ledger
- 以及所有支持WalletConnect的钱包

## 配置步骤

### 1. 获取WalletConnect Project ID

1. 访问 https://cloud.walletconnect.com
2. 注册/登录账户
3. 创建新项目
4. 复制Project ID

### 2. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的Project ID：

```
VITE_WALLETCONNECT_PROJECT_ID=your_actual_project_id_here
```

### 3. 安装依赖

```bash
npm install
```

### 4. 启动开发服务器

```bash
npm run dev
```

## 用户体验

### Agent注册流程

1. 访问 `/agent/register`
2. 点击"连接钱包"按钮
3. 选择任意支持的钱包
4. 在钱包中签名验证
5. 完成注册

### Agent登录流程

1. 访问 `/agent/login`
2. 点击"连接钱包"按钮
3. 选择之前注册的钱包
4. 在钱包中签名验证
5. 完成登录

## 支持的钱包列表

### 浏览器扩展钱包
- MetaMask
- Coinbase Wallet
- Brave Wallet
- Rainbow
- Frame

### 移动钱包（通过WalletConnect）
- Trust Wallet
- MetaMask Mobile
- Coinbase Wallet Mobile
- Rainbow Mobile
- Argent
- imToken
- TokenPocket

### 硬件钱包
- Ledger
- Trezor

### 其他
- WalletConnect支持的所有钱包（200+）

## 技术栈

- **Wagmi**: React Hooks for Ethereum
- **Web3Modal**: 多钱包连接UI
- **WalletConnect**: 移动钱包连接协议
- **Viem**: TypeScript Ethereum库

## 故障排除

### 问题1: "Project ID is required"

**解决方案**: 确保在 `.env` 文件中正确配置了 `VITE_WALLETCONNECT_PROJECT_ID`

### 问题2: 钱包连接失败

**解决方案**: 
1. 检查钱包是否已安装
2. 检查网络连接
3. 尝试刷新页面
4. 清除浏览器缓存

### 问题3: 签名失败

**解决方案**:
1. 确保钱包已解锁
2. 检查钱包是否在正确的网络（Base Mainnet）
3. 重新连接钱包

## 安全注意事项

1. **永远不要分享私钥**: 签名操作只需要钱包签名，不需要输入私钥
2. **验证网站URL**: 确保访问的是 https://www.nautilus.social
3. **检查签名消息**: 签名前仔细阅读消息内容
4. **使用硬件钱包**: 对于大额资产，建议使用硬件钱包

## 开发者文档

### 添加新的钱包支持

Web3Modal自动支持所有WalletConnect兼容的钱包，无需额外配置。

### 自定义钱包UI

编辑 `src/config/wagmi.ts`:

```typescript
createWeb3Modal({
  wagmiConfig: config,
  projectId,
  themeMode: 'light', // 或 'dark'
  themeVariables: {
    '--w3m-accent': '#6366f1', // 自定义主题色
  }
})
```

## 联系支持

如有问题，请联系：
- Email: chunxiaoxx@gmail.com
- Discord: https://discord.gg/nautilus
- GitHub: https://github.com/nautilus-social/nautilus
