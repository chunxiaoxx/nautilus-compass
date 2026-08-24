# HANDOFF · V3.0 上线冲刺交接(2026-08-24 深夜 → 新会话开工即用)

> 新会话第一句建议:「接 HANDOFF_20260824_V3_launch,V3.0 上线冲刺」——recall 会带出本文。
> 权威账本:GOAL_SSOT_20260823.md(V3.1 迭代版)· 理论底座:~/Projects/verification-learning-papers · 资产:ASSET_MAP_v3.md

## 一、当前状态快照(全部 8/22-8/24 实测,非自报)

- **v3.0.0 已立版本地**(pyproject/CHANGELOG/继承债三件套 + tag v3.0.0,**未 push**)
- 本机引擎全绿:daemon v2.3.1(recall 带 body)/心跳自愈(已立功)/燃料入池 hook 在跑/torch 短路径修复
- 四合约已核销(gold-replication/fuel-loop×2/recall-usefulness);dogfood-bridge 差三框重写(due 8/26)
- 云:load 已修(三幽灵杀完);记忆池 68.8k→2967;**但主项目 pkl 损坏 → 重嵌入卡死**(见下)
- 蒸馏 L4a(4090,V5 框)在跑,判据未出,due 8/29,决策树已预注册
- 博文草稿就绪(published:false,过强声明已修);升级通告已发三框 repo 根

## 二、新会话执行序(第一优先在前)

### 🔴 第一件:云 daemon pkl 落盘补丁(根治卡死)
- 病根:`/opt/nautilus-compass-v1/daemon.py` 嵌入缓存只在内存,优雅停机也不回写(8/24 实测 c096d6883da3.pkl 仍 7/15),重启即丢进度;消费方并发把 32 in-flight 槽打满 → "overloaded" 活锁
- 修法:daemon 加**周期性落盘**(如每 embed 50 文件写一次 pkl);补丁后重启,预计 1-2 小时重建完
- 顺带:本机 repo daemon.py 同步此修复(它有同样隐患)

### 🔴 第二件:V3.0 收口链(C1→C2→C3)
1. C1 回归门:pkl 重建完后,云 9876 直发双查询(飞书单选/loop state)验 ok+命中
2. C2:`git push origin v3.0.0`(分支+tag;含本分支 30+ commit)
3. C3:云 `/home/ubuntu/nautilus-compass` `git pull --ff-only` + systemd 重启 compass-bge-daemon/compass-mcp-tcp(部署规程 ops/DEPLOY_DISCIPLINE.md;**mcp_http_server.py 已入 repo,部署后云上孤本副本可退役**)

### 🟡 第三件:功能补全(按 V3.1 表)
- N3:三框重启+ingest(通告已发,等用户;验收=云 C--Users-chunx 出现 platform/v5/fde agent_type 的 obs)
- C4:worktree 55→<20(活/死清单,fragments 直清)
- V3.1-A act-on 9.87%→40%:先读数(di drift_history),瓶颈多半在提醒可达性
- V3.1-B 发文:回归门过后 dev.to+Show HN(排除调研已做,差异点=部落事实+MEM-α 引用)

### ⚫ B1 蒸馏判据(8/29,外部等):V5 广播后按 GOAL SSOT 预注册决策树走,compass 独立重放对照表验收(verify rc=0 口径,不收自报)

## 三、防跑偏提醒(本冲刺最容易犯的)

1. **先收口后扩张**——博文/新功能全部排在 C1-C3 后(用户 8/24 已纠过一次)
2. push 前确认回归门真过,别把"pkl 重建中"当绿灯
3. 云操作全程部署规程:ff-only/禁 scp 覆盖/改完必验记分牌
4. 三框自报不算:云端 obs 的 agent_type 是唯一核销证据

## 四、指针速查

| 要什么 | 去哪 |
|---|---|
| 目标/判据/due | GOAL_SSOT_20260823.md |
| 冰山资产/生接眠死 | ASSET_MAP_v3.md + 附录A |
| 实验 harness | tools/recall_usefulness_exp.py(数据 outputs/recall_usefulness_20260823.json) |
| 燃料池 | vtf/fuel_pool/(pending 待周五 QC) |
| 博文 | paper/BLOGPOST_memory_evidence_20260824.md |
| 云入口 | ssh cloud(43.160.239.61:24860)· daemon 9876 · MCP 9877 · REST 8770 |
| token 库 | ~/.claude/.cache/compass_cloud_tokens.env(6 框) |
| 蒸馏任务书 | nautilus-v5/TASK_L4A_distill_first_run.md |
