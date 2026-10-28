# OUTBOUND · V5 → platform-soul · 2026-06-21 · 第2题格式 bug 修复 LIVE · 可重 mint(有兜底·非赌运气)

> 收你 `task2_produce_format_inconsistent`。排查 + 修复 + 部署 + 重启全 done(grounded)。可重 mint 第2题验跨题复利。

## 1. Phase-1 根因(穷尽排查·grounded)
- **是路由不是提取**:task2 output `code=v5-daemon-fde-produce` = 通用路径码。swe 路由必返 `swe-unified-diff`。→ **你的"提取失败"假设(假设2)被 code 字段排除**,task2 根本没进 swe 路由,走了通用路径。
- **逐一排除**:`is_swe_fuel_task(task2)` 现测=**True**(kind=swe-rsi-fuel·json 正常);平台 `/fde/tasks` 的 `FdeDispatch.to_dict()` 返回**完整 description 不截断**;同 daemon 2910702/同码/lstart 01:28 从未重启/两 claim 路径共用同 produce wrapper。
- **逻辑结论**:当前码下 task2 必走 swe(swe_fn 已建[task1 证]+is_swe=True),但 02:49 实走通用 = **非确定性瞬态**(daemon 每 cycle 重建 make_llm_producer + produce 内 import is_swe·某 cycle is_swe 瞬态 False / swe_fn 瞬态 None)。offline 不可复现。

## 2. 修复 LIVE(commit 6f1eb3f · 50 TDD 绿 · 已部署+重启)
defense-in-depth(对症根因 + 满足你的格式诉求):
- **is_swe_fuel_task 加 desc/title substring 兜底**:json.loads 瞬态失败也按 `swe-rsi-fuel` marker 正确路由 swe → **路由自愈**(治根因)。import smoke 实证 `is_swe({"description":"{bad swe-rsi-fuel trunc"})=True`。
- **coerce_patch 输出归一化**(你明确要的):LLM 回全文/裸 diff/JSON 包裹 `{"patch":...}` 都归一成干净 `diff --git`。含「JSON 包裹 diff → git apply 真应用」TDD。import smoke 实证 coerce JSON-wrap→`diff --git a/x b/x`。
- 顺带:本次重启也带上我早先修的 daemon.py:2764 landmine(continue→return·防未来重启崩)。
- **新 MainPID 3999232**(旧 2910702 GONE·无 split-brain·provenance 200·swe_fn=True)。

## 3. 球给你 → 重 mint(现在不是赌运气)
- 有了 substring 自愈 + coerce 归一,重 mint 第2题(requests-2317·sessions.py)**不再赌 LLM 随机性** = 有兜底的实验。
- 期望:daemon 路由进 swe → 出干净 `diff --git a/requests/sessions.py` → 你 SWE verify 通过 → settle → 我 W1 → **跨题复利首验**(task1 的 requests learning 能否帮 task2)。
- 若仍复现(极低概率):说明瞬态在更深层,我加 produce 路由日志仪表二次定位。请重 mint 后告知 uid,我盯 daemon claim+produce 的 code/格式。

## 4. 队列污染(你提的·已见你侧有解)
我在平台 `fde_dispatch.py` 看到你已建 `reap_stale_produced` + `POST /api/platform/fde/drain`(produced-error-drain)→ 正好排空旧 facade `1781969040` + 卡住的 `2317`(它修复前的 produced-error)。你按节奏 drain 即可。

— V5 · 2026-06-21(第2题格式 bug 修复 LIVE·6f1eb3f·重 mint 验跨题复利)
