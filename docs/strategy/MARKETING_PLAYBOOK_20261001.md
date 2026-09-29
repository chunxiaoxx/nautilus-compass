# Assay 推广营销方法论与工具箱(2026-10-01)

> 不是渠道清单,是方法论——为什么选这个渠道、说什么话、怎么衡量。
> 基于 9/8-9/30 实战 23 天的教训(7 个渠道实测,1 个有效,6 个待判/失败)。

---

## 第一层:定位(你是谁的什么)

### 一句话定位
**Assay 是 AI agent 时代的验证机构——我们考试,我们复算,我们签名。**

### 三个不是
- 不是 benchmark 工具(我们不开源 benchmark,我们开源**验证协议**)
- 不是 AI 产品(我们是给 AI 产品做**审计的**)
- 不是开源项目(开源是我们的**获客渠道**,不是商业模式)

### 信任飞轮
```
免费考试(BC1) → 成绩上墙 → 有人不服 → 复算请求(M1) → 付费审计(M2) → 成交(M3)
```
每一步都在验证上一步——**我们用自己验证自己**。

---

## 第二层:受众分层(跟谁说话)

| 层 | 是谁 | 在哪 | 关心什么 | 转化动作 |
|---|---|---|---|---|
| **A. AI 工程师**(核心) | 写 agent 代码的人 | GitHub/Reddit/X/Discord | "我的 agent 到底行不行" | 考 BC1 / 用 jev-trust |
| **B. AI 产品决策者** | 选型/采购的人 | LinkedIn/Newsletter/HN | "这家供应商的数字可信吗" | 复算请求(M1) |
| **C. AI 开源维护者** | Jev/mem0/Letta 等作者 | GitHub/Discord | "我的校准好吗" | 免费 mini 审计(D3 模式) |
| **D. 研究者** | 论文作者 | arXiv/学术会议 | "评测方法可复现吗" | 引用我们/合作 |

**优先级:A > C > B > D**——A 是用户量,C 是口碑传播者,B 是付费者,D 是长期背书。

---

## 第三层:信息架构(说什么)

### 核心叙事(所有渠道共用)
**"我们的判分器先错了,我们自己抓的。"**

这是不可伪造的 credential——没有别的 AI 公司会主动公布自己的错误。这个故事本身就是产品。

### 信息分层(按受众)

| 受众 | 钩子 | 证据 | CTA |
|---|---|---|---|
| A(工程师) | "30 题考你的 agent 记得住自己的历史吗" | BC1 三臂数据(16/11/18) | 来考试(GitHub) |
| C(维护者) | "你的 Jev 校准在别域会崩,测过吗" | TypeSafe 复算(444x=真的但取决于对照) | 发我 5 个决策样本 |
| B(决策者) | "供应商说快 444 倍——你信吗" | 两簇发现(16-18x vs 184-440x) | 来免费复算 |
| D(研究者) | "验证应是协议,不是机构" | G4 论文(全文+工件) | 引用/审稿 |

### 内容素材库(已有的可复用资产)

| 素材 | 格式 | 最佳用途 |
|---|---|---|
| TypeSafe 复算背书信 | 英文帖 | Reddit/HN/Newsletter |
| 两簇发现图 | 数据可视化 | X/Reddit |
| BC1 自考 11/18→18/18 | 故事弧 | 任何地方的开场 |
| 伦理短文《会记得的 AI》 | 中文长文 | 知乎/公众号 |
| 三门真门 | 技术架构 | 工程师社区 |
| F15 三供应商复判 | 数据表 | 学术/工程 |

---

## 第四层:渠道策略(在哪说)

### 方法论:三问筛选法

每个渠道回答三个问题:
1. **目标受众在那吗**?(不是"人在那"而是"我们的受众在那吗")
2. **我们能持续贡献吗**?(不是发一次广告,而是能持续提供价值吗)
3. **有先例吗**?(类似产品在这个渠道成功过吗)

### 渠道矩阵(已验证+高确定性)

| 渠道 | 受众匹配 | 我们实测 | 先例 | 决策 |
|---|---|---|---|---|
| **awesome 列表** | C(维护者) | ✅ 2/2 MERGED | 开源标配 | **扩大**(投更多列表) |
| **GitHub issue/PR** | C | 🔄 4 发 0 回(48-72h 窗口内) | 开源标配 | **继续但降低预期** |
| **Reddit** | A(工程师) | 未试 | 多个 AI 工具成功案例 | **本周必做** |
| **Product Hunt** | A+B | 未试 | AI 工具日均 500-5000 访问 | **本周必做** |
| **Newsletter 投稿** | A+B | 🔄 1 投(Latent Space) | AI newsletter 接受 guest post | **扩展投稿 3 家** |
| **X/Twitter 有机** | A+B | 未系统做 | AI 圈核心阵地 | **每天 1 条数据点** |
| **arXiv 预印本** | D | 未做 | 学术圈标配 | **本月** |
| **HN** | A+B | ❌ 首帖被 flag | 需养号 | **养号后重试** |
| **dev.to** | A | ❌ 零流量 | 平台已衰退 | **放弃** |
| **知乎** | 中文 A | 🔄 2 文(1 审核中) | 中文技术圈 | **维持,不投入更多** |

### 不做的渠道(及理由)

| 渠道 | 理由 |
|---|---|
| 付费广告(X/知乎) | 先榨干免费渠道;受众太窄,付费 ROI 差 |
| YouTube | 制作成本高;我们不是视觉产品 |
| Facebook/Instagram | 受众不对(B2B vs B2C) |
| 线下会议 | 疫情后线上为主;成本高 |

---

## 第五层:执行节奏

### 本周(10/1-7):基础铺开

| 天 | 动作 | 耗时 | 预期 |
|---|---|---|---|
| 周二 | Reddit 发帖(r/LocalLLaMA:TypeSafe 两簇) | 30 min | 1-5k 阅读 |
| 周二 | X 发第一条有机帖(两簇图) | 10 min | 100-500 展示 |
| 周三 | Product Hunt 准备(页面+截图+一句话) | 1 h | — |
| 周四 | Product Hunt 正式发布(太平洋 00:01) | 15 min | 500-5000 访问 |
| 周五 | AI 工具目录提交×3 | 30 min | SEO 长尾 |
| 持续 | X 每天一条(数据/发现/坑) | 5 min/天 | 累积关注 |

### 本月(10 月)：深度内容

| 周 | 动作 | 预期 |
|---|---|---|
| W1 | 上述基础铺开 | 首批流量 |
| W2 | arXiv 预印本(BC1+三臂+复算方法) | 学术引用 |
| W3 | Newsletter 扩展投稿(Latent Space 之外 2-3 家) | 万级读者 |
| W4 | 回顾:哪个渠道带来了第一个 M1 请求 | 数据驱动决策 |

### 长期(持续)

- **开源贡献式营销**:给 mem0/Letta/Jev 生态提 PR(文档改进/bug 修复),签名里带 Assay
- **每月 Trust Report**:透明度报告=持续内容源
- **每个复算案例=一篇内容**:做完一个复算,写一篇分析(脱敏后)

---

## 第六层:度量(怎么知道有没有用)

| 指标 | 当前 | 目标(10 月底) | 怎么测 |
|---|---|---|---|
| GitHub 仓 star | ~50 | 200 | GitHub Insights |
| BC1 报名 | 0 | 5 | exam-signup issues |
| M1(复算请求) | **0** | **1** | issue/邮件/信箱 |
| PH 得票 | — | 100+ | Product Hunt |
| Reddit karma | — | 100+ | Reddit |
| X 粉丝 | — | 200 | X Analytics |

**核心判据:M1>0 是唯一真正重要的指标。** 其他都是过程指标。

---

## 第七层:工具箱(具体怎么干)

### Reddit 发帖模板
```
标题: We recompute TypeSafe's "444.6x cheaper" claim — the results surprised us
正文:
- 背景(2 句):我们建了一个 AI 组织记忆考试,先考自己,判分器先错了
- 方法(3 句):90 次实测,四家模型对拍,发现倍数不是连续的是两簇
- 数据:快模型全挤 16-18x,重量级 184-440x
- 意义:单个倍数是营销,倍数-对照曲线才是信息
- CTA:完整数据+复算脚本在 GitHub(链接)
```

### Product Hunt 发布模板
```
名称: Assay — Verification as a Protocol
一句话: We test AI agents' memory, recompute vendor claims, and sign everything.
标签: Developer Tools + AI
描述:
- 30-question exam from 130 days of real org history
- Our own grader failed first (7 wrong, including 2 wrong answer keys)
- Controlled three-arm experiment: one config flag = 7 points difference
- TypeSafe recompute: "444.6x cheaper" is real, but only vs opus 5
- Every number traceable to repo artifacts. Public grader. Challenge window.
```

### X(Twitter)有机帖模板(每天一条)
```
Day 1: 数据点 — "Jev is 0.44s whether you ask 1 question or 3. MiniMax: 7.7s."
Day 2: 故事 — "Our benchmark grader was wrong on 7/18 items. We published the errors."
Day 3: 发现 — "Fast models cluster at 16-18x vs Jev. Heavy models: 184-440x. Two clusters, not a spectrum."
Day 4: 坑 — "mem0's write compression drops artifact:null fields. That's exactly what audits need."
Day 5: 问题 — "Your AI vendor says 444x faster. Against what? Ask for the comparator."
```

### Newsletter 投稿 pitch 模板
```
Subject: Guest post pitch — "We recompute our own grading errors" (verification as protocol)

Hi [Newsletter],

I'd like to pitch a guest post for your AI engineering audience.

The core story: we built an exam to test AI agent memory, and the first
thing it caught was us — our own grader was wrong on 7 of 18 items.

[3-4 sentences of hooks: three-arm experiment, TypeSafe recompute, two-cluster finding]

Draft is 3,800 words, every number traceable to repo artifacts.

— Assay (github.com/chunxiaoxx/nautilus-compass)
```

---

## 附:已烧的钱 vs 学到的东西

| 动作 | 成本 | 学到 |
|---|---|---|
| awesome-jev PR×2 | ¥0 | 小列表有效,立即执行 |
| GitHub issue×7 | ¥0 | 冷触达回复率<15%,但值得 |
| Discord 帖×3 | ¥0 | 社区帖生命周期短(<2h) |
| dev.to 文章 | ¥0 | 平台在衰退,放弃 |
| HN 帖 | ¥0 | 需要账号信誉,养号后重试 |
| TypeSafe 社区帖 | ¥0 | 同行复现姿态正确,但需时间 |
| **总投入** | **¥0** | **一个渠道已验证有效(awesome),两个待判(GitHub/Discord)** |
