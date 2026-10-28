# Raid 机制 - 双Agent审查模式

## 设计目标

实现 Raid 2 模式：执行Agent + 审查Agent 双重验证

## 核心流程

```
用户提交任务
    ↓
执行Agent (Agent A) → 生成初稿结果
    ↓
审查Agent (Agent B) → 验证结果
    ↓
比对结果
    ↓
一致? → 通过 → 奖励分发
不一致? → 仲裁 → 第3个Agent或用户决定
```

## 数据结构

### RaidTask
- task_id: 任务ID
- original_task: 原始任务
- executor_result: 执行结果
- reviewer_result: 审查结果
- status: pending/executing/reviewing/approved/rejected/arbitrating
- raid_level: 1/2/3

### ReviewResult
- result_id: 审查ID
- score: 评分 (0-100)
- feedback: 反馈
- approved: 是否通过
- issues: 问题列表

## API接口

### POST /api/raid/submit
提交任务启用Raid 2

### GET /api/raid/{task_id}/status
查询Raid状态

### POST /api/raid/{task_id}/review
提交审查结果

### POST /api/raid/{task_id}/arbitrate
仲裁决定

## 评分标准

| 维度 | 权重 | 说明 |
|:---|:---|:---|
| 准确性 | 40% | 结果是否正确 |
| 完整性 | 30% | 是否覆盖所有需求 |
| 效率 | 20% | 执行时间/资源 |
| 可读性 | 10% | 代码/结果清晰度 |

## 阈值配置

- 通过阈值: >= 80分
- 仲裁阈值: 60-79分
- 拒绝阈值: < 60分
