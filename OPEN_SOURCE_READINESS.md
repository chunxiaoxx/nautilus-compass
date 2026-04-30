# zenmind-mem · Open Source Readiness Brief

> **当前状态 (2026-04-29)**: 内部用 ✅ · 公开开源待 LongMemEval 数据 + 6 月维护承诺

## 一句话定位

> The only Claude Code memory plugin with **task-shaped persona drift L3 detection** + **DPT-style strategy distillation** — so your AI doesn't slip into bad habits across sessions.

## 真实数据 (实测 vs 业界)

| 指标 | zenmind-mem | mem0 (paper) | Letta | claude-mem |
|---|---|---|---|---|
| Retrieval MRR (本地 28 mem leave-one-out) | **0.969** | ~0.55-0.65 | ~0.5-0.6 | n/a (only stop-hook) |
| LongMemEval-S subset 4 (bge-m3) | **0.760** | ~0.4-0.6 | n/a | n/a |
| LongMemEval-S subset 4 (e5-small) | 0.762 | n/a | n/a | n/a |
| LongMemEval-S subset 4 (bge-small-zh) | 0.414 | n/a | n/a | n/a |
| **LongMemEval-S subset 12 (m3) · MRR** | **0.663** | n/a | n/a | n/a |
| **LongMemEval-S subset 12 (m3) · P@5** | **0.75** | ~0.6 (claimed) | n/a | n/a |
| Persona drift detection AUC | **0.92** | ❌ | ❌ | ❌ |
| Strategy distillation | ✅ DPT-style | ❌ | partial | ❌ |
| Multilingual | ✅ bge-m3 100+ 语 | ✅ | ✅ | ✅ |
| Hook lifecycle | UserPromptSubmit + Stop + PostToolUse | recall API | agent state | Stop only |
| Anchors per-domain | ✅ vc / zenmind / default | ❌ | ❌ | ❌ |
| Time-bucket recall | ✅ 24h vs 7d+ warning | ❌ | ❌ | ❌ |

> ⏳ TODO: LongMemEval-S 公开 benchmark 数字 (跑中) → 让"0.969 leave-one-out 转 0.X public benchmark"可信

## 4 步演化暴露的设计哲学

| 步 | 改动 | AUC | 教训 |
|---|---|---|---|
| 0 | Anchors 抽象格言 + centroid mean | 0.51 | 抽象层错配 = 抛硬币 |
| 1 | Anchors 改任务样式 (跟 prompt 同语态) | 0.79 | 锚点必须跟数据分布同分布 |
| 2 | 切 bge-m3 (vs bge-small-zh) | 0.84 | 多语 + 大模型小幅提升 |
| 3 | + 10 hard FP 进 negative_anchors | **0.92** | 迭代法 (eval → hard ex → 重训) |

> 这 4 步本身就是**开源 README 的故事弧线** —— 不是吹"我们做了 drift detection"，是讲"为什么 drift detection 难做对，我们怎么 from 0.5 到 0.92 的"。

## 缺什么才能开源 (decision tree)

### 必做 (才能 ship 1.0)
- [ ] **LongMemEval-S 公开数字** (跑中)
- [ ] **README 头图 = head-to-head 对比表**（mem0 / Letta / claude-mem 同 dataset）
- [ ] **`pip install zenmind-mem` 包装** (不只是 plugin dir)
- [ ] **MIT license + CONTRIBUTING.md**
- [ ] **Examples**: 3 个 30 行能跑的示例
- [ ] **CI**: GitHub Actions 跑 selftest + deeptest + eval suite (跨 Win/Mac/Linux)

### 强推荐 (decide 1.0 vs 0.x)
- [ ] **完整 LongMemEval-S 跑通 (500 题)** —— 不能只 subset
- [ ] **mem0 / Letta head-to-head 实跑** —— 不是引用别人的 paper
- [ ] **AUC 0.92 在 unseen prompt distribution 上是否 holds** (用 history.jsonl 真用户 prompt 测一次)
- [ ] **Anchor 标准化流程**: 普通用户没法手写 50 条 anchors · 提供生成器 + 模板 + 微调脚本
- [ ] **Tri-band hook 输出文档化** (aligned / neutral / deviation 各档怎么用)

### 维护成本评估 (go/no-go)
- 时间: 6 月最少 (issues / PRs / discord / discord)
- 已有 4 项目 (才燊 / Nautilus / 禅心 / 创投日报) · 协调 ROI?
- 替代方案: 写**arXiv preprint + blog post + 可下 demo**, 不开源 repo
  - Pros: 0 维护负担, 影响力可能更大 (Anthropic Persona Vectors 论文热度 + Claude Code 4.7 周期)
  - Cons: 没社区贡献 → 没 ground truth datasets
  
**我的判断**: 如果 LongMemEval-S 数字 ≥ mem0 公开数字, 走开源 (full repo)
                如果只是接近, 走 blog post + GitHub gist (轻量)

## 不开源 (但留作 Nautilus / 才燊护城河)

- 才燊 6 部门 Agent 用 zenmind-mem 当 persona 一致性保险
- Nautilus 内部 V5 SuperAgent 用 strategy distillation 跨 session 学习
- 这两个**应用层**反正是私有, drift detection 内部用就够用

## 下一步 owner

| 任务 | 估时 | 输出 |
|---|---|---|
| LongMemEval-S subset 12 → 500 全跑 | 1.5h (m3 in-loop) | 公开数字 |
| mem0 / Letta head-to-head | 1 天 | head-to-head 表 |
| pip 包装 + setup.py + entry_points | 半天 | `pip install zenmind-mem` |
| README 头图 + 4 步演化 narrative | 半天 | 公开 GitHub |
| 决定 go/no-go | 看 LongMemEval 数字后 | merge or pivot to blog |
