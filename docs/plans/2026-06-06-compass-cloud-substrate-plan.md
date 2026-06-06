# compass 云 substrate 部署 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> **执行须 fresh session**(本设计 session 太长 · R3)· P0/P1 需用户先 provision spot T4 + CPU 服 sudo · P2 gated 平台签 token。

**Goal:** 把 compass 部署成 spot-T4-GPU + 持久-CPU-服 的云 substrate,实现多 agent 共享记忆 + 个人跨设备,抗 spot 抢占。

**Architecture:** 云权威 daemon(A→C)· 单写权威(零冲突)· spot T4 纯 GPU 算力 / 持久 CPU 服存状态 + 冷备 fallback。设计见 `2026-06-06-compass-cloud-substrate-design.md`。

**Tech Stack:** Python · daemon.py · bge-m3/bge-reranker-v2-m3 · postgres · systemd · ssh · spot GPU 实例。

---

## Phase 0 · un-gated 代码前置(可现在 TDD · 不需 T4)

### Task 1: 修 CJK-surrogate ingest 崩 bug(P1 必修前置 · 独立价值)

**背景:** 调研定位跨设备 ingest 静默失败根因 = CJK-name surrogate 崩(`session_20260605_dual_flywheel_wiring` Finding1)。云权威下所有 ingest 走一条路,这条路**不能崩在 CJK**。

**Files:**
- 先 systematic-debugging 定位:`Grep` `surrogate|encode|UnicodeEncodeError|gbk` in `daemon.py` / `bridge` / ingest 路径
- Modify: ingest 路径文件(定位后定)
- Test: `tests/test_ingest_cjk_surrogate.py`

**Step 1:** 写失败测试 — ingest 一条含 CJK + emoji + surrogate-pair 字符的 obs → 断言不抛 UnicodeError 且条目落库。
**Step 2:** 跑测试确认 FAIL(复现崩)。
**Step 3:** 最小修(UTF-8 显式 + surrogatepass/errors 处理 · 参 PR#37 `e2e74de` bridge UTF-8 修法)。
**Step 4:** 跑测试 PASS + 跑既有 ingest 测试无回归。
**Step 5:** Commit `fix(ingest): CJK surrogate 不崩(跨设备 ingest 前置)`。

### Task 2: 语料 seed/pull 脚本(CPU 服 ↔ T4)

**Files:** Create `ops/corpus_sync.py` · Test `tests/test_corpus_sync.py`
- `push_corpus(local_memory_dir, remote)` — 只镜像 memory `.md`(排除 transcript · 实测仅 ~5MB/项目 · 非 1.8GB)· rsync/scp 封装
- `pull_corpus(remote, local_cache)` — T4 启动时拉
- TDD:mock 文件树 → 断言只 .md 被选 + transcript 排除 + 幂等(再跑无重传)。
- Commit。

### Task 3: PoI 快照 pull(T4 读快照非 live postgres)

**Files:** 复用既有 `regen_poi_snapshot.sh` / poi_credit_snapshot.json 机制(daemon 本就读快照)· Create `ops/snapshot_pull.py` · Test。
- T4 daemon 启动 + 定期从 CPU 服拉 `poi_credit_snapshot.json`(cron regen on CPU 服)。
- TDD:mock 快照 → 断言 boost 读到。
- Commit。

### Task 4: 客户端 fallback(T4 优先 · 挂则 CPU 服)

**Files:** Modify 客户端 recall 入口(daemon client / recall hook)· Test `tests/test_client_fallback.py`
- `recall_with_fallback(query, primary=T4_endpoint, fallback=CPU_endpoint)` — primary 超时/拒连 → fallback。
- TDD:mock primary 抛 ConnectionError → 断言走 fallback + 返回结果。
- Commit。

---

## Phase 1 · CPU 服冷备 + ingest 写路径(需 CPU 服 sudo · 用户 ops)

### Task 5: CPU 服冷备 daemon systemd(冷备 · 抢占触发)
**runbook(非 TDD · ops):** CPU 服装 compass daemon(CPU 模式 · `ZMM_DEVICE=cpu`)· systemd unit `compass-daemon-fallback.service`(`WantedBy` 手动/触发 · 非 always · 守内存:实测箱子已 swap → 平时不启)· 健康端点。验:手动 `systemctl start` → 1 分钟内 recall 可服(载 bge-m3 ~1.7G · 那时 available 8.7G 够)。

### Task 6: ingest 统一写云(单写权威)
**Files:** Modify stop-hook ingest + agent ingest → 都打云 daemon ingest API(非本地写)· Test。
- TDD:mock ingest API → 断言写转发 + 本地不再独立写语料(消灭多写)。
- Commit。

---

## Phase 2 · spot T4 GPU daemon(需用户 provision T4 · ops)

### Task 7: T4 spot 实例起 GPU daemon
**runbook(ops):** spot T4 · 装 daemon + 拉语料(Task 2)+ 拉快照(Task 3)+ `COMPASS_PROD_RERANK=1`(reranker 默认开 · T4 GPU ~0.6-0.9s)· systemd + spot 抢占信号 handler(收 2min 警告 → drain ingest → 标记下线让客户端 fallback)· 自动重拉(spot fleet restart)。

### Task 8: 客户端指向 T4 + 抗抢占验证
**runbook:** 你本机 recall hook primary=T4 · fallback=CPU 服(Task 4)· 验:跨设备 recall 通 + reranker lift 生效 + **手动 kill T4 daemon → 1 分钟 fallback 到 CPU 服**(实测抗抢占)。

---

## Phase 3 · 多 agent(gated G-token · 平台签 token)

### Task 9: Phase B authz scope 层(见 2026-06-06-compass-mcp-3agent-dogfood-design.md §4 B2)
per-tool scope 强制 · 平台签 v5/v7/kairos token + 注册 endpoint · 每 agent recall+ingest 实测。

---

## Phase 4 · 本地只读缓存(C · 离线)

### Task 10: 本地只读副本(单向从云拉 · 离线 recall)
单向 pull replica · 写仍去云 · 零冲突 · 离线 recall 兜底。

---

## DONE 判定
- P0:CJK ingest 不崩 + sync/snapshot/fallback 脚本 TDD 绿(可现在做 · 不需 T4)
- P1:CPU 冷备可 1 分钟接管 + ingest 单写权威
- P2:T4 GPU daemon LIVE + reranker 默认开 + 抗抢占实测(kill→fallback)
- P3:多 agent 共享(gated)· P4:离线缓存

## 关联
设计 `2026-06-06-compass-cloud-substrate-design.md` · Phase B `2026-06-06-compass-mcp-3agent-dogfood-design.md`。
