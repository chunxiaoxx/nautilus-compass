# 第二刀:producer 可复现产物 + soul canonical verify(闭合 reward loop)Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让一条 GenOpt 轨迹第一次走完「producer 产可复现解 → 独立 verify 复现分数 → PATCH external-verify → agent_survival.total_income > 0(SQL 可证)」全链,平台历史第一行外部 gate 的 income。

**Architecture:** 不新造服务。① 修 `gpt55_local_runner.py` 持久化完整解(每轮全码 + best 解独立文件 + sha256),TLS 旁路改为显式开关(默认 verify=True,cloud 生产不走 insecure);② 新 `soul_canonical_verify.py`:从轨迹取完整 best 解 → sha256 对账 → 独立重跑 `verification/evaluate.py` 复现 combined_score → 容差内一致才 PATCH `/external-verify`,不可复现/不匹配一律拒绝(防橡皮图章);③ cloud 端到端:GPT5.5 走 cloud(Linux OCSP 软失败,qixuw 7/5 实测 200),产新轨迹 → persist 新 verdict → canonical verify → 3 判据收口。

**Tech Stack:** Python 3 stdlib + requests(runner)· pytest(verify 脚本 TDD)· cloud 43.160.239.61(backend localhost:8000 · pid 见 memory)。

**Grounded 前提(2026-07-06 实测):**
- 旧轨迹(H800 harness 产)`best_round_source` len=160(docstring 预览),rounds 无完整码 → **旧 verdict 永久不可外部验证,保持 unverified(诚实)**,走新轨迹新 verdict。
- `gapclosed_runner.py:246` 已存每轮完整 `candidate_code` — verify 脚本必须兼容该格式。
- JobShop verifier `verification/evaluate.py` 接口:`--benchmark-dir <task_root> --candidate <solver.py> [--baseline]`,cwd 写 metrics.json,per-instance timeout 60s,自述 deterministic(verifier_qc 三铁律已 PASS)。
- candidate 解本身可能含 wall-clock 预算(anytime 算法)→ verify 须先做 determinism 自检(同解连跑 2 次),再按容差判定。

**4 防剧场硬约束(继承第一刀):** 幂等 / 只 False→True 入账 / 只整数 producer_agent_id / verifier_source ≠ verdict.source。第二刀新增第 5 条:**轨迹无完整解 = 直接拒绝 verify,绝不 fallback 到 preview**。

---

### Task 1: `gpt55_local_runner.py` 持久化完整解 + TLS 显式开关

**Files:**
- Modify: `genopt_factory/tools/gpt55_local_runner.py`

**Step 1: 改动点(4 处)**

1. `chat()` 增加 `tls_verify` 参数,`requests.post(..., verify=tls_verify)`;`main()` 加 `--insecure` flag(默认 False)。默认 verify=True(cloud/生产);本机 driver 备援才 `--insecure`。docstring 同步更新。
2. round 记录:`"source_preview": code[:300]` 改为同时存全码:
   ```python
   "source": code,                # 完整解 · 可复现性的根
   "source_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
   "source_preview": code[:300],  # 兼容旧读取方
   ```
3. 追踪 best 解:循环里 `if score > best_score:` 时记 `best_code, best_round = code, r`;循环后把 best 解写独立文件 `<out>.best_solution.py`,轨迹顶层加:
   ```python
   "best_round": best_round,
   "best_round_source": best_code,          # 完整,不截断
   "best_solution_file": os.path.basename(best_sol_path),
   "best_solution_sha256": sha256(best_code),
   ```
   best 解不存在(全轮 invalid)时三字段为 None。
4. `cert_workaround` 字段改为按 `--insecure` 实际值记录,不再硬编码。

**Step 2: 语法自检**

Run: `python -c "import ast; ast.parse(open('genopt_factory/tools/gpt55_local_runner.py',encoding='utf-8').read())"`
Expected: 无输出(过)。

### Task 2: `soul_canonical_verify.py`(TDD)

**Files:**
- Create: `genopt_factory/tools/soul_canonical_verify.py`
- Test: `genopt_factory/tools/test_soul_canonical_verify.py`(pytest · 用假 evaluate.py fixture,不碰网络)

**行为契约:**
- `load_best_solution(traj) -> (code, claimed_score) | raise NotReproducible`:
  - 优先级:顶层 `best_round_source` 长度 > 500 → 用它;否则扫 rounds 里 score==best_score 的轮取 `source` / `candidate_code`(gapclosed_runner 格式);都没有 → `NotReproducible`(**160 字符 preview 一律拒**:len < 500 视为截断)。
  - 轨迹带 `best_solution_sha256` 时必须对账,mismatch → `NotReproducible`。
- `reproduce_score(task_dir, code) -> float`:写临时 solver 文件,子进程跑 `evaluate.py --benchmark-dir --candidate --baseline baseline/init.py`(cwd=tempdir,timeout 1200s),读 metrics.json 的 `combined_score`;valid != 1 → raise。
- determinism 自检:`reproduce_score` 跑 2 次,`|s1-s2| > 1e-9` → 输出 NONDETERMINISTIC 并拒绝(不 PATCH)。
- 判定:`|reproduced - claimed| <= --tolerance`(默认 0.01)→ MATCH;否则 MISMATCH 拒绝。
- MATCH 且非 `--dry-run` → `PATCH {platform_url}/api/platform/fde/verdict/{verdict_id}/external-verify`,body `{"verifier_source": "soul-canonical-verify", "reproduced_score": ..., "tolerance": ...}`;打印返回的 `income_recorded / amount`。
- 退出码:0=MATCH(+PATCH ok),2=NotReproducible,3=MISMATCH/NONDETERMINISTIC,4=PATCH http 失败。

**Step 1: 写失败测试(RED)**

测试用 tmp_path 造假 task_dir(假 `verification/evaluate.py` 固定输出 metrics.json)+ 假轨迹 JSON,覆盖 5 用例:
1. `test_preview_only_trajectory_rejected` — best_round_source len=160 → NotReproducible(exit 2 语义)
2. `test_full_source_reproduced_match` — 轨迹全码 + 假 verifier 回同分 → MATCH,dry-run 不 PATCH
3. `test_score_mismatch_rejected` — 假 verifier 回差 5 分 → MISMATCH
4. `test_sha256_mismatch_rejected` — 轨迹 sha256 与码不符 → NotReproducible
5. `test_gapclosed_format_candidate_code_supported` — rounds[].candidate_code 格式可取到 best 解

Run: `python -m pytest genopt_factory/tools/test_soul_canonical_verify.py -x -q`
Expected: 全 FAIL(模块不存在)。

**Step 2: 实现(GREEN)**

单文件 ~180 行,stdlib only(urllib PATCH,不引 requests——cloud 上零依赖)。

Run 同上 → 全 PASS。

### Task 3: Commit(本地改动收口)

```bash
git add genopt_factory/tools/gpt55_local_runner.py genopt_factory/tools/soul_canonical_verify.py genopt_factory/tools/test_soul_canonical_verify.py docs/plans/2026-07-06-second-cut-reproducible-producer-verify.md
git commit -m "feat(genopt): producer 持久化完整解 + soul canonical verify(第二刀 reward loop)"
```

### Task 4: cloud 端到端(live 闭环)

1. 打包 scp 到 cloud `/home/ubuntu/genopt_live/`:JobShop task bundle(Task.md / baseline / verification / data / frontier_eval/delivery_metadata.txt / metrics.json)+ 3 个脚本(runner / verify / persist_trajectory_verdict.py)。
2. cloud 上 export qixuw 凭据(取自本机 `~/.claude/.cache/.fde_api_secrets.env`,只进 shell env,不落文件)→ `--smoke` 先验连通(**不加 --insecure**,Linux 走正常 TLS)。
3. 跑新轨迹:`python gpt55_local_runner.py --task-dir <task> --rounds 3 --model gpt-5.5 --out gpt55_trajectory_cloud_20260706.json`。
4. persist 新 verdict:`persist_trajectory_verdict.py --producer-agent-id 9000009 --platform-url http://localhost:8000`(source 记 cloud 跑点)。
5. canonical verify:`python soul_canonical_verify.py --task-dir <task> --trajectory <traj> --verdict-id <new> --platform-url http://localhost:8000` → MATCH → PATCH。
6. **binding-DONE 判据(3 条全过才算)**:
   - `GET /api/platform/fde/verdict/genopt_or_jobshop_orlib_v1_001_20260702` → 新 verdict `external_verified=true`
   - `psql ... "SELECT total_income FROM agent_survival WHERE agent_id=9000009"` → > 0
   - 重跑 PATCH → `income_recorded=false, idempotent=true`,income 不再涨

### Task 5: SSOT + memory 收口

- `LOOP_STATE_SSOT.md` 四行更新(闭环判据第 1 条状态)+ commit。
- memory:session 文件记录闭环证据(3 判据输出原文)。
