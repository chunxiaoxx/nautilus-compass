# compass 功能价值登记簿(B1 价值证明门)

> 每个记忆功能上线前必须在此登记可测价值 claim(helps_whom / on_task / measured_by)。
> 空 claim = ⚠️ 待补价值证明 = 不该继续投入(反"堆死机制"·canonical §2.1)。
> 校验器 = `proof/value_gate.py::admit_feature`。

| 功能 | helps_whom | on_task | measured_by | 状态 |
|---|---|---|---|---|
| reinforce_on_recall_hit | tier ladder | 让常被召回的胶囊晋升 | reinforce_count 累积→tier mutation | ✅ claim 完整·待 live 实测 |
| apply_tier_weight | recall consumer | 跨 agent peer learning 召回质量 | PoI cumulative_impact delta | ✅ claim 完整·待 live 实测 |
| tier_promotion_driver | 召回排序 | 高价值胶囊优先 | tier mutation count + recall-hit 命中前移 | ⚠️ 待部署+实测 |
| l2_distiller | 召回压缩/降噪 | 多碎片→高密度摘要 | recall-hit on L2 摘要 | ⚠️ 待部署+实测 |
| OKF exporter/validator | 对外互操作 | 记忆被任何 OKF 工具读 | — | ⚠️ 待补价值证明(互操作价值未绑可测下游) |
| GEP P3 poi_rerank | recall consumer | 已证高影响胶囊前置 | PoI cumulative_impact | ✅ claim 完整·待 serving 接 cumulative_impact |
| GEP P1/P2 capsule_schema | — | — | — | ⚠️ 待补(预备态·gated on V5 写端) |

## 纪律
- 新功能 PR 前:跑 `admit_feature` 自检,空/含糊 claim 直接 defer。
- ⚠️ 行:要么补可测下游价值,要么 defer(不因"已写了代码"就上线=沉没成本陷阱)。
