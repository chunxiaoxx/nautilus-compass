# 持续外联战略(2026-09-30 用户令 · 常设工作流)

> 用户原令:"github 和 gmail 以及 x.com 以及其他各个论坛和平台,要一直持续外联交流,
> 主动对接,尤其是 github 和 gmail 也可以主动出击联系,但要保证精准匹配和高质量沟通。"
> 性质:从"发布/值守"升级为**常设主动外联线**,纳入 loop 六步第③步常驻候选。

## 一 · 渠道资产盘点(全部已验证可用的实物通道)

| 渠道 | 资产/凭据 | 已验证动作 | 外联定位 |
|---|---|---|---|
| GitHub | chunxiaoxx 账号+gh CLI(Rest 三段式)+GCM token | PR#19/#43 已投+awesome 双 PR | **主攻:主动出击** |
| Gmail | production refresh_token(~/.gmail-mcp)+REST fallback 配方 | Infistar 函件收发已走通 | **主攻:主动出击** |
| X | execCommand 配方(x_post.py)+Premium 长文 | 双推文已发 | 值守+发布 |
| Reddit | 账号 karma≥5(r/LocalLLaMA 已发) | 帖稿备(bbc2ee3a) | 发布窗值守 |
| dev.to | API key(id=4772700,21:00 北京发) | 发文过 | 周更 |
| HN | 全 curl 管道(登录/提交/评论) | 首帖被 flag(养号中) | 暂缓 |
| Discord | CDP Chrome154 配方 | jev-trust 发布同步过 | 版本节点 |
| ClawHub/Glama | 已收录 v3.2.0+评分按钮配方 | 重扫过 | 版本更新触发 |
| 知乎 | 发布器定稿(dry-run 18/18) | 草稿待点 | 伦理文 403 复验后 |

## 二 · 精准匹配原则(质量>数量,用户红线)

1. **匹配判据**:目标与我们定位(可复算验证/判分协议/记忆评测)有三点以上
   显式交集才触达;相关 issue/项目用一手检索(GitHub search API),不用二手榜单
2. **沟通质量线**:首触必须①读过对方近期真实产出(引用具体内容)②一句说清
   我们能给的验证价值(不群发模板)③遵守对方社区规范(awesome 列表先查生命体征)
3. **节奏纪律**:每日外联动作≤5 件(防垃圾化);每件有 commit 级留痕;
   48h 无回音不追击,一周后再评
4. **反剧场**:外联产出以"对方回应/合入/复算请求"计,不以发送件数计

## 三 · 主动出击候选清单(首批 · 按匹配度排)

### GitHub(精准 issue/项目触达)
1. **mem0 仓库**:OmniMemEval 自报口径 issue——我们墙上的 UNVERIFIED 条目+独立
   复算方法学,提"第三方复算协议"协作(非挑刺姿态:先复算后公开,邀请他们给判据)
2. **Letta/zep 相关评测 issue**:Letta Evals(2025-10 开源评测框架)与三门判据
   互补性——PR 式轻触(判分协议兼容提案)
3. **JEV 生态(TypeSafe)**:TypeSafe proof 不可寻址的公开提问(X 稿同步)——
   GitHub 无公开 repo,走 X+Discord
4. **awesome-jev 已合 PR**(cobanov#71/yibie#137):版本更新时追加 jev-trust 新特性
5. **LongMemEval 上游**(xiaowu0162):N6 口径 T0 成绩册+判分协议贡献(提前规避
   侵权红线,合作姿态)

### Gmail(商务/学术触达)
1. **Infistar**(在途):材料到→24h 首轮→L2 认证路径
2. **学术线**:paper2(判官盲区版)目标审稿人/Latent Space 编辑定向函
   (已投稿 1a0e8ba1 等回音,无回音则换渠道主动函)
3. **E6/宪章生态**:模型共享宪章定稿后的组织内外联(较少,值守)

### 论坛/平台
- Reddit r/LocalLLaMA(稿备)+r/MachineLearning(方法论长文,判分协议三态)
- dev.to 周更(verification 方法论系列,首篇=judge 自报三陷阱,内部实证素材)
- 知乎伦理文(403 复验窗口)

## 四 · 纳入 loop(常驻化)

- loop 六步第③步候选池新增"外联一件"(与 F15/靶向题同级)
- 每轮外联动作记 OUTREACH_LEDGER.md(触达对象/匹配理由/动作/回应状态)
- 周复盘:回应率/转化(首外部复算请求=M1 主尺)
