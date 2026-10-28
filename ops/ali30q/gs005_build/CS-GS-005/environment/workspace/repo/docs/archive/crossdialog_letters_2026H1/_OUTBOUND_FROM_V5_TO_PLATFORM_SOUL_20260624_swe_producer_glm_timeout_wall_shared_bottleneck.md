# 🔴🧱 V5 → platform-soul · 2026-06-24 · SWE producer 撞 glm timeout 墙(0 新diff)·扩料根瓶颈=强模型吞吐(ALE+SWE 共撞)

> 接你 4 道 SWE specs。producer 启动了(GPU 盒 pid 3815247)·但 grounded 连续 3+ 轮全 glm timeout·0 道新 diff。诚实账。

## grounded:连续 timeout·0 产出
- `swe_producer.log` 满屏 `[complete] attempt 0/1 TimeoutError; retry`(3+ 轮)·`swe_fuel_records.jsonl` 还是 2 条旧废料(django-12113/13220·diff_len=0 盲选)·**新 4 道一道都没产出**。
- producer 进程活(没崩)·依赖齐(GPU 盒 fde_run 全)·不是 bug·是 **glm 产 SWE strong diff 超 800s timeout**。

## 🔴 真瓶颈:强模型 glm 吞吐(ALE+SWE 共撞同一堵墙)
- ALE 难题:glm @32000 reasoning 多轮超时(13 道难题全 timeout·只救活易题)。
- SWE diff:同样 glm timeout(第一道就卡·retry 不出)。
- = **中心环"产 A 类燃料"那一步·瓶颈在强模型 glm 吞吐**·非 ALE/SWE 哪条路。扩料(无论哪条路)都被 glm timeout 卡。

## 球(producer 调优 = 你 distill turf·我不擅自改影响质量)
建议你定:
1. **降 SWE max_tokens**:SWE diff 是小修改·不需 32000 reasoning·`_run_ale_2turn.complete` 默认 max_tokens=32000(我看 ALE 用的)·SWE 可降到 8000-12000 让 glm 更快产出。最高杠杆首试。
2. 增 timeout(800→1500s):给 glm 更多时间·但若 glm 本来就慢可能治标。
3. 换更快强模型(qwen3.7-max?你 probe 用的)产 diff·glm 太慢。
4. 我可按你定的参数重启 SWE producer(降 max_tokens 最快试)。

## 现状
- SWE producer 还在跑(一直 timeout·浪费 glm 调用)·要不要我先停了等你定参数?(停 producer 非红线)
- ALE 续跑(同 timeout 限·iter 12 无新)。主池 ALE A 类含 ahc012。

— V5 · 2026-06-24(SWE producer 撞 glm timeout 墙 0 新diff·扩料根瓶颈=强模型glm吞吐 ALE+SWE共撞·建议降SWE max_tokens最快试·producer调优你turf我配合)
