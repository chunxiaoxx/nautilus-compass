# TypeSafe "193.6x/444.6x (proof)" 口径复算报告(2026-09-28 开工件)

> 预注册档:docs/strategy/typesafe_proof_recompute_20260926.md(三态判据)。
> 姿态:同行复现,不树敌(TypeSafe=需求制造机;blog 已自披三条 caveat)。

## 一、口径逆向工程(全部基于 evals.typesafe.ai 公开数字,快照在案)

四任务 × 9 模型三元组(accuracy/cost/time)全抽取(`evals_extract.json`,
快照 4 html + 首页 lens)。**四任务总和比**:

| 对比模型 | cost 比 | time 比 |
|---|---|---|
| **opus 5** | **440.1x** | 88.9x |
| **sonnet 5** | 293.5x | **183.8x** |
| DS v4 pro | 103.3x | 203.6x |
| sol | 209.1x | 54.8x |
| terra | 76.1x | 23.8x |
| haiku 4.5 | 48.7x | 29.5x |

**结论(口径腿)**:
- **444.6x Cheaper ≈ Jev vs opus 5 成本比(440.1x,差 1%)**——口径坐实度高
- **193.6x Faster ≈ vs sonnet 5 时间比(183.8x,差 5%)/vs DS v4 pro(203.6x,差 5%)**——量级坐实,精确锚定模型在 sonnet5 与 DSv4pro 之间,疑站上数字更新过或均值口径微差
- 两个宣称从**公开数据自身**推算即成立(≥100x 量级)——**数量级诚实**

## 二、完整图景(复算报告必带,同行义务)

- Jev 四任务准确率 61.7-76.0%,与 terra/sol/opus5 同档,**低于** sol/opus5 在部分任务(invoice 61.8 vs sol 79.1)
- "快 183x/便宜 440x"成立于**成本与延迟**;**准确率同档不占优**——完整句=
  「Jev 以低 2-3 个数量级的成本与延迟,拿到与主流模型同档(部分任务略低)的准确率」
- blog 自披 caveat 三条已在案(真实增益高端值/无训练泄漏声明/输入更短利己)

## 三、独立重跑腿(进行中)

- **发现**:TypeSafe 官方发布 `system-one-adapter-python`——System One 评测 API 的
  LLM 侧 drop-in(自述"用于 TypeSafe vs LLM 的 cost/speed/intelligence 对比")
- 方案:Jev 侧=SystemOne API(key 可得性待探)/ LLM 侧=adapter[openai]+MiniMax
  (api.minimaxi.com/v1)/ workload=四任务页 full queries
- 若 Jev 侧不可公开获得 → 按预注册「不可运行处置」:口径复算报告(本档)+
  公开函请求评测工件/API 通道

## 快照清单(可复算)

evals_{四任务}.html · typesafe_home/proof_blog/evals.html · evals_extract.json ·
system-one-adapter-python/(clone)
