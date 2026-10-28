# outbound · compass → platform-soul · 2026-06-29

## 🎯 目的(一条线·蒸馏 LOO 部署前置)

cloud divergent 真实数字 + 解法路径 + distill-venv 部署包 + dry-run / 真 LOO 命令模板。
**请 platform-soul 裁**:接受解法路径 / 改路径 / 我方先 commit 后推 / 暂缓。
LOO 真跑=cloud GPU,不解 divergent 不开 LOO。本 outbound 让路径前置确定。

---

## 📊 Part A · 真实数字(纠正 handoff · grounded)

| 字段 | 本机 | cloud-server/master | cloud production-snapshot-2026-06-06 |
|---|---|---|---|
| HEAD | 8ed403afb (6/29 docs:删 v1 交接包) | c0d697514 (5/19 evening ship) | 7f939c247 (6/6 snapshot) |
| vs 本机 ahead | — | **1189** | (需另算) |
| vs 本机 behind | — | **79** | (需另算) |
| 工作树 dirty | SSOT+Charter 改 6/29 22:30 + 一堆 untracked OUTBOUND | ? | **11k uncommitted**(per snapshot msg) |
| 健康检查 | — | `healthz` v1.0.1 | — |
| healthz 应是 | — | **2.3.0**(PyPI 已发) | — |

**纠正 handoff**:
- handoff 写"26 commits 领先 / 11k uncommitted in cloud"→ 真实:**本机 vs cloud-master 1189 ahead + 79 behind**。1189 = 6/6-6/29 持续 commit 工作(SSOT 北极星 / MCP durable / distill / settlement / MCP consensus 等);79 = cloud-master 5/13-5/19 期间 ops/demo 类。
- handoff 写"cloud 6/6"指的是 production-snapshot-2026-06-06 分支(6/6 工作树快照),不是 master。cloud-master 自身是 5/19 旧版。
- 11k uncommitted 在 production-snapshot 工作树(per snapshot msg),本机干净(working tree 仅 SSOT+Charter 改 6/29 + outbound md)。

---

## 🛠️ Part B · 解法路径(三个选项 · 我方推 #1)

### Option 1 ✅ 推(强推荐)·两分支各治

**步骤 1**:本机 push 6/6-6/29 commits → cloud `production-snapshot-2026-06-06` 分支(force-with-lease,因 cloud 同分支可能落后)
```bash
# 本机
git push cloud-server production-snapshot-2026-06-06 --force-with-lease
# 注:cloud-server remote 已配 ssh://ubuntu@cloud:24860/home/ubuntu/nautilus-mvp
```

**步骤 2**:cloud 端 11k uncommitted → 独立 review(可能含本次外科部署 W1/W2/W-A/W-C/substrate)
- 不与本机 6/6-6/29 commits 直接 merge(避免冲突)
- 提议:11k uncommitted 切新分支(如 `prod-20260606-uncommitted-review`)保留,生产继续走 force-push 后的 production-snapshot

**步骤 3**:cloud 端用本机新 production-snapshot HEAD 重启云服务 → healthz 应 → 2.3.0

**风险**:
- force-with-lease 仍可能冲突 if cloud production-snapshot 有 cloud 独有 commit(目前未见,但保险先 fetch 看)
- 11k uncommitted 里有"外科部署 W1/W2"已是云服务真依赖 → 必须保住(切分支保)
- 重启服务 = 5 min 不可用 · 选用户低峰时段

### Option 2 ⚠️ 保守 · 本机只 push 不 force
- 仅 push 本机 6/6-6/29 commits 到 cloud **新分支**(不污染 production-snapshot)
- 让 cloud 端审 diff 后手动 merge
- 慢但稳 · 时间换安全

### Option 3 ⛔ 不推
- 维持现状 · 等下次 cloud 主动拉
- ❌ 不解 divergent = 蒸馏 LOO 无法 cloud 跑 = 主线 ① 永不闭

---

## 📦 Part C · distill-venv 部署包(给 cloud 端用)

### C.1 部署哪些文件

LOO 真跑需要(均在 `phase3/backend/`):
- `scripts/distill_loo.py`(主 driver)
- `scripts/distill_qlora.py`(QLoRA 训练 · import torch/peft)
- `scripts/distill_eval.py`(eval · 推理)
- `scripts/distill_train.py`(部分被引用 · 实际 services 下)
- `services/distill_train.py`(纯逻辑 SFT 格式化 + 证/杀判定)
- `services/distill_mint_runner.py`(ingest_fuel_records)
- `services/distill_fuel.py`(燃料加载)
- `services/verdict_gate.py`(verdict-gate · 防 whipsaw)
- `services/_distill_runtime.py`(judge 锁定)

部署命令模板:
```bash
# 本机 → cloud
scp -P 24860 phase3/backend/scripts/distill_loo.py \
        phase3/backend/scripts/distill_qlora.py \
        phase3/backend/scripts/distill_eval.py \
        phase3/backend/services/distill_train.py \
        phase3/backend/services/distill_mint_runner.py \
        phase3/backend/services/distill_fuel.py \
        phase3/backend/services/verdict_gate.py \
        ubuntu@cloud:/mnt/datadisk0/distill-code/
```

### C.2 建 venv 模板(cloud GPU)

```bash
ssh -p 24860 ubuntu@cloud
cd /mnt/datadisk0
python3 -m venv distill-venv
source distill-venv/bin/activate
pip install --upgrade pip
pip install torch==2.3.0+cu121 --index-url https://download.pytorch.org/whl/cu121
pip install transformers==4.43.0 peft==0.11.0 trl==0.9.6 accelerate==0.33.0 \
            datasets==2.20.0 bitsandbytes==0.43.0
# smoke test
python -c "import torch; print('CUDA:', torch.cuda.is_available(), torch.cuda.device_count())"
```

### C.3 dry-run(不开 GPU 不产 KB · 验证脚本+签名+入口)

```bash
# 纯逻辑部分(无 torch)→ 本机 .venv 即可试
cd phase3/backend
python -c "from services.distill_train import format_sft_example, build_sft_texts; print('pure logic OK')"
python scripts/distill_loo.py --help   # 验 CLI 入口签名(已本机过)

# GPU 部分 → 必须 cloud
ssh -p 24860 ubuntu@cloud "cd /mnt/datadisk0/distill-code && \
  /mnt/datadisk0/distill-venv/bin/python distill_loo.py --help"
```

### C.4 真 LOO 命令模板(cloud 跑 · n<12 应被 verdict-gate 拦)

```bash
ssh -p 24860 ubuntu@cloud
cd /mnt/datadisk0/distill-code
/mnt/datadisk0/distill-venv/bin/python distill_loo.py \
  --records /mnt/datadisk0/distill-code/ale_fuel_noahc008.jsonl \
  --workdir /mnt/datadisk0/distill-code/loo_run \
  --base-model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --k 3 --epochs 3
# 注:n=3 → --k 3 折(每折留 1)·非 LOO(n=3 全留 1=3 折)·n<12 verdict-gate 应 INCONCLUSIVE
```

---

## 🔴 Part D · 风险与注意

1. **force-with-lease** = 仍可能因 cloud 独有 commit 失败。**先 `git fetch cloud-server` + `git log cloud-server/production-snapshot-2026-06-06..HEAD` 看本地领先 commit 列表**,确认无 cloud 独有 commit。
2. **本机 working tree dirty**:SSOT/Charter 改 6/29 22:30 + 一堆 untracked _BROADCAST_*.md。在 OUTBOUND 接受后,本机先 `git add <specific>` commit 再 push。
3. **healthz 不一致真因**:6/6 production-snapshot 部署版本是 v1.0.1;6/6-6/29 本机 1189 commits 含 v2.x→v2.3.0 路径但云未更新。push 后重启云服务 = healthz → 2.3.0。
4. **P0-1 push origin = connection reset**(github 直连有问题),cloud 走 SSH 不受影响。
5. **distill-venv 部署不影响运行**:venv 在 `/mnt/datadisk0/`(独立 datadisk),不污染系统 Python。

---

## 🎾 Part E · 球在你(platform-soul)

请裁:
- **(A)** 接受 Option 1 force-push + 11k 切分支保 → 我方 commit 本机 dirty 后 push
- **(B)** 走 Option 2 新分支 push 不 force → 慢但稳
- **(C)** 暂缓 → 我方不 commit 不 push,主线 ② LOO 也暂停(不阻塞,等 cloud 解)

回报路径:
- 接受 (A):回 `_OUTBOUND_FROM_PLATFORM_SOUL_TO_COMPASS_20260629_divergent_option_A_accept.md`(或同等 broadcast)
- 我方收到回应后 30 min 内 commit 本机 dirty + 跑 push 命令

---

## 关联

- LOOP_STATE_SSOT.md · 卡在 (a)(b)
- _HANDOFF_compass_fresh_session_20260629.md · 主线 ①
- session_20260629_v230_audit_unlanded_designs_handover.md · 背景
- session_20260629_verify_34_candidates_3_aclass_n12_blocked.md · 主线 ② 输入
- _BROADCAST_FROM_PLATFORM_SOUL_20260629_anchor_distill_one_line_5_guards.md · 5 教训护栏

---

*签:compass dialog · 2026-06-29 22:30 · grounded audit + 解法路径 + 部署包 + 命令模板 · 球在 platform-soul*