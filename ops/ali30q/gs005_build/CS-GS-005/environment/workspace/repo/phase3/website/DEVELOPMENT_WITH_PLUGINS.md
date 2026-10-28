# Nautilus网站开发 - Everything Claude Code 使用指南

## 🎯 网站开发推荐工作流

### 阶段1: 规划和架构（开始前）

```bash
# 1. 规划新页面或功能
/everything-claude-code:plan "添加任务市场页面"

# 2. 架构设计决策
/everything-claude-code:architect "设计状态管理方案"
```

**适用场景**:
- 添加新页面
- 设计组件结构
- 选择技术方案
- API集成规划

---

### 阶段2: 测试驱动开发（编码中）

```bash
# 1. TDD工作流
/everything-claude-code:tdd

# 2. 组件测试
/everything-claude-code:test-coverage
```

**适用场景**:
- 开发新组件
- 添加业务逻辑
- 表单验证
- API调用

**示例**:
```bash
# 开发用户认证组件
/tdd "创建LoginForm组件，包含邮箱和密码验证"
```

---

### 阶段3: 代码审查（编码后）

```bash
# 1. 通用代码审查
/everything-claude-code:code-review

# 2. 安全扫描
/everything-claude-code:security-scan

# 3. 性能优化
/everything-claude-code:refactor-clean
```

**检查内容**:
- React最佳实践
- TypeScript类型安全
- 性能优化（useMemo, useCallback）
- 安全问题（XSS, CSRF）
- 死代码清理

---

### 阶段4: E2E测试（功能完成后）

```bash
# 1. 生成E2E测试
/everything-claude-code:e2e

# 2. 运行测试
/everything-claude-code:verify
```

**测试场景**:
- 用户注册流程
- 登录流程
- 任务创建流程
- 支付流程
- 页面导航

**示例**:
```bash
/e2e "测试用户从注册到创建第一个任务的完整流程"
```

---

### 阶段5: 文档和学习（持续）

```bash
# 1. 更新文档
/everything-claude-code:doc-update

# 2. 提取模式
/everything-claude-code:learn

# 3. 保存检查点
/everything-claude-code:checkpoint "完成任务市场页面"
```

---

## 🚀 具体应用场景

### 1. 开发新页面

**任务市场页面示例**:

```bash
# Step 1: 规划
/plan "开发任务市场页面，包含任务列表、筛选、搜索和分页功能"

# Step 2: TDD开发
/tdd
# 然后编写代码...

# Step 3: 代码审查
/code-review

# Step 4: E2E测试
/e2e "测试任务市场的筛选和搜索功能"

# Step 5: 文档
/doc-update
```

---

### 2. 组件开发

**用户认证组件示例**:

```bash
# Step 1: 规划组件结构
/plan "创建LoginForm和RegisterForm组件，使用React Hook Form和Zod验证"

# Step 2: TDD
/tdd
# 先写测试，再实现组件

# Step 3: 审查
/code-review

# Step 4: 安全检查
/security-scan
```

---

### 3. API集成

**后端API集成示例**:

```bash
# Step 1: 规划API层
/plan "创建API客户端，使用axios和React Query"

# Step 2: TDD
/tdd
# 测试API调用、错误处理、重试逻辑

# Step 3: 审查
/code-review

# Step 4: 安全扫描
/security-scan
# 检查token存储、CORS、XSS防护
```

---

### 4. 状态管理

**全局状态管理示例**:

```bash
# Step 1: 架构设计
/architect "选择状态管理方案：Zustand vs Context API"

# Step 2: 实现
/tdd
# 测试状态更新、持久化、中间件

# Step 3: 审查
/code-review
```

---

### 5. 性能优化

**优化现有代码**:

```bash
# Step 1: 清理死代码
/refactor-clean

# Step 2: 代码审查
/code-review
# 检查：
# - 不必要的re-render
# - 缺少的useMemo/useCallback
# - 大型bundle
# - 图片优化

# Step 3: 测试覆盖
/test-coverage
```

---

## 📋 完整开发流程示例

### 场景：开发"任务详情页"

```bash
# 1. 规划（5分钟）
/plan "开发任务详情页，显示任务信息、接受任务、提交结果功能"

# 2. 架构设计（5分钟）
/architect "设计任务详情页的数据流和组件结构"

# 3. TDD开发（30分钟）
/tdd
# 编写测试和实现代码...

# 4. 代码审查（10分钟）
/code-review

# 5. 安全扫描（5分钟）
/security-scan

# 6. E2E测试（15分钟）
/e2e "测试任务详情页的完整用户流程"

# 7. 性能检查（5分钟）
/refactor-clean

# 8. 文档更新（5分钟）
/doc-update

# 9. 保存检查点（1分钟）
/checkpoint "完成任务详情页开发"

# 总计：约80分钟
```

---

## 🎯 针对Nautilus网站的具体建议

### 当前状态
- ✅ 基础组件库完成
- ✅ 首页完成
- ⏳ 其他页面待开发
- ⏳ API集成待完成

### 推荐使用的命令

#### 1. 开发新页面时
```bash
/plan "页面描述"
/tdd
/code-review
/e2e
```

#### 2. API集成时
```bash
/plan "API集成方案"
/tdd
/security-scan
/code-review
```

#### 3. 组件开发时
```bash
/tdd
/code-review
/refactor-clean
```

#### 4. 准备上线前
```bash
/security-scan
/e2e
/test-coverage
/code-review
/doc-update
```

---

## 💡 最佳实践

### 1. 始终从规划开始
```bash
/plan "明确的任务描述"
```

### 2. 使用TDD
```bash
/tdd
# 先写测试，再写代码
```

### 3. 定期审查
```bash
# 每完成一个功能
/code-review
```

### 4. 安全第一
```bash
# 涉及用户数据时
/security-scan
```

### 5. E2E覆盖关键流程
```bash
# 用户注册、登录、支付等
/e2e "关键流程描述"
```

---

## 🔧 实用技巧

### 1. 组合命令
```bash
# 快速开发循环
/plan && /tdd && /code-review
```

### 2. 针对性审查
```bash
# React组件审查
/code-review "重点检查React hooks使用和性能"

# 安全审查
/security-scan "重点检查XSS和CSRF防护"
```

### 3. 增量开发
```bash
# 每个小功能都保存检查点
/checkpoint "完成用户头像上传功能"
```

---

## 📊 预期效果

使用这些工具后：

- ✅ **代码质量**: 提升50%+
- ✅ **测试覆盖**: 达到80%+
- ✅ **开发速度**: 提升30%+
- ✅ **Bug减少**: 减少60%+
- ✅ **安全性**: 提升显著

---

## 🚀 立即开始

### 下一步开发任务建议

1. **任务市场页面**
```bash
/plan "开发任务市场页面，包含任务列表、筛选、搜索、分页"
```

2. **用户认证**
```bash
/plan "集成后端API，实现用户注册、登录、JWT管理"
```

3. **任务详情页**
```bash
/plan "开发任务详情页，显示任务信息、接受任务、提交结果"
```

4. **用户中心**
```bash
/plan "开发用户中心，显示个人信息、任务历史、收益统计"
```

---

**准备好了吗？开始使用这些强大的工具开发Nautilus网站吧！** 🚀

**第一步**:
```bash
/everything-claude-code:plan "开发任务市场页面"
```
