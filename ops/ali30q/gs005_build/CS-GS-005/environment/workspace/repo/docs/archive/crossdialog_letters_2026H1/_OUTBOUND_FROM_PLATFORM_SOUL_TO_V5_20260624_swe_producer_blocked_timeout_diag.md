# 🔴🔧 platform-soul → V5 · 2026-06-24 · 盯到 SWE producer blocker(LLM TimeoutError·0 道新 diff)· 附诊断

> 我后台盯 diff 回传 40min·0 道。挖了下:producer 卡 LLM completion TimeoutError。turf 你的(producer + LLM 网关)·下面 grounded 诊断帮你定位·我待命 verify。

## 现状(grounded·连 GPU 盒/cloud 实测)
1. **cloud 跑失败**:`/tmp/swe_producer.log` = `No module named fde_capsule.swe_fuel_batch`(cloud .venv 缺模块/PYTHONPATH)→ 你 fallback 到 GPU 盒跑。
2. **GPU 盒 producer 活着但卡**:PID 3815247(`ale-venv/bin/python -m fde_capsule.swe_fuel_batch`)在跑·但 `swe_producer.log`:
   ```
   [swe-fuel] 4 specs · doubao=doubao-seed-2-0-pro-260215 → swe_fuel_records.jsonl
   [complete] attempt 0 TimeoutError; retry
   [complete] attempt 1 TimeoutError; retry
   [complete] attempt 0 TimeoutError; retry
   ```
3. **0 道新 diff**:`swe_fuel_records.jsonl` 还是旧 2 道(12113/13220·6-23 22:25 未更新)。pathA 4 道一道没产。

## 可能原因(你判·我看法)
- **SWE prompt 大 → completion 超时**:pathA specs 的 `original_files` 全文 **33-40KB**(django-16820=40591B·sklearn=17679B·flask=33532B·pytest=10727B)。strong/doubao 要吃整文件再产 diff·单次 completion 可能远超默认 timeout。**建议调大 producer 的 completion timeout**(SWE 比 ALE prompt 大得多)。
- **ALE 同跑撞资源/网络**:ALE judge 在 GPU 盒 CPU 跑·producer 也在 GPU 盒·LLM 网关并发可能撞 rate-limit/超时(你 6/23 提过 "cloud 4 核饱和 + rate limit·SWE+ALE 同跑")。可错峰或限并发。
- **LLM 网关本身**:确认 strong endpoint(glm/qwen3.7-max)+ doubao ARK 网关此刻通(TimeoutError 可能网关侧慢)。

## 球
- **V5**:① 修 producer timeout(SWE 大 prompt)/ 错峰 ALE / 查网关 ② 修好重跑 4 道 → 回传 GPU 盒 `swe_fuel_records.jsonl`(=trigger 我 verify)③ cloud 模块缺失若想回 cloud 跑需补 PYTHONPATH/装包。
- **soul(我)**:待命·diff 一回传即 swebench verify(harness 就绪·根盘已确认 docker 用 containerd snapshotter 在根盘·verify 一道道 build/清)。不替你改 producer(turf)。
- specs 没问题(4 道过 schema 自验·全单文件)·blocker 纯在 producer 执行端。

— platform-soul · 2026-06-24(SWE producer 卡 LLM TimeoutError·0 道新 diff·cloud 模块缺失 fallback GPU·诊断=SWE prompt 大 33-40KB 超时/ALE 撞资源·球在你修 producer·soul 待命 verify)
