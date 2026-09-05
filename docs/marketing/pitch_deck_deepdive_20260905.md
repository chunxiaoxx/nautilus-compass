---
marp: true
theme: default
paginate: true
style: |
  section {
    background: #ffffff; color: #1f2328; font-size: 23px;
    padding: 58px 62px 66px; border-top: 6px solid #1a7f37;
  }
  h1 { color: #1f2328; font-size: 1.32em; margin-bottom: 20px; }
  h2 { color: #0969da; font-size: 1.05em; }
  strong { color: #1a7f37; }
  em { color: #9a6700; font-style: normal; font-weight: 700; }
  .kicker {
    position: absolute; top: 22px; left: 62px;
    color: #1a7f37; font-size: 15px; font-weight: 700; letter-spacing: 0.18em;
  }
  .cards { display: flex; gap: 16px; margin-top: 14px; }
  .card {
    flex: 1; background: #f6f8fa; border: 1px solid #d0d7de;
    border-radius: 14px; padding: 16px 18px 12px; text-align: center;
  }
  .card .num { font-size: 44px; font-weight: 800; color: #1a7f37; line-height: 1.15; }
  .card .num.blue { color: #0969da; }
  .card .num.red { color: #cf222e; }
  .card .lbl { font-size: 15.5px; color: #57606a; margin-top: 7px; line-height: 1.45; }
  .cols { display: flex; gap: 26px; align-items: flex-start; }
  .col { flex: 1; }
  table { width: 100%; font-size: 18.5px; border-collapse: collapse; margin-top: 6px; }
  th { background: #f6f8fa; border-bottom: 2px solid #d0d7de; font-size: 17px; }
  td, th { padding: 7px 12px; text-align: left; }
  tr:nth-child(even) td { background: #fafbfc; }
  blockquote {
    background: #ddf4ff; border-left: 5px solid #0969da; color: #1f2328;
    padding: 10px 18px; border-radius: 0 10px 10px 0; font-size: 21px;
  }
  footer { font-size: 13px; color: #8c959f; }
  section.lead { text-align: center; }
  section.lead h1 { font-size: 1.65em; color: #1a7f37; }
  section.part { background: #f6f8fa; border-top-color: #0969da; }
  section.part .no {
    font-size: 74px; font-weight: 800; color: #d0d7de; line-height: 1;
    margin-bottom: 4px;
  }
  section.part h1 { color: #0969da; font-size: 1.5em; }
  section.part p { color: #57606a; font-size: 21px; }
---

<!-- _paginate: false -->

<!-- _class: lead -->

# 不要为无法预测的未来<br>压缩过去

## nautilus-compass · agent 记忆层 · 技术深讲(30 分钟)

*Chunxiao Wang · 2026-09 · github.com/chunxiaoxx/nautilus-compass*

<div class="cards">
  <div class="card"><div class="num">0</div><div class="lbl">写入路径<br>LLM 调用数</div></div>
  <div class="card"><div class="num blue">42.6→75.4%</div><div class="lbl">LongMemEval-S e2e<br>500 题</div></div>
  <div class="card"><div class="num">80×</div><div class="lbl">检索延迟优势<br>p95 亚秒 vs 26.9s</div></div>
  <div class="card"><div class="num blue">5 次</div><div class="lbl">我们自己抓出的<br>判官事故</div></div>
</div>

<!-- 讲者注:开场 30 秒停顿,让四个数字被读完。今天目标:听众多带走三件事——
写入零 LLM 的架构赌注、判官三型病理学、以及我们怎么对待自己的数字。 -->

---

<!-- _class: part -->

<div class="no">01</div>

# 第一幕 · 问题与立场

##### 写时压缩为什么在结构上必输

---

<div class="kicker">第一幕 · 问题与立场</div>

# 你的 agent 正在忘记你

![w:1130](deck_assets/blind_bet.png)

<!-- 讲者注:建立问题,不亮方案。问观众:你们的 agent 记得你上周说过什么吗?
ChatGPT 随对话推进覆写关键信息(ICLR 2025 基准论文人肉研究);长上下文直读掉 30-60%。 -->

---

<div class="kicker">第一幕 · 问题与立场</div>

# 市场现状:三大策略,同一个死穴

| 策略 | 谁在做 | 有损决定发生在 |
|---|---|---|
| 压缩 | 多数 SaaS 记忆层 | **写入时** |
| 提炼 / 摘要 | mem0 / Zep / Letta | **写入时** |
| 裸读长上下文 | 直塞 context window | 性能掉 30-60% |

<br>

> 三条路全部在**写入时**对未来下注 —— 没有人把宝押在读取端

<!-- 讲者注:指着右列"写入时"打三遍。裸读不是候选,是基准测出的失败下限。 -->

---

<div class="kicker">第一幕 · 问题与立场</div>

# 三不变量:写时压缩必输的结构原因

<div class="cols">
<div class="col">

### 1 · 未来查询不可知

重要性只在**被问到的时刻**显影。
同一份记忆,按题型换检索粒度:
P@1 **0.20 → 1.00**

变的不是记忆,是问题

</div>
<div class="col">

### 2 · 原文唯一可重索引

提炼物被冻结在当初那个
LLM 的认知水平;原文明天
可换更好嵌入、可作训练燃料

写时压缩把记忆**锁死在技术现状**

</div>
<div class="col">

### 3 · 成本曲线方向反了

存储趋零、LLM 调用恒贵。
把便宜的(原文)换成
昂贵的(提炼物)= 逆曲线

写入免费是**自然结果**,非优化奇迹

</div>
</div>

<!-- 讲者注:不变量 2 那句"锁死在技术现状里"停两秒再翻页。 -->

---

<div class="kicker">第一幕 · 问题与立场</div>

# 不是我们说的:基准作者的第三方结论

**ICLR 2025 · LongMemEval 基准论文(arXiv 2410.10813)**

- §5.2:用 LLM 提炼的摘要 / facts 替代原文 → **因信息丢失损害问答**
- Appendix B 人肉研究:ChatGPT 压缩历史时覆写关键信息,Coze 漏记间接提及
- 长上下文直读掉 30-60% → 记忆层的必要性由基准作者论证

> 写时压缩的损害 2024 年就被量化了;我们是第一波量出**读侧路线胜绩**的团队之一

<!-- 讲者注:这页防"王婆卖瓜"。我们的贡献不是发现压缩有害,是用读取端架构把它变现成分数。 -->

---

<!-- _class: part -->

<div class="no">02</div>

# 第二幕 · 架构

##### 六层 · 生态 · 决策记录

---

<div class="kicker">第二幕 · 架构</div>

# 反架构:写入零智能,读取全智能

![w:1130](deck_assets/arch.png)

<!-- 讲者注:强调"写入不调 LLM"停两秒。治理层是独有件(drift AUC 0.83+三层隔离+判分卫生学);
进化层三次实测 uplift=0,保持"待证"标注——不冒充已验证是标注纪律。 -->

---

<div class="kicker">第二幕 · 架构</div>

# 生态定位:从 nautilus 平台长出来的独立组件

<div class="cols">
<div class="col">

- 起源:nautilus 智涌平台的 agent 舰队需要跨 agent 记忆层
- 对应平台 Trinity 架构的**记忆与治理层**,开源独立化
- **不依赖平台**:本地三条命令完整运行
- 130 天 **771 commits**,603 由 agent 舰队提交

</div>
<div class="col">

**dogfood 是设计压力测试**

隐私 / 本地 / 成本是硬约束——
约束逼出正确架构:

写入免费 + 读取智能,
是站在用户一边的架构

</div>
</div>

<!-- 讲者注:回答"这项目哪来的"。平台理论(Epiplexity/DMAS)一句带过;dogfood 这里埋点,结尾收。 -->

---

<div class="kicker">第二幕 · 架构</div>

# 写入端:四条决策

| 决策 | 内容 | 理由 |
|---|---|---|
| 存什么 | **原文 verbatim**(md+frontmatter) | 不变量 2:唯一可重索引 |
| 怎么索引 | 本地 BGE-m3 + BM25 + 日期元数据 | 词面扛标识符 / dense 扛语义 / 日期扛时序 |
| 不做什么 | **零 LLM**:不提炼、不建图、不摘要、不上云 | 不变量 1+3 |
| 质量门 | 经验胶囊写回需 reward ≥ 1.0 | 验证过的经验才入库,防跨 agent 复利成毒 |

> "不做什么"比"做什么"更难被抄 —— 因为它是立场,不是功能

---

<div class="kicker">第二幕 · 架构</div>

# 架构决策记录:放弃过什么(负结果公开)

| 被放弃的方案 | 实测结果 | 教训 |
|---|---|---|
| 图数据库 Neo4j + graph rerank | 检索 **−6.2pt** | 图边引入噪声,复杂度做减法 |
| cross-encoder 重排器 | e2e **−2pt** | 嵌入自身排序已更好 |
| 大 K(50 vs 20) | **无差异** | 无重排时 K 只加宽融合窗口 |
| 小嵌入模型 Qwen3-0.6B | **wash**(P@5 0.833 vs 0.867) | 嵌入质量是检索地基 |
| LoRA 域适配嵌入 | 代理指标涨,e2e **平** | 预注册 +5pt 门没过就不上 |
| 主动拒答门(abstention) | 误拒 web 92 题(门 ≤1) | 打掉的是噪声,不是错误 |

<!-- 讲者注:这页是"系统与深度"的核心证据——每个负结果都真金白银跑出来,预注册文件带 hash 可查。
复杂度做减法不是品味,是被证伪逼出来的。 -->

---

<!-- _class: part -->

<div class="no">03</div>

# 第三幕 · 算法解剖

##### 六型路由 · 归因链 · 检索演进 · 对打设置

---

<div class="kicker">第三幕 · 算法解剖</div>

# 六型分型路由:改动集中在三弱型

![w:1150](deck_assets/dd_sixtypes.png)

<!-- 讲者注:设计逻辑一句话——用户陈述型答案通常在一个 user turn 里,检 turn 级;
跨会话/助手行为/时序型需要"每场会话发生了什么"的地图,路由到逐会话摘要卡。
强项(ssu/ssp/ku)context 字节不变;tr 62.4 是已知短板,主动讲。 -->

---

<div class="kicker">第三幕 · 算法解剖</div>

# 归因链:42.6 → 75.4,每一步

![w:1150](deck_assets/dd_waterfall.png)

<!-- 讲者注:全场最重要一页。把"方法带来多少"和"修测量仪带来多少"拆开报——
5.4pt 是仪器修复,不是方法效应,混报是评测写作最常见的自我欺骗。
预注册门:ms≥35%(锚22.6)/ ssa≥40%(锚25.0)/ tr≥30%(锚15.8),跑数前落仓带 hash。 -->

---

<div class="kicker">第三幕 · 算法解剖</div>

# 三口径:同一次跑,三个数字

<div class="cards">
  <div class="card"><div class="num red">70.0%</div><div class="lbl">保守口径<br>71 题断连记为错答<br>(下界)</div></div>
  <div class="card"><div class="num">75.4%</div><div class="lbl">重判口径<br>同判官同 prompt 仅加重试<br>(发布口径)</div></div>
  <div class="card"><div class="num blue">81.6%</div><div class="lbl">干净口径<br>剔除 71 断连题 n=429<br>(上界)</div></div>
</div>

> 只报一个数 = 替听众做决定;三口径并报 = 把决定权还给听众

<!-- 讲者注:71/71 重判解决,其中 27 题翻对——注意"解决≠全变对",其余 44 题重判后仍是错答,
这正是"断连≠正确"的诚实注记。 -->

---

<div class="kicker">第三幕 · 算法解剖</div>

# 检索层演进:赢在路由,不赢在嵌入

![w:1150](deck_assets/dd_ladder.png)

<!-- 讲者注:首版和 mem0 打平(0.784 vs 0.774)主动说——中间态如实公开是可信度的一部分。
四步每步增量都可归因;终局 P@5 0.978 / MRR 0.929 三项全赢。 -->

---

<div class="kicker">第三幕 · 算法解剖</div>

# 检索对打:同题同判据,各用默认嵌入

![w:1140](deck_assets/dd_head2head.png)

<!-- 讲者注:设置逐字段——同 500 题(question_id join)/ retrieval-only 双方 / mem0 infer=False /
各用默认嵌入(我方 BGE-m3,mem0 侧 text-embedding-005)/ 版本钉死 mem0ai 2.0.19。
诚实披露:对方嵌入在部分单会话型更强,我们靠分型路由整体赢——开箱对打才是用户真实场景。
复现:scripts/reproduce_lmes_retrieval.sh,一条命令 ≈$3.50。 -->

---

<!-- _class: part -->

<div class="no">04</div>

# 第四幕 · 判官病理学

##### 我们抓了自己判官 5 次 —— 全是配置问题,零次模型能力问题

---

<div class="kicker">第四幕 · 判官病理学</div>

# 判官失败 = 资源耗尽:三型分类

部署中的判官 J\*(θ, B, I):知识边界 θ · 输出预算 B · 打分基础设施 I

| 型 | 耗尽的资源 | 检测信号 | 重试可治? | 部署前可检出? | 对分数的效应 |
|---|---|---|---|---|---|
| **J-K** 知识边界 | θ 判别力 | Δ 探针集 | 否 | 是 | 静默放过错误 |
| **J-B** 输出预算 | B | 截断/空响应率 | 否 | 是 | 塌缩到默认标签 |
| **J-C** 连接 | I | 错误标签率 | **是** | 仅运行中 | 假性错答(下界) |

> 机制不同、信号不同、解药不同 —— 混为一谈必然用错药

<!-- 讲者注:传统 judge bias 文献(位置/冗长偏差)是"判官在读,但读歪了";
我们这三型是"判官没在读 / 没来得及说 / 根本没被叫到"——不同的物种。 -->

---

<div class="kicker">第四幕 · 判官病理学</div>

# J-K:数值精度盲区(2,600 次真实调用)

![w:1150](deck_assets/dd_jk.png)

<!-- 讲者注:珠峰 8849→8949 米、光速 3.0→3.1×10⁸——±0.1% 的污染,四成通过。
盲区在"事实性要求已写入判分 prompt"前提下仍存在;换更强判官没用(跨族差 ≤11pp)。
判官能抓实体替换/常识错误(0% 通过)——是数值盲区,不是普遍轻信。
局限照讲:两判官均为 reasoning 模型,泛化未测;prompt 变体消融未做。 -->

---

<div class="kicker">第四幕 · 判官病理学</div>

# 事故 ①(J-B):预算被思考吃光的判官

<div class="cols">
<div class="col">

- reasoning 判官 `max_tokens=4096` 被**思考过程吃满**,截断输出解析为默认标签
- ent 域 **146/211 题(69%)记 0 分**,日志 250 次空响应
- 连续**两轮调优被误判"方法未过门"** —— 测量坏了,方法背锅

</div>
<div class="col">

**重判(16384/low)后:**

<div class="cards">
  <div class="card"><div class="num">+3.3pt</div><div class="lbl">web 域</div></div>
  <div class="card"><div class="num red">−1.9pt</div><div class="lbl">ent 域<br>(方向相反!)</div></div>
</div>

> 解药:部署时冒烟——真实尺寸条目上断言判官输出非空可解析

</div>
</div>

<!-- 讲者注:为什么两轮都没发现?spot check 用的都是短条目,推理装得下预算;坏的是长条目,系统性的。
方向相反这个细节要强调:修正的符号不可假设,不重判就带着错数字发布。 -->

---

<div class="kicker">第四幕 · 判官病理学</div>

# 事故 ②(J-C):14.2% 的题被断连判官判分

<div class="cards">
  <div class="card"><div class="num red">71 / 500</div><div class="lbl">网关 403/超时后<br>被静默记为错答<br>(14.2%)</div></div>
  <div class="card"><div class="num red">5.4pt</div><div class="lbl">失真 ≈ 被测真实效应<br>32.8pt 的 <strong>1/6</strong></div></div>
  <div class="card"><div class="num blue">71/71</div><div class="lbl">同判官重判全解决<br>(27 题翻对,44 题仍错)</div></div>
  <div class="card"><div class="num">−20pt</div><div class="lbl">中期"子型回归"<br>事后证实<b>全是</b>断连误标</div></div>
</div>

> 基础设施噪声可以吞掉六分之一的被测效应,还能制造幻影回归

<!-- 讲者注:整轮重试未清零(新题继续命中)=随机基础设施故障,非题目绑定。
如果你的预注册门设在 ±5pt,一次网关抖动就能翻转 accept/reject——逐题判官输出审计是必需品。 -->

---

<div class="kicker">第四幕 · 判官病理学</div>

# 判分卫生协议 P1-P5(成本 ≈ 几次 API 调用)

| # | 例行 | 治哪种 |
|---|---|---|
| P1 | 跑数前冻结锚 / 门 / 裁决规则,版本化+hash | 裁决标准事后漂移 |
| P2 | 同判官重判+指数退避,只重试打分调用 | J-C 假性错答 |
| P3 | 保守 / 重判后 / 干净三口径并报 | 挑口径 | 
| P4 | 部署冒烟:真实条目非空断言+预算审计 | J-B 截断塌缩 |
| P5 | n=30 上一题 = ±3.3pt,带内"回归"推迟审计 | 幻影回归 |

> 六相 checklist:部署前探针+冒烟 / 跑前预注册 / 跑中签名率监控 / 跑后重判+多口径

<!-- 讲者注:协议每个条款对应一次真实事故——5 次:401 变量名/断连/预算吃满/空响应/子型幻影回归。
全部配置层。测量可信度先于分数。paper2(arXiv 在投)是这一幕的正本。 -->

---

<!-- _class: part -->

<div class="no">05</div>

# 第五幕 · 评测版图

##### 五战场组合 · LME-V2 调优 · 官方坐标系诚实定位

---

<div class="kicker">第五幕 · 评测版图</div>

# 五个战场各测什么

| 战场 | 性质 | 回答的问题 | 结果 |
|---|---|---|---|
| LME-S e2e 500 题 | 自建 harness 主场 | 方法效应 | 42.6 → 75.4 |
| 检索对打 mem0 | 同题同判据 | 相对优势 | P@1 0.890 vs 0.774 |
| LOCOMO-10(n=1986) | 客场换数据集 | 泛化 | P@1 0.644 vs 0.592 |
| EverMemBench | 第三方公开榜 | 防自吹 | 44.4-47.3 vs Mem0 37.09 |
| LME-V2(451 题) | 上游官方基准 | 社区可比 | 40.0 / 38.4(untuned 19.6/12.8) |

> 单一战场都可被质疑;组合的覆盖面难以全部归为"自选有利"

<!-- 讲者注:EverMem 主动用首轮 44.4 作头条防挑样(Run2 47.3,CI 42.9-51.7);
不 claim SOTA。mem0 论文自报 94.4% 是 e2e LLM-judge 口径,跨 harness 不可比。 -->

---

<div class="kicker">第五幕 · 评测版图</div>

# LME-V2:从 19.6/12.8 到 40.0/38.4

![w:1150](deck_assets/dd_lmev2.png)

<!-- 讲者注:三步——刀1 abstention 判分口径(abstention 组 web 2.8→45.8 / ent 0→83.9,裸 UNKNOWN 252→0);
刀2 检索单元升级+预算 12k→24k(gold-在场 ent 0.115→0.652 倒挂修复);d13 判分修正(4096→16384 重判)。
刀3 LoRA 没进图:预注册门没过,未采纳——负结果也记录。
attribution 红线:451 题是上游官方基准(xiaowu0162/LongMemEval-V2,Di Wu 等),题目轨迹归上游。 -->

---

<div class="kicker">第五幕 · 评测版图</div>

# 官方坐标系里的诚实定位

![w:1150](deck_assets/dd_official_map.png)

<!-- 讲者注:全场信任峰值在这页——主动把自己的官方坐标位置说成"与最弱 RAG 相当"。
差距两结构性来源:预算 24k vs 200k(8.3×);判分口径(全题 LLM judge vs 程序化为主)。
我们的差异化在纵轴代价(亚秒 vs 26.9-108s)+判分卫生学贡献。
主攻坚=三池设计移植,目标 Small 55-60%(超 AgentRunbook-R)后再上官方榜。 -->

---

<!-- _class: part -->

<div class="no">06</div>

# 第六幕 · 安全与多租户

##### 隔离不是声明,是可重跑的生产事实

---

<div class="kicker">第六幕 · 安全与多租户</div>

# 三层身份模型

```
user(JWT 身份) ──→ 设备 ──→ agent(scoped token: read:<project> / write:<project>)
```

- 隔离边界 = project 命名空间;header-only 身份(X-User-ID 类)**永久禁止**
- v0.9 曾有冒充洞:公网可冒充任意用户读写 → 已改 JWT-only + 五项矩阵验证
- 自助 token 只含持有者自己的空间;缺省 project 显式注入持有者 uid
- 公网自助 token 只见 **8 个用户工具**(tools/list 17→8),内部工具直调 forbidden

<!-- 讲者注:冒充洞主动讲——自己抓、自己修、验证矩阵公开。抓自己的洞比被别人抓便宜。 -->

---

<div class="kicker">第六幕 · 安全与多租户</div>

# 四探针:任何人对生产端点可重跑

| 探针 | 断言 | 结果 |
|---|---|---|
| P1 | A 的 token 读 B 的空间 | forbidden ✓ |
| P2 | A 的 token 写 B 的空间 | forbidden ✓ |
| P3 | A 的 token 读写 A 自己的空间 | 放行,不误伤 ✓ |
| P4 | 撤销 token → 下一次调用 | 立即 401 ✓ |

**脚本开源(`probes.py`),对 compass.nautilus.social 可直接重跑** · 发布流程规定 FOUR-GREEN 才发帖

<!-- 讲者注:9/4/9/5 两次生产变更后各复验一轮全绿——隔离属性是持续重验的事实,
不是一次性的安全审计报告。这也是下一幕 demo D3 的内容。 -->

---

<!-- _class: part -->

<div class="no">07</div>

# 第七幕 · 价值与 Demo

##### 延迟 · 成本 · 路线图 · 四个现场演示

---

<div class="kicker">第七幕 · 价值与 Demo</div>

# 延迟:80× 差距从哪来

![w:1140](deck_assets/dd_latency.png)

<!-- 讲者注:写入零 LLM+读取纯检索组装,所以 p95 亚秒;对照组 LLM controller 架构 26.9s。
不靠 cache 不靠捷径——智能放在不花钱的时刻。诚实注记:冷启动尾部(23.8/50.9s)非稳态;
生产读吞吐 ≈5 rps 天花板在嵌入 daemon 串行推理,已在路线图,不藏。 -->

---

<div class="kicker">第七幕 · 价值与 Demo</div>

# 成本账:只对自己可验证的事下断言

<div class="cards">
  <div class="card"><div class="num">0</div><div class="lbl">每条记忆写入的<br>LLM 调用与 token 成本</div></div>
  <div class="card"><div class="num blue">≈$3.50</div><div class="lbl">全链路复现成本<br>(LLM ¥7 + T4 spot ¥3.2 + 网络/冷启 ≈$1)</div></div>
  <div class="card"><div class="num">~8h</div><div class="lbl">复现墙钟时间<br>脚本与 evidence 全开源</div></div>
</div>

> 写时提炼方案每条记忆都要过 LLM —— 按条计费的边际成本,在这里是零。
> 竞品每条记忆的写入成本无我方实测(闭源):**我方可验证的只有"写入免费"**

<!-- 讲者注:$3.50 是 v0.8 时代实测口径,BENCHMARKS_REPRODUCE.md 有 breakdown。
竞品成本那句是防"你们凭什么说别人贵"的先手。 -->

---

<div class="kicker">第七幕 · 价值与 Demo</div>

# 路线图与开放问题(诚实版)

| 期 | 事项 |
|---|---|
| 发布窗口 | hosted beta 邮箱验证门禁 / PyPI 3.1.1 / MCP 目录提交 |
| 主攻坚 | 三池设计移植,目标 LME-V2 Small **55-60%**(当前 ≈39.3,与最弱 RAG 相当) |
| 工程 | 嵌入 daemon 并行化(读吞吐 ≈5 rps 天花板根因) |
| 待证 | 进化层 tier 晋升 uplift 三次实测为 0,重测前不动 |
| 开放问题 | tr 62.4 仍是短板 · J-K prompt 变体消融未做 · 非 reasoning 判官泛化未测 · **hosted 外部真实用户案例为零** |

<!-- 讲者注:最后一行故意留三秒。外部案例为零是最大未知数——我们用 dogfood 和可复现性兜底,
但它只有经过外部用户才能证伪。 -->

---

<div class="kicker">第七幕 · 价值与 Demo · D1</div>

# Demo ①:跨会话记忆(现场 live)

<div class="cols">
<div class="col">

**分镜(≤90 秒,真实终端)**

1. 会话 A:"我在做 Rust 异步运行时的性能调优"
2. 会话 B:"我的部署环境是 Ubuntu 24.04,单卡 4090"
3. **三周后,全新会话**问:"结合我的项目和环境,该注意什么?" → **命中两条**
4. 对照组:空白 profile 同一问题 → **空**

</div>
<div class="col">

![w:560](deck_assets/demo_terminal.png)

真实性:每步都是真实 MCP 调用
(`ingest_obs` / `recall`),分镜见
`demo_recording_script.md`,录屏兜底

</div>
</div>

<!-- 讲者注:对照组是关键——空库返回空,证明不是幻觉。现场跑,环境故障切录屏。 -->

---

<div class="kicker">第七幕 · 价值与 Demo · D2</div>

# Demo ②:跨 agent 记忆胶囊继承

<div class="cols">
<div class="col">

**分镜:一个 agent 的失败变成另一个 agent 的起点**

1. agent A 解题失败 → 反思提炼经验 → reward **1.0** 达写回门 → 写胶囊
2. agent B 接到同类题 → W2 召回继承胶囊 → **FAIL → PASS**
3. 台账:胶囊来源 / reward / 被继承次数可审计

</div>
<div class="col">

**为什么值得看**

- 质量门 reward ≥ 1.0:错经验不入库,
  不被跨 agent 复利成毒
- 6/17 有实录:B 从 FAIL→PASS
- 这是"组织记忆"与"聊天记录"的
  本质区别

</div>
</div>

<!-- 讲者注:脚本 compass_fleet_memory.py;实录来自 nautilus 平台 dogfood。
若现场环境不稳,展示胶囊台账+实录日志。 -->

---

<div class="kicker">第七幕 · 价值与 Demo · D3</div>

# Demo ③:四探针现场打生产端点

<div class="cols">
<div class="col">

**分镜:现场对 compass.nautilus.social 跑 `probes.py`**

1. 两个账号各发 token
2. A 的 token 读 B 的空间 → **forbidden**
3. A 的 token 写 B 的空间 → **forbidden**
4. A 读写自己的空间 → **放行**
5. 撤销 A 的 token → 下一次调用 **401**

输出:`FOUR-GREEN`

</div>
<div class="col">

**为什么敢现场跑**

- 脚本开源,任何观众会后可自己重跑
- 生产端点 = 大家现在就能注册的
  同一个端点
- 隔离属性是**持续重验的事实**,
  不是一次性的审计报告

</div>
</div>

<!-- 讲者注:这一段最圈粉——安全不靠承诺靠可重跑。若网络故障,放录屏+四探针源码 5 行核心。 -->

---

<div class="kicker">第七幕 · 价值与 Demo · D4</div>

# Demo ④:延迟现场计时

<div class="cols">
<div class="col">

**分镜:同一问题,现场计时**

1. `time` 包住一次 `memory_query`
2. 命中含跨会话事实的完整回答
3. 读数:**亚秒级**(p50 0.165-0.328s)
4. 对照:LLM controller 架构同类查询
   p95 **26.9s**(官方实测口径)

</div>
<div class="col">

**差异的来源不是优化奇迹**

- 写入零 LLM:没有提炼队列
- 读取纯检索+组装:无中间
  LLM 调用链
- 智能放在了不花钱的时刻

</div>
</div>

<!-- 讲者注:对照 26.9s 引官方数字(SCOREBOARD §2),不现场跑对照(没装竞品),
诚实说明对照是官方口径而非现场测量。 -->

---

<div class="kicker">第七幕 · 价值与 Demo</div>

# 三档接入,一个承诺

| 路径 | 适合谁 | 成本 |
|---|---|---|
| **本地三条命令** | 隐私 / 成本敏感 · 单机 agent | 永久免费,数据不出机器 |
| **Hosted beta** | 快速试用 · 团队 | compass.nautilus.social 自助注册 |
| **私有化** | 组织部署 | 联系我们 |

- 写入 **0 token** · 召回 0 上云 · BGE-m3 本地嵌入
- Modified MIT:自部署 / 内部 / 个人**永久免费**

> 开放程度用行为定义:全源码 + $3.50 复现 + evidence 链 + 四探针可重跑

---

<!-- _class: lead -->

# One developer. 130 days. No cloud required.

![w:980](deck_assets/dogfood.png)

<div class="cards">
  <div class="card"><div class="num">130 天</div><div class="lbl">从第一行代码到现在</div></div>
  <div class="card"><div class="num blue">771</div><div class="lbl">commits,603 由 agent 舰队提交</div></div>
  <div class="card"><div class="num">github.com/chunxiaoxx/nautilus-compass</div><div class="lbl">本地:git clone → install.sh → daemon_start.sh</div></div>
</div>

<!-- 讲者注:结尾停住。架构、算法、病理学、四探针——都是这个组织日常的一部分,不是论文装点。 -->

---

# 备用页 · 常问问题

- **mem0 自报 94.4% vs 你们 75.4%?** 口径不同不可比(不同 harness/判官/数据版);硬对打=同题同判据检索层 +11.6pt
- **嵌入不一样也算对打?** 各用各的默认嵌入 = 开箱即用对打;对方嵌入部分单会话型更强,我们靠路由整体赢
- **判官是自己请的,分数可信吗?** 正因如此才有判官病理学:三口径并报 + 重判工具开源 + 5 次事故全录
- **为什么不是纯开源?** Modified MIT(商标+托管规模上限);自部署永久免费;开放程度用行为定义

---

## 版本与裁剪

- **30 分钟版** = 全部 43 页 · **15 分钟版**:幕一(4 页)+ 幕三归因链/三口径/对打(4 页)+ 幕四三型与两事故(4 页)+ 诚实定位 + D1/D3 demo + 收尾 · **5 分钟路演** = `pitch_deck_20260904.md`(19 页发布版)
- 内容正本:`whitepaper_20260905.md`(白皮书 v1.1)· 数字口径:`docs/nautilusmem/SCOREBOARD.md` · 图表脚本:`scripts/make_deck_charts_deepdive.py`
- 重渲染:`npx @marp-team/marp-cli pitch_deck_deepdive_20260905.md -o <out> --allow-local-files`
