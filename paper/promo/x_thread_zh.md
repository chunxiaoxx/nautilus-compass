# Twitter/X Thread · 中文版 · compass v1.0 发布

> 9 推 · 每推 ≤140 字 · 配图位标注 · 发布前替换 <handle> + 链接

---

**[1/9]**
两个月前我开始 Claude Code 8 小时连续写代码 · 一天起码 30 次 "你忘了我刚刚说什么" · 这是上下文窗的天花板 · 也是 LLM agent 上生产的真天花板。

今天开源 Nautilus Compass · 一个把 LLM 长期记忆做对的开源插件。
🔗 github.com/chunxiaoxx/nautilus-compass

---

**[2/9]**
跑分先放:

LongMemEval-S · n=500 · **56.6%**
- 跟 Zep SOTA (55-60%) 持平
- 跟 mem0/MemoBase 拉开 15-20 分
- 总成本 \$3.50 · 是商用 API 方案的 1/15

唯一非美国闭源 LLM 跑到这个分数的开源方案。

[图1: LongMemEval 对比表]

---

**[3/9]**
为什么便宜?

不用 GPT-4o 当 judge · 不用 graph DB · 不上传数据。

栈:
- DeepSeek V3.2 thinking (国产 · API \$0.002/q)
- 本地 BGE-m3 dense + bge-reranker-v2-m3
- 5 步管道 · 全 Python 实现

跑完 500 题 \$3.50 · 一杯星巴克的钱。

---

**[4/9]**
但便宜不是关键 · 关键是哪一步带来分数:

ablation:
- 单 BGE-m3 → 41%
- + 多角度 query 重写 → +27 分 (尤其 single-session-user)
- + cross-encoder rerank → +5 分
- + type-aware prompt → +3 分
- + thinking 模式 → +10 分 (V3.2)

最大收益是 query 重写 · 不是 reranker。反直觉。

---

**[5/9]**
另外一个反直觉发现:

thinking 模式不是越多越好。

- DeepSeek V3.2: thinking-on +10 分 ⬆️
- GLM-5.1: +2 分 ⬆️
- Kimi K2.6: +0 分 (无影响)
- MiniMax M2.7: 拒答率 44% ⬇️ (灾难)
- DeepSeek V4-pro think-high: 持平 V3.2 (\-0.2 分 · 8x cost)

每个模型每个版本必须分开 benchmark · 不能假设。

---

**[6/9]**
EverMemBench-Dynamic 也跑了 (Hu et al. 2026 · arxiv 2602.01313):

n=500 · **44.4%** e2e accuracy · recall@20=94.8%

paper Table 4 对比:
- MemoBase: 34.27
- Mem0: 37.09
- Zep: 39.97 ← compass 这里
- MemOS: 42.55
- EverCore: NOT REPORTED

超过 MemOS · 比 Zep 高 4.4 · 在 4 个 Table 4 baseline 之上。

---

**[7/9]**
v1.0 不只是 benchmark 数字 · 是开发者拿去就能用:

- pip 一行装
- MCP server: Claude Desktop / Cline / Cursor 直接接
- Claude Code 插件: 一个 hook 装上 = 长期记忆
- A2A 协议适配 · 多 agent 之间能传消息
- 全部 MIT · 数据本地不上传

[图2: 装机 30 秒 GIF]

---

**[8/9]**
为什么我做这个 ·

Claude Code 是我每天 8 小时的副驾 · 但 session 一断 · 它忘了我项目所有上下文。
我加了 200 行 hook · 它记住了。
然后想 · 这个东西其他人也要 · 而且要做对。

paper 在 arxiv: <arxiv-id>
demo 视频 90 秒: <link>

---

**[9/9]**
全部数据可复现:

- 评测脚本: scripts/longmemeval_full500.py + scripts/evermembench_bge.py
- 6 个 LLM 全跑分日志
- cross-judge 复制 (κ=0.772)

如果你跑出不同分数 · 提 issue · 我们把 reproducibility 当最高优先。

🔗 github.com/chunxiaoxx/nautilus-compass

转发拜托 🙏 第一批用户最关键。

---

## 配图准备清单

- [ ] 图1: LongMemEval n=500 对比表 (compass 56.6 · Zep 58 · mem0 35 · MemoBase 32)
- [ ] 图2: 装机 GIF (`pip install nautilus-compass && compass-mcp`)
- [ ] 图3: EverMemBench Table 4 截图带 highlight
- [ ] 图4: thinking 模式 5 模型对比柱状图

## 发布时机

- 周二/三上午 9:00 北京 = 周一/二晚上 21:00 PT
- 第 1 推后 5 分钟连发后续 · 不要 wait 互动
- 第 9 推后 30 分钟检查 reply · 同时 retweet 自己置顶

## 互动话术

- 有人问 "比 mem0 怎么样" → 引用 [3]+[4]
- 有人问 "为什么 V4 没用" → "V4 think-high 跟 V3.2 持平 · 但贵 8x · 所以 v1.0 锁 V3.2"
- 有人质疑跑分 → 复现脚本链接 + cross-judge κ
