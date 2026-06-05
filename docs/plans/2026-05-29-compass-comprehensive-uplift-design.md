# Compass v3 全方位提升 · Design Doc

**Date**: 2026-05-29
**Author**: compass-dialog (Claude · session 7h+ R3 override)
**Branch**: `v3-full-fusion`
**Base commit**: `d822174` (Sprint 0 baseline 2/5 placeholder → measured)
**Status**: design draft · pending writing-plans transition

---

## 0. Context · 本次 design 的触发

今天一个 session 内:

1. Sprint 0 baseline 2/5 placeholder → measured · v2.0.1 跑分:
   - **MEME Cas/Del/Abs n=500 · acc=45.6% · recall@30=97.4%** · paper Table 4 reported baselines 第一 (+3.05pp vs MemOS)
   - **LongMemEval-S n=500 · retrieval P@5=0.932 / MRR=0.8585** · vs v0.8 +7.2pp/+17.4pp · 大幅超原 plan "near-zero delta" 预测
   - LongMemEval-S overall acc=0.364 (Gemini-2.5-pro judge · NOT 直接对比历史 56.6% GPT-4o-mini)

2. 实测 dormant differentiation:
   - PoI emit events: **0** (`.cache/poi_emit.jsonl` 不存在)
   - impact_event_count > 0 sessions: **2/1424 = 0.14%**
   - cross-agent contracts consumed: **0** (2 expired in alerts file)
   - drift detection: 25k+ events / act-on rate ≈ 0% (5/27 session)
   - 设计文档充实 (PoI Layer 4 SPEC 400 LOC · v3.5 fusion plan 80h · 6 dormant abilities) · ship 程度低

3. Pilot 0' (5/27) raw data 今日验证:
   - 24 task n=1 dogfooding: A2 naive RAG 87.5% vs A3 compass 83.3% · A3_full 同 verdict
   - 4 实验 (factual/A3-full/drift/recency) · 整体 compass ≈ naive RAG
   - 结论非"compass 没价值" · 是"价值在未测 axes": proactivity 真实 act-on / cross-agent / PoI 经济原语

4. 跨项目 Explore survey (5/22-29 七日):
   - nautilus-core 146 commits · Soul Inc 1/2/3 BINDING-DONE · Inc 1.5 governance vote 复活设计 frozen
   - nautilus-v5 66 commits · RSI-v2 7-task ship · outcome_ledger + telemetry loop ready
   - caishen-ai 14 commits · Phase 2 deep dive (政策图谱 RAGFlow · 残保金自审计自进化)
   - nautilus-compass 5 commits · Stage 1a internal UX shipped · v2.1.2 tag

**核心 insight**: 平台/V5/才燊 70% infra 已 ship · compass 闭环不是"重新发明" · 是"wire 进存量 + ship compass 独有差异化层"。

---

## 1. 理念 (Philosophy)

### 1.1 北星一句话

> **compass v3 = 多 agent 共享的自知预测经济记忆 substrate**

四个修饰词每个有 architectural 后果:

| 词 | H 假设 | 含义 | 落点 |
|---|---|---|---|
| 多 agent 共享 | H3 | 记忆不在 agent 内 · 在 agent 之间 | L4 cross-agent substrate + 平台/V5 事件订阅 |
| 自知 | H5 | compass 知道自己存了什么 + 缺什么 + confidence 多少 | L2 metamemory layer · recall 返 (matches + gaps + confidence + source) |
| 预测 | H1 | 记忆是 agent 预测的 prior · drift = 预测误差 · 误差驱动更新 | L1 drift detection 修 specificity + act-on instrumentation |
| 经济 | H2 | 记忆有 value · outcome impact 量化 · forgetting 是经济淘汰 | L3 PoI emitter + 平台 NAU settlement schema 对齐 |

### 1.2 跟 anchor 的对位

- **anchor #1 agent first / agent 自治生态** → H3 共享 + H5 自知 (agent 间能共享 + 互信任)
- **anchor #2 产品创新 + 递归自我提升闭环优先** → H1 predictive update + H2 PoI 经济信号 (agent 用 compass 输出改自身)
- **anchor #3 反 D 维护 (ship 件数 ≠ 价值)** → H5 metamemory · 治 ssa 76.8pp gap (Gemini hallucinate absence)
- **anchor #5 不重复造轮子** → A 主路径 wire 平台存量 · 不重发 Soul/V5 已 ship 件

### 1.3 明示 defer / 不做

1. **不再追 bench retrieval precision** · Pilot 0' 已证 compass ≈ naive RAG on 单事实 · MEME/LongMem retrieval 当前 SOTA · 这条 saturate
2. **不抢 platform Soul 的 governance 角色** · platform 在 ship governance + NAU settlement · compass 是 substrate 不是仲裁
3. **不抢 V5 RSI 的 agent execution 角色** · V5 在 ship outcome ledger + self-improvement · compass 订阅它的事件流 · 不重做
4. **不靠 H4 时间现象学** · 时间维度已在 (timestamps + recency) · 不算 differentiation
5. **客户获取仍 defer** · 才燊残保金作 bonus grounding · 不是主线 gate

### 1.4 H4 punted 的原因

H4 (temporal phenomenology) 被砍 · 因为 compass 已有 timestamps + recency 加权 · Pilot 0' 实测 recency 加权 A2=86% vs A3=71% · A2 反胜 · 加 H4 这个维度短期回报低。

---

## 2. 架构 (Architecture)

### 2.1 5 层栈结构

```
┌──────────────────────────────────────────────────┐
│ L4 · Cross-agent substrate (H3)                  │
│   - cross-agent contract scanner (已存 · 修 act-on)│
│   - shared memory namespace (新)                 │
│   - 平台 Soul / V5 RSI / 才燊 outcome 订阅 (新 wire)│
├──────────────────────────────────────────────────┤
│ L3 · Economic emitter (H2)                       │
│   - PoI emitter (已设计 SPEC_PROOF_OF_IMPACT)    │
│   - NAU sidecar 跟 platform settlement schema 对齐│
│   - 4-tier 升降级用 PoI cumulative_impact 驱动    │
├──────────────────────────────────────────────────┤
│ L2 · Metamemory layer (H5) ⭐ compass 独立差异化  │
│   - confidence vector (per recall result)        │
│   - "我有 evidence / 我没 evidence" 主动 surface  │
│   - source monitoring (这条 memory 来自哪 session)│
│   - calibration (confidence vs actual correct rate)│
├──────────────────────────────────────────────────┤
│ L1 · Predictive update (H1)                      │
│   - drift event = prediction error signal        │
│   - 修 specificity (false_positive < 5% · 现 ~90%)│
│   - act-on instrumentation (acknowledge / FP / TP)│
│   - 用 act-on 反向更新 anchor 权重               │
├──────────────────────────────────────────────────┤
│ L0 · BGE retrieval (已稳 · 不动)                  │
│   - bge-m3 dense + bge-reranker-v2-m3 · v2.0.1   │
│   - 今天测 LongMem P@5=0.932 · MEME 45.6% · SOTA │
└──────────────────────────────────────────────────┘
```

### 2.2 6 dormant abilities 激活映射

| ability | 现状 | activation path | layer | 工作量 |
|---|---|---|---|---|
| PoI emitter | 0 events | ship code 复用 SPEC_PROOF_OF_IMPACT | L3 | ~400 LOC / 10h |
| cross-agent contracts | 0 consumed / 2 expired | 修 consumer-side scan + emit consumed_by | L4 | ~200 LOC / 5h |
| 4-tier lifecycle | 0 frontmatter | PoI cumulative_impact 驱动 promote/demote | L3↔L4 | ~150 LOC / 4h |
| drift detection | 25k+ events / act-on ≈ 0 | (a) 修 specificity (b) ship act-on UI/log | L1 | ~250 LOC / 8h |
| proactivity (auto-fire) | ✅ fire 中 | 加 act-on instrument (ack/FP/TP) | L1 | ~100 LOC / 3h |
| metamemory confidence | 不存在 | **B 独立切片 · 从零设计 ship** | L2 | ~600 LOC / 16h |

**总计**: ~1700 LOC / 46h · 2-3 周 1 dialog (我) + 部分 dispatch 到 V5 可行

### 2.3 关键 wire 接口 (A 主战场)

```
平台 nautilus-core
  ├─ engine_cycle_outcomes 表 (Soul 产 governance proposal outcomes)
  │   ↓ (read-only subscribe via file watch · ~/.claude/projects/.../memory/_soul/)
  ↓
compass L4 substrate ingest → L0 embed → L3 PoI candidate event
  ↓
平台 NAU settlement (joint schema · platform 仲裁 final)
  ↓ event ack
compass L3 cumulative_impact frontmatter update (in-place)

nautilus-v5 outcome_ledger 表
  ↓ (read-only subscribe)
compass L1 drift detection → act-on event
  ↓ (反喂 V5 telemetry · close loop)
V5 RSI-v2 自提升 cycle
```

### 2.4 compass v3 独立差异化 (B 切片) · L2 metamemory

唯一 compass 全权设计 · 可独立 ship · 不依赖平台:

```python
# recall API 返回升级
class RecallResult:
    matches: list[Memory]              # 现有 · top-K retrieved
    confidence: ConfidenceVector       # 新 · 每条 match 的 confidence
    gaps: list[GapStatement]           # 新 · "我没找到 X 的 evidence" 主动 surface
    source_trail: dict[id, source]     # 新 · 每条 memory origin session
    calibration_score: float           # 新 · 历史 confidence vs actual correct
```

效果: subject LLM 收到 RecallResult 后 · confidence 低 + gaps 显式时 · **不会再 hallucinate "没找到"** · 直接救今天 ssa 76.8pp gap。

### 2.5 跟 platform / V5 边界 contract

| 我 (compass) 做 | 平台 (nautilus-core) 做 | V5 做 |
|---|---|---|
| L0-L2 全栈 own | governance proposal + NAU settlement 仲裁 | agent execution + outcome_ledger |
| L3 PoI candidate emit (joint write NAU schema) | NAU settlement final 仲裁 | V5 调用产 PoI candidate event |
| L4 substrate (subscribe + cross-agent contract scanner) | engine_cycle_outcomes 写表 | outcome_ledger 写表 |
| H5 metamemory (compass 独立) | 不抢 | 不抢 |

---

## 3. 规划 (Planning · 并行三线 · 2-3 周)

R2 override 接受: 4 gates 超期 risk 接受。

### 3.1 Workstream 1 · 理念 · 2-3 天

| 日 | 动作 |
|---|---|
| D1 | 落 philosophy doc 到 docs/plans/ (即此 doc) · cover 北星 + 4 H 对应 + anchor 对位 + defer |
| D2 | issue 2 个 cross-agent contract: compass↔Soul role spec / compass↔V5 outcome sub spec |
| D3 | 等 contract consumer ack (Soul / V5 dialog 回写 consumed_by) · ack 完后 lock 理念 |

### 3.2 Workstream 2 · 架构 · 2 周

#### Week 1 · 并 4 件
- (a) ship L2 metamemory engine 骨架 (confidence vector + gap surface) · ~16h
- (b) PoI emitter 从 SPEC 落代码 (复用 SPEC_PROOF_OF_IMPACT) · ~10h
- (c) drift specificity 修 (target FP <5% · 现 ~90%) · ~8h
- (d) L4 cross-agent contract consumer-side scanner (修 consumed_by emit) · ~5h

#### Week 2 · 并 4 件
- (a) L4 wire 接 Soul engine_cycle_outcomes (read-only subscriber)
- (b) L4 wire 接 V5 outcome_ledger
- (c) drift act-on instrumentation (acknowledge / FP / TP log)
- (d) PoI 4-tier promotion driver

### 3.3 Workstream 3 · 规划 + 测量 · 持续 2-3 周

| 阶段 | 动作 |
|---|---|
| Week 1 | ship telemetry infra (compass-on vs compass-off harness) + N=20 task set curate · 复用 5/27 Pilot 0' 框架 + 加 4 H 维度 task |
| Week 2 | 跑 N=20 受控对比 (compass v2.0.1 vs compass v3 H1+H2+H5 active) · 收 act-on rate / PoI fire / metamemory calibration / cross-agent consumed |
| Week 3 | 分析 · 写 measurement doc · 决 plan_compass_v35_full_fusion Sprint 1-7 gate 是否启 / 调整 |

### 3.4 5th bonus · 才燊 audit pack adopter (可选)

主线 4 gate 走通 + R3 时间允许时启 · 复用 audit_brief.md scope · 跑残保金 audit 真消费 1 个 contract。

---

## 4. 闭环 (Closure · 4 gates 测法)

### 4.1 Gate 1 · Self-dogfooding act-on rate 0 → 30%+

**定义**: compass drift / PoI / metamemory event 触发后 · agent (Claude / V5 / 我) 在下个 turn 真接收并改变行为的事件占比。

**测法**:
- ship `.cache/act_on_log.jsonl` · 每个 drift / PoI / metamemory event 一行
- agent 下回合 acknowledge / FP / TP / ignore 各一个 status
- 2 周窗口 · N(events) ≥ 200 · act-on rate (acknowledge + TP) / N ≥ 30%

**Baseline**: 0% (5/27 session 实测)

### 4.2 Gate 2 · Recursive-improvement metric · compass-on vs compass-off ≥ +10pp

**定义**: N=20 受控 task · 同 model 同 prompt · 唯一变量是 compass active 与否 · 任务质量 delta ≥ 10pp。

**测法**:
- 复用 compass-value-study/run_pilot.py 框架 + 加 H 维度 task
- 任务类型 (4 维): 跨 session 一致性 / 提前 catch contradiction / metamemory 主动 surface gap / cross-agent handoff 不丢
- judge: DeepSeek-v4-pro + 我做 sample human review

### 4.3 Gate 3 · External-agent contract · 0 → ≥ 1 真 consumed

**定义**: cross-agent contract scanner 检测到 1 个 contract 从 outstanding → consumed (consumed_by 字段真填) · 且 consume 行为真消费非假 ack。

**测法**:
- 主战场: compass dialog ↔ V5 dialog / platform dialog 间 issue 真 cross-agent contract
- contract 内容 e.g. "V5 ack compass v3 metamemory schema · 同意订阅" · V5 dialog 在 outcome_ledger 留真 consume trace
- 验证: contract_alerts.jsonl 看 status flip + consumed_by 实有内容

### 4.4 Gate 4 (5th bonus) · Audit pack adopter ≥ 1

**定义**: 才燊残保金 audit 场景跑通 1 个真消费 audit pack contract · evidence pack 至少 E1+E2+E3 三类符合。

**测法**: 接才燊 phase 2 块 3 · compass 作 grounding · audit_brief.md §4 的 6 类 evidence 至少完成 E1/E2/E3 三类 binary 评判。

### 4.5 Closure 反馈环

```
Sprint outcome → act-on rate / recursive metric / consumed count
   ↓
   未达 gate → 回 architecture (修哪层不够) 或 philosophy (北星错了)
   达 gate → 进入 plan_compass_v35_full_fusion sprint 1+ (现 80h 那个)
```

---

## 5. 测试 (Testing Strategy)

### 5.1 不放过的实测

1. **Pilot 0' 复现 + 升级** · 用 compass v3 (H1+H2+H5 active) 跑同 24 task · 看是否仍 ≈ A2 或拉开
2. **N=20 controlled · 加 4 H 维度** · ssa-like (metamemory) / contradiction-prone (drift) / cross-session (sub) / value-laden (PoI)
3. **integration test · wire 接口** · Soul engine_cycle_outcomes 写 mock event · compass 是否 24h 内 ingest
4. **regression test · byte-equal v2.0.1** · COMPASS_USE_LLM_* 全 off 时 · 行为 byte-equal 今天 baseline (Sprint 0 已 lock)

### 5.2 per-anchor 验证清单

| anchor | gate 哪条验 |
|---|---|
| #1 agent first | Gate 3 (cross-agent consumed) · Gate 4 (外部 adopter 若启) |
| #2 递归自我提升 | Gate 1 (act-on rate) · Gate 2 (recursive metric) |
| #3 反 D 维护 | metamemory layer 治掉 ssa hallucinate absence (76.8pp gap 降) |
| #5 不重复造轮子 | architecture A 路径全 wire 平台存量 · 不重发 Soul/V5 已 ship 件 |

---

## 6. Risks · 显式记录

### R2 risk (用户 override 接受)
- 4 gates + 5th bonus + 2-3 周 + 1 dialog → 工作量超 · 接受超期

### R3 risk (本 session > 7h)
- 本 design doc 在 R3 超后产出 · 用户 "持续推进" 默许
- 后续 Sprint 0 architecture ship 会在新 session · 不在本 session 继续

### 平台依赖 risk
- Soul engine_cycle_outcomes 表 schema 若改 · compass L4 wire 断
- 缓解: cross-agent contract 显式 issue · 让 Soul dialog ack schema 不轻变

### 才燊 grounding risk
- 5/8 后停 · 云端 690 commits 未合 · 真消费 audit pack 需先 ssh 验云端活性
- 缓解: Gate 4 是 bonus · 不阻塞主线 4 gates

### V5 dispatch risk
- 部分 architecture 工作量大 · 1 dialog 跑不完 · 需 dispatch 到 V5 dialog
- 缓解: 跟 V5 issue cross-agent contract 明确 ownership · 不假并行

### Innovation 假设 risk
- H1+H2+H3+H5 unified 可能在实测中证伪 (e.g. metamemory 不救 hallucinate)
- 缓解: Gate 2 N=20 受控对比 · 不达 +10pp 触发回 philosophy 修

---

## 7. Next steps

1. ✅ Design doc 写完 (本文件) · commit on v3-full-fusion
2. → invoke writing-plans skill (per brainstorming skill terminal state) · 出实施 plan
3. → writing-plans 出 plan 后 · 转交 executing-plans 或 subagent-driven-development 启 Sprint 0 architecture ship
4. → 2-3 周后 measurement doc · 决 plan_compass_v35_full_fusion 80h 是否真启

---

**Refs**:
- [`plan_compass_v35_full_fusion`](../../../memory/plan_compass_v35_full_fusion.md) (memory)
- [`paper/baseline_v201_sprint0.json`](../../paper/baseline_v201_sprint0.json) (Sprint 0 measured baseline)
- [`paper/SPEC_PROOF_OF_IMPACT.md`](../../paper/SPEC_PROOF_OF_IMPACT.md) (PoI Layer 4 design · 400 LOC)
- [`paper/BLACKBOX_VS_WHITEBOX.md`](../../paper/BLACKBOX_VS_WHITEBOX.md) (honest positioning vs SOTA)
- [`audit_brief.md`](../../../compass-value-study/audit_brief.md) (才燊 audit pack scenario)
- [Pilot 0' raw data](../../../compass-value-study/results/run_20260527-115056.jsonl) (A2≈A3 verified today)
- [Sprint 0 commit `d822174`](https://github.com/chunxiaoxx/nautilus-compass/commit/d822174)
