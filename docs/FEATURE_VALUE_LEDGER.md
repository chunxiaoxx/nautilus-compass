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

## 📊 复测(2026-07-16 · v2.3.0 · 本机 cuda · `tests/eval_recall.py --mode all`)
语料 = C--Users-chunx/memory **131 条** · leave-one-out · bge-m3(cuda)。

| mode | P@1 | P@3 | P@5 | MRR | Δ MRR |
|---|---|---|---|---|---|
| flat | 0.969 | 0.992 | 0.992 | 0.980 | — |
| poi | 0.969 | 0.992 | 0.992 | 0.980 | +0.000 |
| tier | 0.969 | 0.992 | 0.992 | 0.980 | +0.000 |
| gemini | 0.969 | 0.992 | 0.992 | 0.980 | +0.000 |

**判读**:地基 bge-m3 更强(P@1 0.969/MRR 0.980,语料 131 更干净故绝对值高于 6/24);**poi/tier/gemini 仍全 +0.000**——语料诊断 **cumulative_impact!=0 = 0 条 · tier!=working = 0 条 · Gemini off**,三层数学上无信号可作用(非逻辑坏)。第 3 次独立坐实(设计→6/24→今)。**结论不变:lifecycle 三层可测下游 uplift 未证,盒(有真分层信号语料)重测前保持 📊·不美化。**

## 📊 Route A smoke baseline(2026-07-20 · v2.3 · Windows-native Python)

验收口径: 每次提交前至少跑 smoke profile, 产出 `eval-manifest.json`,
`eval_recall.json`, `eval_recall_tuning_hint.json`, `summary.json` 四件套;
full profile 用于长跑分, 不作为每次提交的阻塞项。

- Command: `powershell -ExecutionPolicy Bypass -File tests/bench_profile.ps1 -Suite smoke -Python "C:\Users\chunx\AppData\Local\Programs\Python\Python313\python.exe"`
- Output dir: `.cache/bench-profile-20260720-231150-(default in daemon.py)`
- Python: `Python 3.13.12`
- Corpus: `132` memories
- Recall: flat `P@1=0.970`, `P@3=0.992`, `P@5=0.992`, `MRR=0.9804866850321395`
- Delta: poi/tier/gemini all `+0.000 MRR`
- Tuning risk: `medium`

**判读**: 评测主链已从“单脚本输出”升级为可复现产物链。
当前差异化层仍没有可测 uplift, 主要原因是 tier 信号缺失(`n_tier_nonworking=0`)
和 PoI impact 信号稀疏(`n_impact=1`)。下一轮优化优先级应是写端信号和 tier 晋升,
不是继续堆召回包装。

## 📊 Route C0 dogfood loop(2026-07-21 · eval output -> memory input)

动作: `ops/eval_artifact_to_memory_capsule.py` 将 Route A smoke artifact 写回
`~/.claude/projects/C--Users-chunx/memory`，生成可召回 capsule:
`session_eval_capsule_a1de8859df15_route_a_benchmark.md`。

写端信号:
- `tier: semantic`
- `cumulative_impact: 1.0`
- `impact_event_count: 1`

复测命令: `python tests/eval_recall.py --mode all --out .cache/eval_recall_after_capsule_v2.json`

复测结果:
- Corpus: `133` memories
- Signal counts: `n_impact=2`, `n_tier_nonworking=1`
- flat MRR: `0.981`
- poi delta MRR: `-0.0006265664160400863`
- tier/gemini delta MRR: `-0.0006835269993165083`
- tuning artifact: `.cache/eval_recall_after_capsule_tuning_hint_v2.json`

**判读**: 闭环已从报告进入写端, 差异化层第一次产生可测信号; 但单个
高层 benchmark capsule 对 leave-one-out 排序是轻微负增益。代码解释逻辑已调整:
负 delta 不再被泛化为“没测出”, 而是输出 `retune_lifecycle_weight`。下一步应做
PoI/tier 权重门控与 paired ablation, 而不是继续增加 capsule 数量。

## 📊 Route C1 sparse-signal gate(2026-07-21 · eval output -> tuning input)

动作: 在 `tests/eval_recall.py` 增加 `--signal-policy guarded`。当
`cumulative_impact` 或 promoted-tier 信号低于最小支持量时, 评测主链不让该信号参与
排序加权, 避免单个高层 capsule 把局部查询排序拉偏。默认策略仍为 `raw`, 便于做
paired ablation。

复测命令: `python tests/eval_recall.py --mode all --signal-policy guarded --out .cache/eval_recall_after_capsule_guarded.json`

复测结果:
- Corpus: `133` memories
- Signal counts: `n_impact=2`, `n_tier_nonworking=1`
- Guard threshold: `min_signal_count=3`, `min_signal_fraction=0.02`
- flat MRR: `0.981`
- poi/tier/gemini delta MRR: `+0.000`
- tuning artifact: `.cache/eval_recall_after_capsule_guarded_tuning_hint.json`

**判读**: C1 没有证明 lifecycle 已带来正增益; 它证明了负反馈能进入架构调优闭环。
C0 的轻微负 delta 被门控消除, tuning hint 现在明确输出:
`collect_poi_support_before_enabling_weight` 和
`collect_tier_support_before_enabling_weight`。下一步不是把 guarded 当胜利,
而是继续 dogfood 真实执行结果, 积累至少 3 条以上 impact/tier 支持信号后做
raw-vs-guarded 配对复测。

## 📊 Route C2 paired policy gate(2026-07-21 · raw vs guarded)

动作: `tests/bench_profile.ps1` / `tests/bench_profile.sh` 在原 `run_all`
raw recall 后追加 guarded recall, 再通过 `ops/recall_policy_gate.py` 生成
机器可读晋升门。该 gate 不让诊断性 raw 负反馈使 smoke 失败, 但会阻止 raw
lifecycle 成为默认策略。

复测命令: `powershell -ExecutionPolicy Bypass -File tests\bench_profile.ps1 -Suite smoke -Python "C:\Users\chunx\AppData\Local\Programs\Python\Python313\python.exe"`

复测产物: `.cache/bench-profile-20260721-035112-(default in daemon.py)/`

关键结果:
- Raw: poi `-0.0006265664160400863`, tier/gemini `-0.0006835269993165083`
- Guarded: poi/tier/gemini `+0.000`
- Policy gate: `block_raw_lifecycle_promotion`
- Recommended default: `guarded`
- `raw_lifecycle_allowed: false`

**判读**: benchmark 主链已具备“评测结果驱动架构默认值”的闭环能力。
当前不是宣称 compass lifecycle 已 SOTA, 而是明确给出: raw 加权在信号稀疏时有害,
guarded 是安全默认; 只有当后续真实执行胶囊带来 ≥+0.005 MRR uplift 且无负 delta,
raw lifecycle 才能进入默认候选。

## 📊 Route C3 runtime/default preflight(2026-07-21 · gate -> default)

动作: 新增 `recall_pkg/lifecycle_policy.py` 和 `ops/recall_policy_preflight.py`。
runtime recall 默认策略从 raw 改为 `guarded`; `COMPASS_RECALL_SIGNAL_POLICY=raw`
只作为显式候选开关, 且应先通过 `recall_policy_preflight.py`。`tests/bench_profile.*`
现在在 policy gate 后追加生成 `recall_policy_preflight.json`。

复测命令:
- Raw 拒绝: `python ops\recall_policy_preflight.py --policy-gate ".cache\bench-profile-20260721-035112-(default in daemon.py)\recall_policy_gate.json" --target-policy raw`
- Guarded 接受: `python ops\recall_policy_preflight.py --policy-gate ".cache\bench-profile-20260721-035112-(default in daemon.py)\recall_policy_gate.json" --target-policy guarded`
- Profile: `powershell -ExecutionPolicy Bypass -File tests\bench_profile.ps1 -Suite smoke -Python "C:\Users\chunx\AppData\Local\Programs\Python\Python313\python.exe"`

复测产物: `.cache/bench-profile-20260721-040249-(default in daemon.py)/`

关键结果:
- `policy_gate: block_raw_lifecycle_promotion`
- `policy_recommended_default: guarded`
- `raw_lifecycle_allowed: false`
- `policy_preflight: accept`
- `policy_preflight_target: guarded`

**判读**: C2 的评测结论已经进入默认策略层。现在的安全状态是:
raw 仍可作为诊断/候选评测模式存在, 但不能在当前证据下成为默认召回策略。
这把“输出变输入”从报告推进到了 runtime 配置和发布前检查。

## 纪律
- 新功能 PR 前:跑 `admit_feature` 自检,空/含糊 claim 直接 defer。
- ⚠️ 行:要么补可测下游价值,要么 defer(不因"已写了代码"就上线=沉没成本陷阱)。
- 📊 行:已实测但 delta≈0 → 诚实记录·查根因(逻辑无效 vs 语料无信号)·不混为一谈。
