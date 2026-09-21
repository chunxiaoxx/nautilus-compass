# Jev 结合六向·深度调研报告(2026-09-21 深夜)

> 方法:两轮搜索(LLM observability 竞品×对抗校准学术×TypeSafe 定价×Jev-as-judge
> 生态)+ 既有实弹经验。结论分级:✅调研支持/⚠️待验证/❌假设受损。

## 逐向研判

### ① 持续校准监控(信任 APM)——✅ 空白确认,时机由 Jev 生态本身创造

- **竞品格局**:2026 年 LLM 输出漂移监控已是红海(Confident AI/Galileo 各发九平台
  对比:LangSmith/Arize/Langfuse/Arthur/Galileo…),但**全部监控输出质量/幻觉/drift,
  无一家做概率校准监控(ECE/Brier 追踪)**——不是他们做不到,是生成式 LLM 输出无概率
  语义,校准监控无对象。**Jev 类决策模型兴起第一次让校准监控既有对象又有必要**。
- **成本侧**:TypeSafe 定价 $0.042/M input(output 免费)——抽检式持续监控的边际
  成本≈0(我们 240 题=0.3 美分),订阅制商业模式的成本基础成立。
- **护城河评估**:LangSmith 们有钱有分发,若需求被验证会跟进。我们的结构性优势=
  **独立第三方身份**(监控者不能是被监控模型生态的销售方;TypeSafe 自建监控=自评
  悖论)+判据库+回执格式。⚠️ 需求侧尚未验证(M1 逻辑同款风险)。

### ③ 对抗校准挑战集(研究 #2)——✅ 学术钩子已找到,假设可证伪

- **学术富矿**:RLHF 训练导致 verbalized overconfidence(ICLR 2025,135 引)——
  **Jev 的 RLCD 同属 RL 系训练,是否继承此病?无人测过**(完美钩子:有先例假设、
  无验证、官方宣称 calibrated 构成可证伪声明)。
- 「Your Model Is Most Wrong When It Sounds Most Sure」(2026-04)=公众议题化;
  LLM-as-Judge 过置信(arXiv 2025-08)/校准对分布敏感(apxml)/Dunning-Kruger
  效应(NeurIPS)——引用链完整。
- **研究 #2 设计锚**:对抗分布(指令改写/边界构造/framing)上测 Jev 校准崩溃
  模式;预注册判据已就位(calibration-claim-verify-v1+对抗库四类)。本周可出。

### ⑤ Jev-as-Judge 执照——✅ 生态确认存在

- yibie 目录 evaluation 节实测:judge 实践已活(Jev judge call vs dimension
  scores / event validation 对比 / web analyzer 十问)——被验证的判官=刚需位。
- 我们判据库 15 条中 judge-systematic-inconsistency 等判官类判据现成——
  **认证位是既有能力的自然延伸,零新建**。
- 建议形态:judge 项目挂「assayed judge」回执(ECE+一致性双指标)。

### ② 双门架构(Jev 快筛+密码学终裁)——⚠️ 工程自洽,待触发

六层信任栈活示范;与 v5 分级判分同构。成本(调用 Jev 筛记忆)=每条 0.0004 美分
级。**暂无外部需求触发,列后排**(内部先用:判材预检场景试点)。

### ④ 数据集决策级校准——⚠️ 方向真实,现实性待 Day0 验证

具身数据集带 policy 概率字段的现实比例未知(AGIBOT manifest 待 Day0 时实测)。
若主流数据集不带决策分布,此向降级为「数据集验证的可选维度」。

### ⑥ Assay 判分头(verdict 语料训小判分器)——✅ 可行性已被 NanoJev 证明

0.6B 复刻 RLCD=NanoJev 已证;我们的独有燃料(带签名 verdict 语料 240+ 卷)。
**反自指护栏内建(只训小判分器)**;排 J4(挂语料≥2000+M2 的既定门槛不变)。

## 新发现(调研副产品)

1. **Jev 在 OpenRouter**(typesafe/jev-1.13)——第三分发位,徽章提案的市场面可扩。
2. **无免费层描述但有 250 req/min 限速**——批量评估与监控的吞吐天花板已知。
3. 监控竞品的九平台对比文章本身=**投放渠道清单**(研究#2 发布后可逐家投)。

## 修正后的推荐序

**研究 #2(对抗校准)本周启动**——学术钩子最硬(RLCD 继承假设)+衔接研究#1
边界声明+awesome-jev/TypeSafe 双方都要+发布渠道现成。①(信任 APM)随 TypeSafe
回音产品化。⑤轻件随 judge 项目登门顺带。②④⑥后排各等触发。

来源:Confident AI/Galileo 九平台对比、arXiv 2025-08(LLM-as-Judge 过置信)、
ICLR 2025(RLHF reward calibration)、tianpan.co 2026-04、TypeSafe blog(定价)、
OpenRouter/Requesty/APIDog、yibie/awesome-jev(生态实测)。
