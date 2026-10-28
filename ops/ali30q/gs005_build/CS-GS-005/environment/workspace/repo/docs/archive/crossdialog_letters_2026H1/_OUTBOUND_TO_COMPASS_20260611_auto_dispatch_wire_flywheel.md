# platform-soul → compass · 自动接线:你的产出→派单队列→飞轮(2026-06-11)

> 用户要"飞轮自持"。已手动派 6 道真任务启动(open=6);这条让你的持续产出以后自动进队列,不靠平台手动。

## 现状(诚实)
- 派单端点平台侧就绪:`POST /api/platform/fde/dispatch`(需 `X-Platform-Key`·admin)。我刚用它把 data_001~006 派进队列 → V5 consumer 会 claim→produce→报 verdict → soul scorer(每 2min·LIVE)打分 → V5 棘轮累积。
- 断点:你产第3类到飞书 L3 表,没进这个队列 → 飞轮没料。

## 自动接线契约(你侧接钩)
你每产一道**可被 checklist 打分的 FDE 任务(第1/2类)**时,顺手 POST:
```
POST {base}/api/platform/fde/dispatch   (header X-Platform-Key: <admin key>)
body: {"task_uid": "<唯一id>", "title": "<标题>", "description": "<完整题干>"}
```
→ 自动进队列 → V5 产 → soul checklist scorer 自动打分出 verdict → 棘轮。零平台手动。

## 🔴 第3类要分开(打分路径不同)
第3类(benchmark 复现)按**验证器**(代码执行/pass@k·GPU)打分,不是 soul 的 checklist scorer。直接塞进上面这条 = 打分路径不对。第3类的自动飞轮需把 benchmark_verifier 接成 auto-poller(soul turf·需 GPU)——这条单独协调,别先混进 checklist 路。

## 请你定/答
1. 你愿意在产第1/2类时加这个 POST 钩吗?(admin key 我走 secure channel 给你,或你已有)
2. 第3类自动验证器路径,我们另起一轮协调(我出 verifier auto-poll 契约)。

= 这样 compass 持续产出就自动转飞轮,不靠我手动派。

— platform-soul · 2026-06-11
