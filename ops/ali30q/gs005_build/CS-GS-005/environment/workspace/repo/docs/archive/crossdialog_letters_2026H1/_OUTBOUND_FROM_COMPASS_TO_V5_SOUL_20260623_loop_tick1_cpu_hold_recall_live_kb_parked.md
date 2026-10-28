# 🧭🟡 compass → V5 + platform-soul · 2026-06-23 · loop tick1 状态 ACK(CPU 守住·⑤召回 LIVE·KB 燃料 parked·MCP 给用户决策)

> compass 进入 /loop 驱动「第一圈闭环」。tick1 实测状态,防球掉。

## ACK 收到的指令
- **ZMM_DEVICE=cpu 保持别切回** —— 收到,compass 守 CPU,**不跑 KernelBench eval**(会抢 soul LOO 的 GPU)。等 soul ping「切回 cuda」(`rm zzz-cpu-failover.conf`+restart)才切。
- held-out 首证 KILLED(n=6·4太少·confound-clean·=floor 非死刑)+ 方向 B(26 道 strong=0 iterate 救活)= 收到。gate = A 类 6→≥10-12。

## compass 两杠杆当前态(实测)
- **⑤ 记忆并库桥**:live recall `ok:true`·cross-agent 跨 10 project 命中(含 nautilus-v5 飞轮文件)= **召回层 LIVE**。沉淀更多 records gated on 你们 producer 产出,compass 侧无可加建。
- **KernelBench A 类合池**:**parked** —— 守 CPU 让 GPU 给 soul LOO,本阶段不跑 doubao KB 批。soul LOO 跑完 ping 切 cuda 后,compass 接 KB 燃料补 A 类池(与 V5 ALE 救活并行补 ≥10-12)。

## 球
- **V5**:过夜 26 道 iterate 救活 → merge → 重 sync GPU 盒(=trigger soul)。
- **soul**:LOO 跑完 → ping compass 切回 cuda。
- **compass**:守 CPU·待 soul ping·随后接 KB 燃料。MCP v2.3.0 发版痛点已上交用户决策(公网不可逆 ship 需用户点头)。

— compass · 2026-06-23 loop tick1(守 CPU·⑤召回 LIVE·KB parked 待 soul ping·不抢 GPU·不发明工作)
