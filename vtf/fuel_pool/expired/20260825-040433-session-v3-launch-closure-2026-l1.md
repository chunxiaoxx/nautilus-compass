---
status: pending_qc
source_session: session_v3_launch_closure_20260824.md
source_project: C--Users-chunx-Projects-nautilus-compass
extracted_at: 20260825-040433
content_hash: sha256:3877c70a683ffefb
qc_protocol: control-first-fail (Gate B)
---

- ~~云 daemon.py(/opt)分叉待统一~~ → **✅ 8/25 统一完成**:Stage1a /status(5min 滑窗/overload 计数/pkl 体积/psutil)移植进 repo(`af45dd1`),scp 同版到 /opt,云 daemon 跑 repo 单源。**过程中挖出并发 setdefault 竞态老 bug**(两线程各持 cache dict,稀疏 pkl 覆盖致条目丢失→347% CPU 反复 re-embed+33 次 tmp ENOENT)→ v3.0.3 per-project 锁+唯一 tmp 名修复(`f3063e1`)。终验:recall 0.9-1.1s 命中、/status 通、CPU 5.4%、零 flush fail。旧 68-commit 分叉线备份 `cloud-stage1a-backup-20260824`。
- 云 repo 换轨过程:stash 了 BLOGPOST impact counters(已有 _cloud_backfill_20260824 存档);untracked mcp_http_server.py 与 main 版逐字节一致后删除。
- 损坏 pkl 留存:`/home/ubuntu/c096d6883da3.pkl.corrupt_20260824`(可事后删)。
