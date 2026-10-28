# HomePage 部署指南

**日期**: 2026-02-21
**文件**: HomePage_Optimized.tsx
**目标服务器**: 43.160.239.61

---

## 📋 部署前准备

### 1. 文件信息
- **本地路径**: `C:\Users\chunx\Projects\nautilus-core\phase3\frontend\src\pages\HomePage_Optimized.tsx`
- **远程路径**: `/home/ubuntu/nautilus-mvp/phase3/frontend/src/pages/`
- **文件大小**: ~65KB
- **总行数**: 1,553 行

### 2. 服务器信息
- **IP**: 43.160.239.61
- **用户名**: ubuntu
- **密码**: DRKcx30190310@
- **端口**: 22
- **前端服务端口**: 3000

---

## 🚀 部署方法

### 方法 1: 使用 SFTP 客户端（推荐）

#### 使用 FileZilla
1. 打开 FileZilla
2. 输入连接信息：
   - 主机: `sftp://43.160.239.61`
   - 用户名: `ubuntu`
   - 密码: `DRKcx30190310@`
   - 端口: `22`
3. 点击"快速连接"
4. 导航到远程目录: `/home/ubuntu/nautilus-mvp/phase3/frontend/src/pages/`
5. 上传 `HomePage_Optimized.tsx`

#### 使用 WinSCP
1. 打开 WinSCP
2. 新建站点：
   - 文件协议: SFTP
   - 主机名: `43.160.239.61`
   - 端口: `22`
   - 用户名: `ubuntu`
   - 密码: `DRKcx30190310@`
3. 登录
4. 导航到 `/home/ubuntu/nautilus-mvp/phase3/frontend/src/pages/`
5. 拖拽上传 `HomePage_Optimized.tsx`

---

### 方法 2: 使用 Git（推荐）

#### 在本地
```bash
cd C:\Users\chunx\Projects\nautilus-core
git push origin master
```

#### 在服务器上
```bash
# SSH 登录
ssh ubuntu@43.160.239.61

# 进入项目目录
cd /home/ubuntu/nautilus-mvp

# 拉取最新代码
git pull origin master

# 确认文件已更新
ls -lh phase3/frontend/src/pages/HomePage_Optimized.tsx
```

---

### 方法 3: 使用 SSH + 复制粘贴

#### 步骤 1: 读取本地文件
在本地 Windows 上：
```bash
cat "C:\Users\chunx\Projects\nautilus-core\phase3\frontend\src\pages\HomePage_Optimized.tsx"
```
复制全部内容到剪贴板

#### 步骤 2: SSH 登录服务器
```bash
ssh ubuntu@43.160.239.61
```

#### 步骤 3: 创建文件
```bash
cd /home/ubuntu/nautilus-mvp/phase3/frontend/src/pages/

# 使用 nano 编辑器
nano HomePage_Optimized.tsx

# 粘贴内容
# 按 Ctrl+X, 然后 Y, 然后 Enter 保存
```

---

## 🔄 替换现有文件

### 1. 备份原文件
```bash
cd /home/ubuntu/nautilus-mvp/phase3/frontend/src/pages/

# 备份原 HomePage.tsx
cp HomePage.tsx HomePage_Backup_$(date +%Y%m%d_%H%M%S).tsx

# 确认备份成功
ls -lh HomePage_Backup_*.tsx
```

### 2. 替换文件
```bash
# 方式 A: 直接替换
cp HomePage_Optimized.tsx HomePage.tsx

# 方式 B: 先删除再重命名
rm HomePage.tsx
mv HomePage_Optimized.tsx HomePage.tsx
```

### 3. 验证文件
```bash
# 检查文件大小
ls -lh HomePage.tsx

# 检查文件内容（前20行）
head -20 HomePage.tsx

# 检查是否包含"智涌"
grep "智涌" HomePage.tsx
```

---

## 🔧 重启前端服务

### 1. 停止现有服务
```bash
# 查找 Vite 进程
ps aux | grep vite

# 停止所有 Vite 进程
pkill -f 'vite'

# 确认已停止
ps aux | grep vite
```

### 2. 启动新服务
```bash
# 进入前端目录
cd /home/ubuntu/nautilus-mvp/phase3/frontend

# 后台启动 Vite
nohup npm run dev > /tmp/vite-restart.log 2>&1 &

# 查看启动日志
tail -f /tmp/vite-restart.log

# 按 Ctrl+C 退出日志查看
```

### 3. 验证服务运行
```bash
# 检查进程
ps aux | grep vite

# 检查端口
netstat -tuln | grep 3000

# 测试本地访问
curl http://localhost:3000

# 测试外部访问
curl http://43.160.239.61:3000
```

---

## ✅ 验证部署

### 1. 浏览器访问
打开浏览器访问: http://43.160.239.61:3000

### 2. 检查清单
- [ ] 页面正常加载
- [ ] Hero 区域显示 "Nautilus · 智涌"
- [ ] Slogan "智能如潮，螺旋向上" 可见
- [ ] 4步工作流程图显示正常
- [ ] 4层系统架构图显示正常
- [ ] Logo 图片加载正常
- [ ] 所有图标显示正常
- [ ] 所有链接可点击
- [ ] 颜色和样式正确
- [ ] 无控制台错误

### 3. 测试功能
- [ ] 点击 "浏览任务" 按钮 → 跳转到 /tasks
- [ ] 点击 "立即注册" 按钮 → 跳转到 /register
- [ ] 点击 "GitHub" 按钮 → 打开 GitHub 页面
- [ ] 点击 "查看文档" 按钮 → 打开 API 文档
- [ ] Footer 链接正常工作

### 4. 响应式测试
- [ ] 桌面端显示正常 (>1024px)
- [ ] 平板端显示正常 (768px-1024px)
- [ ] 移动端显示正常 (<768px)

---

## 🐛 故障排查

### 问题 1: 页面无法访问
```bash
# 检查 Vite 是否运行
ps aux | grep vite

# 检查端口是否监听
netstat -tuln | grep 3000

# 查看错误日志
tail -100 /tmp/vite-restart.log

# 重启服务
pkill -f 'vite'
cd /home/ubuntu/nautilus-mvp/phase3/frontend
nohup npm run dev > /tmp/vite-restart.log 2>&1 &
```

### 问题 2: 页面显示旧内容
```bash
# 清除浏览器缓存
# 在浏览器按 Ctrl+Shift+R 强制刷新

# 检查文件是否更新
cd /home/ubuntu/nautilus-mvp/phase3/frontend/src/pages/
grep "智涌" HomePage.tsx

# 重启 Vite 服务
pkill -f 'vite'
cd /home/ubuntu/nautilus-mvp/phase3/frontend
nohup npm run dev > /tmp/vite-restart.log 2>&1 &
```

### 问题 3: 图标不显示
```bash
# 检查 lucide-react 是否安装
cd /home/ubuntu/nautilus-mvp/phase3/frontend
npm list lucide-react

# 如果未安装，安装依赖
npm install lucide-react

# 重启服务
pkill -f 'vite'
nohup npm run dev > /tmp/vite-restart.log 2>&1 &
```

### 问题 4: Logo 图片不显示
```bash
# 检查 Logo 文件是否存在
cd /home/ubuntu/nautilus-mvp/phase3/frontend/public/
ls -lh nautilus-logo-main-final.png

# 检查文件权限
chmod 644 nautilus-logo-main-final.png

# 如果文件不存在，需要上传
# 使用 SFTP 上传到 /home/ubuntu/nautilus-mvp/phase3/frontend/public/
```

### 问题 5: 路由跳转失败
```bash
# 检查 React Router 配置
cd /home/ubuntu/nautilus-mvp/phase3/frontend/src/
cat App.tsx | grep -A 10 "Routes"

# 确认其他页面文件存在
ls -lh pages/TasksPage.tsx
ls -lh pages/RegisterPage.tsx
```

---

## 📊 性能监控

### 1. 检查页面加载时间
```bash
# 使用 curl 测试响应时间
time curl -s http://localhost:3000 > /dev/null
```

### 2. 检查内存使用
```bash
# 查看 Node.js 进程内存
ps aux | grep node | grep vite
```

### 3. 检查日志
```bash
# 实时查看日志
tail -f /tmp/vite-restart.log

# 查看最近的错误
grep -i error /tmp/vite-restart.log | tail -20
```

---

## 🔐 安全注意事项

### 1. 密码管理
- ⚠️ 部署完成后，建议修改服务器密码
- ⚠️ 不要在公共场合暴露密码
- ⚠️ 考虑使用 SSH 密钥认证

### 2. 文件权限
```bash
# 设置正确的文件权限
cd /home/ubuntu/nautilus-mvp/phase3/frontend/src/pages/
chmod 644 HomePage.tsx
chmod 644 HomePage_Optimized.tsx
```

### 3. 防火墙
```bash
# 确认端口 3000 已开放
sudo ufw status | grep 3000

# 如果未开放，添加规则
sudo ufw allow 3000/tcp
```

---

## 📝 回滚方案

### 如果新版本有问题，快速回滚：

```bash
cd /home/ubuntu/nautilus-mvp/phase3/frontend/src/pages/

# 查找备份文件
ls -lh HomePage_Backup_*.tsx

# 恢复备份（使用最新的备份）
cp HomePage_Backup_20260221_*.tsx HomePage.tsx

# 重启服务
pkill -f 'vite'
cd /home/ubuntu/nautilus-mvp/phase3/frontend
nohup npm run dev > /tmp/vite-restart.log 2>&1 &

# 验证
curl http://localhost:3000
```

---

## 📞 联系支持

如果遇到无法解决的问题：

1. 检查日志文件: `/tmp/vite-restart.log`
2. 查看 Git 提交历史: `git log --oneline`
3. 查看本地文档: `HOMEPAGE_OPTIMIZATION_COMPLETE.md`

---

## ✅ 部署完成确认

部署完成后，请确认：

- [x] 文件已上传到服务器
- [x] 原文件已备份
- [x] 新文件已替换
- [x] 前端服务已重启
- [x] 页面可以正常访问
- [x] 所有功能正常工作
- [x] 无控制台错误
- [x] 性能表现良好

---

**部署指南版本**: 1.0
**创建日期**: 2026-02-21
**适用文件**: HomePage_Optimized.tsx

**Nautilus · 智涌 - 智能如潮，螺旋向上！** 🚀
