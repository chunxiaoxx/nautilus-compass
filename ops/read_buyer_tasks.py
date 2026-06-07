"""compass · read_buyer_tasks — 读买方题飞书 Bitable → 规范题行(turf 裁定落地)。

**Turf(2026-06-06 裁定):读归 compass · 派归平台 · 连接器归 V7。**
compass 拥有飞书读管线(feishu_client G3 已连),所以"读买方题"归 compass —
别让平台重造 feishu 集成。compass **只读 + 归一,绝不 POST dispatch**(派单是
平台 /fde/dispatch 的 turf · 跨机连接器是 V7 的 turf · 见 mcp_server
governance_dispatch「不直接 mint platform_bounties」同一红线)。

归一输出键对齐 fde-row-assembler 的二期 16 列输入契约(复用不重造),平台
dispatch 与 assemble_rows 可直接消费同一题行 dict。本模块是库(可被 V7/平台
连接器 import)+ 一个 CLI(--feishu / --input 自检读)。NO LLM · 纯映射。

字段来源:feishu Bitable 记录 = {record_id, fields:{列名:值}}。Bitable 列名
可能用官方 16 列全称(题目领域一级目录 …)或简写(一级目录),两者都归一。
"""
from __future__ import annotations

import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# 派单状态值:表示尚未派单(connector 可据此挑未派单题去派)。
_PENDING_DISPATCH = {"待派单", "未派单", "pending", ""}

# 规范键 → 可接受的 Bitable 列名别名(官方全称在前 · 简写在后)。
# 取第一个在 fields 中出现且非空的别名。
_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "uid": ("UID", "uid", "题目编号", "task_uid"),
    "题目": ("题目",),
    "一级目录": ("题目领域一级目录\n", "题目领域一级目录", "一级目录"),
    "二级目录": ("题目领域二级目录", "二级目录"),
    "三级目录": ("题目领域三级目录", "三级目录"),
    "任务概括": ("任务概括",),
    "专家年限": ("标注专家工作年限（未工作的可以写最高学历）",
               "标注专家工作年限(未工作可写最高学历)", "专家年限"),
    "完成时间": ("人类所需完成时间", "完成时间"),
    "附件格式标签": ("附件格式标签",),
    "附件内容": ("附件内容（总结概括）", "附件内容(总结概括)", "附件内容"),
    "产物格式标签": ("产物格式标签",),
    "产物内容": ("产物内容（总结概括）", "产物内容(总结概括)", "产物内容"),
    "level": ("任务类型", "level", "难度"),
    "做题关键步骤": ("做题关键步骤（可选）", "做题关键步骤(可选)", "做题关键步骤"),
    "打分checklist": ("打分checklist（必填）", "打分checklist"),
    "派单状态": ("派单状态", "dispatch_status"),
}


def _cell_text(v) -> str:
    """飞书单元格 → 文本。富文本 segment list → 拼接 text。"""
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        parts = []
        for seg in v:
            if isinstance(seg, dict):
                parts.append(str(seg.get("text") or seg.get("name") or ""))
            else:
                parts.append(str(seg))
        return "".join(parts).strip()
    if isinstance(v, dict):
        return str(v.get("text") or v.get("name") or "").strip()
    return str(v).strip()


def _pick(fields: dict, aliases: tuple[str, ...]) -> str:
    for name in aliases:
        if name in fields:
            txt = _cell_text(fields[name])
            if txt:
                return txt
    return ""


def bitable_record_to_buyer_task(record: dict, aliases=_FIELD_ALIASES) -> dict:
    """飞书 Bitable 记录 ({record_id, fields:{列名:值}}) → 规范买方题行 dict。

    输出键 = fde-row-assembler 二期输入契约(uid/题目/一/二/三级目录/任务概括/
    专家年限/完成时间/附件格式标签/附件内容/产物格式标签/产物内容/level/
    做题关键步骤/打分checklist)+ 派单元数据(record_id/派单状态)。
    缺失列 → 空串。派单状态缺失 → '待派单'(compass 只读 · 状态供 connector)。"""
    fields = record.get("fields") or record
    task = {key: _pick(fields, al) for key, al in aliases.items()}
    task["record_id"] = str(record.get("record_id") or record.get("id") or "")
    if not task.get("派单状态"):
        task["派单状态"] = "待派单"
    return task


def _is_empty_row(task: dict) -> bool:
    """空行 = 无 uid 且无题目(飞书表常残留空记录)。"""
    return not task.get("uid") and not task.get("题目")


def _is_dispatched(task: dict) -> bool:
    return str(task.get("派单状态") or "").strip() not in _PENDING_DISPATCH


def read_buyer_tasks(records, *, skip_dispatched: bool = False, aliases=_FIELD_ALIASES) -> list:
    """归一一批飞书 Bitable 记录 → 规范买方题行列表。

    · 过滤空行(无 uid 无题目)。
    · skip_dispatched=True → 只返回未派单(派单状态∈待派单/未派单/pending/空)的题,
      便于平台/V7 连接器挑新题去派。默认 False(返回全部 · 读全量)。
    **不做任何派单动作**(turf:派归平台)。返回纯数据供消费方决策。"""
    out = []
    for rec in records:
        task = bitable_record_to_buyer_task(rec, aliases)
        if _is_empty_row(task):
            continue
        if skip_dispatched and _is_dispatched(task):
            continue
        out.append(task)
    return out


# ─── main() · 读买方 Bitable(飞书或本地 JSON)→ 打印规范题行 ──────────────────

def _load_feishu_records(app_token, table_id):
    """经 vtf feishu_client(G3 已连)读 Bitable 全部记录。main()-only。
    从 $COMPASS_VTF_DIR 或兄弟目录解析 feishu_client(与 expert settle 同源)。"""
    import importlib.util
    candidates = []
    env = os.environ.get("COMPASS_VTF_DIR")
    if env:
        candidates.append(Path(env))
    candidates.append(_HERE.parent.parent / "vertical-task-factory" / "fde-toolbox")
    for c in candidates:
        fc = c / "feishu_client.py"
        if fc.exists():
            spec = importlib.util.spec_from_file_location("feishu_client", fc)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            token = mod.tenant_token()
            resp = mod.read_bitable_records(app_token, table_id, token)
            return (resp.get("data") or {}).get("items") or []
    raise SystemExit("[buyer] feishu_client not found — set COMPASS_VTF_DIR")


def main(argv=None):
    import argparse
    import json
    ap = argparse.ArgumentParser(
        description="读买方题 Bitable → 规范题行(JSON)。compass 只读 · 不派单。")
    ap.add_argument("--input", help="本地 JSON 文件:Bitable 记录列表")
    ap.add_argument("--feishu", action="store_true", help="从飞书 Bitable 读")
    ap.add_argument("--app-token", help="飞书 Bitable app_token(配 --feishu)")
    ap.add_argument("--table-id", help="飞书 Bitable table_id(配 --feishu)")
    ap.add_argument("--skip-dispatched", action="store_true", help="只输出未派单的题")
    ap.add_argument("--out", help="写规范题行 JSON 到此文件(默认 stdout 摘要)")
    args = ap.parse_args(argv)

    if args.feishu:
        records = _load_feishu_records(args.app_token, args.table_id)
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            records = json.load(f)
    else:
        raise SystemExit("[buyer] give --input <json> or --feishu --app-token --table-id")

    tasks = read_buyer_tasks(records, skip_dispatched=args.skip_dispatched)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        print(f"[buyer] {len(tasks)} 题 → {args.out}")
    else:
        print(f"[buyer] read {len(records)} records → {len(tasks)} buyer tasks "
              f"(skip_dispatched={args.skip_dispatched})")
        for t in tasks:
            print(f"  · {t.get('uid') or '(无uid)'} [{t.get('level') or '?'}] "
                  f"{t.get('派单状态')} · {(t.get('题目') or '')[:40]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
