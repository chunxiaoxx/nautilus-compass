---
name: orgfuel-ORGD-d4ea109bf5d66f54-a16b43f092
description: "[### 轮 18 · 2026-09-25 17:00-18:3x(用户新令×2:发布前外部基线+小额投流)] - 进"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-d4ea109bf5d66f54
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 轮 18 · 2026-09-25 17:00-18:3x(用户新令×2:发布前外部基线+小额投流)] - 进展:①**mem0 双臂基线管线建成**(runtime/assay_bc1_20260927/mem0_baseline/run_baseline.py:18 题×记忆臂/对照臂,backbone=doubao,判分纪律=只读槽位不读真值,判分器污染正本副作用已堵:快照恢复)②**发布日机械腿** scripts/bc1_launch_day.py(check-links 5/5 绿+预告块置换干跑 1 匹配+幂等;③Discord④中文稿仍人工)③投流预注册档(docs/strategy/paid_promo_preregister_20260927.md:¥2000 上限/成功判据=可归因报名数非曝光/止损 ¥500·48h/物料两件)④墙页发布块+通报函物料备好
- 问题分析:**coding plan 月额度耗尽**(429 AccountQuotaExceeded,9/28 23:59 重置)→ 用户拍板 LLM=MiniMax M3,管线已接(--provider minimax 默认+本地 bge-m3 向量,零 ARK 依赖),本机 CLI token 9/14 过期待刷新(用户开一次 App 即续);墙页拓扑查明:正本墙=compass.nautilus.social/wall.html(apex /wall=platform 试金局页,BC1 上 apex 依赖 platform);服务器仓因 9/23 重写分叉(ahead535/behind1139),部署只走 scp;arkcli SSO refresh_token 失效(plans 查询不可用);9/25 函件归档断档(993 经姐妹函 994 恢复)——归档纪律漏洞待堵;判分
