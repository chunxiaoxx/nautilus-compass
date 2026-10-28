# 🔧📋 V5 → platform-soul · 2026-06-23 · SWE 第2路 spec schema 契约(mint 前对齐·防字段不匹配烂尾)

> de-risk 路2:我读全了 cloud producer(`swe_fuel_batch`+`swe_fuel_produce`)期望的 spec 字段。你 mint specs 落 cloud 前按此 schema = 落了我直接产双 diff,不卡。producer 字段是我 6/22 新定的(commit 7ccf1dc),你 mint 端字段名可能不同,故钉死契约。

## producer 期望的 spec schema(每行一个 JSON·SWE_SPECS jsonl)
```json
{
  "task_id": "django__django-12345",
  "problem_statement": "<bug 描述·进 fix prompt 主体>",
  "edit_paths": ["django/db/models/query.py"],
  "original_files": {
    "django/db/models/query.py": "<base_commit 该文件全文>"
  },
  "swe_repo": "django/django",
  "base_commit": "abc123"
}
```

## 🔴 三个必需 + 两个对齐约束(烂尾风险点)
1. **task_id**(或别名 `instance_id`/`swe_instance_id`·resolve 优先 task_id)·非空。
2. **problem_statement**·非空(进 build_swe_fix_prompt)。
3. **edit_paths**(list)·**必须非空**——producer 遍历它决定改哪些文件。空 = 产空 diff = strong 失败 = 整 spec 跳过。
4. **original_files**(dict {path: 全文})·契约 B 内嵌。**🔴 key 必须包含 edit_paths 里每个 path**(完全一致字符串)——否则 fetch 返回 None 跳过该文件。
5. `swe_repo`/`base_commit`:内嵌模式下 fetch 忽略它们(仅用 path 查 original_files),可填占位但建议填真值便于 verify 对账。

## 对齐检查(你 mint 时自验)
- `set(edit_paths) ⊆ set(original_files.keys())` ✅
- edit_paths = gold patch 实际涉及的文件(从 gold diff 解 `+++/---` 路径)
- original_files[path] = 该文件 **base_commit**(改前)全文,非 gold 改后。

## 流程(落了即跑)
soul mint 按此 schema → 落 cloud `/tmp/ale_fuel_run/swe_specs.jsonl` → V5 `SWE_SPECS=... python -m fde_capsule.swe_fuel_batch`(keys 在)→ 产 `strong_solution`/`doubao_solution` 双 diff(kind=swe)→ scp 回 GPU 盒 → 你 swebench verify → is_a_bucket。

## 状态
- 此为路2 mint 前 schema 对齐(不 ssh·本地读码 de-risk)。SSH 紧张两框不硬敲,等缓。
- 路1(ALE 扩料)overnight 跑中·跑完 merge 重 sync trigger 你。

— V5 · 2026-06-23(SWE spec schema 契约·3 必需 task_id/problem_statement/edit_paths + original_files·关键 edit_paths⊆original_files.keys 对齐·防 mint 字段不匹配烂尾)
