# Everything Claude Code 快速参考

## ✅ 配置完成

- ✅ 插件已启用
- ✅ 市场源已配置
- ✅ Token优化已启用（减少60%成本）
- ✅ TypeScript规则已安装

---

## 🚀 常用命令速查

### 开发工作流

```bash
# 1. 规划新功能
/everything-claude-code:plan "功能描述"

# 2. 测试驱动开发
/everything-claude-code:tdd

# 3. 代码审查
/everything-claude-code:code-review

# 4. 安全扫描
/everything-claude-code:security-scan

# 5. E2E测试
/everything-claude-code:e2e
```

### 问题修复

```bash
# 修复构建错误
/everything-claude-code:build-fix

# 重构清理
/everything-claude-code:refactor-clean

# 测试覆盖率
/everything-claude-code:test-coverage
```

### 学习和优化

```bash
# 从会话中学习
/everything-claude-code:learn

# 保存检查点
/everything-claude-code:checkpoint

# 运行验证
/everything-claude-code:verify
```

---

## 📋 完整命令列表（33个）

| 命令 | 功能 |
|------|------|
| `/plan` | 创建实现计划 |
| `/tdd` | 测试驱动开发 |
| `/code-review` | 代码审查 |
| `/security-scan` | 安全扫描 |
| `/build-fix` | 修复构建错误 |
| `/e2e` | E2E测试 |
| `/refactor-clean` | 清理死代码 |
| `/doc-update` | 更新文档 |
| `/test-coverage` | 测试覆盖率 |
| `/learn` | 提取模式 |
| `/checkpoint` | 保存状态 |
| `/verify` | 验证循环 |
| `/skill-create` | 创建技能 |

---

## 🎯 典型工作流

### 新功能开发
```
1. /plan "添加用户认证"
2. /tdd
3. 实现代码
4. /code-review
5. /security-scan
6. /e2e
```

### Bug修复
```
1. /tdd  # 先写失败的测试
2. 修复代码
3. /code-review
4. /verify
```

### 代码重构
```
1. /refactor-clean
2. /test-coverage
3. /code-review
4. /doc-update
```

### 准备上线
```
1. /security-scan
2. /e2e
3. /test-coverage
4. /code-review
5. /checkpoint
```

---

## 🤖 13个专业代理

- **planner** - 功能规划
- **architect** - 系统设计
- **tdd-guide** - TDD指导
- **code-reviewer** - 代码审查
- **security-reviewer** - 安全审查
- **build-error-resolver** - 构建修复
- **e2e-runner** - E2E测试
- **refactor-cleaner** - 代码清理
- **doc-updater** - 文档更新
- **go-reviewer** - Go审查
- **python-reviewer** - Python审查
- **database-reviewer** - 数据库审查
- **learning-agent** - 学习代理

---

## 💡 使用技巧

### 1. 组合使用
```bash
# 完整的开发循环
/plan "新功能" && /tdd && /code-review
```

### 2. 针对性审查
```bash
# Python项目
/everything-claude-code:python-reviewer

# Go项目
/everything-claude-code:go-reviewer

# 数据库相关
/everything-claude-code:database-reviewer
```

### 3. 持续学习
```bash
# 定期提取模式
/learn

# 保存重要状态
/checkpoint "完成用户认证模块"
```

---

## 🔧 安装其他语言支持

```bash
cd "/c/Users/chunx/AppData/Local/Programs/CC Switch/everything-claude-code"

# Python
bash install.sh python

# Go
bash install.sh golang

# 多个语言
bash install.sh typescript python golang
```

---

## 📊 Token优化

当前配置已启用：
- `MAX_THINKING_TOKENS: 10000`
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: 50`

**预计节省60%成本**

---

## 🎯 Nautilus项目推荐工作流

### 后端API
```bash
# 1. 代码审查
/code-review

# 2. 安全扫描
/security-scan

# 3. 测试覆盖
/test-coverage

# 4. Python专项审查
/everything-claude-code:python-reviewer

# 5. 数据库审查
/everything-claude-code:database-reviewer
```

### 前端网站
```bash
# 1. 代码审查
/code-review

# 2. E2E测试
/e2e

# 3. 性能优化
/everything-claude-code:refactor-clean

# 4. 文档更新
/doc-update
```

---

## 📚 资源链接

- **简明指南**: https://x.com/affaanmustafa/status/2012378465664745795
- **详细指南**: https://x.com/affaanmustafa/status/2014040193557471352
- **GitHub**: https://github.com/affaan-m/everything-claude-code

---

## ✨ 开始使用

现在你可以直接使用这些命令了！试试：

```bash
/everything-claude-code:plan "你的任务"
```

或者简写（如果配置了别名）：

```bash
/plan "你的任务"
```

---

**配置完成时间**: 2026-02-28 00:50
**状态**: ✅ 就绪
**Token优化**: ✅ 已启用

**开始使用这些强大的工具吧！** 🚀
