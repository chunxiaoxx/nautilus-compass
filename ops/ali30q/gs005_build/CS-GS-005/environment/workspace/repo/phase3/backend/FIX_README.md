# 数据库配置修复文件说明

## 问题
生产环境配置了 PostgreSQL，但实际使用 SQLite，原因是 `utils/database.py` 在 `load_dotenv()` 之前读取环境变量。

## 修复文件

### 1. utils/database.py ✅ 已修复
**主要修复文件**
- 在文件顶部添加了 `from dotenv import load_dotenv` 和 `load_dotenv()`
- 确保环境变量在使用前正确加载

### 2. verify_db_config.py
**配置验证脚本**
```bash
python3 verify_db_config.py
```
用于验证数据库配置是否正确加载，会检查：
- DATABASE_URL 是否正确
- 是否使用 PostgreSQL
- 数据库连接是否成功

### 3. quick_fix.sh ⭐ 推荐
**一键修复脚本（最简单）**
```bash
cd /home/ubuntu/nautilus-mvp/phase3/backend
chmod +x quick_fix.sh
./quick_fix.sh
```
自动完成：备份 → 修复 → 重启 → 验证

### 4. deploy_fix.sh
**完整部署脚本**
```bash
cd /home/ubuntu/nautilus-mvp/phase3/backend
chmod +x deploy_fix.sh
./deploy_fix.sh
```
包含更详细的检查和验证步骤

### 5. DEPLOYMENT_GUIDE.md
**详细部署指南**
- 完整的部署步骤
- 故障排查方案
- 回滚方案
- 常见问题解答

### 6. FIX_REPORT.md
**完整修复报告**
- 问题分析
- 修复方案
- 验证结果
- 风险评估

## 快速部署（3 步）

### 方法 1: 使用 quick_fix.sh（推荐）

```bash
# 1. SSH 登录服务器
ssh cloud

# 2. 进入项目目录
cd /home/ubuntu/nautilus-mvp/phase3/backend

# 3. 运行修复脚本
chmod +x quick_fix.sh && ./quick_fix.sh
```

### 方法 2: 手动修复

```bash
# 1. SSH 登录
ssh cloud

# 2. 编辑文件
cd /home/ubuntu/nautilus-mvp/phase3/backend
nano utils/database.py

# 3. 在文件开头添加（第 4-7 行）：
from dotenv import load_dotenv

# Load environment variables BEFORE any configuration
load_dotenv()

# 4. 保存并重启
sudo systemctl restart nautilus-backend

# 5. 验证
curl http://localhost:8000/health
```

## 验证修复

```bash
# 检查服务状态
sudo systemctl status nautilus-backend

# 查看日志（应该看到 PostgreSQL 连接）
sudo journalctl -u nautilus-backend -n 50

# 测试健康检查
curl http://localhost:8000/health

# 验证数据库
psql -U postgres -d nautilus -c "\dt"
```

## 回滚

如果出现问题：
```bash
# 恢复备份（找到最新的备份文件）
ls -lt utils/database.py.backup.*
cp utils/database.py.backup.XXXXXX utils/database.py

# 重启服务
sudo systemctl restart nautilus-backend
```

## 当前状态

- ✅ 代码已修复
- ✅ 本地验证通过
- ⏳ 等待部署到生产环境

## 注意事项

1. **SSH 连接问题**: 如果 SSH 连接超时，可以通过云服务器控制台登录
2. **权限问题**: 部分命令需要 sudo 权限
3. **备份**: 脚本会自动创建备份，无需担心数据丢失
4. **监控**: 部署后建议监控日志 10 分钟确保稳定

## 联系支持

如有问题，检查：
- 服务日志: `sudo journalctl -u nautilus-backend -f`
- 数据库日志: `sudo tail -f /var/log/postgresql/postgresql-*.log`
- 详细文档: 查看 DEPLOYMENT_GUIDE.md
