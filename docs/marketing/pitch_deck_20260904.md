---
marp: true
theme: default
paginate: true
style: |
  /* ===== 高对比版式(与 deepdive v4 同源)· 19 页路演版重建 2026-09-05 ===== */
  section {
    background: #ffffff; color: #1f2328; font-size: 22px;
    padding: 96px 60px 46px;
  }
  section::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 62px; background: #0e4429;
  }
  .kicker {
    position: absolute; top: 21px; left: 60px;
    color: #7ee2b8; font-size: 14px; font-weight: 700; letter-spacing: 0.2em;
  }
  h1 { color: #0e4429; font-size: 1.3em; margin-bottom: 14px; }
  strong { color: #1a7f37; }
  em { color: #9a6700; font-style: normal; font-weight: 700; }
  .cards { display: flex; gap: 16px; margin-top: 14px; }
  .card {
    flex: 1; background: #dafbe1; border: 1px solid #a6ddb8;
    border-top: 5px solid #1a7f37;
    border-radius: 12px; padding: 15px 16px 11px; text-align: center;
  }
  .card.blue { background: #ddf4ff; border-color: #a5d8ff; border-top-color: #0969da; }
  .card .num { font-size: 38px; font-weight: 800; color: #0e4429; line-height: 1.15; }
  .card.blue .num { color: #0550ae; }
  .card .lbl { font-size: 15.5px; color: #424a53; margin-top: 6px; line-height: 1.4; }
  .panel {
    background: #f6f8fa; border: 1px solid #d0d7de; border-left: 5px solid #1a7f37;
    border-radius: 10px; padding: 12px 18px; margin-top: 10px;
  }
  .panel.blue { border-left-color: #0969da; }
  table { width: 100%; font-size: 18.5px; border-collapse: collapse; margin-top: 8px; }
  th { background: #1f2328; color: #ffffff; font-size: 16.5px; padding: 8px 12px; text-align: left; }
  td { padding: 7px 12px; text-align: left; border-bottom: 1px solid #d0d7de; }
  tr:nth-child(even) td { background: #f6f8fa; }
  blockquote {
    background: #ddf4ff; border-left: 5px solid #0969da; color: #0e2a40;
    padding: 10px 18px; border-radius: 0 10px 10px 0; font-size: 20px;
  }
  img { background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 12px; padding: 6px; display: block; margin: 6px auto 0; }
  pre { background: #0b2818; color: #7ee2b8; border-radius: 10px; padding: 16px 20px; font-size: 17px; }
  footer { font-size: 13px; color: #8c959f; }
  section.lead {
    background: linear-gradient(135deg, #0b2818 0%, #0e4429 62%, #116329 100%);
    color: #ffffff; text-align: center; padding: 80px 70px;
  }
  section.lead::before { background: transparent; height: 8px; }
  section.lead h1 { color: #ffffff; font-size: 2.0em; line-height: 1.25; margin-bottom: 14px; }
  section.lead h2 { color: #7ee2b8; }
  section.lead .cards { margin-top: 26px; }
  section.lead .card { background: rgba(255,255,255,0.09); border: 1px solid rgba(255,255,255,0.22); border-top: 4px solid #7ee2b8; }
  section.lead .card .num { color: #ffffff; }
  section.lead .card .lbl { color: #cde8da; }
---

<!-- _paginate: false -->

<!-- _class: lead -->

# Don't Summarize the Past<br>for a Future You Can't Predict

## nautilus-compass · agent memory

*Chunxiao Wang · 2026-09 · github.com/chunxiaoxx/nautilus-compass*

<div class="cards">
  <div class="card"><div class="num">0</div><div class="lbl">写入 LLM 调用</div></div>
  <div class="card blue"><div class="num">42.6→75.4%</div><div class="lbl">e2e · LongMemEval-S 500 题</div></div>
  <div class="card"><div class="num">80×</div><div class="lbl">p95 延迟优势<br>亚秒 vs 26.9s</div></div>
</div>

---

<div class="kicker">问题</div>

# 你的 agent 正在忘记你

![h:372](deck_assets/blind_bet.png)

<!-- 讲者注:建立问题,不亮方案。长上下文直读掉 30-60%;ChatGPT 压缩历史覆写关键信息(基准论文人肉研究)。 -->

---

<div class="kicker">问题</div>

# 市场现状:三大策略,同一个死穴

| 策略 | 谁在做 | 何时做有损决定 |
|---|---|---|
| 压缩 | 多数 SaaS 记忆层 | **写入时** |
| 提炼/摘要 | mem0 / Zep / Letta | **写入时** |
| 裸读长上下文 | 直塞 context window | 牺牲性能(掉 30-60%) |

<div class="panel red" style="margin-top:20px">

### 全部在写入时对未来下注 —— 没有人把宝押在读取端

</div>

---

<div class="kicker">架构</div>

# 反架构:写入零智能,读取全智能

![h:372](deck_assets/arch.png)

<!-- 讲者注:写入不调 LLM 停两秒。治理层是独有件;进化层胶囊写回 reward≥1.0 质量门。 -->

---

<div class="kicker">架构</div>

# 三不变量:为什么写入时压缩必输

![h:352](deck_assets/cost_curve.png)

> 未来查询不可知 · 原文唯一可重索引 · 成本曲线方向反了 —— 写入免费是自然结果,不是优化奇迹

<!-- 讲者注:三不变量一句一个;图是不变量 3 的可视化。 -->

---

<div class="kicker">方法</div>

# 读取端四件套

![h:372](deck_assets/pipeline.png)

<!-- 讲者注:同样公开的负结果:rerank 有害(−2pt)· K=50 无增益 · 小 embedder 更差。 -->

---

<div class="kicker">证据 ①</div>

# e2e 主战场:42.6 → 75.4

![h:372](deck_assets/e2e.png)

<!-- 讲者注:同样的记忆同样的题,变的只是读取端路由;+32.8 = 方法 27.4 + 测量修正 5.4,拆开报。 -->

---

<div class="kicker">证据 ②</div>

# 六分型成绩单

![h:372](deck_assets/breakdown.png)

<!-- 讲者注:tr 62.4 是已知短板,主动讲;ms/ssa/tr 是摘要层带起来的三弱型。 -->

---

<div class="kicker">证据 ③</div>

# 同题同判据对打

![h:372](deck_assets/headtohead.png)

<!-- 讲者注:各用默认嵌入(我方 BGE-m3,mem0 侧 text-embedding-005)= 开箱对打;对方嵌入部分单会话型更强,我们靠路由整体赢。复现 ≈$3.50。 -->

---

<div class="kicker">证据 ④</div>

# 客场作战:第三方榜单

![h:372](deck_assets/evermem.png)

<!-- 讲者注:EverMem 主动用首轮 44.4 防挑样;LOCOMO 客场 P@1 0.644 vs 0.592;不 claim SOTA。 -->

---

<div class="kicker">证据 ⑤</div>

# 官方基准 LME-V2:双域翻倍

![h:372](deck_assets/lmev2.png)

<!-- 讲者注:451 题上游官方基准(xiaowu0162,Di Wu 等),attribution 归上游;untuned 19.6/12.8 → 三刀调优 40.0/38.4;
官方坐标系里我们 ≈39.3 与最弱 RAG 相当——预算 1/8、延迟 1/47,效率轴是差异化,攻坚目标 55-60%。 -->

---

<div class="kicker">价值</div>

# 延迟:80× 差距从哪来

![h:372](deck_assets/latency.png)

<!-- 讲者注:智能放在不花钱的时刻;冷启动尾部非稳态,诚实注记。 -->

---

<div class="kicker">可靠性</div>

# 判分卫生学:我们抓了自己判官 5 次

![h:372](deck_assets/judge_cards.png)

<!-- 讲者注:判官会静默失败——不抓,排行榜就是虚构的。全部配置层事故,零模型能力问题。 -->

---

<div class="kicker">可靠性</div>

# 预注册文化:否决自己也是产出

<div class="panel red">

- LoRA 检索增强:代理指标涨,端到端平 → **关闭**

</div>

<div class="panel">

- abstention gate:误拒答 92/89 题(门 ≤1/≤2)→ **预注册拒收**

</div>

<div class="panel blue">

- cheap-tier 三改组合:双域未超现役 → **关闭**

</div>

> 拒绝噪声改进,和拿到提升一样,是结果

<!-- 讲者注:每个负结果都是真金白银跑出来,预注册文件带 hash 落仓。 -->

---

<div class="kicker">dogfood</div>

# 我们自己的组织跑在上面

![h:352](deck_assets/dogfood.png)

<!-- 讲者注:130 天 771 commits,603 由 agent 舰队提交——这本身就是产品的证明。 -->

---

<div class="kicker">Demo</div>

# 跨会话记忆(现场 live)

![h:340](deck_assets/demo_terminal.png)

<!-- 讲者注:对照组空库返回空,证明不是幻觉;环境故障切录屏(demo_recording_script.md)。 -->

---

<div class="kicker">接入</div>

# 三档接入,一个承诺

| 路径 | 适合谁 | 成本 |
|---|---|---|
| **本地三条命令** | 隐私/成本敏感 · 单机 agent | 永久免费,数据不出机器 |
| **Hosted beta** | 快速试用 · 团队 | compass.nautilus.social 自助 signup |
| **私有化** | 组织部署 | 联系我们 |

- 写入 **0 token** · 召回 0 上云 · BGE-m3 本地嵌入
- Modified MIT:自部署/内部/个人**永久免费**

> 开放程度用行为定义:全源码 + $3.50 复现 + 证据链全公开

---

<div class="kicker">接入</div>

# 接入(30 秒版)

```
git clone https://github.com/chunxiaoxx/nautilus-compass \
  ~/.claude/plugins/nautilus-compass
bash ~/.claude/plugins/nautilus-compass/install.sh
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
```

<div class="panel blue" style="margin-top:18px">

不想本地跑:**compass.nautilus.social** · 自助 signup → scoped token → 任意 MCP 客户端

</div>

> One developer. 130 days. No cloud required.

---

# (备用页)常问问题

<div class="panel">

**mem0 自报 94.4% vs 你们 75.4%?** 口径不同不可比;硬对打=同题同判据检索层 **+11.6pt**

</div>

<div class="panel blue">

**Modified MIT 是什么?** MIT + 商标保护 + 托管规模上限;自部署/内部/个人永久免费

</div>

<div class="panel">

**多租户谁验证的?** 四探针脚本开源,任何人对生产端点可重跑

</div>

<div class="panel blue">

**为什么不是纯开源?** 全源码可得 + $3.50 复现全链路 + 证据链全公开——开放程度用行为定义,不用标签

</div>
