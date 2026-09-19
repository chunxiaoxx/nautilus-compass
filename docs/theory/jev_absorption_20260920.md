# Jev 架构吸收路线图(2026-09-20 · 承 flywheel 调研 v0 + 我方 NanoJev 实审)

> flywheel 已立四层栈蓝图(L3 Jev决策/L2世界模型/L1 VLA/LV验证器=我方创新位)。
> 本档=compass 侧吸收清单:Jev 五创新如何为我所用。

## 一 · 五项架构创新 → 我们的三条吸收线

### 吸收线 A:决策头=我们小判分器的正确架构(T7 合规形态)
Jev 核心:冻结主干+决策头,状态问题进、**完整概率分布出、零输出解码**。
我们的燃料层判分器(语料≥2000 后训)照此造:
- 输出空间=固定三态 {agree, disagree, not_computable}(+可扩判据 id 的
  dynamic choice:2-N 候选各给概率——**"适用哪条 CATALOG 判据"本身就是
  dynamic choice**);
- **架构级消灭裁量**:LLM 判官 14.2% 无声错标的根因=自由文本解码;决策头
  输出空间固定=神经判官拿到"构造保证"的下限——Q1 边界的架构解;
- 零解码=低延迟=**可进 ingest 热路径**(记忆门毫秒级判分);
- 训练=CE/Brier 校准(paired proper-reward,NanoJev 已开源全流程)——
  校准即安全层,判分器 AUC 门之外加 Brier/ECE 门。

### 吸收线 B:轨迹验证格式=VerifyPack 的具身扩展
初态哈希+冻结 cohort+控制器规则显文化+重放校验(NanoJev 全套,我 Tier-2 已
实测)。落法:VerifyPack v0.3 增 `episode` claim kind(payload=cohort jsonl,
check=replay);判据库增 calibration-claim-verify-v1(校准声明复算:Brier/ECE
在公开 holdout 上重算)。flywheel Day0 规格(568 函)同源。

### 吸收线 C:并行决策=多声明一次判
Jev "6状态·18问题·44候选·1次forward"。我们对应:一个 pack 内 N 条声明,
判分器批量一次 forward 出全 verdict 分布——回执批量化的延迟基础。

## 二 · 分工(flywheel 蓝图上的我方位)

- **LV 验证器层=compass 主场**:小判分器(决策头)+轨迹回放判分器+判据库;
- flywheel:L1-L3 数据与训练基础设施(他们已在调研 SOTA);
- 燃料闭环:verdict 语料(现在 ~50 行)→ ≥2000 → 训 A/B 线判分器 →
  AUC≥0.87∧Brier 门 → ingest 门实装 → 更多 verdict → 复利。

## 三 · 近期工程件(与 loop v2 对齐)

1. 判据库:calibration-claim-verify-v1 注册(1 天);
2. VerifyPack v0.3:episode claim kind+replay check 骨架(2 天);
3. NanoJev 权重级物理重放=第一张全栈复算回执(GPU/CPU 推理 0.6B,可行);
4. 语料聚合器:把创世回执+考试 verdict 聚成训练集视图(1 天);
5. (挂语料量)判分器训练试点:Qwen-0.6B+三态头,NanoJev 训练脚本可借。

## 四 · 红线

T7 反自指不变(判分器不判自己的考试;三门仍构造保证,神经判分只做语义域
辅助+ingest 门);对 Jev/NanoJev 的吸收=借架构不抄代码(MIT 允许但注明出处,
他们是盟友不是猎物)。
