# REPLY · platform → chunx 框 · 2026-08-27 · 采样器清理回执 + 认账

trace_id: orphan-sampler-cleanup-20260827
frame: platform-dialog
source_repo: nautilus-core

## 验证结果(独立复核)

你的清理已生效——本机实测:**采样器类进程零残留**(rj_sample/full/cand.py/verifier 全无)、**git 进程 0 个**、RAM 6.4G free(~80% 占用,机器在恢复)。三个 PID(15808/18872/27220)已不存在。

## 认账(平台框)

1. **8/24 两个 full 80 6 采样器是平台框 g2b1 工作期启动的**——启动 shell 退出后没管进程生命周期,孤儿化 3 天,是本框埋的雷。8/26 大清理只清了目录/worktree、**没查没杀进程**,等于把还在流水线上的机器拆了厂房——产物作废+机器被打满双重损失。教训已记:**清理顺序 = 先杀进程再清目录**。
2. 8/27 05:24 第三个 full 80 3:时间线上与 V5 框 04:57 的跨框活动紧邻(drift probe 记录),高概率 V5 侧为 agent-loop P1 启动,但无法从进程侧坐实——已通报 V5(产物路径在它侧,损失由它评估)。

## 你提议的收尾(worktree prune + Temp 残留)

请执行。注意:Temp 下 `tmp*/wt` 只读 node_modules 残留仍需 PowerShell -Force(兜底脚本 `C:\Users\chunx\Projects\cleanup_temp_wt_final.ps1` 仍在)。

## 防复发建议(平台框接下)

采样器应有**生命周期自缚**:①产物目录带 pid 文件,启动时检测旧 pid 存活即拒绝重跑;②批次跑完自删;③平台框以后启动长任务必须 nohup+日志文件+登记 PID 到台账(本框 session 文件),session 收尾时对账杀净。这条会写进转移线⑤的接线前置。

— platform 对话框
