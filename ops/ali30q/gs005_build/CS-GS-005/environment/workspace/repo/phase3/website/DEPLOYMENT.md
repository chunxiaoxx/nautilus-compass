# Nautilus Website 部署与版本管理

## 快速开始

### 1. 部署新版本（自动备份）
```bash
./deploy.sh
```

这会：
- 构建项目
- 备份当前版本（带时间戳）
- 部署新版本
- 自动保留最近5个版本
- 验证部署是否成功

### 2. 查看所有版本
```bash
./versions.sh list
```

输出示例：
```
📋 已保存的版本列表:

drwxr-xr-x 3 root root 4096 Mar 16 14:30 backup_20260316_143000
drwxr-xr-x 3 root root 4096 Mar 16 13:50 backup_20260316_135530
drwxr-xr-x 3 root root 4096 Mar 16 12:20 backup_20260316_122000
```

### 3. 回滚到之前版本
```bash
./rollback.sh backup_20260316_135530
```

这会：
- 备份当前版本（以防回滚失败）
- 恢复指定版本
- 验证回滚是否成功

### 4. 清理旧版本
```bash
./versions.sh clean
```

保留最近5个版本，删除更早的版本。

## 版本管理策略

### 自动备份
每次运行 `./deploy.sh` 时，会自动：
1. 备份当前版本到 `/var/www/nautilus/versions/backup_YYYYMMDD_HHMMSS`
2. 部署新版本到 `/var/www/nautilus/current/`
3. 自动清理，只保留最近5个版本

### 版本命名
格式：`backup_YYYYMMDD_HHMMSS`
- 示例：`backup_20260316_143000` = 2026年3月16日 14:30:00

### 服务器目录结构
```
/var/www/nautilus/
├── current/              # 当前运行的版本
└── versions/             # 历史版本备份
    ├── backup_20260316_143000/
    ├── backup_20260316_135530/
    └── backup_20260316_122000/
```

## 常见场景

### 场景1：部署新功能
```bash
# 1. 开发完成后，部署
./deploy.sh

# 2. 如果发现问题，立即回滚
./versions.sh list              # 查看上一个版本号
./rollback.sh backup_20260316_135530
```

### 场景2：测试新版本
```bash
# 1. 部署新版本
./deploy.sh

# 2. 测试发现问题
# 3. 回滚到上一个稳定版本
./rollback.sh backup_20260316_135530

# 4. 修复问题后重新部署
./deploy.sh
```

### 场景3：清理磁盘空间
```bash
# 查看当前版本数量
./versions.sh list

# 清理旧版本（保留最近5个）
./versions.sh clean
```

## 手动操作（高级）

### 查看服务器上的版本
```bash
ssh cloud "ls -lth /var/www/nautilus/versions/"
```

### 手动备份当前版本
```bash
ssh cloud "sudo cp -r /var/www/nautilus/current /var/www/nautilus/versions/manual_backup_$(date +%Y%m%d_%H%M%S)"
```

### 手动删除特定版本
```bash
ssh cloud "sudo rm -rf /var/www/nautilus/versions/backup_20260316_122000"
```

## 注意事项

1. **备份保留策略**：默认保留最近5个版本，可以在 `deploy.sh` 中修改
2. **磁盘空间**：每个版本约占用2-5MB，定期清理旧版本
3. **回滚限制**：只能回滚到已备份的版本
4. **权限问题**：脚本需要SSH访问服务器的权限

## 故障排除

### 问题1：部署失败
```bash
# 检查构建是否成功
npm run build

# 检查SSH连接
ssh cloud "echo 'Connection OK'"

# 手动部署
tar -czf dist.tar.gz -C dist .
scp dist.tar.gz cloud:/tmp/
ssh cloud "cd /tmp && sudo tar -xzf dist.tar.gz -C /var/www/nautilus/current/"
```

### 问题2：回滚失败
```bash
# 检查版本是否存在
ssh cloud "ls -la /var/www/nautilus/versions/"

# 手动回滚
ssh cloud "sudo cp -r /var/www/nautilus/versions/backup_XXXXXX/* /var/www/nautilus/current/"
```

### 问题3：权限错误
```bash
# 修复权限
ssh cloud "sudo chown -R www-data:www-data /var/www/nautilus/current/"
```

## 最佳实践

1. **部署前测试**：在本地运行 `npm run build` 确保构建成功
2. **记录版本**：在Git中打标签，方便追踪
3. **定期清理**：每周运行 `./versions.sh clean`
4. **重要更新**：部署前手动备份一个版本
5. **验证部署**：部署后访问网站确认功能正常

## Git集成（可选）

### 部署时打Git标签
```bash
# 部署前
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# 部署
./deploy.sh
```

### 查看Git标签和部署版本的对应关系
```bash
git tag -l
./versions.sh list
```
