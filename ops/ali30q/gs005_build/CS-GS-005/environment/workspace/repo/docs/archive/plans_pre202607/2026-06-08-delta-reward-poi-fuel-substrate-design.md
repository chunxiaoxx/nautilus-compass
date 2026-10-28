# ΔReward → PoI fuel substrate 设计(Horizon 2 · 闭环复利)

> 回 cnt_compass_platform_deltareward_fuel_c3(compass→platform):实测 ΔReward(grounded-vs-裸·A 簇客观打分)是否升格 PoI 真 fuel + 怎么落库/消费。
> 承接 `2026-06-08-rsi-grounded-retrieval-soul-half-design.md`(Horizon 2)+ soul 已 ship `grounding_probe_twosample`/`grounding_probe_continuous`(出 ΔReward + escapes_noise)。

## 1. 裁定(platform/soul 半边)
**ΔReward 升格 PoI 真 fuel:✅ 是,但 gated on `escapes_noise=True`。**
- ΔReward = grounded−裸 在真 benchmark(AutoLab radix_sort 等)上的客观连续测量 → **外部 ground truth·非内部 verdict 自评** → 直击 self-referential PoI 病(6/3-6/4 那轮 "executed_ok 算不算够格 fuel" 的自指顾虑根除)。
- **只 escapes_noise=True 的行 PoI-eligible**(ΔReward>0 且置换/符号检验 p<0.05)。平/降/不显著 = 不给 credit(不给噪声印币·anchor#3)。
- = 6/1 `design_external_selection_pressure` 要的外部选择压力,第一次有客观落点。

## 2. 为什么单独表(不混 fde_verdicts)
fde_verdicts 语义 = 单交付物的 checklist verdict(items/veto/overall_pass)。ΔReward 语义 = **一道 benchmark 题、两臂、N 候选的配对实验结果**。强塞 fde_verdicts = schema 滥用(同 fde_verdict 模型 docstring "Deliberately SEPARATE from engine_cycle_outcomes—do not merge" 原则)。→ 新表 `fde_rsi_deltas`。

## 3. Schema:`fde_rsi_deltas`(待 build·见 §5 gate)
| 列 | 类型 | 说明 |
|---|---|---|
| id | int PK | |
| delta_id | str unique | 幂等键(`<benchmark>\|<producer>\|<run>`) |
| benchmark | str | 如 `autolab_radix_sort` |
| task_uid | str | 题 uid |
| producer_model | str | 如 `doubao-2.0`(归因 + 防混臂) |
| n_bare / n_grounded | int | 每臂候选数(power 审计·N≥5) |
| bare_mean / grounded_mean | float | 两臂均 reward |
| delta_reward | float | grounded_mean − bare_mean |
| p_value | float | 置换/符号检验 |
| escapes_noise | bool | **PoI-eligible 闸** |
| grounding_source | json | 注入的避坑 reason 摘要(可追溯·复利分析) |
| created_at | datetime | |

## 4. 接口(mirror fde_verdict.py 模式)
- `POST /api/platform/fde/rsi_delta`:soul 跑完 grounding_probe → 落一行(幂等 on delta_id)。envelope `{success,data,error}`。
- `GET /api/platform/fde/rsi_delta/{task_uid}`(或 list `?escapes_only=true`):读回。
- **compass PoI 消费契约**:订阅 `escapes_noise=True` 的行 → PoI credit ∝ `delta_reward`(客观外部 lift)· 归因 producer_model/agent。**绝不消费 escapes_noise=False**(否则又退回噪声自指)。
- **复利测量**:同 benchmark 随语料增长 ΔReward 的时间序列 ↑ = RSI 真在发生且可量化(平台数周追的 RSI 证据)。难题加权:按 `轴 C best 前沿分低` 的题上 ΔReward 给避坑原子排序(compass turf)。

## 5. Build gate(anchor#3 · 反 speculative)
**本 doc 只设计 + 定契约,不 build 表/端点。** 理由:
- ΔReward 数据**还不存在**(首验未跑)。为不存在、且可能永不为正(escapes_noise 可能恒 False)的数据建表 = speculative infra(ship 件数≠价值)。
- 区别于 grounding feed(暴露**已存在**的 verdict reason·故已 build)。
- **build 触发条件**:首验产出**第一个 escapes_noise=True 的 ΔReward**(真值得持久化的外部正信号)→ 那时按本 schema build 表 + 端点(TDD·mirror fde_verdict·~1 session)+ 告知 compass 接 PoI。
- 在此之前:compass 拿本契约规划 PoI 消费侧;cnt_c3 = 设计/契约交付(裁定 + schema + 消费规则)。

## 6. 数据流(全景)
```
V5 run_two_arm(N≥5/臂·doubao)→ compass eval(客观 reward)
  → soul grounding_probe_twosample → {delta_reward, p_value, escapes_noise}
  → [escapes=True] POST /fde/rsi_delta(待 build)→ fde_rsi_deltas
  → compass PoI 订阅 escapes 行 → credit ∝ delta_reward(外部·非自评)
  → 语料增长→同题 ΔReward 时序↑ = RSI 复利可量化
```

## 7. 红线
- PoI 只从 escapes_noise=True 流(不给噪声/不给内部自评)。
- ΔReward 必须来自客观自动验证器(AutoLab/KernelBench reward·非 LLM judge)。
- 不 build 表直到首验出第一个正 escapes(YAGNI)。
