# 统一验证合同 v0 · 从四套验证协议到第三方验证平台(2026-08-31)

> 定位:数据飞轮的目标 = **数据第三方验证平台(有效性验证)**。compass 早期"接地召回/接地监管"
> 的记忆有效性验证与具身数据飞轮的 P1 数据效用验证,是同一合同在不同物理层的实例。
> 本文把已盘点的四套验证协议抽象为一份统一合同,标出现有实物与缺口。
> trace_id: unified-verification-contract-20260831 · 状态: v0 草案待用户拍板

## 1. 已有实物盘点(全部可独立复核)

### A. 记忆有效性验证(compass 本行 · "接地召回/接地监管"的落地形态)

| 原语 | 实物位置 | 验证什么 |
|---|---|---|
| proof-of-recall | `docs/PROOF_OF_RECALL.md`(v1.5)+ `tests/test_proof_of_recall*` | recall 返回 recall_token(30min TTL),下游引用 token 才算消费——协议级杀"召回了但忽略"假闭环(P1-1 家族) |
| proof-of-impact | `tests/test_mcp_proof_of_impact.py` + MCP `proof_of_impact` | 记忆被组合进产出后回写影响 |
| drift 门 | `tests/drift/`(firing/no_progress/specificity_baseline/v2)+ `eval_drift*` 四件 + MCP `drift_check/history` | 人格/口径漂移监管 |
| governance 族 | MCP `governance_audit/dispatch/lock_check/plan` + `examples/v7_governance_demo.py` | 治理审计与派单门 |
| SSOT 副本探针 | recall hook v2.3(commit 141040c) | 跨 repo 哈希漂移亮牌(今天仍在工作) |
| recall 有用性实验 | `tools/recall_usefulness_exp.py` | F2 delta=1:检索组 vs 盲打组对照 |
| 探针纪律 | 护栏#3"自报不算,探针才算" | 一切 alive/done 声明的仲裁口径 |

### B. 数据/燃料有效性验证(飞轮侧 · **实物已在 compass 仓,交汇点已存在**)

| 原语 | 实物位置 | 验证什么 |
|---|---|---|
| fuel intake | `tools/fuel_intake.py`(stop hook,0-LLM) | 信号词提炼→pending 池,content_hash 去重,source_session 溯源 |
| Gate B QC | `tools/fuel_qc_batch.py` | **control-先失败门**:裸模型答不出=有 headroom→过门转正;14 天过期;月增 ≥10 条判据 |
| 交付 QC 门 | `vtf/batch_guoshu_202607/verifiers/qc_gate_v0.py` | v0 门 23 行判读与人工 QC 零漏判零误伤 |
| 双门+独立复现 | external_verified 只认独立复现(护栏#1) | income 唯一门 |
| 数据效用协议 P1 | 飞轮框 Task18(Ap 81% vs B1 0%) | 精选数据 vs 对照的真实效用差 |
| 双判分互核 | `tools/cross_judge_analysis.py` + v4 翻案案例 | 平台判分→生产者重测→仲裁翻案(单边判分两边都会错的实证) |
| 预注册判据 | d12/d13/v4/d6 全在用 | 先写死过门条件再跑,防事后挪门 |
| 基准复算器 | LME-S 三指标 + `scripts/reproduce_lmes_retrieval.sh`(fa71bda) | 对外数字的一键独立复算 |

**关键发现**:`vtf/fuel_pool/` 就是两个飞轮的代码层交汇点——记忆(session 提炼)已经在被当"燃料数据"走 intake→QC→入池管道。统一验证平台不是新造,是把这次交汇正式化。

## 2. 统一验证合同 v0(五步 schema)

```
CLAIM    生产者提交:这条记忆/这段数据/这道题/这个权重 有效
VERIFIER 注册验证方法(四选一,可组合):
         V1 control-先失败(Gate B:裸模型先答不出=有 headroom)
         V2 独立复算(固定 env+固定数据+一键脚本,如 d13/LME-S)
         V3 对照效用(P1 协议:精选臂 vs 对照臂差值)
         V4 物理不可仿真性(具身:熵含量 QC,协议有、验证器待建——唯一空位)
PREREG   预注册判据(过门条件先写死并公开)
DUAL-GATE 双门执行(生产者臂 vs 独立臂)+ 幂等去重
VERDICT  签名回执→台账→消费计数;分歧时第三方互核仲裁(v4 模式)
```

映射:记忆有效性 = CLAIM(教训有用)+ V1/V2 + proof-of-recall 消费;
燃料有效性 = CLAIM(题有 headroom)+ V1;具身数据 = CLAIM(仿真器造不出)+ V4/P1;
对外 benchmark 数字 = CLAIM(跑分属实)+ V2 复算器。

## 3. 缺口(从"各自的验证"到"平台"的四步)

1. **无统一合同接口**:四套协议各有 schema,无共同 claim→verdict 信封;`_OUTBOUND` 函缺 trace 字段(hook 亮牌中)是同一病根。
2. **消费闭环半断**:proof-of-recall token 机制在,但消费计数未接全部下游(v4 验证积压靠人催、raid 46 败/天无声空转都是此缺口)。
3. **对内 only**:全部验证能力走内部 MCP,第三方供方/需方无入口——产品化缺口即平台化缺口。
4. **V4 空位**:物理不可仿真性验证器无实物,只有协议思想;具身数据进来只能走 P1 间接验证。

## 4. 落地路线(最小步,不开新战线)

1. **v0(纯文档,本文)**:合同 schema 定稿 + 四协议映射,等用户拍板。
2. **v1(首个正式案例)**:d13 定案按合同格式归档(claim=刀3 LoRA 有效/无效,verifier=V2 独立复算,prereg=d12 对照,verdict=待出)——用真案例校准 schema,不写代码。
3. **v2(最小接口)**:验证回执统一 JSON schema(`{claim_id, verifier_type, prereg_ref, verdict, receipt_sig}`)进台账;`_OUTBOUND` 函模板补齐 5 字段。此时对外"第三方验证平台"才有第一个可卖的接口。
4. **V4 验证器**(具身侧,依赖飞轮框协同):不可仿真性测试 = 用仿真器重放候选数据,测其统计特征能否被仿真器分布再生;产出即具身数据的"Gate B"。

## 5. 营销联动(回答"一炮而红"的定位差异)

市面记忆/数据产品的跑分全是自报;compass 全链数字附一键复算脚本 + 独立判分记录(d13 双域、v4 互核翻案全程公开)。
**"验证文化"就是第三方验证平台的第一个对外 SKU**:对内是基础设施,对外是品牌差异点——
landing 页"为什么可信"一节 = 本合同的对外版(自报不算+复算入口+预注册判据)。
