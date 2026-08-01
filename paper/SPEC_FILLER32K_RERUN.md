# Spec · filler32k rerun on DeepSeek(P0 真活)

> 2026-05-19 · v10 plan 真 P0 · paper3 真 unblock · $50-100 · 24h walltime
> disambiguate compass-mechanism vs context×LLM-artifact

## §0 真问题

E1 真 nofiller 100ep · Cas 12.8% vs paper avg 3% · **+9.8pp absolute**(`reference_meme_bench_compass_results_2026-05-17.md`)

**真 unfair**:
- paper(MEME Jung et al. arXiv 2605.12477)真 baseline 用 **filler-32k**(32k context)
- 我们 E1 真用 **nofiller**(short context · easy mode)
- → 真 lift 是 compass mechanism · 还是 long-context degradation 真 less severe in our setup?**真不知**

**真 disambiguation**:
- 跑 E2: filler-32k 100ep · 同 DeepSeek-v3.2 judge · 真对比
- 真 outcome 1: Cas filler32k 真 > 3%(paper avg)→ **compass mechanism effect**(真大新闻)
- 真 outcome 2: Cas filler32k drop to floor(< 3%)→ **context×LLM artifact**(真诚 limitation · paper 仍 valuable as honest negative)
- 任一 outcome 都有 paper value

## §1 真 budget

| 项 | 真 cost |
|---|---|
| DeepSeek-v3.2 API token(100ep × ~32k input × ~500 output)| $50-100 · 真 amortized 估 |
| GPU walltime(运行 compass code + bench harness)| T4 ~24h(从 reference_meme_bench_compass_adapter_phase1.md `code/agents/compass_memory.py` 已 ready)|
| 真 wallclock | 24-48h(parallel 8 worker 真可降 walltime)|

## §2 真启动 sequence(用户启 · 我 ship script)

**用户启**(需 user 决):
1. `DEEPSEEK_API_KEY` 真注入 cloud `.env`(已有?见 `reference_credentials_inventory.md` 真核)
2. T4 GPU 真启动(`infra_t4_gpu_server.md` · `43.173.164.32` · PEM `C:\Users\chunx\Downloads\11111.pem`)
3. 真 `cd ~/Projects/nautilus-compass && python3 code/agents/run_meme_bench.py --filler 32k --episodes 100 --judge deepseek-v3.2 --output results/E2_filler32k_$(date +%Y%m%d).json`

**我 ship**(本 session 之后 · ~30min):
- `run_meme_bench.py` 真 launcher script · 真 ~120 LOC(基于 phase1 真现有 compass_memory.py)
- args:`--filler` `--episodes` `--judge` `--output`
- 真集成 phase1 真 compass_recall + drift_filter
- 真 log:每 ep 真 Cas/Del/Abs/ER/Agg/Tr · 真存 jsonl

## §3 真 pre-registered analysis(防 over-claim)

按 `feedback_verify_metric_source_before_reporting.md` 真规则 — 真 pre-register 标准:

| outcome | Cas filler32k 真值 | 真 paper framing |
|---|---|---|
| **A** "mechanism effect" | Cas ≥ 3.5%(paper avg + 0.5pp margin)| compass `depends_on:` 真 long-context 真 work · 真大新闻 |
| **B** "artifact" | Cas < 1%(near-zero baseline)| 真诚 limitation · paper as honest negative · 真仍 valuable |
| **C** "ambiguous" | 1% ≤ Cas < 3.5% | 真需 multi-seed + filler-16k 真 intermediate 排查 |

**outcome C 真不发 paper 真 conclusion** — 真需 expansion experiments。

## §4 真 paper3 真 reframe(post-E2)

**真重要**(本 session 真发现):MEME paper Appendix K.2 verbatim 已描述 "explicit contingencies and active dependency propagation"(Opus 4.7 LLM-extracted)→ compass `depends_on:` 真是 **schema-declared · write-time-LLM-free** 版 · 不是发明。

paper3 真新 framing:
- ❌ "first system with depends_on: field"(misleading · K.2 真 prior art)
- ✅ "schema-declared variant of K.2's contingency propagation · zero ingest-time LLM cost"

→ 真不在 E2 outcome 之前真投 arXiv · 真等 E2 + reframe 完成。

## §5 真关联

- `[[plan_v10_active_strategic_anchor]]` · P0 #1 filler32k rerun 真在这
- `[[OUTLINE_PAPER3_MEME_EXTENSION]]` · §5.1 Seokwon 0 reply + §6.1 K.2 verbatim + §8.1 6 caveats 已加
- `[[SPEC_DECLARATION_FIELD]]` · 真 schema 真支撑 E3+E4(depends_on on/off ablation)
- `[[reference_meme_bench_compass_adapter_phase1.md]]` · phase1 E1 真账 + harness 真 ready
- `[[infra_t4_gpu_server]]` · T4 真 location + PEM 路径
- `[[reference_credentials_inventory]]` · DEEPSEEK_API_KEY 真位置

## §6 真不做

- ❌ filler-16k(intermediate · 真留 outcome C 才跑)
- ❌ cross-LLM 3 judge(E5 · 真 sequence in E2 之后)
- ❌ `depends_on:` field 真 prototype(E3 · 真 wait declaration_field code ship)
- ❌ ingest LLM(anchor 真违反)

---

— compass-dialog · 2026-05-19 · v10 P0 真 spec · 用户启 + 我后续 ship launcher
