# Assay-Head 立项书(Jev 吸收线 A 终局件 · 2026-09-22 用户拍板)

> 命题来源:Compass×Assay×Jev 融合四向第 ①号(反常识:裁判先自裁——验证器长成
> 被验证范式的形状)。承 Jev 吸收路线图 J4 训练试点(docs/theory/jev_absorption_
> 20260920.md),吸收 NanoJev 已验证的 RLCD 训练配方。**反自指护栏内建**。

## 一 · 定义

**Assay-Head = 一个 Jev 式小判分头(0.6B 级),输入题卷三元组,输出三态+校准概率。**

```
输入: (starter_code, produced_diff, test_file_paths) → tokenized
输出: { verdict: agree | disagree | not_computable,
        confidence: calibrated probability,
        gate_fail_type: syntax | apply | test_fail | nc_missing_dep | clean }
```

角色=**预筛选**(pre-verdict):90% 显然没问题/显然有问题的卷子毫秒级分流;
10% 边缘案例走完整密码学管线(三门+人工终判)。**永不冒充 verdict**——输出
名 pre-verdict,终判权在判卷方,墙只认 verdict。

## 二 · 反自指护栏(五红线,违一条即停)

1. **只训小判分器**(≤1B 参数),不训生成模型,不训与被测 agent 同代的模型
2. **训练数据全带签名出处**(verdict 语料经 VerifyPack 导出器,行级 criteria_ref)
3. **Assay-Head 自己的校准用我们的判据验**(calibration-claim-verify-v1)——
   裁判被判,递归信任
4. **语料门槛 ≥2,000 行 verdict**+M2 后才启动正式训练(当前 ~400 行,先做
   zero-shot baseline)
5. **不可用 Assay-Head 判定 Assay-Head 自己的输出**(禁止直接自评;独立校准
   集必须外部)

## 三 · 架构(承 NanoJev 配方,改造点)

| 组件 | NanoJev | Assay-Head 改造 |
|---|---|---|
| 底座 | Qwen3-0.6B | 同(或同家族最新小底座) |
| 训练目标 | RLCD(校准决策强化) | 同+**成本加权**(错放一个 disagree 比错放一个 agree 贵——门代价不对称) |
| 输出空间 | Noul/Choice/Score | **Choice(三态)+ Score(gate_fail_type 置信度)+ Noul(can_judge?)**——第四输出:模型自判「这题我能不能判」,低置信时主动弃判(→人工),这是 NC 态的架构化实现 |
| 输入格式 | state+questions | (starter, diff, tests) 三元组 token 序列;diff 用 hunk 标记对齐 |

## 四 · 数据(现盘点)

| 来源 | 行数 | 状态 |
|---|---:|---|
| 首考 5 题(含 pass@2) | 12 verdict | 已签名 |
| 重考 3 题 | 9 | 已签名 |
| 扩量 4+1 题 | 12 | 已签名 |
| 三臂 9 卷(3 臂×3 题) | 9 | 部分已签 |
| 10-verdict 复算 | 10 | 已签名 |
| C 族校准 6 条 | 6 | 已签名 |
| **合计** | **~58 verdict** | **缺口:1,942 → 需攒** |

攒语料路径(按密度排序):①分级判分试点(v5 702)每轮产生全量 pre-verdict
vs verdict 对→语料行;②考场周考扩量(每周 4-5 题×多点);③外部 DCR 订单
(每单 200-600 题);④对抗样本库(注入负例,无需真实 LLM 产出)。

## 五 · 分阶段(与现有里程碑挂钩)

**Phase 0(现在-10/26):zero-shot baseline**
用 hosted Jev 直接当 pre-verdict(不改权重):输入=题卷描述(state=diff 摘要,
question=「will this pass tests?」)。零训练成本,出一致性读数。**这不需要任何
GPU,本周可做**。

**Phase 1(M2 后):SFT 冷启动**
语料 ≥2,000 行时,LoRA 微调 0.6B(参考 NanoJev 训练配方,GPU 短租半天)。
产出=assay-head-v0.1,部署为 MCP 工具(assay_pre_verdict)。

**Phase 2(M3 后):RLCD 校准精调**
用校准损失精调(CE→Brier 渐进),目标是 ECE ≤0.05(预筛不需要 0.01,边缘
自然走人工)。**成本不对称加权**在此步引入。

**Phase 3(远期):在线学习**
分级判分试点产生的新 verdict 实时回流=持续校准(信任即订阅的内部版)。

## 六 · 评估(预注册判据)

Assay-Head 的成绩单用我们自己的判据来出:
- calibration-claim-verify-v1:ECE ≤0.05=可上线预筛;0.05-0.10=仅 advisory
  (置信度显示但不分流);>0.10=不上线
- judge-systematic-inconsistency-v1:同卷重跑一致性 100%(温度=0)
- 对抗样例库:四类盲区不降级

## 七 · 商业闭环

- **内部**:判分吞吐 24h→<1s(趋势线出点密度×1000);考场可日考不周考
- **外部**:assay-head-v0.x 的校准报告本身是一张 DCR——「我们验证器的校准
  水平」挂墙=判分能力即营销
- **API 化**(远期):pre-verdict MCP 工具对社区开放(免费层)——SDK 生态
  的第二个装机路径
