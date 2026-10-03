# 前沿对照调研:组织四主线 × 学界业界 2026 活跃点(2026-10-03)

> 性质:调研档(口径=组织各框近期目标与教训 × 学界业界前沿 → 解决方案落位)。
> 检索:WebSearch 三把(PRM/test-time scaling·judge 校准/conformal·LoRA 遗忘/具身验证闭环),2026-10-03。
> 证据层:学界状态=检索读数[实测·二手](未读原文全文,引用前须核);我方对应=仓内实测。

## 一、理论锚:因果倒置的四句同一性

四主线(compass/assay/论文/动态训练)是同一原理的四个实例化——验证从下游成本变为上游源头:

| 主线 | 倒置形态 | 一句话 |
|---|---|---|
| assay | 验证前置于能力声明 | 先考试,后宣称 |
| compass | 验证前置于信任 | 先复算,后采信 |
| P3 训练 | 验证前置于权重 | 真值驱动更新,回归门后才上岗 |
| 论文 | 验证前置于知识 | 可复算才发表(sha 锚定+预注册) |

压缩必有损,验证是压缩的对偶补差;倒置=验证从事后审计变为事前结构。竞品(Aegis/mem0/Zep)全在压缩侧(记忆治理),对偶侧无人占位。

## 二、学界业界 2026 活跃点 × 我方对应(三踩中一空位)

### 2.1 LLM-as-Judge 校准与偏差(最热)

- 学界 [实测·二手]:ICLR 2026《Robust Statistical Evaluation with Imperfect Judges》(小规模人标校准集估 TPR/FPR→方差校正估计量);《Calibration as a First-Class Criterion in LLM Evaluation》(HF,2026-09 position paper);conformal prediction 判官区间(首个分布无关覆盖保证框架);LatentEval per-bias map(逐偏差配检测+校正);agreement/position bias 校正系。
- 我方对应:jev-trust"校准即产品"(ECE 三态)+三供应商终判+非实现者复算+判官自报三陷阱(is_correct 复写/M2 等价改写误伤/特征含被检输出)。
- 差分:我方多一层**组织制度版**——判据演进程序化(用户裁+技术审定 T1/T2+止损线防加注,10/3 v2-final 首例)在学界无对应物。

### 2.2 PRM 过程监督与 test-time scaling

- 学界 [实测·二手]:Snell et al.(test-time compute>参数扩容,过程验证器奖励);自动化 PRM(MCTS 生成 step 标注)成主流;generative vs discriminative verifier 成设计轴;label-free verification(hidden-state 轨迹)兴起;VisualPRM/VersaPRM 多域化。
- 我方对应:帧级判据(sign 语义+幅度带宽)=过程监督的具身版;verdict 语料(1468+增量管道,带签名出处/判因/白名单门)=稀缺的 step 级标注源;P3 动态判官(回归门上岗)=verifier 的持续学习形态。

### 2.3 LoRA 持续学习与遗忘

- 学界 [实测·二手]:ICLR 2026 LoRA 遗忘理论;正交子空间 LoRA(spectral thresholding,每任务独立子空间);SAE 引导激活正则(plasticity/stability 权衡)。
- 我方对应:P3 回归门(REG-100 零 correct→incorrect 翻转)=行为级防遗忘;热启动+replay 1:1。
- 实测(10/3 S3 工程):challenger(2 epochs delta14+replay14)binary 0.9122 vs champion 0.9189,微降 0.7pt 三门全绿——行为门在微增量下天然少触发。

### 2.4 具身数据验证闭环(真空位)

- 检索零直接命中("embodied data curation verifier loop"无竞品研究)——数据引擎(verifier-in-the-loop)概念在自动驾驶有,具身数据 QC+第三方判分无学界对应。
- 我方占位:G1 三锚定案+pusht 全弧(帧级/配对/rollout 两版判据+终判)+QC 判据(修复三判据)+噪声底三级证据链(权重 bit 同/帧级字节同/任务级逐局同)。

## 三、解决方案落位(缺口×前沿映射)

1. **判官学习化**←自动化 PRM 路线:判例→样本转换器内嵌判读工具(verdict 结构天然映射训练样本),语料 schema 对齐 PRM 格式——进入学界主流训练法的入场券。瓶颈=流入速率(14/案 vs 200 门槛),解=转换器机制化+案源扩。
2. **判分置信升级**←conformal prediction:jev-trust 0.3 加 conformal 模块(三态+覆盖率保证,纯 CPU 有开源实现)——从 ECE 实测升到保证级校准,jev-trust 从工具变方法贡献。
3. **判官偏差治理**←LatentEval 同构:我方"三陷阱+T1/T2"升级为**偏差地图组织版**(每类偏差:定义/检测探针/校正程序/判例)——进判例集 v1 与 assay protocol V1,对学界热题的独立贡献。
4. **遗忘防线**←行为门+正交子空间双保险:大训练单(≥200)时叠加正交子空间法,让 G1 门从"经常挡"变"天然少触发"。
5. **五框分工**:flywheel 数据(真空位实证主体)·v5 燃料(PRM 格式入场券)·platform 治理(宪法 V1.2 vs Constitutional AI,独立 shorts 素材)·compass 判分(偏差地图+conformal)·assay 考场(对抗题库+诚信计分=动态基准缺的验证协议标准化位)。

## 四、论文谱系(校准后)

paper1 系统(drift 检测,已发)→ paper2《Judge Failure in the Wild》问题侧(素材熟,待提交)→ **paper3《验证前置:因果倒置的验证机构》方法制度侧**(§3 判据演进案例=10/3 活案例;§实证=具身真空位+七演;novelty 有据)→ 验证学习(kimi①,理论)→ 元理论(压缩×验证哲学,更远)。

## 五、Sources(引用前须读原文核验)

- Snell et al., Scaling LLM Test-Time Compute Optimally(openreview.net,697+ cites)
- Process Reward Models for Unlocking Test-Time Scaling(ACM RecSys'26)
- Automated Process Reward Model via MCTS(arxiv.org,2025-10)
- Calibration as a First-Class Criterion in LLM Evaluation(huggingface.co,2026-09)
- Robust Statistical Evaluation of LLMs with Imperfect Judges(ICLR 2026)
- Analyzing Uncertainty of LLM-as-a-Judge with Conformal Prediction(github.com/BruceSheng1202)
- Theoretical Insights on LoRA's Forgetting(ICLR 2026)
- Spectral Thresholding in Continual LoRA(openreview.net)
- LatentEval: per-bias map for LLM judges(2026-05)
- MRT: Meta Reinforcement for Test-Time Compute(ICLR)

> 注:本档结论的学界状态部分为检索摘要级 [实测·二手],写论文引用前逐篇读原文; upgrade_path=每条引用处读原文后升 [实测]。
