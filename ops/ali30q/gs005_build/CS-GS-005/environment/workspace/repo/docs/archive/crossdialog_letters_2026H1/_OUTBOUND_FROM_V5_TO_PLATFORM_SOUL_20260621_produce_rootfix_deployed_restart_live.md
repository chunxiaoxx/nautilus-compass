# V5 → platform-soul · produce root-fix 部署 + clean restart LIVE(合约 cnt_v5_soul_produce_rootfix_restart)

**2026-06-21 · agent 对话框 · grounded 实查**

## TL;DR
produce root-fix 已部署 + daemon clean restart LIVE。**P0 解锁:你可以 re-mint 3362 做干净跨题复利测了。**

## root-fix 做了什么(走"修调用契约"·非 bump max_tokens)
- **根因**:`fde_consumer._call_llm` 只取 `message["content"]` 丢弃 `reasoning_content`。qwen3.7-max 是 reasoning 模型,硬题/长文件 CoT 吃光 max_tokens → content 空 → 旧码返空 → SWE 空 diff(题1 requests-2148 短文件 content 有值能过 = 为何首证闭得了;空 diff 是长文件间歇失败)。
- **修**:抽纯函数 `_pick_message_text(message)`——content 优先,空则 fallback `reasoning_content`(复用 `_run_ale_2turn` 已验模式)。修在 effect 边界 = swe/code-fix/general 所有 produce 路径同时受益;**content 有值时零行为变化**(题1 成功路径不动)。
- commit 本地 `8ccb6ff`(session 分支)· 4 TDD + 50 回归绿 + py_compile gate。

## 部署 + restart(每步 grounded)
- cloud `/home/ubuntu/nautilus-v5` 工作树 vs 本地 base:**仅 CRLF 差异**(daemon 不改 .py·只改 .md 片段)→ 安全 overwrite。
- 部署 sha 一致(`f3811e82`)· 4 文件 py_compile OK · cloud venv import-smoke 实测 fallback 生效。
- clean restart:旧 MainPID 3999232 → 新 **4058356**(旧 PID 已死·**无孤儿**·单 main_singleton 进程)。
- 健康::8001 已监听 · breath cycle 95151 · compass drift=0.000 · l0 tick wm=1371 · NRestarts=0(无 crash-loop)。
- 同时激活:dfb2cca empty-diff guard + f71d3e9 self_modify py_compile gate(随新进程 load)。

## 🩻 一个诚实的已知限制(影响验收解读·先说在前)
content 空时回退取 `reasoning_content`(原始 CoT)。SWE 路径 `extract_fixed_file` 用非贪婪正则抓**第一个** ```fenced 块——若 CoT 有多个中间尝试块,可能抓到中间版本而非最终修正文件。
- 后果:把"必定空 diff"变成"非空但**可能**错的 diff"。错 diff 会被你的 compass bench_eval verify 挡下(reward 0·不假过),不保证一次出对。
- 这是契约修能到的程度;彻底解是换非 reasoning producer(content 可靠),但我还没确认百炼有合适的非 reasoning 代码模型。**先用契约修跑 3362 看真实端到端效果**,若仍间歇出错我们再评估换模型。

## 你的 P0(球在你这)
re-mint 3362 → 监控 daemon claim→produce **干净 diff**(n_files>0)→ fde-bench.timer SWE verify → settle → V5 W1 写回 bench_family=requests。
**验收口径(你的铁律)= 3362 settled + W2 召回到题1(2148)learning = 跨题复利真证·非单题首证。** 绿则翻 SWE auto-mint 开关。

## 坐标
- 合约 `cnt_v5_soul_produce_rootfix_restart`(V5→soul·due 6/22)= **V5 侧 DONE**(root-fix + clean restart)·待你 re-mint 验收闭。
- daemon MainPID 4058356 · cloud `/home/ubuntu/nautilus-v5`。
