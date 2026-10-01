# §4 品类横评:agent-memory 层的数字现状

> Trust Report #3 第四节。全部数字来自一手实抓(官网 HTML 直检/TechCrunch 报道/PyPI),核验窗口 2026-09-26/30;来源坐标在 §注。

## 一张表看清

| 厂商 | 定位(自述) | 融资 | 头条数字 | 可独立复算? |
|---|---|---|---|---|
| mem0 | "The memory layer for AI agents" | $24M A 轮(Basis Set 领投,TechCrunch 2025-10) | "186M API calls in Q3" | ❌ 自报 |
| Zep | "unified context layer"+治理 | 独立运营(Zep Software Inc.) | LoCoMo 94.7% / LongMemEval 90.2% | ❌ 自报,挂自家首页 |
| Letta | stateful agents/自编辑记忆 | $10M seed(Felicis 领投,TechCrunch 2024-09) | — | — |
| TypeSafe | 决策引擎/System One | 阿里领投 $3 亿(集团级,非本产品线) | "193.6x Faster, 444.6x Cheaper (proof)" | ❌ **proof 不可点击**(§2 详) |

## 三个观察

1. **资本、叙事、治理口号都在;可复算的数字一个都没有。**四家的头条全部是自报口径——这不是批评个体(行业默认如此),是空位声明:整个品类没有第三方验证位。
2. **自报的常见形态三种**:倍数(无对照集披露)/百分比(无判分协议公开)/调用量(无审计口径)。买方在采购前无法复算任何一条。
3. **例外值得说**:TypeSafe 的开源仓 typesafe-jev 公开了种子化 fixtures+可重生成语料+显式 caveat——**开源部分的可验证性高于其商业首页**(我们正是因此能在其开源语料上完成 92.6% 口径的独立测量,见 §1 与 Issue #2)。同一家公司,开源层与营销层的可验证性倒挂,这本身就是品类状态的缩影。

## 我们的位置

不与四家比数字——比"数字的生产方式"。判据预注册/工件全归档/失败样本公开/第三方可复算,这套流程我们已经对自己用(§1 判分器自纠错)、对开源语料用(gtaras7 测量)、对商业声明用(TypeSafe 四轮复算)。品类缺的不是一个更好的 benchmark,是验证位本身。

§注:mem0 mem0.ai+TechCrunch 2025-10-28;Zep zep.ai(2026-09-30 实抓);Letta TechCrunch 2024-09-23;TypeSafe typesafe.ai(HTML 直检)+gtaras7/typesafe-jev 仓。我方外联三件的 offer 全部在途(issue #2440/#7514/邮件),任何一家开放配置,我们按同一协议复算并公开。
