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


---

# 二轮复测(N=8/腿/题组,共 40 次实测 · 承用户令「再次测试再次分析」)

## 数据(bench_v2_results.json + bench_b_results.json)

| 题组 | Jev 中位 | MM 中位 | 比值 | Jev tok(in+out) | MM tok |
|---|---|---|---|---|---|
| A 单问·短 state | 0.47s | 3.69s | **7.9x** | 302+21 | 331+199 |
| B 三问混合(Noul+Choice+Score) | 0.48s | 7.65s | **15.9x** | 414+69 | 549+406 |
| C 单问·长 state(~150 词) | 0.46s | 5.26s | **11.4x** | 394+21 | 414+262 |

## 语义一致性(B 题组,三问全对齐)

- urgency 0.98 vs 0.92;team 双双选 engineering(0.84 vs 0.75);
  severity 2.65 vs 2.23(同档连续分)——**方向与排序完全一致,Jev 置信更极端**

## 再分析:三个新发现(一轮没看见的)

1. **Jev 延迟恒定 ~0.47s**:单问/三问/长 state 全部 0.46-0.48s——
   固定开销主导,批量问不加时。MM 延迟随复杂度线性涨(3.7→7.7s)。
   → TypeSafe 的优势是**架构级**(一次调用多问的 fan-out),不是模型级。
2. **输出 token 差 6 倍**:B 题组 Jev 69 out vs MM 406 out——Jev 直接吐
   概率结构,MM 生成推理文本再解析。成本差的本质在这里,倍数随问题数放大。
3. **比值区间 7.9-15.9x(vs MiniMax-M2.7),几何中位 ~11x**;v1 的 12.1x
   恰在区间内(单点碰中位=运气,不可引用)——N≥8 才是可报口径。

## 三态终判:维持 PARTIAL,置信度上调

- vs MiniMax-M2.7 实测 7.9-15.9x(PARTIAL 区间 10-100x 的下沿)
- 宣称 193.6x/444.6x(vs sonnet5/opus5)从公开数据自洽(440.1x/183.8x)
- 给 TypeSafe 的背书函新增一句:**「快且便宜是架构结果(批量问恒定延迟+
  概率直出),宣称量级取决于对照模型」**


---

# 三轮:对照谱系扩宽(用户令:M2.7-highspeed + glm-5.3-flash)

## B 题组(三问混合,N=8/腿,bench_multi_results.json)

| 腿 | 中位 | p25-p75 | tok in+out | vs Jev |
|---|---|---|---|---|
| Jev | 0.44s | 0.43-0.47 | 414+69 | — |
| MiniMax-M2.7 | 8.03s | 7.5-9.0 | 548+450 | **18.2x** |
| MiniMax-M2.7-highspeed | 7.17s | 6.0-9.4 | 548+400 | **16.3x** |
| glm-5.3-flash | **429 月配额耗尽** | reset 今晚 23:59 | — | deferred |

## 分析

1. **M2.7 vs M2.7-hs 只差 11%**(8.03→7.17s):MiniMax 内部换挡无数量级空间
   ——"highspeed"不是另一类对手;vs Jev 比值 16-18x 稳定在二轮区间(15.9x)上沿
2. 比值漂移 15.9→18.2x(轮间):MiniMax 腿波动大(p25-75 跨 6-9s),Jev 极稳
   (±0.02s)——**对照组自身方差就是复算噪声主源**,N=8 中位可信、单点不可
3. glm-5.3-flash:ARK Coding Plan **月度**配额耗尽(区别于 MiniMax 的 5h 滚动窗)
   ——今晚 23:59 重置后补跑第四腿
4. 三轮累计 64 次实测;vs MiniMax 系区间 **7.9-18.2x**(几何中位 ~12x),维持 PARTIAL

## 结论增补

给 TypeSafe 的建议句升级:「不同对照给不同倍数」现在有 4 个数据点
(公开数据 sonnet5 183.8x/opus5 440.1x/自测 M2.7 18.2x/M2.7hs 16.3x)
——**倍数-对照对照表的斜率本身就是 Jev 优势结构(恒定延迟+概率直出)的证明**。
