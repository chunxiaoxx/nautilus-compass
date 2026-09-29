# Product Hunt 发布准备件(2026-10-01)

> 目标:发布日(建议周四 10/8)拿到 100+ upvotes + 3+ 条真实评论 + ≥5 GitHub 访问转化。
> 发布时间:太平洋时间 00:01(北京时间 15:01),提前 24h 在 PH 预约。

---

## 一、产品信息(PH 表单填写)

### 名称
```
Assay
```

### Tagline(≤60 字符)
```
We test AI agents' memory — and recompute vendor claims
```
(52 字符 ✓)

### Description(≤260 字符)
```
30-question exam from 130 days of real AI org history. Our own grader failed 7/18 first — we published every error. Three-state grading, public grader, signed receipts, 90-day challenge window. We also recompute AI vendors' benchmark claims.
```
(246 字符 ✓)

### 链接
```
https://github.com/chunxiaoxx/nautilus-compass
```

### Topics(选 3 个)
1. `Developer Tools` — 最大分类
2. `Artificial Intelligence` — 主题匹配
3. `Open Source` — 增加曝光

---

## 二、视觉素材(需准备)

| 素材 | 规格 | 内容 | 状态 |
|---|---|---|---|
| Logo | 240×240 | Assay 品牌图(简洁,验证/天平意象) | 🔴 需制作 |
| 截图 1 | 1270×760 | BC1 考题示例(T32-0 fake-green-detect)+ 成绩单 | 🔴 需制作 |
| 截图 2 | 1270×760 | TypeSafe 复算结果(两簇发现图) | 🔴 需制作 |
| 截图 3 | 1270×760 | 墙页(wall.html)带成绩上墙效果 | 🟡 现有可截 |
| GIF(可选) | 800×600 | 判分器跑一遍(30 秒) | 🟡 可后补 |

**Logo 方案**(最简):纯文字 "Assay" + ed25519 签名指纹图形化。或者用天平/图章意象。Python PIL 10 分钟出一张。

---

## 三、Maker's First Comment(发布时刻的第一条评论)

这条评论决定产品的第一印象——比产品描述更重要,因为 PH 用户习惯先看 maker 评论再决定要不要 upvote。

```
Hi Product Hunt 👋

I'm the maker of Assay — and I want to start with the most uncomfortable
thing about it: **our own grader was wrong on 7 out of 18 questions**,
including two wrong answer keys. The examinee was right; our ground truth
was wrong.

That's not a bug — that's the thesis.

We spent September building a 30-question exam that tests whether an AI
agent can correctly remember its own operating history (ours = 130 days,
parameterized). The exam caught:

1. **mem0's default config loses 7 points** — write-time semantic
   compression drops the exact machine-checkable fields (artifact: null)
   that audits need. Controlled three-arm experiment, field-level anatomy.

2. **TypeSafe's "444.6x cheaper" claim is real** — but only vs opus 5.
   Against fast models it's 16-18x. We ran 90 timed calls to prove this.
   The multiplier-vs-comparison curve is two clusters, not a spectrum.

3. **Judges err too** — we misattributed 5 failures to an evaluator, got
   overturned by our own recompute, and published the whole chain.

Everything is signed (ed25519), the grader is public, and there's a
90-day challenge window. We eat our own cooking and publish the kitchen
fires.

Try it: sign up for the BC1 exam (GitHub issue), or bring us a claim
you want recomputed. First one's free.

— Assay / 伊洛科技有限公司
```

---

## 四、预发布准备(T-7 到 T-0)

| 时点 | 动作 | 状态 |
|---|---|---|
| T-7(10/1) | PH 账号确认(需有历史活动,不能是新号) | 检查你的 PH 账号 |
| T-7 | Logo+3 截图制作 | 本文档批准后立即 |
| T-5(10/3) | PH 预约提交(填表+选日期 10/8) | 材料齐后 |
| T-3(10/5) | "Coming Soon" 页面生成(PH 自动) | 自动 |
| T-1(10/7) | X/Reddit 发预告("明天上 PH") | 文案备好 |
| T-0(10/8) | 北京时间 15:01 发布 + Maker 第一条评论 | 关键动作 |
| T-0 持续 | 前 4h 回复每条评论(时区覆盖) | 需要 |
| T+1 | 数据复盘(upvotes/评论/点击/GitHub star) | 30 min |

---

## 五、预期与止损

| 指标 | 乐观 | 中性 | 悲观 |
|---|---|---|---|
| Upvotes | 150+ | 50-100 | <20 |
| 评论 | 10+ | 3-5 | 0-1 |
| GitHub 访问 | 500+ | 100-300 | <50 |
| Star 新增 | 30+ | 5-15 | 0-2 |
| BC1 报名 | 3+ | 0-1 | 0 |
| **M1 请求** | **1** | **0** | **0** |

**止损判据**:如果 PH 发布日悲观(<20 upvotes),说明产品故事不够有传播性——不是因为渠道不好，是因为**钩子不对**，需要回到信息层重新打磨。

---

## 六、需要你确认/操作的

| # | 事项 | 谁 |
|---|---|---|
| 1 | PH 账号确认(你有吗？有历史活动吗？) | 你 |
| 2 | Logo 方案批准(文字型 vs 图形型) | 你 |
| 3 | 发布日期确认(建议周四 10/8) | 你 |
| 4 | Maker 评论文案批准 | 你 |
| 5 | T-1 的 X/Reddit 预告文案批准 | 你 |
