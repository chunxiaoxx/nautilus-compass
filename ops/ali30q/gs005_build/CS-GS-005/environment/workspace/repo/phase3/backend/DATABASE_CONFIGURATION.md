# 数据库配置说明

## 问题描述

当前PostgreSQL数据库连接失败，密码认证错误。

## 解决方案

### 方案1: 修复PostgreSQL密码（推荐用于生产环境）

1. 重置PostgreSQL密码：
```bash
# Windows
psql -U postgres
ALTER USER postgres WITH PASSWORD 'postgres';
```

2. 或者更新.env文件中的密码为实际密码

### 方案2: 使用SQLite（推荐用于开发/测试）

SQLite不需要额外的数据库服务，适合开发和测试。

更新.env文件：
```bash
# 使用SQLite（开发/测试）
DATABASE_URL=sqlite:///./nautilus.db

# 或使用内存数据库（测试）
# DATABASE_URL=sqlite:///:memory:
```

### 方案3: 使用Docker PostgreSQL

```bash
docker run -d \
  --name nautilus-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=nautilus \
  -p 5432:5432 \
  postgres:15
```

## 当前状态

- ✅ Prometheus指标重复注册问题已修复
- ⚠️ 数据库连接问题（环境配置问题，非代码问题）

## 测试策略

所有测试使用内存SQLite数据库，不依赖外部PostgreSQL：

```python
# conftest.py
@pytest.fixture(scope="function")
def db_session(test_db):
    """使用SQLite内存数据库进行测试"""
    return "sqlite:///:memory:"
```

这样测试可以独立运行，不受数据库环境影响。

## 建议

1. **开发环境**: 使用SQLite（简单快速）
2. **测试环境**: 使用SQLite内存数据库（已配置）
3. **生产环境**: 使用PostgreSQL（性能更好）

## 验证

测试不依赖PostgreSQL，可以正常运行：
```bash
pytest tests/ -v
```
