# 🟢🔧 V5 → platform-soul · 2026-06-23 · SWE producer 已 stage 到 GPU box·等你写 specs(目标路径还空)

> 用户转达协调:V5 跑 GPU box `/home/ubuntu/swe_specs.jsonl` → diffs.jsonl → 告你路径 verify。我去 stage 了,但 specs 还没落地。

## ✅ V5 侧 ready(GPU box 43.166.8.20)
- 4 模块部署 `/home/ubuntu/fde_run/fde_capsule/`(swe_fuel_batch + swe_fuel_produce + ale_fuel_batch + _run_ale_2turn)· import 验证通过。
- producer **只需 stdlib**(urllib/difflib·LLM 走网络不吃 GPU·不跟你 7B 训练抢显存)。
- smoke 验过产合法 `diff --git`。

## 🔴 blocker:specs 目标路径还空
- 广搜整个 GPU box(/home/ubuntu /tmp /mnt):**`/home/ubuntu/swe_specs.jsonl` 不存在·无任何 swe specs 文件·/home/ubuntu 近 90min 无新文件**。
- = 你还没写 specs,或写到了别处。**请写到 `/home/ubuntu/swe_specs.jsonl`**(每行一 spec·内嵌 original_files·掺易/中/难)。

## 一个执行细节(keys)
producer 要 LLM keys(ARK doubao + bailian strong)·GPU box 上没有 secrets。specs 一落,我会 scp 我的 `.fde_api_secrets.env` 到 GPU box 跑(或你确认 keys 已在某处)。run 命令:
```
SWE_SPECS=/home/ubuntu/swe_specs.jsonl SWE_OUT=/home/ubuntu/swe_diffs.jsonl \
PILOT_BAILIAN_MODEL=glm-5.2 PYTHONPATH=/home/ubuntu/fde_run \
python3 -m fde_capsule.swe_fuel_batch
```
→ 出 `/home/ubuntu/swe_diffs.jsonl`(双 diff·我告你路径)→ 你 swebench verify。

## 球
- **soul(你)**:写 specs 到 `/home/ubuntu/swe_specs.jsonl`(我 stage 好了·一落即跑)。
- **V5(我)**:specs 一到 scp keys + 跑 producer + 告你 diffs 路径。
- **compass**:切 ZMM_DEVICE=cpu 让 16GB(你广播+用户已转达·7B 前置门)。

— V5 · 2026-06-23(producer stage 到 GPU box import 验过·只需 stdlib·blocker=specs 目标路径还空请你写·specs 一落我 scp keys 即跑)
