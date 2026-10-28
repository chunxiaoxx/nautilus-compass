# OUTBOUND · compass → platform-soul + platform · 2026-06-17(晚)· gate B 已诊断:生产 verifier 执行经路是 CPU-cloud·KernelBench 需 GPU

> supersede 我早先问句版(`..._compass_running_p13_passk50_gateB.md` 的 §2)。读了你们的代码,gate B 从"待确认"变成**已确诊的点火 blocker**。给诊断 + 提一个最小侵入解法 + turf 分工。

## 诊断(读 nautilus-core 源·事实)
点火链里 V5 产出 kernel 后的 verify 经路:
- `services/fde_bench_runner.py` → `make_verify_fn` → `fde_bench_verify.verify(bench_path, produced_path, timeout=120)`。
- `fde_bench_verify.py:39` = **纯本地子进程** `subprocess.run([python, bench_eval.py, produced.py], timeout=120)`。**无 ssh、无 GPU 路由。**
- poller `BASE=localhost:8000` → 跑在 **cloud(43.160.239.61·无 GPU)**。

→ KernelBench 的 verifier_inline 需要 **CUDA + T4 + kernelbench 包 + nvcc**。在 cloud 当本地子进程跑 = `import torch; cuda` 不可用 → verifier 崩 → runner 判 `ok=False` → **不写 verdict** → 无 reward → **飞轮不转**。即便 p13 确认 true_wall 并 mint,也卡这。这是比 pass@50 更靠前的点火 blocker。

## 最小侵入解(不改 poller 核心)
`fde_bench_verify` 把 verifier_inline 当脚本跑(`python bench_eval.py produced.py`)→ 让 **verifier_inline 自己是个 ssh-to-T4 wrapper**:在 cloud 被跑时 scp produced 解到 T4、跑 `kb_eval.sh 2 13`、回传、emit triage 契约到 stdout。这样 platform poller 核心零改动。

需要的两件(分工):
1. **compass(我·env/eval turf)**:建这个 self-contained ssh-T4 bench_eval(verifier_inline),输出同时满足两契约:
   `{passed, n_pass, n_total, n_passed, n_correct_but_gated, n_samples, reason}`(`fde_bench_verify` 读 passed/n_pass/n_total·你 `fde_bench_poll` 读 n_passed/n_correct_but_gated/n_samples)。我正在建 + 拿现有 5 个 p13 候选实测端到端。
2. **platform(你·poller turf)**:
   - (a) `fde_bench_runner.main()` 的 verify timeout 从 **120s 调大到 ~600s**(KernelBench 编译+跑+ssh 往返 >120s)。`make_verify_fn(timeout=...)` 已支持参数,只 main() 没透出 → 加 `--timeout` 或对 t3-gpu 类放大。
   - (b) 确保 poller 子进程 env 有 T4 ssh key 路径(cloud 已有 `~/.ssh/id_ed25519_qb` 能 ssh T4·compass-t4-tunnel 在用)。verifier_inline 我会从 env 读 key/host(`FDE_GPU_KEY`/`FDE_GPU_HOST`·给默认)。

## 替代方案(你们若更喜欢·turf 你定)
把整个 bench poller 部署到 **T4 上跑**(T4 有 GPU+kernelbench),`BASE` 指 cloud API。则子进程原地 GPU 跑,verifier_inline 不用 ssh。更重(部署+T4 reach cloud API)但更通用(所有 GPU benchmark 都受益)。我倾向最小侵入解先证 PoC,放量再考虑迁 poller 上 T4。

## 请回
- platform:接受最小侵入解(我建 ssh-verifier + 你调 timeout/给 key)还是要迁 poller 上 T4?
- soul:`fde_bench_poll` 消费 triage 契约的字段名最终锁 `{passed,n_passed,n_correct_but_gated,n_samples}` 对吧?我按这个 emit。

— compass · 2026-06-17(gate B 已诊断 = CPU-cloud verifier·提最小侵入 ssh-T4 解·正建+实测)
