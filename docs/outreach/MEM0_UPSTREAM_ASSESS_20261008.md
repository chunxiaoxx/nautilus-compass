# mem0 上游贡献价值评估(2026-10-08 · R323 主件 · 外部总账深度件③)

## 摸底[实测 10/8]

- 我方线程 #7514:open,0 评论,9/30 后静默(原为 maintainer 面向讨论);
- mem0 上游当前高热 issue 与我方资产的**精准对位**:
  - **#5352(54 评论)"time-blindness + semantic conflicts + missing CRUD → 记忆污染"**——我们 **dedup_check(写入前三档查重)+fact_status(measured/inferred/heard)** 正是此病药方,M5 今晨刚上生产;
  - **#5245(22 评论)"批量 embedding 部分失败 → 静默丢记忆"**——我们 embed 代理+fail-fast+失败回退纪律同题;
  - **#7283(21 评论)"Faithfulness check before memory write"**——即我们的写入门方向(社区自己在要这个功能);
  - 附:#6493(16 评论)embedding 维度自动传播=我们踩过并修过的同类坑。

## 价值判断(三线)

1. **技术匹配度:高**——四个高热 issue 全部命中我方已有实物(不是为贡献而造);BC1 mem0 三臂对照(16/11/18 压缩元凶+7)是我们独有的**带实测的批评资格**;
2. **引流杠杆:中高**——mem0 repo 28k+ star,issue 评论量=曝光位;但 48h 窗纪律+我们是"批评者兼方案者"身份,姿态须是**贡献方案而非踢馆**;
3. **成本:低**——方案文档+可选 PR,材料大半现成(M5 patch/BC1 数据/判据纪律)。

## 建议动作(呈批,不自行发)

**A(推荐)**:在 #5352 发一评——披露我们生产环境遇到同病+三件套方案(查重门/事实状态标注/沿链),附 BC1 三臂对照实测与判据披露页链接;不 PR 代码(方案层贡献,尊重其 SDK v3 架构自主权);
**B**:加发 #7283 同款短评(faithfulness check=我们 fact_status 门,一鱼两吃);
**C**:不做——保持纯裁判独立性(理由:判读机构对被测对象上游做贡献有轻微利益冲突;但 counter:方案层贡献不涉评测口径,rsi-bench 先例已开)。

**独立性护栏**(若批):评论中不引用我们的榜上 mem0 对比名次(那是测量线);只引工程方案;披露身份"we run an independent eval org, and hit this in production"。

—— compass · MEM0-UPSTREAM-ASSESS(候用户批 A/B/C)
