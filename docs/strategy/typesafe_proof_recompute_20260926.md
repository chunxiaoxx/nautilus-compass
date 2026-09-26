# TypeSafe「193.6x/444.6x (proof)」公开复算立项档(2026-09-26 用户批)

> 用户令:五件全批之五。姿态定调(承 9/20 reassessment):**agree 是礼物
> 不树敌**——TypeSafe 是需求制造机,复算=给他们背书或帮他们收紧口径,
> 两种结果都是市场动作。

## 一手事实(9/26 官网+blog 实抓)

- 首页宣称:"193.6x Faster, 444.6x Cheaper *based on workflows for
  System One tasks (proof)"
- blog《Introducing System One Models and Jev》已自我披露三条 caveat:
  ①"we expect that these are on the higher end of real world gains"
  (自认是真实增益的高端值)②workflows"not in our training distribution"
  (声称无训练泄漏)③"The relatively shorter input paints our model in
  an advantageous light"(自认输入更短利于己方)
- 对比对象含 GPT-5.6 Terra;blog 有"Extraordinary claims"段自引

## 预注册判据(开工前写死,只许更严;对外报数纪律适用)

1. **目标**:独立复现 193.6x/444.6x 的**可复现性**(数量级),非复刻
   精确值——workflow 级计时+成本,同 workload 对拍(Jev vs 一个主流 LLM)
2. **三态结论**:
   - REPRODUCIBLE:我方独立跑出 ≥100x/≥100x(数量级一致)→ 公开背书函
   - PARTIAL:10-100x → 如实双报+口径差异分析(哪一段差距来自测量口径)
   - NOT-REPRODUCIBLE:<10x 或无法运行 → 公开问询函(请求工件/口径)
3. **不可运行处置**:若 proof 工件不公开/不可跑,产出=「请求工件公开」
   公开函(calibration-claim-verify-v1 的标准动作:宣称即义务,
   工件即证据)
4. 红线:不指控造假(人家自己贴了 caveat,是诚实的强者);复算函
   语气=同行复现,不是审计执法


## 工件坐标·预备轮实抓(2026-09-27 02:3x,轮 40 · 快照在 runtime/typesafe_*.html)

| 工件 | 坐标 | 公开度 |
|---|---|---|
| proof 声明本体 | 首页 (proof) 链接 → `typesafe.ai/blog/introducing-system-one-models-and-jev`(blog 正文,非独立基准页) | 全公开 |
| **workflow 对拍数据** | `evals.typesafe.ai` 首页 Lens 图:Jev 67.8%/$0.0004/**0.4s** · terra 67.9%/$0.0304/10.1s · opus5 73.1%/$0.1761/37.8s · sol 74.1%/$0.0836/23.3s · sonnet5 67.8%/$0.1174/78.1s · haiku4.5 53.6%/$0.0195/12.5s · DS v4×2 · luna | **数字全公开**(每模型 accuracy/cost/time 三元组) |
| 四任务 per-case 页 | evals 站:security_incidents / agent_trace_observability / invoice_processing / customer_service(.html) | 待细抓(9/28 第一动作) |
| 可跑接入 | `github.com/typesafe-ai/system-one-adapter-python`(System One LLM Python adapter) | repo 公开 |
| 直测入口 | console.typesafe.ai/playground?share=shr_13a74b49…(blog 内可分享 playground) | 需 console 账号? |
| 第三方参照 | llm-benchmarks.diegoromero.es(blog 引) | 弱相关 |

**初步口径分析(预备轮推算,待 9/28 细核)**:
- 444.6x Cheaper ≈ opus5 workflow 成本比(0.1761/0.0004=**440x**)——宣称大概率锚定 opus 5 workflow 口径
- 193.6x Faster 与首页图任何一对(0.4s vs 最慢 78.1s=195x sonnet5!78.1/0.4=195.25≈193.6 量级)——**疑似锚定 sonnet5 workflow 时间**;细核待四任务页
- 注意:evals 图里 Jev 67.8% 与 terra 67.9% 准确率几乎持平,而 opus5/sol 更高(73.1/74.1)——「快且便宜但不更准」是复算报告要如实呈现的完整图景(同行复现姿态)

## 9/28 开工清单(就绪状态)

1. 抓四任务 per-case 页(runtime 快照)+定位 193.6/444.6 精确出处对
2. clone adapter-python,跑通最小调用(是否需 API key=playground/console)
3. 对照腿:MiniMax(配方=memory minimax-coding-plan-provider)同 workload 计时+成本
4. 产出:三态判定(≥100x=REPRODUCIBLE / 10-100x=PARTIAL / <10x 或不可跑=NOT-REPRODUCIBLE→公开问询函)

## 执行计划

- 9/28-29:抓 proof 工件坐标(blog 内链/GitHub)+搭 workload 对拍脚手架
- 9/30-10/2:跑复现(MiniMax 供对照 LLM,Jev API 直测)
- 产出:复算报告(三态之一)+公开函草稿(呈用户批后外发)
- 与英文架构文同期发布(《验证即协议》第一案例=同行复现 TypeSafe)

## 关联

jev_reassessment_20260920(需求制造机论)/masterplan §四(判绩账×
Jev 生态)/@宪法第十二条第一层(coding 验证=真值工厂)
