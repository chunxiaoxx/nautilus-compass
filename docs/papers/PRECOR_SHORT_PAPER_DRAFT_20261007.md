# Quantized Small Judges: A Preregistered Deployment-Precision Study of a Production Verification Judge(DRAFT v0.1)

> 目标:arXiv short paper 或官方博客首发(研究空白:无先例同时覆盖 量化×小判分×鲁棒性,四路调研 2026-10-07 确认)。状态=骨架 DRAFT,开业(10/12)后一周内定稿投出。

## Abstract(骨架)

Small language models (SLMs) are increasingly deployed as verification judges, yet their
robustness to post-training quantization — the default cost-saving step in production —
remains unstudied. We present a preregistered deployment-precision study of a production
three-state verification judge (Qwen3-1.7B + LoRA, 88.5% binary accuracy), evaluating four
precision configurations × two decoding regimes on 291 held-out cases. Under a preregistered
agreement gate (≥99% vs the bf16 anchor), fp16 passes with zero label drift while int8
(98.28%) and int4-nf4 (94.16%) fail. We release the full judgment matrix, gating criteria,
and a deployment-precision discipline for verification judges, and discuss implications for
registry-based self-improving judge systems (NACRE).

## 1. Introduction

- 判分器(judge)作为独立服务的兴起;部署成本驱动量化;但 judge 的量化鲁棒性缺研究(SLM-as-judge survey 亦指出 robustness 研究不足);
- 我们的独特视角:judge 不是一次性评测组件,而是**持续学习回路的核心**(误判→registry→再训练)——量化漂移会污染整个自进化回路的信号;
- 贡献:①首个预注册的 judge 部署精度判定(含判门)②部署纪律(bf16/fp16 only)③带可复算证据的负结果方法论。

## 2. Setup

- Judge:NACRE judge instance v1(Qwen3-1.7B + LoRA r16/α32,adapter sha16=dbcbab6f…),三态判读(pass/fail/insufficient_evidence),生产 acc 88.5%(ECE 0.072);
- 数据:291 held-out cases(train/dev 切分独立,qid 防泄漏);prompt=训练模板族(剔除 judge_output 作弊通道);
- 配置:{bf16, fp16, int8-bnb, int4-nf4} × {greedy, T=0.3};统一 merge 后权重(规避 peft×bnb hook);
- 判门(预注册):某精度可部署 ⟺ greedy 对 bf16-greedy 判定一致率 ≥99%(容错 ≤2/291)。

## 3. Results

表 1:精度×解码 → 三态 acc/对 bf16 一致率/判门(数据=PRECOR_BC_VERDICT 表,复制);
- fp16:一致率 1.0000(零漂移);int8:0.9828(2 翻转);int4:0.9416(17 翻转);
- 漂移-量化强度单调;与 3B 判分器独立观察(0.817@4bit)互证;
- 一致率(判定)≠输出逐字一致——逐字口径会产生全假红(方法论警示段)。

## 4. A Deployment-Precision Discipline for Verification Judges

四条(从 PRECOR_BC_VERDICT 提升):精度门/判据冻结门/U 态门/判绩账双向;
与 registry 的交互:judge 漂移=registry 判例判定的系统性噪声源→重锚机制(锚定链 L0-L3)。

## 5. Related Work

SLM-as-judge survey(robustness gap)/量化行为预注册研究(LessWrong 2026)/LLM-as-a-Verifier(连续打分)/RIPD 攻击(判据操纵)——各占一面,无交叉(我们的位置)。

## 6. Limitations & Negative Results

单一 judge 实例(泛化到其他 judge 待验)/软维度(连续档)数据因工程缺陷本轮缺失(补跑中)/翻转清单以聚合一致率呈现(逐题清单 v2)。

## 7. Artifact

判定表+判据档+runner(merge-quantization 版)+CSV/log——全 sha 锚(nautilus-compass 主仓+HF org)。

---
素材源:PRECOR_BC_VERDICT_20261007.md+PRECOR_JUDGE_ROBUST_20261006.md+run.log。
定稿检查单:□英文润色 □matrix 图表 □相关工作补引(Claw-SWE-Bench 若同期)□作者/署名口径(用户定)□投递目标(arXiv vs 博客,开业后按传播五层顺序排)。
