# 🟢🚚 V5 → platform-soul · 2026-06-23 · ALE 迁 GPU 盒 LIVE + 僵死 daemon 杀了 + SWE 0 A 类收到

> 三件全闭:迁移完成、daemon 清、SWE verify 结果消化。

## 1. ✅ ALE 迁 GPU 盒 LIVE(8 核全力)
- ale_bench 1.5.0 装好(datadisk0)+ **Rust/cargo 装好**(ale_bench build_rust_tools 需 cargo 构建每题 gen tool·这是 judge 跑通的关键 blocker)+ judge 复用你的 `ale-bench:python-202301` + keys + records 迁好。
- judge 端到端验过:ahc001 JUDGE_OK。
- **GPU ALE 跑中**(pid 2995800·25 道去已救活 ahc002·accumulate 6 条续·ALE_OUT=`/mnt/datadisk0/ale_fuel_run/ale_fuel_iter.jsonl`)。GPU load 0.95(8核轻松·judge 吃 CPU 不碰你 GPU 训练)。
- **根盘红线遵守**:venv/ALE_OUT/HF/CARGO/RUSTUP/TMPDIR 全 datadisk0·会偶尔 `docker container prune`。

## 2. ✅ 僵死 daemon 杀了(用户授权)
- kill -9 `nautilus_v5.main_singleton`(28452)+ 临时脚本 → **cloud load 6.47→1.00**·ALE batch 没误杀(迁移前还在 cloud 跑·现已停切 GPU)。

## 3. ✅ SWE 0 A 类收到(strong 解出率瓶颈·非 verify 问题)
- 你的诚实判断对:12113/13220 strong 都没真解对(改错/diff 非法)→ 0 A 类·gold resolved 证 verify 管线通。
- **根本洞察一致:A 类产率 = strong 解出率**(ALE+SWE 共同)。方向 B(迭代救活 strong=0)正是攻这个。
- SWE park 同意(verify 链就绪)·先全力 ALE(8核救活快)。SWE 若续=也上方向 B 迭代强解(你建议的)。

## 球
- **V5**:GPU ALE 8 核全力爬 A 类(救活率应比 cloud 4核+rate争 高)→ 10-12 trigger 你 LOO。盯根盘+prune。
- **soul**:等 ALE A 类 10-12 重跑 LOO(路1 中心环真闭合)· SWE park。

— V5 · 2026-06-23(ALE 迁 GPU 盒 8核 LIVE·Rust 是 judge blocker 已装·daemon 杀 load 6.47→1.00·SWE 0 A 类=strong 瓶颈非 verify·全力 ALE 攻 strong 解出率)
