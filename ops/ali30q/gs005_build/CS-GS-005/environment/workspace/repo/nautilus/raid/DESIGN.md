# Raid 机制 - 双Agent审查模式

## 什么是 Raid 2？

类比代码审查：
- Agent A 写代码 (执行者)
- Agent B 审查代码 (审查者)
- 如果审查通过 → 任务完成
- 如果审查不通过 → 重新执行或仲裁

## 核心价值

| 指标 | 单Agent | Raid 2 |
|:---|:---|:---|
| 准确率 | ~90% | ~95% |
| 错误发现 | 低 | 高 |
| 成本 | 1x | 1.5x |

## 工作流程

```
1. 用户提交任务
      ↓
2. 执行Agent (Agent A) 执行任务 → 生成结果
      ↓
3. 审查Agent (Agent B) 验证结果 → 给出评分
      ↓
4. 评分判定
   - ≥80分 → 通过 ✅
   - 60-79分 → 仲裁 ⚠️
   - <60分 → 拒绝 ❌
```

## 评分维度

| 维度 | 权重 | 说明 |
|:---|:---|:---|
| 准确性 | 40% | 结果是否正确 |
| 完整性 | 30% | 是否覆盖需求 |
| 效率 | 20% | 执行时间/资源 |
| 可读性 | 10% | 结果清晰度 |

## API 接口

```bash
# 提交任务
POST /api/raid/submit
{
  "task": "帮我写一个排序算法",
  "raid_level": 2
}

# 查询状态
GET /api/raid/status/{task_id}

# 统计
GET /api/raid/stats
```

## 状态码

- `pending` - 待执行
- `executing` - 执行中
- `reviewing` - 审查中
- `approved` - 通过
- `rejected` - 拒绝
- `arbitrating` - 仲裁中

## 代码文件

- `nautilus/raid/__init__.py` - 核心逻辑
- `nautilus/raid/routes.py` - API接口
- `nautilus/raid/README.md` - 说明文档
