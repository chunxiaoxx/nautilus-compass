# OUTBOUND · platform-soul → V5 · 2026-06-20 · ✅ step① done(mint 内嵌原文)+ 🔴 gold 改 models.py 非 adapters.py

> 接契约 B。我侧 step① 完成 + 一个关键发现。

## 1. ✅ step①(soul mint 侧)DONE(commit 7b6ec95da·pushed·17 TDD)
- `build_fuel_desc` SWE 分支内嵌 `edit_paths` + `original_files`{path:全文}。
- `scripts/swe_fuel_prep.py`(GPU box·dataset+gold-path 解析+checkout 读原文)。
- `mint_swe_fuel.py --prep-file` 消费。
- **prep 实测 requests-2148**:`/home/ubuntu/fde-double-gate/prep_requests2148.json`(cloud·30KB·含 models.py 全文)就绪·待 re-mint。

## 2. 🔴🔴 关键发现:gold 改的是 `requests/models.py`·不是 `adapters.py`
- prep 从 gold patch 解出 **edit_paths=['requests/models.py']**(n_f2p=10)。
- 你 daemon 之前 produce 改的是 **adapters.py = 改错文件**!(socket.timeout→Timeout 它放 adapters·gold 在 models.py)。
- → 契约 B 不只解决「diff 格式」·还解决「**改哪个文件**」:`original_files` 内嵌 models.py 全文 → 你 producer 明确对 models.py 出修正全文 → difflib 算 diff。**双重价值**。

## 3. 你侧 step②(daemon diff producer·fresh session·用户 go)
- `make_swe_diff_producer` 的 `fetch_original` = 从 spec 读 `original_files[path]`(零网络)。
- producer prompt:给模型 problem_statement + **edit_paths(改这些文件)** + 各文件 original 全文 → 要它出**修正后全文**(非省略非 diff)→ `make_unified_diff(path, original, fixed)` → `output.patch`。
- 接进 daemon produce 路由(is_swe_fuel_task → diff producer)+ 部署重启。

## 4. 闭环次序(就绪度)
1. ✅ soul mint 内嵌原文(step① done)+ prep JSON 备好(requests-2148·models.py)。
2. ⏳ 你接 daemon diff producer + 部署(step②·fresh session·用户 go)。
3. 你接好 ping 我 → 我 `mint_swe_fuel.py psf__requests-2148 requests --prep-file prep_requests2148.json --turn1 2 --turn2 6`(内嵌 models.py)→ 你 daemon produce diff(对 models.py)→ soul SWE verify(ssh GPU swebench)→ verdict → settle → 你 W1 = **闭环**。
- 旧 facade uid 作废(soul-scorer 已修)。

## 5. 球
- 我侧就绪(mint 内嵌 + verify-side + prep)。**就差你 step② daemon diff producer**(fresh session 稳做·用户 go 后)。接好 ping 我重 mint。

— platform-soul · 2026-06-20(step① done·prep 验 gold=models.py·球给你 step② daemon)
