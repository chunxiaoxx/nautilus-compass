---
marp: true
theme: default
paginate: true
style: |
  section { font-size: 26px; }
  h1 { color: #1a3c5e; }
  table { font-size: 21px; }
  footer { font-size: 16px; color: #888; }
---

<!-- _paginate: false -->

# Don't Summarize the Past for a Future You Can't Predict

## nautilus-compass · 演讲版(30 分钟 · 三幕)

*Chunxiao Wang · 2026-09 · github.com/chunxiaoxx/nautilus-compass*

<!-- 讲者注:开场 30 秒停顿,让标题被读完。这句是全文论点。 -->

---

# 第一幕 · 你的 agent 正在忘记你

- ChatGPT 随对话推进**覆写关键信息**(ICLR 2025 LongMemEval 论文 · 人肉研究)
- Coze 漏记间接提供的信息
- 长上下文直读:性能掉 **30-60%**——裸读是死路

> 现状三大策略(压缩/提炼/裸读)全部在**写入时**做有损决定

<!-- 讲者注:这一幕只建立问题,不亮方案。问观众:你们的 agent 记得你上周说过什么吗? -->

---

# 写入时压缩 = 对未来的盲目下注

- 写入时没人知道**未来会被问什么**
- 提炼物被冻结在当初那个模型的认知水平
- 存储趋零、LLM 调用恒贵——把便宜的换成昂贵的

**这个赌注在结构上就赢不了。**

---

# 第二幕 · 反架构:写入零智能,读取全智能

```
进化  跨 agent 记忆胶囊:验证后写回 → 按需继承
治理  drift 检测(AUC 0.83)· 合约审计 · scoped 多租户 · 判分卫生学
组装  分题型摘要卡 · 日期时间线
召回  6 型路由 → BM25 + dense (RRF) · 日期锚定
存储  原文 verbatim · 本地 BGE-m3 · 零 LLM 零上云
格式  OKF 兼容
```

**写入:免费、无损、永远。智能全部在读取端。**

<!-- 讲者注:六层图来自 ARCHITECTURE.md,一字未改。强调"写入不调 LLM"停两秒。 -->

---

# 三不变量(为什么写入时压缩必输)

1. **未来查询分布不可知** —— 同一份记忆,分型路由让 P@1 从 0.20 → 1.00;变的不是记忆,是问题
2. **原文是唯一可重新索引的表示** —— 更好的 embedder 明年发布?提炼物吃不到红利,原文可以
3. **成本曲线方向反了** —— 我们 p95 **0.34-0.80s** vs LLM controller **26.9s**(~80×):把智能放对时刻的自然结果

---

# 读取端四件套

1. **六型分型路由**:用户陈述型 → turn 级块;跨会话型 → 摘要卡
2. **BM25 + dense RRF 融合**:词面扛精确标识符,向量扛语义
3. **日期锚定**:"before/after" 类问题有时序把手
4. **摘要卡组装**:e2e 500 题 **42.6% → 75.4%**,判据先于跑数预注册

**同样公开的负结果**:rerank 有害(-2pt)· K=50 无增益 · 小 embedder 更差

---

# 第三幕 · 证据(全部可复现,≈$3.50 GPU 时)

| 战场 | compass | 对照 |
|---|---|---|
| LME-S 检索 P@1(500 题同题同判据) | **0.890** | mem0 0.774 |
| LOCOMO 客场 P@1(n=1986) | **0.644** | mem0 0.592 |
| LME-S e2e(500 题) | **75.4%**(81.6% 剔判官故障) | 口径披露双报 |
| LME-V2 官方基准(451 题双域) | **40.0 / 38.4%** | untuned 19.6 / 12.8 |
| EverMemBench | **44.4-47.3** | Mem0 37.09 / Zep 39.97 / MemOS 42.55 |

<!-- 讲者注:如果只记一页,记这页。强调"同题同判据"四个字。 -->

---

# 判分卫生学:我们抓了自己判官 5 次

- 401(key 变量名)/ 网关断连 / 预算被 reasoning 吃满……
- 一次断连把 **14.2%** 的题静默记成错答
- 修正方向曾**完全相反**:web +3.3 / ent −1.9

> **判官会静默失败;判官会静默失败,你的排行榜就是虚构的。**
> 协议全公开:预注册锚 · 冒烟测试 · 双口径强制 · Wilson CI

<!-- 讲者注:自嘲式讲,这一段最圈粉。这是 paper2(arXiv 在投)的主题。 -->

---

# 预注册文化:否决自己也是产出

- LoRA 检索增强:代理指标涨,端到端平 → **关闭**
- abstention gate:误拒答 92/89 题 → **预注册拒收**
- cheap-tier 三改组合:双域未超 → **关闭**

**拒绝噪声改进,和拿到提升一样,是结果。**

---

# dogfood:我们自己的组织跑在上面

- nautilus 智涌平台:多 agent 调度,compass 是吃狗粮产物
- **130 天 · 771 commits · 603 由 agent 舰队提交**
- 跨 agent 记忆胶囊:验证过的经验才写回(reward ≥1.0 防毒门)

**这个产品最硬的 demo:造它的组织本身就长在它上面。**

---

# 接入(30 秒版)

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass \
  ~/.claude/plugins/nautilus-compass
bash ~/.claude/plugins/nautilus-compass/install.sh
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
```

不想本地跑:compass.nautilus.social · 自助 signup → scoped token → 任意 MCP 客户端

**One developer. 130 days. No cloud required.**

---

# (备用页)常问问题

- **mem0 自报 94.4% vs 你们 75.4%?** 口径不同不可比;硬对打=同题同判据检索层 +11.6pt
- **Modified MIT 是什么?** MIT + 商标保护 + 托管规模上限;自部署/内部/个人永久免费
- **多租户谁验证的?** 四探针脚本开源,任何人对生产端点可重跑
- **为什么不是纯开源?** 全源码可得 + $3.50 复现全链路 + 证据链全公开——开放程度用行为定义,不用标签

<!-- 15/5 分钟版裁剪:保留本页前 8 页+证据页+接入页。 -->
