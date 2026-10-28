# 🎯 /goal · FRESH SESSION 启动(platform-soul 框)· 2026-06-25 · RSI+FDE 基准提升验证(主线)

> 接 6/24 超长 session(战略大收敛 + 头脑风暴归 parking lot)。本文 = 下个 session 无缝接续。粘进 /goal 即可。

## 0. 第0读(必先)
- memory `MEMORY.md` 续17(头脑风暴=parking lot·主线=基准提升验证)+ 续16(统筹 plan)+ 续15(5断点修3)
- memory `plan_20260624_ale_squeeze_gap2_register_statutory`(实操基线)+ `project_20260624_brainstorm_parkinglot_mainline_benchmark_verify`(定调)
- `nautilus-core/FDE_BUSINESS_CHARTER.md`(§7 confound 铁律新加)
- 读 nautilus-core/ 下新 `_OUTBOUND_`/`_BROADCAST_` 入站(尤其 V5 qwen 重产进展)
- 第1 response 输出「今日 active anchor: X/Y」

## 1. 主线焦点(用户钉死·别被 parking lot 带跑)
**RSI+FDE 基准测试提升验证。** 头脑风暴(不卷 LLM 做 agent 驾驭栈 / 三自最小闭环 / self-play RLVR GLM+H100 / 世界模型具身基准 / 案例蒸馏)= **parking lot·飞轮闭环后再推·现在不碰**。

## 2. 起手第一件(单焦点·grounded)
查 V5 是否已用 **qwen3.7-max + max_tokens 8000** 重产 SWE(sklearn-25638 / django-16820)回传 GPU 盒 `swe_fuel_records.jsonl`:
- 有 → soul verify(`/home/ubuntu/verify_pathA_one.py <id>` · **必用 `/mnt/datadisk0/swe-rsi/venv/bin/python`** · 有 swebench 4.1.0 · 系统 python3 没有=会假 applied=False)→ is_a_bucket → 攒 SWE A 类。
- V5 没动 → ping V5(它留 fresh session 做 qwen 重产 + 迁 docker datadisk0 根治根盘)。

## 3. 主线下一步
SWE A 类 + ALE clean A 类(~12·Agent A 实测非 11)一起跑**最干净一次 LOO**:`distill_loo.py --k4 --max-seq 4096` + `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`。判据:held-out 蒸馏后分数提升 = RSI「系统可证变强」首证;仍弱 ~0.18 = 坐实 ALE 天花板·诚实杀不再投 ALE。

## 4. 🔴 红线/gotcha
- **confound-discipline**:任何 KILLED/0/失败先核 confound(系统 python3 无 swebench / 清根盘误删 sweb.env / seq 截断 / OOM / 进程死 · 6/24 抓了 6+ 假失败)。别单 fold 外推。
- **别 9→11→12 小增量**(无梯度已证)· 要 qwen 榨更多料或 SWE 对比。
- **SSH** 走 `ssh gpu`(43.166.8.20 T4)/ `ssh cloud`(生产 PG + nautilus-v5/compass)· 瞬断退避别硬敲。**根盘 50G 易满**(containerd 在根盘·SWE verify build 涨)· 清 `docker images|grep sweb|xargs rmi`(**别碰 ale-bench judge 镜像**)· datadisk0=99G。
- **生产 DB 改动**先备份 + 端到端验证(R3)。
- **不卷 LLM·不碰 parking lot 方案**(飞轮闭环后)。

## 5. 各框球(协调)
- **V5**:qwen 重产 SWE + 迁 docker datadisk0(fresh session 起手)· ALE qwen 续榨。
- **soul(本框)**:qwen diff 回传即 verify + 跑最干净 LOO + 协调中枢。
- **compass**:A 轨 parked / B 轨 conditional-go(sync box + dry-run + 真 ΔMRR 再挂 daemon)。

— platform-soul 交接 · 2026-06-24(主线=RSI+FDE 基准提升验证·头脑风暴 parking lot·起手=V5 qwen 重产 SWE 回传 verify+LOO·confound 铁律+根盘红线)
