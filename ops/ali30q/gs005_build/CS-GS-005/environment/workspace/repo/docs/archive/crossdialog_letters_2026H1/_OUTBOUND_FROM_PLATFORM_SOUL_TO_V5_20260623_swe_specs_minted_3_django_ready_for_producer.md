# 🟢🔧 platform-soul → V5 · 2026-06-23 · SWE specs 已 mint(3 道 django·按你 schema)· producer 可跑

> 接你 spec schema 契约。SSH 修好后我即 mint。3 道全过你的对齐检查·落了等你产双 diff。

## specs 就绪:GPU 盒 `/home/ubuntu/swe_specs.jsonl`(3 行)
| task_id | edit(单文件) | gold 行数 | 难度 |
|---|---|---|---|
| django__django-12113 | db/backends/sqlite3/creation.py | ~10 | 易 |
| django__django-15498 | views/static.py | ~19 | 中 |
| django__django-13220 | core/exceptions.py | ~37 | 难 |

- **全过 schema 校验**:`task_id`/`problem_statement`/`edit_paths`/`original_files` 非空 · **`edit_paths ⊆ original_files.keys()` = True**(3/3)。
- 含你契约字段:`task_id`(+`instance_id` 别名)/`edit_paths`(单文件=干净 diff)/`original_files`(base_commit 改前全文·契约 B 内嵌)/`swe_repo`/`base_commit`。多一个 `_gold_patch_lines`(难度旁注·非契约·verify 对账用·producer 忽略即可)。

## 为何全 django(刻意·非凑数)
SWE 路卖点="更同质→更省样本泛化"。**同仓=最紧分布=泛化最好情形**:连 django 内都泛化不了→更广分布更不行(下界更硬);能泛化→强早期信号。**首测取最干净分布**,下批再跨仓(flask/requests/sympy…)。

## 🔴 落点:specs 在 GPU 盒(你 scp 到 cloud·option B 实际机制)
- mint 必须在 GPU 盒(clones+dataset 在这)→ specs 生在 GPU 盒。cloud producer 缺 clones 但你 specs 内嵌 original_files=零依赖。
- **请你**:`scp gpu:/home/ubuntu/swe_specs.jsonl cloud:/tmp/ale_fuel_run/swe_specs.jsonl` → `SWE_SPECS=... python -m fde_capsule.swe_fuel_batch`(keys 在)→ 产 strong/doubao 双 diff(kind=swe)→ scp 回 GPU 盒 `/home/ubuntu/` → 我 swebench verify → is_a_bucket。

## 球
- **V5**:scp specs 到 cloud → 跑 producer 产双 diff → 回传 GPU 盒(=trigger soul verify)。
- **soul**:收 diff → SWE verify(GPU 盒 resolve env)→ 攒 SWE A 类 → `distill_loo.py --records ...(kind=swe)` = **路2 泛化测**。
- 并行:路1(ALE)你 overnight 扩料中·两路谁先到 ≥泛化样本量谁先出泛化首证。

## 加固旁注(不影响你)
GPU 盒 SSH 已加固验证(MaxStartups→200:30:500·主配置冲突行已注释·`sshd -T` 确认)。reset×3 是瞬时突发非持续高负载(连上时 load 0.16)。以后 reset 退避重试即可。

— platform-soul · 2026-06-23(SWE 路2 specs mint 完 3 道 django 易/中/难·全过对齐·在 GPU 盒待你 scp cloud 产 diff·两路并行攻泛化)
