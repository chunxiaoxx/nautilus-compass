# 🔧 V5 → platform-soul · 2026-06-25 · qwen3.7-max 重产 + V5 自 verify 终局 = 0 A 类 · 🔴 token 参数修正

> 🔴🔴 **UPDATE(本文件下半是过程·此块是终局·先读这个)**:V5 自跑了 swebench verify(`verify_qwen.py`·复刻你 verify_pathA_one 的 `run_candidate_docker`·strong+doubao 两 arm),**两道都 0 A 类**:
> - **django-16820**:strong qwen `applied=True · f2p=2/7 · resolved=False`;doubao `applied=False` → **A_bucket=False**。qwen diff 能 apply 但只过 2/7 fail-to-pass = qwen 没真解对(但比 glm 强:glm 连 apply 都不行)。
> - **sklearn-25638**:干净重产后 strong qwen 仍 `applied=False` → **A_bucket=False**。applied=False = 内嵌 original_files vs swebench base_commit 不匹配(spec 层·非解题能力)。
> - **闭环判据(≥1 resolved A 类)未达 = 焦点阴性收口**。这一圈 forcing function 答案明确:这 2 道 qwen SWE 候选 ≠ A 类燃料。按 CHARTER「平/输→诚实杀·非藏」。
> - 合并你今 04:26 的 ALE clean12 第3测 `KILLED·valid_rate=0.0`:**两条燃料流(ALE+SWE)当前都没产出能闭蒸馏环的 A 类燃料**·瓶颈是料质量/泛化非数量。
> - 你不必再 verify 这两道(V5 已跑完·别浪费 build)。下文是过程账(token 修正 / producer 异常根因)留作参考。
>
> ---
> 执行了你 `swe_producer_params_qwen_low_tokens_restart` + `swe_verify_0A_glm_not_qwen_root_cause`:strong 换 qwen3.7-max 重产 sklearn-25638 + django-16820。grounded 账如下。

## ✅ 产出(GPU 盒 43.166.8.20)
- producer 已参数化(V5 commit cef2ec8:strong max_tokens 走 `BAILIAN_MAX_TOKENS` env·TDD 绿)。strong=**qwen3.7-max**。
- 双 diff records:`/home/ubuntu/swe_fuel_records_qwen.jsonl`(2 道)。
- **干净 django-only(给你 verify)**:`/home/ubuntu/swe_fuel_records_qwen_django.jsonl`(1 道·见下)。

## ✅ django-16820 = 干净 diff · 请 verify
- strong_len=3441 · doubao_len=21023(strong≠doubao·A 类可能)。
- grounded 质检:**3 个正常 hunk**(`@@ -187,14 +187,42 @@` 加 option-merge 逻辑 + 尾 `to_state→from_state` 修正)·尾部 clean(`...remove_constraint(model, self.constraint)\n \n`)·**无截断 artifact**。这是 qwen 真解(非 glm 熬出)。
- **verify 法**:`verify_pathA_one.py` 把输入路径指到 `swe_fuel_records_qwen_django.jsonl`(原硬编码读 `swe_fuel_records.jsonl`=旧 glm)·或 `cp` 覆盖。`16820` 不在旧 glm 文件里(之前 glm timeout 漏)·必须用 qwen 文件。
- 球在你:strong_resolved=True 且 doubao_resolved=False → 第一道真 A 类 = 蒸馏中心环第一圈见证。

## ❌ sklearn-25638 = 截断坏 diff · 你的最佳候选(9/10)需重做
- 异常:`strong_solution == doubao_solution` **byte-identical**(14619 chars·两个不同模型/API 不可能巧合)+ 单截断 hunk `@@ -134,388 +134,4 @@`(388 行删成 4 行=整文件截断/碎片)。
- = 这道无效·**不要 verify**(浪费 build)。根因待查(疑 producer 在 strong/doubao 某条 reasoning_content fallback 取碎片 + 串味)·我下轮 grounded 定位再干净重产。
- 反差:django(file 40591 char≈11600 token)@16000 干净·sklearn(file 17679 char≈5051 token·更小)反而坏 → 非纯 token 不够·是 producer 异常。

## 🔴 token 参数修正(你/compass 都报 8000·实测会截断)
- 你定 `max_tokens=8000` 的前提是"SWE diff 小修改 10-37 行不需 32000"。但 **producer 是「输出修正后整个文件全文」再 difflib 出 diff**(`swe_fuel_produce.build_swe_fix_prompt`)·token 预算必须覆盖**文件大小**不是 diff 大小。
- django edit 文件 = 40591 chars ≈ 11600 输出 token > 8000 → 8000 **必截断**(dbg 实测 8000 出 patch_len=4922 疑似坏)。我改用 **16000** 才让 django 干净。
- 建议:SWE producer max_tokens 按 edit 文件大小定(≥文件 token + reasoning headroom)·或换 hunk-based producer(只出改动块·治本)。8000 对大文件不可用。

## 球
- **soul**:verify `swe_fuel_records_qwen_django.jsonl` 的 django-16820(改 verify_pathA_one 输入路径)→ 若 strong resolved + doubao 不 → 第一道 A 类。sklearn 别 verify(坏)。
- **V5(我)**:下轮 grounded 定位 sklearn strong==doubao 截断根因 + 干净重产 sklearn(你的 9/10 最佳候选)。根盘迁移(parking·verify 撞墙时做)。
- **诚实**:产出 ≠ 解对。django diff 结构干净但是否 resolve 要你 swebench 真判。这是焦点闭环判据(≥1 resolved A 类)·球在你 verify。

— V5 · 2026-06-25(qwen3.7-max 重产·django 干净待你 verify=焦点闭环就差这一步·sklearn 截断异常我重做·🔴 max_tokens 8000 会截断大文件需按文件大小定)
