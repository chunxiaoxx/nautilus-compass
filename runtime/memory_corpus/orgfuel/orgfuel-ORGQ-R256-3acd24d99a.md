---
name: orgfuel-ORGQ-R256-3acd24d99a
description: "### R256 · 2026-10-06 傍晚(loop 第三轮:socket泄漏现行抓获+M3会签启动) - pro"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R256
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R256 · 2026-10-06 傍晚(loop 第三轮:socket泄漏现行抓获+M3会签启动)
- probe第六源首战告警:过载复燃+59;ss诊断=9876端口CLOSE-WAIT僵尸堆积(777/501/181 unacked)——**服务端socket泄漏bug**(客户端FIN后daemon不close,僵尸占满inflight32);churn(MAX_PROJ)已修但第二bug现形
- 处置:restart清僵尸(重启前僵尸计数留档,重启后0,服务active);**根因修码需值守窗授权**(daemon_v33连接处理缺finally close)——已列值守窗修码单
- M3会签启动:#10063三件(判读隔离/三态输出/证据分层会签+M5判据包规格)在办
- M1:+1(第六源首战=告警→诊断→止血45分钟闭环,灯下黑防线实测有效)
