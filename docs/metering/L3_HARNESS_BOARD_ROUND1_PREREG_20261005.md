# L3 harness 对比榜 · 首期预注册判据骨架 v0(2026-10-05 落)

> 链条:#3116(L3 owner=compass 判分读数供给,10/12 榜页上线)→ 榜判据 v1(LEADERBOARD_PREREG_CRITERIA_V1_20261005,sha16=282a268ca84ecf72)→ **本期判据(本档,开跑前必须齐,判据只许更严)**。
> 纪律:空白字段如实标"待回填",不臆写;齐备前不开跑、不出读数。

## 期判据表(开跑前置件)

| 字段 | 值 | 状态 |
|---|---|---|
| 被测物 A | v5-harness | ⏳ 坐标待回填(repo/commit sha16/运行环境) |
| 被测物 B | 第二开源 harness | ✅ **mini-swe-agent**(2026-10-05 platform 3194 函拍定:"同意 mini-swe-agent 首推(官方血统+轻量+活跃)";坐标 repo/commit 回填待其 v5 侧无既定栈时落实) |
| 模型配置(双臂同一) | — | ⏳ 待回填(模型 id+量化/采样参数钉死) |
| 任务集(双臂同一) | — | ✅ **SWE-bench Verified 单集起步**(2026-10-05 platform 3194 函确认:"确认你的推荐——SWE-bench Verified 单任务集起步(500 题 resolved%,L1 注记口径已冻结,双臂可比优先)") |
| 样本量门 | n≥30 进名次区;n<30 进观察区(榜判据 v1 N4) | ✅ 冻结 |
| 判分口径 | 按任务集口径引 L1 注记(SWE-bench=resolved%/GAIA=exact match/Terminal-Bench=task resolve rate,harness+dataset 双 tag) | ✅ 冻结(随任务集回填落具体值) |
| 判分者 | compass 独立判分读数供给(判读免费);harness 自报读数只收引用标 [不可验](UNVERIFIABLE 墙) | ✅ 冻结 |
| 证据层 | 全档 [实测]/[推断]/[不可验] 强制标注 | ✅ 冻结 |
| 名次规则 | 单一主指标;并列明写;负结果照实名次;U 态不上名次 | ✅ 冻结 |
| 利益披露 | 双方无装订关系;赞助按榜判据 v1 N5 披露 | ✅ 冻结 |

## 任务集选择(✅ 2026-10-05 已拍=SWE-bench Verified 单集起步,platform 3194 函确认;下文推荐理由留档)

- 首期建议单任务集起步(双臂可比性优先,不铺面);
- 推荐 **SWE-bench Verified**(500 题,resolved%,harness 对比最主流口径,L1 注记已冻结其口径与 cutoff 披露);备选 Terminal-Bench(resolve rate,harness+dataset 双 tag 天然适配 harness 对比叙事);
- GAIA 需工具栈披露且 validation 主轨 165 题,首期不作推荐。

## 可比性纪律(✅ 冻结)

1. 双臂必须**同任务集+同模型配置+同采样参数**,任一不同=不可比,只出单臂读数不出对比;
2. 开跑前各自落期判据补全本档空白字段(只许更严),齐备后 sha16 锚定再跑;
3. harness 运行环境(镜像/依赖版本)双臂各自申报并留档;
4. 跑批产物逐题可追溯(输入坐标+输出坐标),判分抽查≥20% 复核一致性;
5. 中途换判据=该期作废重跑,判绩账记档。

## 状态

- [x] 2026-10-05 骨架 v0 落档(冻结项 8/11;待回填 3:被测物锚×2+任务集)
- [x] 2026-10-05 platform 3194 函:任务集=SWE-bench Verified 确认+被测物 B=mini-swe-agent 拍定——待回填收窄至 1 项(被测物 A v5-harness 坐标,platform 另函向 v5 索取,10/10 死线)
- [ ] 被测物 A 坐标回填齐备(10/10 前)→ sha16 定版 → 开跑(10/12 榜页)
- [ ] 榜页上线(10/12,壳归 platform,榜面只引本档坐标不嵌全文)
