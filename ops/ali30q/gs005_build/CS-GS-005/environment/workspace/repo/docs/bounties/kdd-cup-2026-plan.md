# KDD Cup 2026: Data Agents — Nautilus 参赛方案

## 赛题概述

**官网**: https://dataagent.top/
**注册截止**: 2026-04-23 (AoE) — **19天**
**Phase 1 提交**: 2026-05-23
**Phase 2 提交**: 2026-06-30
**奖金**: Champion $6K, Runner-up $4K, 3rd $2.5K

## 为什么这是 Nautilus 的完美战场

赛题要求：**构建自主 AI agent，处理异构数据包（数据库、PDF、JSON、图表），自动分解问题、选择工具、多步推理、合成结果。**

这就是 Nautilus 的 RAID + A2A + 多模态的精确应用场景。

## 架构设计: 5-Agent RAID 系统

```
User Question
    │
    ▼
┌─────────────────────────┐
│   Orchestrator Agent    │  ← KAIROS 级别决策
│   (Task Decomposition)  │
└─────────┬───────────────┘
          │ A2A 消息分发
    ┌─────┼─────┬─────┐
    ▼     ▼     ▼     ▼
┌──────┐┌──────┐┌──────┐┌──────┐
│ SQL  ││ Doc  ││ Chart││ Calc │
│Agent ││Agent ││Agent ││Agent │
│      ││      ││      ││      │
│SQLite││PDF/  ││PNG   ││JSON/ │
│CSV   ││DOCX  ││Chart ││Math  │
└──┬───┘└──┬───┘└──┬───┘└──┬───┘
   │       │       │       │
   └───────┴───┬───┴───────┘
               ▼
      ┌────────────────┐
      │ Synthesis Agent │  ← RAID-3 共识
      │ (Answer + Verify)│
      └────────────────┘
```

### Agent 职责

1. **Orchestrator**: 解析自然语言问题 → 识别需要哪些数据源 → 分发子任务
2. **SQL Agent**: 处理 SQLite/CSV 结构化数据，生成并执行 SQL 查询
3. **Document Agent**: 处理 PDF/DOCX 非结构化文档，提取关键信息
4. **Chart Agent**: 处理 PNG 图表，用 Gemini Vision 或 MiniMax 理解视觉数据
5. **Calculation Agent**: 执行数学计算、统计分析、数据转换
6. **Synthesis Agent**: 聚合所有子结果，RAID-3 交叉验证，输出最终答案

### 通信协议 (A2A)

```python
# Agent 间消息格式
{
    "from_agent": "orchestrator",
    "to_agent": "sql_agent",
    "message_type": "task_assignment",
    "payload": {
        "sub_question": "What is the total revenue in Q3 2024?",
        "data_sources": ["sales.sqlite", "quarterly_report.csv"],
        "expected_output": "numeric_value"
    },
    "correlation_id": "kdd_q42_sub1"
}
```

### LLM 分配策略

| Agent | 主力 LLM | 理由 |
|-------|---------|------|
| Orchestrator | Gemini 3.1 Pro | 需要最强推理，免费 |
| SQL Agent | MiniMax M2.7 Highspeed | 快速生成 SQL, 100 TPS |
| Document Agent | Gemini 3.1 Pro | PDF 理解需要长上下文 |
| Chart Agent | Gemini Vision | 图像理解 |
| Calculation Agent | MiniMax M2.7 | 数学计算，快 |
| Synthesis Agent | Gemini 3.1 Pro | 需要综合推理 |

## 评分标准

> "A prediction receives 1 only when it completely and accurately covers all gold columns; otherwise it receives 0."

**Binary 评分** — 必须包含所有正确列。这意味着：
- 不能遗漏任何数据列
- 必须精确匹配
- RAID-3 共识验证特别有用——3个 agent 独立分析，取共识结果

## 实施路线图

### Week 1 (Apr 4-10): 注册 + 基础框架
- [ ] 注册 KDD Cup (Google Form)
- [ ] 下载 DataAgent-Bench 数据集
- [ ] 搭建 5-agent 框架骨架
- [ ] 实现 A2A 消息传递管道

### Week 2 (Apr 11-17): 核心能力
- [ ] SQL Agent: text-to-SQL + 执行 + 结果解析
- [ ] Document Agent: PDF/DOCX 提取 + 摘要
- [ ] Chart Agent: 图表理解 + 数据提取
- [ ] Orchestrator: 问题分解逻辑

### Week 3 (Apr 18-24): 集成 + 测试
- [ ] 端到端集成测试
- [ ] 在 DataAgent-Bench Easy/Medium 级别测试
- [ ] 调优 prompt 和 agent 协作逻辑
- [ ] 首次提交到 Phase 1 排行榜

### Week 4-7 (Apr 25 - May 23): 优化冲刺
- [ ] 处理 Hard/Extreme 级别任务
- [ ] RAID-3 共识验证提升准确率
- [ ] 错误分析 + 针对性优化
- [ ] Phase 1 最终提交

## 竞争优势

1. **多模态原生**: Gemini Vision + MiniMax image-01 处理图表
2. **多 LLM 引擎**: 不依赖单一模型，混合使用最擅长的
3. **A2A 通信**: 真正的 agent 间协作，不是简单的串行调用
4. **RAID-3 共识**: 多 agent 独立分析后投票，提升准确率
5. **开源平台**: 在 Nautilus 上运行，展示平台能力

## 技术风险

1. **数据规模**: Extreme 级别 128K+ tokens，需要分块处理
2. **Binary 评分**: 全对全错，容错率为零
3. **模型幻觉**: 需要严格的 ground-truth 验证
4. **时间压力**: 19 天完成注册+开发

## 资源需求

- Gemini API: 免费额度足够
- MiniMax: 4500 calls/5h Token Plan
- 服务器: 现有 cloud server
- 人力: KAIROS + MiniMax Agent + Claude 全力投入
