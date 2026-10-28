# 依赖和许可证审查报告

## 执行时间
2026-03-14

## Backend 依赖分析

### 核心依赖 (Production)

| 包名 | 版本 | 许可证 | 状态 |
|------|------|--------|------|
| fastapi | ≥0.104.1 | MIT | ✅ 兼容 |
| uvicorn | ≥0.24.0 | BSD-3-Clause | ✅ 兼容 |
| sqlalchemy | ≥2.0.0 | MIT | ✅ 兼容 |
| pydantic | ≥2.5.0 | MIT | ✅ 兼容 |
| python-jose | ≥3.3.0 | MIT | ✅ 兼容 |
| web3 | ≥6.0.0 | MIT | ✅ 兼容 |
| redis | ≥4.5.0 | MIT | ✅ 兼容 |
| chromadb | ≥0.4.0 | Apache-2.0 | ✅ 兼容 |
| langgraph | ≥0.0.20 | MIT | ✅ 兼容 |
| langchain | ≥0.1.0 | MIT | ✅ 兼容 |
| alembic | ≥1.13.0 | MIT | ✅ 兼容 |
| python-socketio | ≥5.10.0 | MIT | ✅ 兼容 |
| prometheus-client | ≥0.19.0 | Apache-2.0 | ✅ 兼容 |
| pandas | ≥2.0.0 | BSD-3-Clause | ✅ 兼容 |
| numpy | ≥1.24.0 | BSD-3-Clause | ✅ 兼容 |

### AI/ML 依赖

| 包名 | 版本 | 许可证 | 状态 | 注意事项 |
|------|------|--------|------|----------|
| torch | ≥2.0.0 | BSD-3-Clause | ✅ 兼容 | 体积大 (~2GB) |
| transformers | ≥4.30.0 | Apache-2.0 | ✅ 兼容 | |
| sentence-transformers | ≥2.2.0 | Apache-2.0 | ✅ 兼容 | |

### 开发依赖

| 包名 | 版本 | 许可证 | 状态 |
|------|------|--------|------|
| pytest | ≥7.4.3 | MIT | ✅ 兼容 |
| pytest-cov | ≥4.1.0 | MIT | ✅ 兼容 |
| pytest-asyncio | ≥0.21.1 | Apache-2.0 | ✅ 兼容 |

## Frontend 依赖分析

### 核心依赖

| 包名 | 版本 | 许可证 | 状态 |
|------|------|--------|------|
| react | ^18.3.0 | MIT | ✅ 兼容 |
| react-dom | ^18.3.0 | MIT | ✅ 兼容 |
| react-router-dom | ^6.21.3 | MIT | ✅ 兼容 |
| @tanstack/react-query | ^5.90.21 | MIT | ✅ 兼容 |
| axios | ^1.6.5 | MIT | ✅ 兼容 |
| zustand | ^4.5.0 | MIT | ✅ 兼容 |

### Web3 依赖

| 包名 | 版本 | 许可证 | 状态 |
|------|------|--------|------|
| ethers | ^6.10.0 | MIT | ✅ 兼容 |
| viem | ^2.47.0 | MIT | ✅ 兼容 |
| wagmi | ^3.5.0 | MIT | ✅ 兼容 |
| @metamask/sdk | ^0.33.1 | MIT | ✅ 兼容 |

### UI 依赖

| 包名 | 版本 | 许可证 | 状态 |
|------|------|--------|------|
| tailwindcss | ^4.0.0 | MIT | ✅ 兼容 |
| framer-motion | ^12.35.1 | MIT | ✅ 兼容 |
| lucide-react | ^0.312.0 | ISC | ✅ 兼容 |
| recharts | ^3.8.0 | MIT | ✅ 兼容 |

### 开发依赖

| 包名 | 版本 | 许可证 | 状态 |
|------|------|--------|------|
| vite | ^5.0.11 | MIT | ✅ 兼容 |
| typescript | ^5.3.3 | Apache-2.0 | ✅ 兼容 |
| vitest | ^4.0.18 | MIT | ✅ 兼容 |
| eslint | ^8.56.0 | MIT | ✅ 兼容 |
| prettier | ^3.2.4 | MIT | ✅ 兼容 |

## 许可证兼容性总结

### ✅ 所有依赖许可证兼容

所有依赖使用的许可证：
- **MIT License**: 最宽松，完全兼容
- **Apache-2.0**: 宽松，完全兼容
- **BSD-3-Clause**: 宽松，完全兼容
- **ISC**: 类似 MIT，完全兼容

### 无冲突

- ✅ 无 GPL 许可证（会要求开源）
- ✅ 无专有许可证
- ✅ 无限制性许可证

## 依赖优化建议

### 1. 可选依赖优化

**Torch (PyTorch)** - 体积 ~2GB:
```python
# 如果不使用本地 AI 模型，可以移除
# torch>=2.0.0
# transformers>=4.30.0
# sentence-transformers>=2.2.0

# 改用 API 调用外部模型
```

**建议**:
- 如果使用云端 AI 服务，可以移除这些依赖
- 如果需要本地推理，保留但在文档中说明

### 2. 未使用的依赖

需要检查是否实际使用：
```bash
# 检查未使用的依赖
pip-autoremove --list
```

可能未使用的包：
- `asteval` - 需要确认是否使用
- `boto3` - AWS SDK，如果不用 AWS 可以移除
- `bandit` - 安全检查工具，应该在 dev dependencies

### 3. 版本固定

**当前**: 使用 `>=` 允许自动升级
```
fastapi>=0.104.1
```

**建议**: 开源项目使用范围版本
```
fastapi>=0.104.1,<0.105.0
```

或使用 `requirements.lock` 固定精确版本。

## 依赖安全检查

### 运行安全审计

```bash
# Python
pip install pip-audit
pip-audit

# Node.js
npm audit
npm audit fix
```

### 设置 Dependabot

创建 `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

## 依赖文档

### 创建依赖说明

在 README.md 中添加：

```markdown
## 依赖说明

### 核心依赖
- **FastAPI**: Web 框架
- **SQLAlchemy**: ORM
- **Web3.py**: 区块链集成
- **ChromaDB**: 向量数据库
- **LangGraph**: Agent 引擎

### 可选依赖
- **PyTorch**: 本地 AI 模型（可选，体积大）
- **Boto3**: AWS 集成（可选）

### 安装选项

最小安装（无本地 AI）:
```bash
pip install -r requirements-minimal.txt
```

完整安装:
```bash
pip install -r requirements.txt
```
```

## 行动项

### 立即执行

1. **创建 requirements-minimal.txt** (不含 torch)
2. **运行安全审计**
3. **设置 Dependabot**
4. **更新 README 说明依赖**

### 后续优化

1. **移除未使用的依赖**
2. **固定版本范围**
3. **定期更新依赖**

## 结论

✅ **所有依赖许可证兼容，可以安全开源**

主要建议：
1. 考虑将 PyTorch 设为可选依赖（减小安装体积）
2. 设置 Dependabot 自动更新
3. 定期运行安全审计

## 下一步

继续 Task #10: Docker化和部署配置
