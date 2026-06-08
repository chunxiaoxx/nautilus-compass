# Runbook: compass daemon + reranker 上 T4 GPU(2026-06-07 实测)

> Phase 2 Task 7 of `docs/plans/2026-06-06-compass-cloud-substrate-plan.md`.
> 本 runbook 记录把 compass daemon(bge-m3 + bge-reranker-v2-m3)跑在 Tesla T4 GPU 上的
> 实测步骤 + 实测数字 + 一个坑。所有步骤已在 43.163.80.46(`ssh t4`)真跑过。

## T4 环境(实测)
- Tesla T4 15GB · driver 580.126.20 · Ubuntu 22.04.5 · 8C/30G · Python 3.10.12 · 无 nvcc(reranker/embedder 走 pip torch 自带 runtime,无需 CUDA toolkit)。

## 1. 装 GPU 依赖 + 预下模型
```bash
pip install --user sentence-transformers          # 拉 torch 2.12+cu130(~2.5G)+ transformers
python3 ops/_t4_fetch_models.py                    # 验 torch.cuda + 预下 bge-m3(~2.2G)+ bge-reranker-v2-m3(~2.2G)
```
实测:torch 2.12.0+cu130 · cuda_available True · Tesla T4 · bge-m3 dim 1024 加载 137s(含下载)· reranker 加载 253s · HF 缓存共 6.4G。HF 在 T4 直连可达(0.0s),无需 hf-mirror。

## 2. 推语料(.md only)
生产路径用 `ops/corpus_sync.py push --local <memory> --host <t4> --remote ~/.claude/projects/<proj>/memory`(rsync · 幂等)。
⚠️ **Windows 开发盒无 rsync** → 用等价 tar-over-ssh:
```bash
cd <memory_dir> && tar czf - *.md | ssh t4 'cd ~/.claude/projects/<proj>/memory && tar xzf -'
```
daemon 只读 `mem_dir.glob("*.md")`(**非递归**,daemon.py:523)。实测推 966 个 .md。

## 3. 起 daemon(GPU + reranker)
```bash
ssh t4
cd ~/compass   # daemon.py 已 scp 至此(daemon 自包含 · 仅可选 query_rewrite,保持 OFF)
PATH=$HOME/.local/bin:$PATH \
ZMM_DEVICE=cuda \
COMPASS_PROD_RERANK=1 \
ZMM_RERANKER_MODEL=BAAI/bge-reranker-v2-m3 \
COMPASS_USE_INOTIFY=0 \
setsid python3 daemon.py > ~/compass_daemon.log 2>&1 < /dev/null &
```
- `setsid + </dev/null`:必须。普通 `nohup ... &` 后跟长 for-loop 在同一 ssh 命令里会让 ssh 挂(实测 exit 255 + daemon 没活)。检查就绪要**另起一条 ssh** poll `ss -tln | grep 9876`。
- 实测:BGE 12.1s 载入 GPU → `listening 127.0.0.1:9876`。

## 🔴 坑:reranker 路径无 HF-fallback
`daemon.py:96-99` 的 `_RERANKER_MODEL` 默认 = modelscope 缓存路径字符串,**没有** embedder 那样的 `if exists() else "BAAI/..."` 兜底(对比 daemon.py:325-327)。
HF-cache 机器(如本 T4)上,不设 env 会报 `reranker failed · Path .../modelscope/.../bge-reranker-v2-m3 not found` → 静默 fallback 到 dense 顺序(recall 仍返回但**没 rerank**)。
- **解(已用)**:起 daemon 时设 `ZMM_RERANKER_MODEL=BAAI/bge-reranker-v2-m3`(从 HF 缓存加载)。
- **建议根因修(未做 · 留 PR)**:给 `_RERANKER_MODEL` 加与 embedder 一致的 `Path(...).exists() else "BAAI/bge-reranker-v2-m3"` 兜底,消除此 footgun。

## 4. 验证(实测 · verification-before-completion)
```bash
ssh t4 'cd ~/compass && python3 _recall_test.py'   # 用 recall_fallback.call_endpoint 发 recall
```
实测 3 查询(project=compass-t4-demo · 966 文件语料):
| query | top hit | 说明 |
|---|---|---|
| compass T4 deploy benchmark pass@k | `plan_compass_t4_deploy_benchmark_env_handoff_20260607.md` | 命中正确 |
| drift guardrail false positive tune out | `session_20260527_drift_loop_open_tuneout.md` | 命中正确 |
| capstone truncation eval bug | BGE 评估 bug 修复 sessions | 命中正确 |

- reranker engage 确认:日志 `reranker loaded · BAAI/bge-reranker-v2-m3 on cuda · 6.9s` + GPU 占用 2.3G→**6.3G**(双模型)+ 候选顺序相对 dense-only 重排。
- **延迟实测**:首次 recall 冷启 75.8s(首查嵌入全部 966 文件)· 之后 dense warm 0.2-0.3s · **reranked warm ~4.2s/query**(reranker 跑 `COMPASS_RERANK_CANDIDATES=30` 个 cross-encoder pass)。
  - ⚠️ 注:plan 估"T4 GPU ~0.6-0.9s"对应单次嵌入,非 30 候选全 rerank。30 候选 reranked ≈ 4s。若要降延迟,调小 `COMPASS_RERANK_CANDIDATES`。

## 当前状态(本 session 结束时)
- daemon **仍在 T4 跑**(`pgrep -f "python3 daemon.py"` · 127.0.0.1:9876 · GPU 6.3G)。
- 这是**手动 setsid demo daemon**,**非** systemd。Phase 2 完整 Task 7(systemd unit + spot 抢占 2min handler + drain + 自动重拉)+ Task 8(客户端指 T4 · kill→fallback 实测)= 仍待做(需 spot 实例策略 + 客户端 recall hook 接 recall_with_fallback)。
- corpus_sync/snapshot_pull/recall_with_fallback 代码已 TDD ship(Phase 0 Task 2/3/4)。
