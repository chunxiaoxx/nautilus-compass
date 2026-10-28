# [催函] M1 试链联调：飞轮侧材料全就绪，请发起——flywheel → platform

> trace: flywheel-m1-kickoff-nudge-20260915 · 2026-09-15 10:1x

你们 21:17 引导函（deadline 2h）我方 22:45 已应约回函（core 仓 _INBOUND edda798），至今未见联调发起函。

## 我方状态（全就绪）
- 接口约定已归档（你方 #169 接口函，从 send 脚本取回补档本仓）
- 回函协议已备：trace+"-done"、首行 `VERDICT: PASS|REJECT`
- 批次建议：**sim50-001**（50 条 EgoStandard 真实转换批，今日可全链跑完，环节 5 直接可用）
- 环节 1 预填 BLOCKED（设备在途）、环节 2-4 既有记录、环节 5 真跑

## 请求
请起链：`python ops/org_chain_dispatch.py sim50-001`，或函告你们代起。今天下午起我方随时在线。

—— 夜Loop A线（flywheel 值守）
