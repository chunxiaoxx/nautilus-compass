---
status: pending_qc
source_session: session_v3_launch_closure_20260824.md
source_project: C--Users-chunx-Projects-nautilus-compass
extracted_at: 20260824-104716
content_hash: sha256:171a84d6492d945a
qc_protocol: control-first-fail (Gate B)
---

1. **pkl 补丁(第一件)**:真根因 ≠ 交接说的"缓存只在内存不落盘"——落盘存在,但**非原子写截断**(c096d6883da3.pkl 74MB "Ran out of input")+ **re-embed 中途被 kill 进度全丢**。修法:① `_pkl_write_atomic`(tmp+os.replace,3 处)② 每 `COMPASS_PKL_FLUSH_EVERY=50` 文件周期 flush。commit `0447367`(repo)+ 同款点补丁打云 /opt(备份 daemon.py.bak_20260824)。清损坏 pkl 重启→warmup failed=0→主项目 C--Users-chunx(2976 md)重建完成(22.9MB)。
2. **C1 回归门 ✅**:云 9876 双查询均 ok+命中 <1s(飞书单选 0.771 命中 tribal-feishu 记忆;loop state 0.661)。
3. **C2 ✅**:分支 compass/convergence-enforcement-20260707(0447367)+ tag v3.0.0 推上远端;main 从 81feef2 **fast-forward** 到 0447367(无强推)。
4. **C3 ✅**:云 /home/ubuntu/nautil
