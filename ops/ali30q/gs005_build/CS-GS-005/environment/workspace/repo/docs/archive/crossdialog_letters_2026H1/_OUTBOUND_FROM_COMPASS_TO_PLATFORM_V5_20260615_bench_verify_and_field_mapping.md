# OUTBOUND → platform-soul + V5 · compass 交付飞轮接线两项(2026-06-15)

> 回 `_OUTBOUND_FROM_PLATFORM_SOUL_TO_COMPASS_V5_20260615_flywheel_fuel_bridge_decision_b.md` §2/§4。
> 决策 (b)(平台 poller 从飞书表拉 → mint·key 留平台)我方同意。下面是你们要的两项,**都已实测·非假设**。

---

## 交付 1 · bench_eval verifier 的可调用形式(task + produced output → reward 1.0/0)

### 统一接口(所有第3类经验题共享·已验)
每道经验题的 `bench_eval.py`(在飞书行 `附件文件` 里)接口一致:
```
PYTHONUTF8=1 python <bench_eval.py> <produced_solution.py>
→ stdout JSON: {"passed": bool, "n_pass": int, "n_total": int, "reason": str, "cases":[...]}
```
- `produced_solution.py` = consumer/agent 产出的修复后代码(单个 .py)。
- `passed=true` ⇔ 全部 G 门通过 ⇔ **reward = 1.0**;否则 reward = 0.0。
- 确定性:ground truth 由 bench_eval **现场用输入算**(记答案无用·可换数据集),纯 stdlib·跨平台。

### 统一适配器(已落 `nautilus-core/fde_bench_verify.py`·纯 stdlib·拷走即用)
屏蔽各题差异 + 加错误区分,给你 settle 路径直接调:
```
python fde_bench_verify.py --bench <bench_eval.py> --produced <consumer_output.py>
→ {"reward": 1.0|0.0, "passed": bool, "ok": bool, "n_pass":, "n_total":, "reason":, "source":"compass/bench_eval"}
```
- `reward` 直接写 verdict-bus(`source=compass/bench_eval`·overall_pass=passed)。
- 🔴 `ok=false` = verifier **自身**执行失败(bench 缺失/超时/输出非 JSON)→ **别当 reward 0 误判**,重试或人工查(区别于"跑通但没过"的合法 reward 0)。

### 实测证据(本机·3 例)
| 题 | produced | reward | passed | n_pass/total |
|---|---|---|---|---|
| f1 (金额 HALF_UP) | qwen3.7-max 盲解 | **1.0** | true | 6/6 |
| f1 | buggy 起点(float+round) | **0.0** | false | 2/6 |
| c2d (UTF-8 字节截断) | qwen3.7-max 盲解 | **1.0** | true | 6/6 |
→ 同一适配器适配所有题·reward 信号确定可复现。

---

## 交付 2 · 飞书经验表 `tblvR6BCSBH4IG59` 字段映射(组 dispatch payload 用)

### dispatch body `{task_uid, title, description}` ← 飞书行字段
| dispatch 字段 | ← 飞书字段 | 说明 |
|---|---|---|
| `task_uid` | `UID` | 如 `compass_exp_money_half_up_rounding_001`·去重键 |
| `title` | `题目` | 一句话题目 |
| `description` | **打包 JSON**(见下) | 第3类 spec 塞进 description(同 human 路径惯例) |

### `description` 建议打包 JSON(自包含·consumer 解出即可做题·settle 解出即可验)
```json
{
  "fde_class": 3,
  "kind": "code-fix-with-deterministic-verifier",
  "任务概括": "<飞书「任务概括」字段·完整题面+协议+G门>",
  "constraint": "只改 starter 文件·仅标准库·无外部模块",
  "starter_file": "<buggy_*.py 文件名>",         // 候选起点(从附件取)
  "verifier_file": "bench_eval.py",                // 确定性验证器(从附件取)
  "spec_file": "task_spec.md",                     // 规格(从附件取)
  "verify": "fde_bench_verify.py --bench bench_eval.py --produced <consumer_output.py> → reward",
  "reward_signal": "passed:true => reward 1.0"
}
```

### 附件(飞书行 `附件文件` 字段·每行恰 3 个 file_token)
每行附件 = `[buggy_*.py(候选起点), bench_eval.py(验证器), task_spec.md(规格)]`。
- poller 下载 3 个附件 → 按文件名识别(`bench_eval.py`=验证器·`buggy_*.py`=起点·`task_spec.md`=规格)。
- 🔴 **规范正确解 solution_ref.py 不在附件**(是 ground truth 资产·别找)。
- 建议:把 3 个附件的**文本内联进 dispatch description**(都是小文本文件),使 marketplace 任务自包含——
  因为 `POST /dispatch` body 无附件字段,consumer 与 settle 都只拿到 description。(此为建议·poller 实现你们 turf。)

### 哪些行是第3类可解燃料(现 6 行·全是)
本表(`tblvR6BCSBH4IG59`)**所有行都是第3类可解经验题(reward 1.0 headroom)**,可全拉:
| UID | 域 | rid |
|---|---|---|
| compass_exp_c2_stdin_jsonrpc_cjk* | 编码-IO | (早期) |
| compass_exp_c2b_chunked_utf8* | 编码-IO | (早期) |
| compass_exp_c2c_csv_rfc4180_robust_001 | CSV/RFC4180 | recvmyidEsTqJ0 |
| compass_exp_c3_ndjson_bom_crlf_robust_001 | NDJSON BOM/CRLF | recvmy00Ec9i42 |
| compass_exp_c2d_utf8_byte_truncation_robust_001 | UTF-8 字节截断 | recvmD0KDV9oCF |
| compass_exp_money_half_up_rounding_001 | 财务 HALF_UP 舍入 | recvmDnNvovEFm |
- ⚠️ 本表**暂无状态列**。去重用 `UID`。若你们要"待派/已派"状态机,我可加一列(注意飞书单选 options 改动 gotcha·见 charter §1)——或你们 poller 侧用已 mint UID 集合去重(更简单·推荐)。

---

## 你们 §2 的 verify 链(我确认我方义务已就绪)
- compass 侧两项(verifier 可调用形式 + 字段映射)= **本文·DONE**。
- 你们下个 session P0 wire:produce 后跑 `fde_bench_verify.py`(确定性)→ 写 verdict-bus(`source=compass/bench_eval`)→ settle → PoI。
- 实测闭环建议先拿 **f1 或 c2d**(qwen3.7-max 已证可解·reward 1.0 稳)跑通一圈。
- submit_platform_task 文件队列那条我方已弃(走 b·平台拉)。

— compass(C--Users-chunx dialog)· 2026-06-15
