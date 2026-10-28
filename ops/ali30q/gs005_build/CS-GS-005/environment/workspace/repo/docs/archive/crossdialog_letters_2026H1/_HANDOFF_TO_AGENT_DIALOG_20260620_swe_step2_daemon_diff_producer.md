# 给 agent(V5)对话框的协调指令 — SWE 闭环 step② daemon diff producer(2026-06-20)

> 用户:在 agent(V5)对话框开 fresh session·把下面整段粘进去当 /goal。platform-soul 侧(step①)已全部就绪·只差 V5 daemon 接线这一步闭环。

---

你是 V5(nautilus-v5·RSI producer + W1/W2)。读 repo 根 `_OUTBOUND_FROM_PLATFORM_SOUL_TO_V5_20260620_*`(契约B / step1_done / contract_B)+ memory `session_20260619_pathB_rsi_harness_built_pilot_install_hell_docker_pivot`。

## 背景(platform-soul 已完成·别重做)
- SWE-substrate RSI 闭环·契约 B 拍板:soul mint 内嵌 `original_files`+`edit_paths` → 你 daemon 零网络零 dataset 出 diff。
- soul 侧全就绪:① mint 内嵌原文(commit 7b6ec95da·done)② SWE verify-side LIVE(fde-bench ssh GPU box swebench)③ prep JSON 备好 `/home/ubuntu/fde-double-gate/prep_requests2148.json`(requests-2148·**gold 改 requests/models.py**·n_f2p=10)。
- 🔴 关键:你 daemon 之前 produce 改的是 adapters.py = **改错文件**·gold 是 models.py。契约 B 内嵌 edit_paths 会告诉你改对文件。
- 你已建:`fde_capsule/swe_fuel_produce.py`(commit b2c7122+08d2034·make_unified_diff git-apply 验+make_swe_diff_producer+is_swe_fuel_task·16 TDD)。

## 唯一 P0(单一 forcing function·TDD·binding-DONE)
**把 SWE diff producer 接进 daemon produce 路由 + 部署**:
1. daemon produce 路由:`is_swe_fuel_task(task)`(desc kind=swe-rsi-fuel / 有 swe_instance_id)→ 走 `make_swe_diff_producer`·非 SWE → 原通用 code_fix produce。
2. `fetch_original` 实现 = 从 task desc spec 读 `original_files[path]`(零网络·spec 已内嵌)。producer prompt:给 problem_statement + edit_paths(改这些文件)+ 各文件 original 全文 → 要模型出**修正后文件全文**(非省略非 diff)→ make_unified_diff(path, original, fixed)→ output.patch(unified diff)。
3. 部署 + 重启 daemon(用户 go)。
- done 判据:daemon 收到 swe-rsi-fuel 任务 → produce 出 output.patch(git unified diff·对 models.py)。

## 闭环次序(接好后)
你 daemon 接好 + 部署 → 写 outbound 给 platform-soul(`_OUTBOUND_FROM_V5_TO_PLATFORM_SOUL_*_daemon_diff_wired`)→ soul 重 mint requests-2148 fresh uid(--prep-file prep_requests2148.json·内嵌 models.py)→ 你 daemon 自动 claim+produce diff → soul SWE verify(ssh GPU box swebench)→ verdict → settle → 你 W1 writeback bench_family=requests = **SWE-substrate RSI 复利首证(燃料侧)闭环**。

## 铁律
- daemon 改 + 部署重启 = 生产改动·TDD 先行·实测 produce 出真 diff 再部署。
- 别重 mint 前先确认 daemon 能 produce diff(免空转·soul 会等你 ping)。
- 收敛:单一 forcing function·binding-DONE。

---

**协调闭环**:V5 接好 daemon → outbound 通知 soul → soul 重 mint → 自动跑完闭环。两框都已就绪·只差这一步 daemon 接线。
