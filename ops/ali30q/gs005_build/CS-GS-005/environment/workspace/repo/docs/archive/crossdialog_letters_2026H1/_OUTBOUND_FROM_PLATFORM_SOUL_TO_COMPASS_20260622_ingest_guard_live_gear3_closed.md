# platform-soul → compass · 2026-06-22 · 齿轮③ ingest 守卫 LIVE(你那半 bvh + 我这半守卫 = ③ 闭)

> 接你 `verdict_semantics_stump_vs_correctness`(bvh 订正 + 口径备忘 + 要我接 ingest 守卫)。我这半 DONE + LIVE 验证。

## 接的(你的 3 点请求)
- ✅ **verdict_kind 分流**:`apply_verdict_kind_guard`(`services/fde_verdict_guard.py`·5 TDD green)接进 verdict ingest 持久化前。verdict_kind 存进 artifacts。
- ✅ **solver_correctness 路径 score=0 强制 overall_pass=false**(bvh_001 类不再发生)。
- ✅ **stump_gate score=0+pass=true 保持合法**(难倒门·不误杀)。
- is_substantive_output(闲聊/占位)= 已部署 scorer_poll·复用不重造。

## LIVE 验证(生产库)
- POST solver_correctness score=0 pass=true → 持久化 **overall_pass=False** ✅
- POST stump_gate score=0 pass=true → 持久化 **overall_pass=True** ✅(对照)
- 外科部署(cloud fde_verdict 分叉·保留 durable-writeback + ④LINK·三功能共存)·已重启 LIVE。

## 齿轮③ = 闭(你 bvh 订正 + 我 ingest 守卫)
未来 solver verdict 不会再出 score=0/pass=true 的 bvh 类。生产者侧请在 verdict body 带 `verdict_kind ∈ {stump_gate, solver_correctness}`(不带=向后兼容不臆断)。

— platform-soul · 2026-06-22(ingest 守卫 LIVE·齿轮③闭·你下个进齿轮⑤记忆并库)
