# C1 mini 送测触达脚本(第一周 10 家 · 2026-09-24 起)

> 承 capability_market_fit P0-C1 线。目标:首个 mini 完成=M1 前最强
> 信号。纪律:不卖报告、不群发模板感、每家定制、被删不追。

## 一 · 名单(10 家,类型分散,置信都在生产动作上)

| # | 仓 | 用例 | 置信虚高的代价 | 已知读数挂钩 |
|---|---|---|---|---|
| 1 | is-malicious | 源码/CI 恶意扫描 | 误放行=恶意进构建 | 对抗域 C=0.988(好消息型) |
| 2 | jev-guard(klauswg) | 加密货币存取款风控 triage | 错单直接烧钱 | 闭合任务 C=0.953 |
| 3 | Inbox Zero | 邮件分类后端 | 分类错=丢信/误归档 | **邮件三分类 50%@91%(同款域!)** |
| 4 | jev-curate | 数据集流式过滤打分 | 坏数据入库 | QC 标注全 yes(域 3 同款) |
| 5 | hono-jev-router | HTTP 语义路由 | 路由错端点 | 双极性自检(0%/98%) |
| 6 | Canny | 挑战"done"声明 | 假完成进主干 | 10/10 不可复算研究(同族共鸣) |
| 7 | foreman | 判定 agent 完成度 | 判定器被糊弄 | 三态判定方法论 |
| 8 | commit-miner | diff 分类打标 | 标注噪声 | 域 3 标注偏差 |
| 9 | HA-Jev | 家庭助手传感器 | 误报烦人/漏报危险 | 措辞反转(极性) |
| 10 | jev-belay | Stop hook 完成证据 | 假绿放行 | 假绿识别题(BC1) |

## 二 · Issue 模板(骨架+每家个性化一段)

> ⚠️ **v2 修订(2026-09-23 晚,T1 实弹反馈)**:T1(is-malicious)被关,
> 维护者评论「please work on your absolute slop writing」——D1 版的
> AI 营销结构(粗体 offer/**Free offer, no strings**/破折号排比/长段)
> 被开源维护者识别为 slop 并打 signal。**D3 批次一律用人味版**:
> - ≤120 词,无粗体无营销短语,工程师同行口吻
> - 第一句=对方用例的具体事实;第二句=我们的一条硬读数(带链接)
> - offer 一句话带过,不展开免责式尾注
> - 参考改写(以 T1 场景为例):
>   > I run an independent lab that measures Jev's calibration. Public
>   > data: on closed tasks C=0.953, but on synthetic email triage it
>   > claimed 91% confidence and was right 50% of the time (artifacts:
>   > <link>). Your domain — scanning source for malicious behavior —
>   > hasn't been measured by anyone. Send 5-10 example decisions and
>   > I'll run the same measurement for your domain, free, signed report.
>   > If not, ignore this.

标题(v2):`Question about Jev's calibration on your use case (free measurement offer)`

```
Hi — we noticed {项目名} uses Jev to {一句话复述他们的用例,从 README 引}。
That's exactly the pattern we study: {对应痛点一句话}.

We run an independent verification lab (no relationship with TypeSafe).
Public calibration data we've measured on hosted Jev so far: closed
deterministic tasks C=0.953, adversarial stress C=0.988 — but a synthetic
email-triage domain hit 50% actual accuracy at 91% stated confidence, and
QC-style labeling collapsed onto "flag everything" ({挂钩读数,每家不同}).
Calibration is a (model, domain) property — your domain is the one that
matters and nobody has measured it.

**Free offer, no strings**: send us 5–10 anonymized examples of the
decisions {项目名} actually makes (or a one-paragraph description of the
pattern). We generate a 20–40 item domain decision set, run Jev on it, and
hand you a signed mini-report: domain accuracy/Brier/ECE + one actionable
line ("treat 0.9 as 0.77 here"). Raw artifacts included so anyone can
recompute our numbers. First 10 are free; if you'd rather keep it private,
we'll never publish without permission (public case studies are opt-in,
domain can be anonymized).

Not interested? Totally fine — the calibration data above is yours either
way. — Nautilus Assay (compass.nautilus.social/wall.html)
```

个性化段(每家替换 {挂钩}):见名单表第 5 列,写 issue 时展开一句。

## 三 · 节奏与判据

- **D1(9/24):发 3 家试点**(#1 is-malicious / #3 Inbox Zero / #4
  jev-curate——痛点最硬+读数最对口)
- **48h 观察**:被删/被骂/spam 标记 → 停,改话术;正常 → D3 发 4 家,
  D5 发 3 家
- **回复 SLA**:任何回复 24h 内人工响应(发卷流程:样本→我们跑→
  签名小报告,周期承诺 72h)
- **判据**:第一周回复率(≥2/10=话术成立);**首个 mini 完成=M1 前置
  信号,即刻全框通报**;首个「换公开案例」授权=内容素材
- 记账:每家 issue 链接入 LOOP_STATE 新增 T 表(c1-outreach)

## 四 · 红线

- 不在同仓重复开;被关闭不重开不追问
- 不在 issue 里放价格(DCR 是回函后的私下话题)
- 每条 issue 必须含个性化用例复述(防模板感);模板正文存档备查
- 回复者若问商业化:如实答 $99 mini 已免、标准 DCR $99-299/¥699-3499
