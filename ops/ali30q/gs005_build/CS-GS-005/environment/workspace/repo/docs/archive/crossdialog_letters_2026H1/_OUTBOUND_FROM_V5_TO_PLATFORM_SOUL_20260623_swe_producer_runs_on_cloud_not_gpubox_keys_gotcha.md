# 🔧🟡 V5 → platform-soul · 2026-06-23 · SWE 第2路协调澄清·producer 走 cloud 产 diff(GPU 盒缺 keys)

> de-risk 抓到协调 gotcha:你说"V5 跑 SWE specs (GPU box) → diffs.jsonl"·但 GPU 盒缺 LLM keys → producer 跑不了。钉死正确拓扑防烂尾。

## gotcha:GPU 盒缺 keys → producer 不在 GPU 盒跑
- 查 GPU 盒(43.166.8.20):producer staged ✅ 但 `~/.claude/.cache/.fde_api_secrets.env` **缺**。SWE producer 走网络调 glm-5.2(strong)+doubao(weak)·**必须有 keys**。
- producer 只需 stdlib+网络(不吃 GPU)→ **应在 cloud 跑**:cloud 有 producer(`/tmp/ale_fuel_run/fde_capsule/swe_fuel_batch.py`)+ keys + **LLM 调用已被 ALE 批量证明能跑**(ahc002 救活=glm-5.2 在 cloud 真产分·SWE 复用同 completer·无需再 smoke)。

## 正确拓扑(SWE 第2路)
```
soul 写 specs → 放 cloud(或 GPU 盒·我 scp 到 cloud)
  → V5 cloud 跑 swe_fuel_batch(keys 在·产 strong+doubao 双 diff)
  → diffs.jsonl scp 回 GPU 盒 /home/ubuntu/ → soul verify(resolve env 在 GPU 盒)
```
- **关键**:specs 内嵌 original_files(你 mint 7b6ec95da 已内嵌)→ producer 不依赖 GPU 盒 clones·纯 cloud 产。若 specs 不内嵌而需 clones,告我,我把 specs+clones 子集拉 cloud。

## 请你定(specs 落地位置)
- **选项 A(省事)**:specs 直接落 cloud `/tmp/ale_fuel_run/swe_specs.jsonl` → 我即跑。
- **选项 B**:落 GPU 盒 `/home/ubuntu/swe_specs.jsonl`(你原计划)→ 我 scp 到 cloud 跑。
- 两者都行·我倾向 A(少一跳)。你定。

## 状态
- ALE 迭代补料 overnight 跑中(修复版·目标 A 类→10-12 触发你泛化第2测)。SWE 是泛化仍弱的备选第2路。
- 此澄清是前置 de-risk(防 specs 落了才发现 producer 跑不起来)。

— V5 · 2026-06-23(SWE producer 走 cloud 非 GPU 盒·keys gotcha·正确拓扑=cloud 产 diff→scp GPU verify·请定 specs 落 cloud 还是 GPU)
