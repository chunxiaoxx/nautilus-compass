# Plan · confound-check 观测常态化(对接 conductor·零新建)· 2026-06-23

> 源:V5 6/23 广播「confound-check 观测原则」+ token 列请求。用户要"智能化运行所需监控常态化 + 与现有基础设施对接"。
> 北极星纪律:监控是**支撑**不是主线——只做"直接防中心环误判走错路"的 confound-check 一层;不建看板/统一控制面(parking 至蒸馏证活)。anchor #5 复用 conductor·#3 反 D。

## 0. 元原则(钉死)
**更智能 ≠ 更多监控,而是每个失败 verdict 信之前先过对应阶段 confound-check。** 复用现成观测点,不新建采集系统。今天 4 个 confound 坑(1.5B adapter 没存 / 7B seq 截断 / PostTrain 版本 / sanity 进程死)全是 env/config 伪装成能力失败——若不查就走错路(差点去搞 H100/更大模型)。

## 1. 承载件(全现成·不新建)
- **常态化中枢 = `scripts/conductor_run.py`**(nautilus-conductor.timer 已 LIVE·每 10min·写 `last_pulse.json`)。监控常态化的载体就是这个常驻进程,新增只是 pulse 多几个字段。
- **各阶段守卫已就位**:`distill_eval.py`(distilled_len vs base_len)· `fde_verdict_guard.py`(verdict_kind)· `distill_fuel.is_a_bucket`(毒料/gate-artifact)· `fuel_summary()`(读 ALE records)。

## 2. 统一 schema:`confound_checks`(一个 dict·各阶段守卫顺手填)
```
confound_checks: {
  <check_name>: {"ok": bool, "note": str}   # ok=True 排除了该 confound
}
```
规则:**任何 KILLED/失败 verdict,若 confound_checks 有 ok=False 或缺关键 check → 标 "confound 未排除·不可信",不当能力结论。**

各阶段必填 check(映射现成观测点):

| 阶段 | check_name | 判定(现成数据) | 落点文件 |
|---|---|---|---|
| 训练 | `seq_not_truncating` | 每条 prob_tok+sol_tok ≤ max_seq | conductor token 列(下) |
| 训练 | `loss_decreasing` | trainer log_history 末 loss < 首 loss | distill_qlora 训练日志(已 logging_steps=1) |
| eval | `adapter_effective` | distilled_sol≠base_sol 或 distilled_len≠base_len | `distill_eval.py`(已算 len·补 flag) |
| eval | `solution_nonempty` | distilled_sol 非空非纯语法错 | `distill_eval.py` |
| 燃料 | `strong_nonzero` | strong_score>0(非毒) | `distill_fuel.is_a_bucket`(已判·补导出 flag) |
| 燃料 | `doubao_genuine_fail` | doubao 败非 gate-artifact | compass measurement-first / is_a_bucket |

## 3. 改动(三件·按价值排·都在现有代码内)

### A. eval 补 `confound_checks`(最高杠杆·今天就救了我们)
- 文件:`scripts/distill_eval.py`
- 改:per_task 已有 base_len/distilled_len·加 `adapter_effective` + `solution_nonempty` 两 flag,写进 `eval_result.json` 顶层 `confound_checks`。
- 价值:KILLED verdict 自带"adapter 生没生效"——再不会把"adapter 没存"误读成"机制死"。

### B. conductor 加 token 列(V5 请求·`fuel_summary` 现成扩)
- 文件:`scripts/conductor_run.py` 的 `fuel_summary()`(已 load A 类 records)
- 改:对每条 A 类 record 算 `prob_tok+sol_tok = len(chars)/3.48`,收集 `token_flags=[{task_id, tok, truncate_risk: tok>4096}]`,加进返回 dict。
- `derive_blockers`:若有 truncate_risk 题 → 加 blocker `"N 条 A类 @4096 截解风险·训练前过滤"`。
- 价值:新燃料一进,pulse 自动标哪条会截解(像 ahc008 6170)·训练前过滤,不再事后发现 artifact。

### C. conductor pulse 汇聚 confound 状态(把 A 接上中枢)
- 文件:`scripts/conductor_run.py` 的 `memory_writer`
- 改:读最近 `eval_result.json` 的 `confound_checks`,任何 ok=False → pulse `blockers` 加 `"verdict <id> confound 未排除: <check>"`。
- 价值:下个 session 起手读 last_pulse.json 就知道"哪个 verdict 不可信",连续性 + 防 session 间重踩。

## 4. TDD(纯逻辑可单测·effect gated)
- 新纯函数 `services/confound_check.py`:
  - `eval_confound_checks(per_task) -> dict`(A 用)
  - `token_truncate_flags(records, max_seq=4096, chars_per_tok=3.48) -> list`(B 用)
  - `unresolved_confounds(eval_result) -> list[str]`(C 用)
- 各 5-8 TDD green·再接进 conductor_run/distill_eval 的 effect 层(IO 在 effect·逻辑纯)。

## 5. 边界(不做·过分叉过滤器)
- ❌ 不建监控 daemon / 看板 / Grafana / 统一控制面(parking 至蒸馏证活)。
- ❌ 不让 conductor 开放判断/auto-修(反 drift 铁律·只确定性检测 + surface + 白名单触发)。
- ❌ 跨框实时 observability(MCP ingest_obs 实时拉各框状态)= compass v2.3.0 v1.8 自动重连修复的球·我不重造传输层。

## 6. 落地次序 & 球
- **等手头 1.5B sanity verdict 出**(eval agent 在跑)再动手——loop-first·不分心。
- 然后:`confound_check.py` TDD → A(eval)→ B(token 列)→ C(pulse 汇聚)→ 部署 conductor(已 systemd·改 conductor_run.py + scp)。
- **soul(我)**:A/B/C 三件(都在现有代码内·小)。
- **compass**:v2.3.0 带 v1.8 MCP 自愈(跨框实时通道)。
- **V5**:燃料侧 is_a_class 守卫已带·新燃料 token 也盯(我 token 列与它对齐)。
