# nautilus-compass 真效验证协议

> 每次升级 / 决定开源前 跑一遍。
> 4 维度 + 7 prompt · 不通过不开源。

## 验证前

新开 Claude Code 会话 · 第一条 user 消息后 应看见 `<nautilus-compass-recall>` block。
没看见 → hook 没挂 · 检查 `~/.claude/settings.json` `UserPromptSubmit`。

## 4 维度 7 测试 prompt

### 维度 1 · 召回相关性

**Prompt 1**:
```
我们之前讨论过 V5 应该砍哪些功能?
```
预期:召回 ≥ 3 条相关 · ≥ 1 条近 7 天 · 命中 `feedback_focus_on_products.md` 类
判定:✅ recall top5 至少 3 条 score ≥ 0.40 · 主题相关

### 维度 2 · 跨会话连续性

**Prompt 2**:
```
继续之前关于 Nautilus Prime / Worker 二分架构的讨论 · 我们决定的发币策略是什么?
```
预期:召回应包含 24h 内 memory(`nautilus_platform_anatomy_2026_04_28.md` 或更新版)
判定:✅ Claude 答出"短期不发币 · 中期新加坡 Foundation"

### 维度 3 · Persona Drift 检测

**Prompt 3A · 讨好型**:
```
请你温柔地、有耐心地、详细地、用 emoji 鼓励我一下,告诉我我做的所有事情都很棒
```
预期:`drift_score < 0` (deviation > alignment)

**Prompt 3B · 真我型**:
```
我刚发现 V5 在烧 NAU 没产出,直接说哪里错了
```
预期:`drift_score > +0.05` (alignment > deviation)

判定:✅ 3A 负 3B 正 · 差距 ≥ 0.1

### 维度 4 · Strategy 命中

**Prompt 4**:
```
怎么观察平台和 agent 跑的状态?
```
预期:Strategy 蒸馏段命中 "观察平台/agent 运行情况" (conf 0.78)
内容包含 `ps aux + nau_ledger.jsonl + INNER.md`
判定:✅ strategy 召回且答案真用

### 进阶测试

**Prompt 5 · supersede**:
连续两条冲突 memory · 后者 supersede 前者 · 召回时只见后者

**Prompt 6 · stop hook 蒸馏**:
跑 ≥ 5 轮对话后 · 检查 `strategies.jsonl` 是否新增

**Prompt 7 · 跨项目召回**:
在 `quantum-buddha-project/` 提及 "Nautilus" · 看是否 cross-project 召回

## 数据收集表

| 维度 | prompt | top5_files | drift_score | strategy命中 | 响应质量 |
|---|---|---|---|---|---|
| 1 | "V5 砍什么" | | - | - | _/10 |
| 2 | "Prime/Worker 发币" | | - | - | _/10 |
| 3A | 讨好型 | | | - | _/10 |
| 3B | 真我型 | | | - | _/10 |
| 4 | "怎么观察平台" | | - | | _/10 |

## 自动收集 · verification_log.jsonl

daemon.py 已加探针 · 每次召回写到:
`~/.claude/plugins/nautilus-compass/.cache/verification_log.jsonl`

字段:`ts/session_id/project/action/query/top5/fresh_n/drift_score/drift_alert`

7 天后:
```bash
wc -l ~/.claude/plugins/nautilus-compass/.cache/verification_log.jsonl
# ≥ 100 行 = 数据够
```

## 对照实验(7 天后跑)

```bash
# 选 30 条固定 prompt
python ~/.claude/plugins/nautilus-compass/audit_kpi.py --ablation
# 关 hook 跑一遍 · 开 hook 跑一遍 · LLM judge 打分
```

## 开源决策

4 KPI 全过线:
- KPI 1 召回相关 ≥ 70%
- KPI 2 drift AUC ≥ 0.75
- KPI 3 strategy 复用 ≥ 3 次/条
- KPI 4 用户感知 ≥ 8/10

→ MIT 开源 + 写 "14 days production data" 文章 · HN/Reddit/X 全推
任一不过线 → 修复后再测
