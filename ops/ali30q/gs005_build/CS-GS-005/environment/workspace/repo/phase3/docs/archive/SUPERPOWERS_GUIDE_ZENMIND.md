# Superpowers技能系统 - 禅心AI项目应用指南

**目标项目**: 禅心AI (ZenMind AI)
**当前状态**: V3.5部署准备完成，待用户配置
**应用目的**: 提升开发效率和代码质量

---

## 🎯 什么是Superpowers？

Superpowers是一套完整的AI编程工作流系统，为Claude Code提供14个可自动触发的"技能"，帮助你：
- 系统化地调试问题
- 强制执行TDD流程
- 并行开发多个功能
- 结构化代码审查
- 隔离开发环境

**核心理念**: 不是建议，而是强制执行的工作流

---

## 📚 14个核心技能

### 🐛 调试和测试技能

**1. systematic-debugging（系统化调试）**
- **何时使用**: 遇到任何bug、测试失败或意外行为
- **4阶段流程**: 重现问题 → 隔离根因 → 实施修复 → 验证修复
- **禅心AI应用**:
  - 修复Redis缓存问题
  - 解决WebSocket连接不稳定
  - 调试多人格切换bug

**2. test-driven-development（TDD）**
- **何时使用**: 实现任何功能或修复bug前
- **核心原则**: 写测试 → 看它失败 → 写代码 → 看它通过 → 提交
- **禅心AI应用**:
  - 为新的API端点编写测试
  - 为UI组件添加测试
  - 为Redis缓存逻辑编写测试

**3. verification-before-completion（完成前验证）**
- **何时使用**: 声称工作完成、修复或通过前
- **要求**: 运行验证命令，确认输出，证据优先
- **禅心AI应用**:
  - 部署前验证所有功能
  - 确认性能优化真正有效
  - 验证多人格系统正常工作

---

### 🤝 协作和审查技能

**4. brainstorming（头脑风暴）**
- **何时使用**: 开始编码前，需要细化需求
- **流程**: 提问 → 探索方案 → 分段展示设计 → 保存文档
- **禅心AI应用**:
  - 规划新功能（如知识图谱可视化）
  - 设计多语言支持方案
  - 探索向量数据库集成策略

**5. writing-plans（编写计划）**
- **何时使用**: 设计批准后，开始实施前
- **输出**: 2-5分钟的小任务，包含文件路径、完整代码、验证步骤
- **禅心AI应用**:
  - 规划知识图谱可视化实施
  - 制定多语言支持计划
  - 设计性能优化路线图

**6. requesting-code-review（请求代码审查）**
- **何时使用**: 完成任务、实现主要功能或合并前
- **流程**: 预审查清单 → 按严重性报告问题 → 阻塞关键问题
- **禅心AI应用**:
  - 审查Redis缓存实现
  - 审查多人格系统代码
  - 审查WebSocket实现

**7. receiving-code-review（接收代码审查）**
- **何时使用**: 收到代码审查反馈时
- **要求**: 技术严谨，验证建议，不盲目实施
- **禅心AI应用**:
  - 响应性能优化建议
  - 处理安全审查反馈
  - 改进代码质量问题

---

### 🚀 开发流程技能

**8. subagent-driven-development（子Agent驱动开发）**
- **何时使用**: 有计划后，需要快速迭代
- **特点**: 为每个任务派发新子Agent，两阶段审查
- **禅心AI应用**:
  - 并行开发多个UI组件
  - 同时实现多个API端点
  - 并行优化多个性能瓶颈

**9. dispatching-parallel-agents（派发并行Agent）**
- **何时使用**: 面对2+个独立任务
- **要求**: 无共享状态，无顺序依赖
- **禅心AI应用**:
  - 同时开发前端和后端功能
  - 并行编写文档和测试
  - 同时优化多个独立模块

**10. executing-plans（执行计划）**
- **何时使用**: 有书面实施计划，需要批量执行
- **特点**: 分批执行，人工检查点
- **禅心AI应用**:
  - 执行多语言支持计划
  - 实施性能优化路线图
  - 部署知识图谱功能

**11. using-git-worktrees（使用Git工作树）**
- **何时使用**: 开始功能开发，需要隔离环境
- **特点**: 创建隔离工作空间，新分支，干净基线
- **禅心AI应用**:
  - 为知识图谱功能创建独立分支
  - 隔离多语言支持开发
  - 并行测试不同优化方案

**12. finishing-a-development-branch（完成开发分支）**
- **何时使用**: 任务完成，所有测试通过
- **选项**: 合并/PR/保留/丢弃
- **禅心AI应用**:
  - 合并知识图谱功能
  - 创建多语言支持PR
  - 清理实验性分支

---

### 📝 元技能

**13. using-superpowers（使用Superpowers）**
- **何时使用**: 开始任何对话
- **作用**: 建立如何查找和使用技能

**14. writing-skills（编写技能）**
- **何时使用**: 创建新技能或编辑现有技能
- **作用**: 遵循最佳实践创建技能

---

## 🎯 禅心AI项目具体应用场景

### 场景1: 实现知识图谱可视化

**步骤1: 头脑风暴**
```
"use brainstorming to explore knowledge graph visualization requirements and design"
```

**步骤2: 编写计划**
```
"use writing-plans to create a detailed implementation plan for knowledge graph visualization"
```

**步骤3: 创建隔离环境**
```
"use using-git-worktrees to create an isolated branch for knowledge graph feature"
```

**步骤4: 子Agent驱动开发**
```
"use subagent-driven-development to implement the knowledge graph plan with parallel agents"
```

**步骤5: 请求审查**
```
"use requesting-code-review to review the knowledge graph implementation"
```

**步骤6: 完成分支**
```
"use finishing-a-development-branch to merge the knowledge graph feature"
```

---

### 场景2: 修复Redis缓存Bug

**步骤1: 系统化调试**
```
"use systematic-debugging to analyze and fix the Redis cache issue"
```

**步骤2: TDD修复**
```
"use test-driven-development to write tests for the Redis cache fix"
```

**步骤3: 验证修复**
```
"use verification-before-completion to verify the Redis cache is working correctly"
```

---

### 场景3: 添加多语言支持

**步骤1: 头脑风暴**
```
"use brainstorming to explore multi-language support strategies"
```

**步骤2: 编写计划**
```
"use writing-plans to create a detailed multi-language implementation plan"
```

**步骤3: 并行开发**
```
"use dispatching-parallel-agents to implement multi-language support in parallel:
- Agent 1: Backend i18n
- Agent 2: Frontend i18n
- Agent 3: Database schema updates"
```

**步骤4: 执行计划**
```
"use executing-plans to implement the multi-language plan in batches"
```

---

### 场景4: 性能优化

**步骤1: 系统化调试**
```
"use systematic-debugging to identify performance bottlenecks"
```

**步骤2: 编写计划**
```
"use writing-plans to create a performance optimization roadmap"
```

**步骤3: TDD优化**
```
"use test-driven-development to write performance tests before optimization"
```

**步骤4: 验证优化**
```
"use verification-before-completion to verify performance improvements"
```

---

## 📊 预期效果

### 开发效率提升

**使用前**:
- 开发时间: 100%
- Bug修复时间: 100%
- 代码质量: 基准

**使用后**:
- 开发时间: -30%（并行开发）
- Bug修复时间: -50%（系统化调试）
- 代码质量: +20%（强制TDD）
- 测试覆盖率: +40%

### 具体指标

**禅心AI项目**:
- 知识图谱开发: 5天 → 3天
- Bug修复速度: +50%
- 测试覆盖率: 60% → 85%
- 代码审查效率: +40%

---

## 🚀 如何开始

### 1. 验证安装

检查Superpowers是否已安装：
```
"what superpowers skills are available?"
```

### 2. 测试技能

尝试使用一个技能：
```
"use systematic-debugging to analyze the current deployment status"
```

### 3. 应用到实际工作

选择一个待办任务，使用相应技能：
```
"use brainstorming to explore the knowledge graph visualization feature"
```

---

## 💡 最佳实践

### 1. 始终使用TDD
- 写测试 → 看它失败 → 写代码 → 看它通过
- 不要跳过任何步骤
- 违反规则的字面意思就是违反规则的精神

### 2. 系统化调试
- 不要靠猜测
- 遵循4阶段流程
- 始终验证修复

### 3. 完成前验证
- 运行验证命令
- 确认输出
- 证据优先于断言

### 4. 并行开发
- 识别独立任务
- 使用并行Agent
- 提高开发效率

### 5. 隔离环境
- 使用Git工作树
- 避免污染主分支
- 安全实验

---

## 📋 禅心AI项目待办任务（使用Superpowers）

### P0 - 立即执行

**1. 部署验证**
```
"use verification-before-completion to verify V3.5 deployment readiness"
```

**2. 性能测试**
```
"use systematic-debugging to analyze and optimize performance bottlenecks"
```

### P1 - 短期执行

**3. 知识图谱可视化**
```
"use brainstorming to explore knowledge graph visualization"
"use writing-plans to create implementation plan"
"use subagent-driven-development to implement"
```

**4. 多语言支持**
```
"use brainstorming to explore multi-language support"
"use dispatching-parallel-agents to implement in parallel"
```

### P2 - 中期执行

**5. 向量数据库集成**
```
"use using-git-worktrees to create isolated branch"
"use test-driven-development to implement with tests"
```

**6. 代码质量提升**
```
"use requesting-code-review to review all major modules"
```

---

## 🎓 学习资源

- **官方文档**: https://github.com/obra/superpowers
- **博客文章**: https://blog.fsck.com/2025/10/09/superpowers/
- **技能目录**: ~/.claude/skills/

---

## ✅ 总结

**Superpowers为禅心AI项目提供**:
- ✅ 系统化的开发流程
- ✅ 强制的质量保证
- ✅ 并行开发能力
- ✅ 结构化的问题解决
- ✅ 完整的验证机制

**立即开始使用，提升开发效率30%+！** 🚀

---

**创建时间**: 2026-03-09
**适用项目**: 禅心AI (ZenMind AI)
**状态**: ✅ 可立即使用
