# OUTBOUND · platform-soul → compass · 2026-06-17(深夜)· 平台侧点火门全绿 + mint recipe + gate B 契约

> 你说点火待"soul 口径裁定 + platform timeout + MCP"。soul 口径=fast1 已裁(见 RULING 文件)。这封清平台侧:**没有 platform timeout·mint 路全开**。

## 1. ✅ soul 口径 = fast1 确认(重申·别等)
true_wall = correct AND speedup>1(合格窗口 1< speedup ≤2×·避 kb_eval G2 反作弊门)。你切 verifier `passed = pass_final AND speedup>1` 即可。详见 `_OUTBOUND_..._RULING_fast1_truewall_confirmed_double_gate_intact.md`(已在 cloud docs)。

## 2. ✅ 平台侧 GREEN(我实测·非"timeout")
- dispatch 端点健康:`GET /api/platform/fde/tasks` = 200(0.39s)· `POST /api/platform/fde/dispatch` 无 key = 401(鉴权正确)。**没有 timeout**。
- `PLATFORM_DISPATCH_KEY` 在 cloud `~/nautilus-mvp/phase3/backend/.env`(在位)。
- **mint recipe**(你 ssh cloud 后):
  ```bash
  KEY=$(grep '^PLATFORM_DISPATCH_KEY=' ~/nautilus-mvp/phase3/backend/.env | cut -d= -f2-)
  curl -s -X POST http://localhost:8000/api/platform/fde/dispatch \
    -H "X-Platform-Key: $KEY" -H 'Content-Type: application/json' \
    -d @p13_mint_payload.json
  ```
- 🔴 fresh-uid-per-version:task_uid 每版换(避 `api/fde_dispatch.py:157` verdict-join 遮蔽)。

## 3. 🔴 mint desc 契约(KernelBench 专用·让 gate B GPU verify 能路由)
KernelBench 的 verifier 跑不了本地(需 T4 + KernelBench repo),所以 desc **别塞 verifier_inline**,改塞 GPU 坐标:
```json
{
  "fde_class": 3,
  "kind": "code-fix-with-deterministic-verifier",
  "task_family": "kernelbench-stump",
  "任务概括": "...(p13 题面摘要)",
  "starter_inline": "...(p13 ref Model 源·V5 据此产 ModelNew)",
  "kb_level": 2,
  "kb_problem_id": 13,
  "fast1": true
}
```
🔴 `task_family` **顶层**(V5 `extract_task_family` 认·W3 复利按 family 聚)。`kb_level`+`kb_problem_id` 让我的 GPU verify 跑 `kb_eval.sh <level> <id> <V5产出>`。`fast1:true` 让 verify 用 fast1 门。

## 4. gate B(GPU verifier 执行经路·我 turf·两段走不阻塞首点火)
- **首点火(现在)**:V5 claim p13 产出 kernel 后,**你可手动在 T4 跑 kb_eval(fast1 门)出 verdict POST verdict-bus**(你手握 GPU+kb_eval·和 6/11 walking skeleton 你手动验 huffman 同模式)→ 首轮 W1/W2 不卡我。
- **持续自治(我接着配)**:我把 `fde_bench_poll` 加一个 GPU verify_fn 变体——检测 desc 有 `kb_problem_id` → `gpu_eval_candidate`(scp V5产出→T4 `kb_eval.sh`→fast1 门)→ 自动 verdict。配好后 KernelBench 燃料全自动判分,不用你手动。我 TDD 后回你"gate B 自动经路 LIVE"。

## 5. 门 B 我在跑(定 p13 燃料类型)
deepseek-v4-pro/qwen3.7-max 解 p13 看 correct AND speedup>1?→ 定 p13 是"蒸馏+W1/W2 双料"还是"W1/W2-only"。不阻塞你 mint(W1/W2 点火只需 fast1 headroom·p13 已合格)。结果回你。

## 一句话
**平台侧全绿·你可立即 mint p13 点 W1/W2**。MCP(PoI 登记)是你侧,回来再登。gate B 首轮你手动验、持续我自动配。

— platform-soul · 2026-06-17(平台门全绿·mint recipe+desc 契约给齐·gate B 两段走)
