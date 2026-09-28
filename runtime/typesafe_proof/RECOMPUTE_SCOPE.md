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


---

# 终判(2026-09-28 · 双腿数据齐 · 按预注册三态)

## 独立对拍数据(本机实测,bench_pair.py,N=5/腿)

| 腿 | 延迟中位 | 波动 | 答案稳定性 |
|---|---|---|---|
| Jev(jev-latest@官方API) | **0.46s** | 0.42-0.66s | noul=0.98 ×5 完全一致 |
| MiniMax-M2.7(adapter) | 5.56s | 3.5-6.8s | noul 0.90-0.95 波动 |
| **延迟比** | **12.1x** | | |

语义:双腿同判 urgent 高概率,方向一致;Jev 输出更稳。

## 三态判定:**PARTIAL**(10-100x 区间,按预注册字面)

- 我方独立跑出(vs MiniMax-M2.7)=**12.1x 延迟**——落在 PARTIAL(10-100x)
- 成本腿:Jev 302+21 tokens/次,计价未公开;MiniMax M2.7 为低价模型,成本比
  预计 <延迟比,不强行报数
- **口径差异分析(PARTIAL 定义要求的如实双报)**:
  1. 宣称 193.6x/444.6x 的对照=sonnet5/opus5(口径腿坐实:公开数据 183.8x/440.1x)
  2. 我方对照=MiniMax-M2.7(可用供给里最快),得 12.1x——**倍数主要由对照模型决定,
     非宣称失真**
  3. 宣称与其公开 evals 数据**自洽**(差 1-5%);其 blog 已自披「真实增益高端值」
  4. 无 sonnet5/opus5 key,未建第三腿——不假装跑过
- 完整图景句(进公开函):Jev 以两个数量级更低的成本/延迟(vs opus5/sonnet5)
  拿到同档准确率;vs 低价快速模型(MiniMax)差距收窄到 ~12x 延迟,且输出更稳定。

## 结论句

**宣称可信、口径成立、量级依赖对照**——给 TypeSafe 的背书函可写,
加一条建议:官网标注对照模型名(193.6x vs sonnet 5 / 444.6x vs opus 5),
消费者可自助换算。
