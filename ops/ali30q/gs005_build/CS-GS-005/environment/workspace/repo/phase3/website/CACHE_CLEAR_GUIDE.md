# 清除浏览器缓存查看最新版本

## 问题
部署了新版本，但浏览器显示的还是旧版本。

## 原因
浏览器缓存了旧的静态文件（HTML, CSS, JS）。

## 解决方案

### 方法1: 强制刷新（推荐）

**Windows/Linux:**
- Chrome/Edge: `Ctrl + Shift + R` 或 `Ctrl + F5`
- Firefox: `Ctrl + Shift + R` 或 `Ctrl + F5`

**Mac:**
- Chrome/Edge: `Cmd + Shift + R`
- Firefox: `Cmd + Shift + R`
- Safari: `Cmd + Option + R`

### 方法2: 清除浏览器缓存

**Chrome/Edge:**
1. 按 `Ctrl + Shift + Delete` (Mac: `Cmd + Shift + Delete`)
2. 选择"时间范围": 全部时间
3. 勾选"缓存的图片和文件"
4. 点击"清除数据"

**Firefox:**
1. 按 `Ctrl + Shift + Delete` (Mac: `Cmd + Shift + Delete`)
2. 选择"时间范围": 全部
3. 勾选"缓存"
4. 点击"立即清除"

### 方法3: 无痕/隐私模式

**Chrome/Edge:**
- `Ctrl + Shift + N` (Mac: `Cmd + Shift + N`)

**Firefox:**
- `Ctrl + Shift + P` (Mac: `Cmd + Shift + P`)

### 方法4: 禁用缓存（开发者模式）

**Chrome/Edge:**
1. 按 `F12` 打开开发者工具
2. 点击 Network 标签
3. 勾选 "Disable cache"
4. 刷新页面

## 验证新版本

访问 https://www.nautilus.social 后检查：

### 1. 首页优化
- ✅ 产品演示区域有动画（任务发布者 → AI Agent）
- ✅ 统计数据显示真实API数据
- ✅ "开始使用"按钮点击跳转到 /agent/register
- ✅ "了解更多"按钮点击跳转到 /docs

### 2. Agent注册页面 (/agent/register)
- ✅ 显示"连接钱包"按钮
- ✅ 支持200+种钱包选择
- ✅ 有"创建你的第一个Web3钱包"链接

### 3. 创建钱包页面 (/create-wallet)
- ✅ 3步引导流程
- ✅ 钱包选择（MetaMask/Coinbase）
- ✅ 详细安装指南

### 4. 二级页面
- ✅ 文字清晰可见（不再是白底白字）
- ✅ 所有页面正常显示

## 如果还是看不到

### 检查1: 确认访问的是正确的URL
```
https://www.nautilus.social
```

### 检查2: 查看页面源代码
1. 右键点击页面 → "查看网页源代码"
2. 查找 `index-D6thudJK.css` 和 `index-DZu-UU1C.js`
3. 如果文件名不同，说明还是旧版本

### 检查3: 查看Network请求
1. 按 `F12` 打开开发者工具
2. 切换到 Network 标签
3. 刷新页面
4. 查看 index.html 的响应时间
5. 如果是 "from disk cache" 或 "from memory cache"，说明使用了缓存

### 检查4: 服务器时间戳
```bash
ssh cloud -p 24860 "ls -lh /var/www/nautilus/current/index.html"
```
应该显示最新时间（2026-03-15 23:25）

## 部署时间
最新部署: 2026-03-15 23:25 UTC+8

## 联系支持
如果清除缓存后仍然看不到更新，请提供：
1. 浏览器类型和版本
2. 访问的URL
3. 开发者工具 Network 标签截图
