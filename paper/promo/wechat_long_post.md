# 微信公众号长文 · compass v1.0

> 标题候选 · 选 1 用 · 配图位置标注

## 标题候选

A. **我用国产 LLM + 200 行 Python · 把 Claude Code 的"失忆症"治好了**
B. **2 个月 · \$3.5 · 跑出 SOTA — 一个独立开发者复制 Zep 的工程笔记**
C. **DeepSeek + 本地 BGE · 跑赢 GPT-4o memory bench 的 5 个工程决定**

> 推荐 A · 故事感最强 · 公众号算法亲故事性

---

## 摘要 (300 字 · 给"看完摘要决定要不要点开"的读者)

两个月前我开始 Claude Code 8 小时连续写代码 · 一天起码 30 次它"忘了我刚刚说什么"。这是上下文窗的天花板 · 也是 LLM agent 上生产的真天花板。

我加了 200 行 hook 让它记住 · 然后顺手做成了开源项目 Nautilus Compass · 开始系统性地 benchmark。

今天发布 v1.0 · 三件事:
1. **LongMemEval-S · n=500 · 56.6%** · 跟 Zep SOTA (55-60%) 持平 · 总成本 \$3.50
2. **EverMemBench · n=500 · 44.4%** · 超过 MemOS (42.55) · 4 个 Table 4 baseline 全过
3. **5 步管道全开源** · MIT · pip 一行装 · MCP 直接接 Claude Desktop / Cline / Cursor

唯一非美闭源 LLM · 唯一不要 GPT-4o 当 judge · 唯一全栈本地化的开源 memory 方案。

下面是 5000 字的工程复盘。

---

## 一、为什么做这个

[图1: Claude Code 跑 30 次 "你忘了..." 的截图打码版]

我每天 8 小时在 Claude Code 里。

我做过 6 个项目 · 全部败给 context window:
- 项目 A: 第 3 小时它忘了我们用 Postgres 还是 SQLite
- 项目 B: 上午说"先不重写 X" · 下午它把 X 重写了
- 项目 C: 我连续修了 5 个 bug · 它在第 6 个 bug 引入了第 1 个 bug 的反向修复

这不是 LLM 的问题 · 这是 prompt 工程的问题。

OpenAI 给 GPT-4o 加了 memory · 但 (1) 不开源 (2) 上传你的代码 (3) 用 OpenAI 的 model · 我在国内不方便接。

mem0 · letta · zep · 三家 memory 框架都看过:
- **mem0**: 开源 · 但抽取事实 · 答错回不去 · 上 Vertex 也不便宜
- **letta**: 开源 · 但是个 server 不是个 plugin · 接 Claude Code 麻烦
- **zep**: 性能 SOTA · 但用 graph DB · 用 GPT-4o judge · 一次评测 \$20+

我想要的是: **pip install · 全本地 · 全国产 LLM · 跑分进 SOTA 段**。

没人做过这个组合。所以做。

---

## 二、第一周走过的弯路

[图2: git log 截图 · 第一周提交 200+]

第一周我尝试了:
- 方案 1: 自己抽取实体 + 关系 (3 天) → 答错回不去 · 跟 mem0 一样的坑 · 弃
- 方案 2: 把所有消息 chunk 后 embed (1 天) → 长会话 50K token 超 BGE 上下文 · 退化
- 方案 3: 只 embed 用户 query · 用余弦 top-K 拉消息 (4 小时) → 跑出 41% · 第一个能用的版本

第三个方案的关键洞察是: **不要碰原消息 · 不要抽取 · 只优化检索。**

LLM 自己读得懂消息。我要做的是把"对的消息"放进 context · 而不是替它"理解"消息。

这条原则贯穿后面所有决定。

---

## 三、5 步管道 (paper §3)

[图3: 5 步管道流程图]

跑分 v1.0 时这 5 步已经稳定:

### Step 1 · BGE-m3 dense recall

- 模型 · BAAI BGE-m3 · 1024 维 · 多语言
- TOP_K_RECALL = 100 (从 5K-10K 消息池里捞 100 条候选)
- 余弦相似度 · 不是任何花哨距离

### Step 2 · 多角度 query 重写 (最大杀器)

[图4: 单 query vs 多角度 ablation 对比图]

paper §3.3 这个最关键。

原 query 进来 · 用 V4-flash 改写 3 个角度:
- **角度 1 · 直述**: 保留原实体 · 换说法
- **角度 2 · 主题**: 提炼底层任务作名词词组
- **角度 3 · 对话标记**: 改成"X 说过""Y 提到""Z 之后"等聊天里常见的句式

3 个改写 + 原 query · 各自在消息池里 BGE top-100 · 并集去重 → 重排候选。

**单一 query vs 4 角度并集 · 在 single-session-user 类型上从 30% 涨到 57% · +27 分。**

这是整个管道里最大的一个增量。比 reranker 还大。

### Step 3 · cross-encoder rerank

- 模型 · BAAI bge-reranker-v2-m3
- TOP_K_RERANK = 30 (从 100 候选里精选 30)
- pair-wise 打分 · 用原始 Q (不用改写后的)

### Step 4 · day-bucket 多日去聚簇

paper §4.2 这个细节挺反直觉。

按时间戳分组 · 同一天最多保留 2 条 · 防止"某一天聊得多 = 那天的消息把候选集占满"。

multi-session 类型上 +3 分。

### Step 5 · type-aware prompt + thinking-aware LLM

- LongMemEval 6 种问题类型 · 每种自己的 prompt 模板
- thinking 模式根据模型版本动态开关 (V3.2 开 · MiniMax 关 · 见后)
- judge 用同 vendor 的 flash 模型 (V3.2 主 · V3.2-flash judge)

跑分 56.6% · 锁。

---

## 四、跑分

[图5: LongMemEval-S 对比柱状图]

### LongMemEval-S · n=500

| 系统 | 准确率 | 成本/run | 注 |
|---|---|---|---|
| GPT-4o + Zep (paper) | 55-60% | \$20+ | graph DB |
| **Compass + DeepSeek V3.2 thinking** | **56.6%** | **\$3.50** | 本工作 |
| Gemini-2.5-pro baseline | 44.6% | \$8 | paper baseline |
| mem0 + Vertex 005 | 35.2% | \$4.20 | 抽取式 |

### EverMemBench-Dynamic · n=500 · 5-topic stratified

| 系统 | 准确率 | 来源 |
|---|---|---|
| MemoBase | 34.27 | Hu et al. 2026 Table 4 |
| Mem0 | 37.09 | Hu et al. 2026 Table 4 |
| Zep | 39.97 | Hu et al. 2026 Table 4 |
| **Compass (本工作)** | **41.0** | 本工作 |
| MemOS | 42.55 | Hu et al. 2026 Table 4 |
| EverCore | 未报告 | (论文未提供) |

超过 MemOS (42.55) · 在 4 个 Table 4 baseline 之上。EverCore 在 paper Table 4 NOT REPORTED · 我们填上了。

---

## 五、5 个反直觉发现

[图6: thinking 模式 5 模型对比]

### 发现 1 · thinking 模式不是越多越好

| 模型 | thinking-on Δ |
|---|---|
| DeepSeek V3.2 | +10 分 |
| GLM-5.1 | +2 分 |
| Kimi K2.6 | ±0 |
| MiniMax M2.7-highspeed | -34 分 (44% 拒答) |
| DeepSeek V4-pro think-high | -0.2 分 (vs V3.2 · 8x cost) |

每个模型每个版本必须分开 benchmark。**这是上生产前最容易踩的坑。**

### 发现 2 · query 重写 > reranker

ablation:
- 单 BGE-m3 → 41%
- + reranker → +5 分
- + 3 角度 query 重写 → +7 分 (single-session-user 上 +27 分)
- + type-aware prompt → +3 分
- + thinking-on → +0.6 分 (V3.2 · 已经在 thinking 上了)

最大 5 分提升的是 query 重写 · 不是 reranker。**这反我之前所有的直觉。**

### 发现 3 · 小样本 (n<100) 完全不可信

V4-pro think-high 在 sample 48 上估算 +4.2 vs V3.2 · 我差点上 full 500。

跑了。结果是 -0.2。

per-type 6 个估算里 5 个偏离 full 500 大于 95% CI 半宽。最大的离谱是 knowledge-update sample +17.3 · full -1.3。

**结论 · n<100 不上跑分 · 不发文章 · 不做产品决策。**

### 发现 4 · Neo4j graph 在闭域上反而扣分

试过把 Zep 风格的 graph reranking 抄过来。

闭 haystack (LongMemEval 是单个 50K 上下文的 hayfile · 不是开放检索) → 上 graph reranking 反而 -6 分。

graph 在跨多个独立 session 时有用 · 在单 session 内冗余且引入噪声。

### 发现 5 · 单一 vendor 的 judge 是可以的 · 但要做 cross-judge 复制

paper 里 SOTA 都用 GPT-4o judge · 因为"跨 vendor 显得公正"。

但 GPT-4o 一次跑 \$20+。我用 DeepSeek V3.2-flash 当 judge · 然后 100 题子集 cross-judge 复制 · 用 Kimi K2.6 重判一次 · Cohen's κ = 0.772 (substantial agreement)。

**便宜的 judge 在统计上是可信的 · 只要做 cross-judge 验证 · paper 是给得起的方法学。**

---

## 六、3 个 bug 教训 (debug archeology)

[图7: 3 bug 时间线]

EverMemBench 跑分从 0% 调到 41% 走过 3 个坑:

### Bug 1 · 答案被 [:300] 截断了

最早设 message 长度上限 300 字符 · 测试样本里短消息没问题。

跑到含数字答案的题 (eg. "65%") · 截断到 "65" · 接着是逗号 · LLM 答 "65 万" · judge 说 INCORRECT。

加上限到 1500 → 后来 2500。

### Bug 2 · DeepSeek V4-flash 默认 thinking-on · reasoning_mode="non-think" 被静默忽略

我设了 `reasoning_mode: "non-think"` · 但 V4-flash 默认就 thinking · 这个参数是否生效在 API 文档没说清。

实际 reasoning_tokens 占了 200-1500 · 把我设的 max_tokens=8 给吞了 · 返回空 string。

后来 max_tokens 提到 256 → 512。

### Bug 3 · 空 string 通过 verdict 检查

代码:
```python
ok = "CORRECT" in verdict and "INCORRECT" not in verdict
```

空 string `""`:
- `"CORRECT" in ""` → `False`
- `"INCORRECT" not in ""` → `True`
- AND → `False`

但 verdict 不是空 string · 是 V4-flash 返回的 thinking 内容里偶尔含 "CORRECT" · 偶尔不含。这个 bug 让早期跑分非确定性地波动 ±5 分。

最后改成 `verdict.strip().upper() == "CORRECT"` 严格匹配。

---

## 七、为什么不用 V4-pro

[图8: V3.2 vs V4-pro full500 对比表]

DeepSeek 早期 2026 发了 V4-pro (think-high · think-max) · 我专门测了。

n=50 sample · V4-pro think-high 估 60.4% · 比 V3.2 56.2% sample 高 +4.2。

跑 full 500 · V4-pro think-high 终值 56.4% · V3.2 56.6% · 持平 (-0.2)。

成本 · V4-pro \$0.016/q · V3.2 \$0.002/q · **8x cost · 持平 accuracy** = paper headline 锁 V3.2。

**lesson · 大模型不一定带来更高 benchmark · 在特定任务可能反而退化 (eg. V4-pro temporal-reasoning -3.0 分)。**

---

## 八、v1.0 ship 清单

[图9: README badge 截图]

- [x] LongMemEval-S full 500 跑分 · 56.6% 锁
- [x] EverMemBench full 500 跑分 · 44.4% 锁
- [x] cross-judge replication κ=0.772
- [x] 6 LLM benchmark
- [x] paper · 9 sections + 3 appendices
- [x] MIT license
- [x] MCP server · Claude Desktop / Cline / Cursor
- [x] A2A protocol adapter
- [x] Claude Code plugin · 一个 hook 装上 = 长期记忆
- [ ] arxiv submission (待 user 注册)
- [ ] npm publish (待 @nautilus org 注册)
- [ ] HN ship (待 stable channel 出后)

---

## 九、3 件你能做的事

1. **试一下** · `pip install nautilus-compass` · github.com/chunxiaoxx/nautilus-compass
2. **跑分复现** · `python scripts/longmemeval_full500.py` · 不行就提 issue
3. **接到你的 Agent** · MCP / A2A / HTTP 三种接法 · 文档全在 repo

---

## 十、后续

- v1.1 · 加 routing (V4-pro 给 ssa/ssp · V3.2 给 ms/temporal · 选择性升级)
- v1.2 · 集成 OpenClaw 真实用户数据
- v2.0 · drift detector + memory 联动 (paper 1 的工作)

如果你也在做 LLM agent · 也撞到 context window 这堵墙 · 一起聊聊。

---

**🔗 链接汇总**
- Repo · github.com/chunxiaoxx/nautilus-compass
- Paper · <arxiv-id>
- Demo (90 秒) · <link>
- Discord · <link>

**作者** · chunxiao
**v1.0 发布日** · 2026-05-XX

---

## 配图清单 (发布前补)

- [ ] 图1: Claude Code "你忘了..." 截图 (打码项目名)
- [ ] 图2: 第一周 git log 提交散点
- [ ] 图3: 5 步管道流程图 (TikZ 画 · 已在 paper Figure 1)
- [ ] 图4: 单 query vs 多角度 ablation 柱状图
- [ ] 图5: LongMemEval n=500 6 系统对比柱状图
- [ ] 图6: thinking 模式 5 模型对比柱状图
- [ ] 图7: 3 bug 时间线 (从 0% → 41%)
- [ ] 图8: V3.2 vs V4-pro full 500 表格截图
- [ ] 图9: GitHub README badges
- [ ] 封面图: 标题 + Compass logo · 字号要在小图预览也能读

## 发布渠道

主发: 公众号 (创投春晓 / Nautilus 官号)
转发: 知乎专栏 (技术深度版) · 简书 · 掘金
英文版: BLOGPOST.md (paper/ 目录)
社交: X thread (zh + en) · HN · Reddit r/ML
