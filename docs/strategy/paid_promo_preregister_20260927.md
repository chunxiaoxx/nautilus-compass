# 付费投流预注册档(2026-09-25 用户拍板 · BC1 发布配套)

> 政策变更记录:capability_market_fit_20260923 错配排除 #4「不做泛营销投放/预算为零」
> 经用户 9/25 拍板修订为「小额买曝光,不买信任」——投流只买"让人看见工件"的
> 机会,转化仍只能靠签名工件本身。本档=花钱前的判据锚,适用报数纪律。

## 预算与渠道(首波,上限 ¥2000)

| 渠道 | 标的 | 预算 | 定向 | 状态 |
|---|---|---|---|---|
| X(Twitter)推广帖 | BC1 发布帖(英文) | $50-100(~¥400-700) | dev/LLM 兴趣 | 待开户 |
| 知乎知+ | BC1 中文稿 | ¥500-1000 | AI/互联网从业 | 待开户 |

不碰:Google Ads(搭建成本高)、朋友圈(受众不对)、泛信息流。

## 预注册判据(花钱前写死,只许更严)

1. **成功指标(主)**:可归因的 exam-signup issue 开立数 + 取卷请求数。
   归因手段:UTM 链接 + 报名模板「从哪听说」字段。
2. **参考指标(次)**:UTM 带参访问量、Discord 新增成员数。
3. **明确不算数**:曝光量/点击量/点赞——虚荣指标,不进账本。
4. **止损线**:单渠道花 >¥500 且 48h 可归因报名=0 → 停该渠道,余款不追加。
5. **结算点**:每渠道投后 48h 一结,读数落 LOOP_STATE;10/26 M1 评审总算。

## UTM 规范

- X: `?utm_source=x&utm_medium=paid&utm_campaign=bc1_launch_0927`
- 知乎: `?utm_source=zhihu&utm_medium=paid&utm_campaign=bc1_launch_0927`
- 落点页:X → GitHub BC1_LAUNCH;知乎 → 中文稿文末入口(墙页/报名 issue)

## 物料

### X 帖文案(工程师口吻——T1 slop 教训:零营销腔)

> BC1 is a 30-question exam for AI memory systems: write-gate discipline,
> relapse rate, attribution traceability, cross-agent consistency.
>
> The grader is public. Our own first attempt scored 11/18 — we published it,
> audited all 7 failures, found 5 bugs in our own questions (2 wrong answer
> keys), fixed them, reran: 18/18. Both scorecards signed, both on the wall.
>
> If your agent remembers things, come get scored. Free during launch week.
> [UTM link]

### 知乎知+ 创意(中文)

- 标题:「你的 AI 说 90% 可信——在谁的数据上?」
- 钩子段:第一个敢写赔付条款(§5b)的 AI 质检;组织记忆考场 BC1 开考,
  出题方自己首考 11/18 的丑成绩和审计链一并上墙。
- 落点:中文稿正文(文末报名入口)。

## 人机分工(自动化边界)

- 机器侧(已就绪):判据档/UTM/文案/48h 计数器脚本(报名 issue 数 gh api
  +UTM 访问 nginx 日志 grep)
- 人的两步:X 广告开户+充值+$50-100 试投点确认;知乎知+开户+充值+投放
  点确认。**未经用户点确认,一分钱不花。**

## 红线

- 创意只许指到工件(签名成绩单/复算链/判分器仓库),不许出现无法复算的
  声称——付费放大自报=双倍违反立身之本。
- 任一渠道素材被平台判违规→停,不申诉不绕道。
