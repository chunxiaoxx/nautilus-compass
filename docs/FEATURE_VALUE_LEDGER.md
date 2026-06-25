# compass 功能价值登记簿(B1 价值证明门)

> 每个记忆功能上线前必须在此登记可测价值 claim(helps_whom / on_task / measured_by)。
> 空 claim = ⚠️ 待补价值证明 = 不该继续投入(反"堆死机制"·canonical §2.1)。
> 校验器 = `proof/value_gate.py::admit_feature`。

| 功能 | helps_whom | on_task | measured_by | 状态 |
|---|---|---|---|---|
| reinforce_on_recall_hit | tier ladder | 让常被召回的胶囊晋升 | reinforce_count 累积→tier mutation | ✅ access 事件 LIVE(daemon bumped=3)·access→tier wire 本地建+TDD(53dce44)·**未部署盒**(gated) |
| apply_tier_weight | recall consumer | 跨 agent peer learning 召回质量 | leave-one-out MRR delta(eval_recall --mode tier) | 📊 **本地实测 Δ MRR +0.000**(2026-06-24·语料 tier 99% working 无信号)·待盒 9720 重测 |
| tier_promotion_driver | 召回排序 | 高价值胶囊优先 | tier mutation count + recall-hit 命中前移 | ✅ 部署 LIVE(盒 timer·2 真 mutation)·但 9720 中仅 2 过门=信号稀疏 |
| l2_distiller | 召回压缩/降噪 | 多碎片→高密度摘要 | recall-hit on L2 摘要 | ⚠️ 待部署+实测 |
| OKF exporter/validator | 对外互操作 | 记忆被任何 OKF 工具读 | — | ⚠️ 待补价值证明(互操作价值未绑可测下游) |
| GEP P3 poi_rerank | recall consumer | 已证高影响胶囊前置 | PoI cumulative_impact | ✅ claim 完整·待 serving 接 cumulative_impact |
| GEP P1/P2 capsule_schema | — | — | — | ⚠️ 待补(预备态·gated on V5 写端) |

## 📊 Benchmark 实测(2026-06-24·阶段1 内部 A/B·`tests/eval_recall.py --mode all`)
语料 = compass-dialog 本地 1106 记忆 · leave-one-out · bge-m3(cuda)。

| mode | P@1 | P@3 | P@5 | MRR | Δ MRR |
|---|---|---|---|---|---|
| D0 flat | 0.807 | 0.841 | 0.857 | 0.836 | — |
| D1 poi | 0.807 | 0.841 | 0.857 | 0.836 | +0.000 |
| D2 tier | 0.807 | 0.841 | 0.857 | 0.836 | +0.000 |
| D3 gemini | 0.807 | 0.841 | 0.857 | 0.836 | +0.000 |

**诚实判读**:bge-m3 地基已强(P@1=0.807·MRR=0.836)。lifecycle 三层在此语料 **全 +0.000**——根因 = 语料 **cumulative_impact=0 文件·tier 99% working·Gemini off**(无元数据信号),**不是 lifecycle 逻辑无用**(rerank TDD 证模式真切换)。
**真瓶颈 = 晋升频率**:盒 9720 中仅 2 过 impact 门、reinforce 多为 1·分层太稀疏推不动召回。要测真 lifecycle delta 必须在盒 9720 语料跑(那里 tier 晋升真跑过)·且需先让分层不那么稀疏(降晋升门槛 / 让 access→tier wire 接上)。
**对 B1 价值门的意义**:tier_weight/PoI 当前可测下游 uplift = 0.000(本地)→ 不能凭"已写代码"主张价值;盒重测前保持 📊 待证·不美化。

## 纪律
- 新功能 PR 前:跑 `admit_feature` 自检,空/含糊 claim 直接 defer。
- ⚠️ 行:要么补可测下游价值,要么 defer(不因"已写了代码"就上线=沉没成本陷阱)。
- 📊 行:已实测但 delta≈0 → 诚实记录·查根因(逻辑无效 vs 语料无信号)·不混为一谈。
