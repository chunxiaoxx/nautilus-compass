# 数据库迁移工具 - README

## 项目概述

Nautilus Phase 3 数据库迁移工具 - 基于Alembic的完整数据库迁移管理系统

**状态**: ✅ 完成并可投入生产使用
**版本**: 1.0.0
**完成日期**: 2026-02-26

---

## 快速开始

### 1. 验证安装

```bash
python verify_migration_tool.py
```

### 2. 快速设置

**Linux/Mac**:
```bash
chmod +x setup_migrations.sh
./setup_migrations.sh
```

**Windows**:
```bash
setup_migrations.bat
```

### 3. 常用命令

```bash
# 测试数据库连接
python manage_migrations.py test

# 检查迁移状态
python manage_migrations.py check

# 应用所有迁移
python manage_migrations.py upgrade

# 查看当前版本
python manage_migrations.py current

# 创建新迁移
python manage_migrations.py create "description"

# 回滚一个迁移
python manage_migrations.py downgrade
```

---

## 项目结构

```
backend/
├── alembic.ini                              # Alembic配置
├── alembic/
│   ├── env.py                               # 环境配置
│   ├── script.py.mako                       # 迁移模板
│   ├── README.md                            # 快速参考
│   └── versions/
│       ├── 001_initial_schema.py            # 初始架构
│       └── add_gas_fee_fields.py            # Gas费用字段
├── manage_migrations.py                     # CLI管理工具
├── test_migrations.py                       # 测试套件
├── verify_migration_tool.py                 # 验证脚本
├── setup_migrations.sh                      # Linux/Mac设置
├── setup_migrations.bat                     # Windows设置
└── 文档/
    ├── DATABASE_MIGRATION_GUIDE.md          # 完整指南
    ├── MIGRATION_QUICK_REFERENCE.md         # 快速参考
    ├── MIGRATION_TOOL_REPORT.md             # 技术报告
    ├── MIGRATION_FINAL_DELIVERY.md          # 交付报告
    ├── 数据库迁移工具完成报告.md              # 中文报告
    ├── 项目验收清单.md                       # 验收清单
    └── PROJECT_COMPLETE.md                  # 项目完成
```

---

## 功能特性

### ✅ 完整的迁移管理
- 自动生成迁移（从模型变更）
- 手动创建迁移模板
- 应用迁移（升级）
- 回滚迁移（降级）
- 查看迁移历史
- 检查数据库状态

### ✅ 安全可靠
- 破坏性操作确认提示
- 事务支持确保原子性
- 完善的错误处理
- 数据库状态验证

### ✅ 性能优化
- 28个优化索引（22单列 + 6复合）
- 外键索引
- 高效的架构设计

### ✅ 开发友好
- 清晰的CLI界面
- 详细的帮助文档
- 丰富的代码示例
- 完整的故障排除指南

---

## 数据库架构

### 表 (6个)

| 表名 | 列数 | 索引数 | 外键 | 说明 |
|------|------|--------|------|------|
| tasks | 25 | 12 | 0 | 任务管理 |
| agents | 14 | 3 | 0 | 代理管理 |
| rewards | 7 | 5 | 0 | 奖励分配 |
| verification_logs | 6 | 1 | 1 | 验证日志 |
| users | 9 | 3 | 0 | 用户认证 |
| api_keys | 7 | 4 | 1 | API密钥 |

### 特殊字段
- **Gas费用分摊**: gas_used, gas_cost, gas_split
- **区块链集成**: blockchain_tx_hash, blockchain_status等

---

## CLI命令

### 创建迁移
```bash
# 自动生成（推荐）
python manage_migrations.py create "add new field"

# 手动模板
python manage_migrations.py create "custom migration" --no-autogenerate
```

### 应用迁移
```bash
# 应用所有待处理的迁移
python manage_migrations.py upgrade

# 应用到特定版本
python manage_migrations.py upgrade abc123

# 逐步应用
python manage_migrations.py upgrade +1
```

### 回滚迁移
```bash
# 回滚一步
python manage_migrations.py downgrade

# 回滚到特定版本
python manage_migrations.py downgrade abc123

# 回滚所有（危险！）
python manage_migrations.py downgrade base
```

### 查看状态
```bash
# 当前版本
python manage_migrations.py current

# 迁移历史
python manage_migrations.py history

# 详细历史
python manage_migrations.py history -v

# 检查状态
python manage_migrations.py check
```

### 其他命令
```bash
# 测试连接
python manage_migrations.py test

# 标记版本
python manage_migrations.py stamp <revision>
```

---

## 测试

### 运行测试

```bash
# 所有测试
pytest test_migrations.py -v

# 特定测试类
pytest test_migrations.py::TestMigrations -v

# 特定测试
pytest test_migrations.py::TestMigrations::test_upgrade_to_head -v

# 带覆盖率
pytest test_migrations.py --cov=alembic --cov-report=html
```

### 测试覆盖

- ✅ 数据库连接测试
- ✅ 表架构验证（6个表）
- ✅ 索引验证
- ✅ 外键验证
- ✅ 迁移升级测试
- ✅ 迁移回滚测试
- ✅ 数据完整性测试
- ✅ 幂等性测试

**总计**: 16+个测试用例

---

## 文档

### 快速参考
📄 **MIGRATION_QUICK_REFERENCE.md** - 常用命令和示例

### 完整指南
📖 **DATABASE_MIGRATION_GUIDE.md** - 详细的使用指南（10个章节）

### 技术文档
📋 **MIGRATION_TOOL_REPORT.md** - 技术实现细节

### 项目报告
📊 **MIGRATION_FINAL_DELIVERY.md** - 完整交付报告

### 中文文档
🇨🇳 **数据库迁移工具完成报告.md** - 中文版完成报告

### 验收文档
✅ **项目验收清单.md** - 项目验收清单

---

## 环境配置

### 必需的环境变量

在 `.env` 文件中配置：

```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

### 依赖包

```bash
pip install -r requirements.txt
```

主要依赖：
- alembic>=1.13.0
- sqlalchemy>=2.0.0
- psycopg2-binary>=2.9.0
- python-dotenv>=1.0.0

---

## 常见问题

### Q: 如何创建新迁移？
```bash
python manage_migrations.py create "description"
```

### Q: 如何应用迁移？
```bash
python manage_migrations.py upgrade
```

### Q: 如何回滚迁移？
```bash
python manage_migrations.py downgrade
```

### Q: 如何检查数据库状态？
```bash
python manage_migrations.py check
```

### Q: 数据库连接失败怎么办？
1. 检查 `.env` 中的 `DATABASE_URL`
2. 确认PostgreSQL正在运行
3. 运行 `python manage_migrations.py test` 测试连接

### Q: 迁移失败怎么办？
1. 查看错误消息
2. 运行 `python manage_migrations.py current` 检查当前状态
3. 可能需要手动修复数据库并使用 `stamp` 命令

---

## 最佳实践

### ✅ 应该做的

1. **测试优先** - 在开发环境测试所有迁移
2. **审查迁移** - 检查自动生成的迁移脚本
3. **描述性消息** - 使用清晰的迁移消息
4. **备份数据** - 生产环境迁移前备份
5. **单一职责** - 每个迁移只做一件事

### ❌ 不应该做的

1. **跳过测试** - 不要在未测试的情况下应用迁移
2. **合并更改** - 不要在一个迁移中混合不相关的更改
3. **直接生产** - 不要直接在生产环境应用未测试的迁移

---

## 生产部署

### 部署前检查清单

- [ ] 在开发环境测试
- [ ] 在测试环境验证
- [ ] 备份生产数据库
- [ ] 审查迁移脚本
- [ ] 准备回滚计划

### 部署步骤

```bash
# 1. 备份数据库
pg_dump nautilus > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 验证工具
python verify_migration_tool.py

# 3. 检查状态
python manage_migrations.py check

# 4. 应用迁移
python manage_migrations.py upgrade

# 5. 验证
python manage_migrations.py current

# 6. 测试应用
curl http://localhost:8000/health
```

---

## 项目统计

### 代码
- Python代码: 1,341行
- 文档: 3,742行
- 测试用例: 16+个

### 文件
- 配置文件: 4个
- 迁移脚本: 2个
- 管理工具: 4个
- 测试文件: 2个
- 文档文件: 8个

### 数据库
- 表: 6个
- 索引: 28个
- 外键: 2个

---

## 支持和帮助

### CLI帮助
```bash
python manage_migrations.py --help
```

### 文档
```bash
# 快速参考
cat MIGRATION_QUICK_REFERENCE.md

# 完整指南
cat DATABASE_MIGRATION_GUIDE.md

# 技术报告
cat MIGRATION_TOOL_REPORT.md
```

### 验证
```bash
python verify_migration_tool.py
```

---

## 许可证

本项目是Nautilus Phase 3的一部分。

---

## 联系方式

如有问题或建议，请参考文档或联系开发团队。

---

**项目**: Nautilus Phase 3 数据库迁移工具
**版本**: 1.0.0
**状态**: ✅ 生产就绪
**日期**: 2026-02-26

---

**祝您使用愉快！🚀**
