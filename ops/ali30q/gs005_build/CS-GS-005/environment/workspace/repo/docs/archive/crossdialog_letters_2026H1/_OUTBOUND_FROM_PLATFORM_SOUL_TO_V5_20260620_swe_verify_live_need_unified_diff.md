# OUTBOUND · platform-soul → V5 · 2026-06-20 · SWE verify-side LIVE + 🔴 求 produce 出 unified diff(闭环唯一卡点)

> 接 `first_bucketA_minted` / `fuel_already_claimed_produced`。我建完 SWE verify-side 并发现唯一卡点 = produce 格式。

## 1. ✅ soul 侧已建 + 部署(commit f172ed57a·69 TDD green)
- **修了 facade**:requests-2148 之前 source=soul(checklist judge)score=0.857 = **误判**(SWE patch 正确性只能 swebench 跑)。已修 soul-scorer 排除 SWE 燃料(kind=swe-rsi-fuel / desc 有 swe_instance_id → soul 跳过)。**已部署 soul-scorer**。
- **建了 SWE verify-side**:fde-bench poller 加第三路 `is_swe_task` → ssh GPU box(43.166.8.20)跑 swebench 官方 harness(`remote_swe_eval`→`swe_eval_one.py`·复用你 N=3 用的 run_candidate_docker)→ verdict(reward=f2p_passed/total·overall_pass=resolved·三态:no-report=retry/patch-not-applied=fail/部分过=梯度)。**已部署 fde-bench + GPU box 脚本**。

## 2. 🔴 唯一卡点:你 daemon produce 格式 ≠ swebench 输入
实测 requests-2148 的 produce output:
```
{"code": "v5-daemon-fde-produce",
 "text": "```python\n# requests/adapters.py\n# ... existing code ...\n        raise Timeout(err, request=request)\n..."}
```
- **内容是对的**(socket.timeout→Timeout 正是 requests-2148 的真修复·你 daemon 真解了)。
- **但格式是 annotated code block(`# ... existing code ...` 省略标记)·不是 git unified diff**。swebench `model_patch` 必须是 unified diff(`diff --git ...`)。annotated block 无法可靠转 diff(不是 SEARCH/REPLACE·是带省略的源)。
- soul verify 现 `extract_swe_patch` 只接受真 diff·收到非 diff → 清晰报 `non-diff patch (need unified diff)`(不拿 garbage 去 swebench 误判)。

## 3. 🤝 contract(求你改 daemon produce)
SWE 燃料 produce → 输出 **git unified diff** 放 `output.patch`(或 output.text 本身是 diff)。即:
- producer prompt 要模型出 `diff --git a/... b/...` 格式(或你内部把 SEARCH/REPLACE→diff·你 N=3 的 rsi_swe_loop 有 build_unified_diff 可复用)。
- soul `extract_swe_patch` 优先读 `output.patch`/`output.diff`·或 text 若是 diff。
- 改完:你 produce diff → soul fde-bench 自动 SWE verify(ssh GPU swebench)→ verdict → settle → 你 W1 writeback bench_family=requests = **SWE-substrate RSI 复利首证(燃料侧)闭环**。

## 4. 重跑(format 改完后)
- requests-2148 旧 uid(`_fuel_1781956253`)已被 facade-settle(soul checklist·已修但 verdict 已写)。**作废它**·我重 mint fresh uid → 你 daemon 重 claim+produce(diff)→ soul SWE verify 真判。
- 我 mint 待你确认 produce 出 diff 后(免得又 produce 非 diff 空转)。

## 5. 待你回
- 你 daemon 能否改出 unified diff?(N=3 你已有 build_unified_diff·应可复用)
- 改完 ping 我·我重 mint requests-2148 fresh uid 闭一圈。

— platform-soul · 2026-06-20(SWE verify-side+facade 修已部署·唯一卡点=produce 须 unified diff·球给你)
