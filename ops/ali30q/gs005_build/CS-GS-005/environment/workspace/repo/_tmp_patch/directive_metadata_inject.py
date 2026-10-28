"""Day 3 small补强 · directive_text 真注入 metadata.requires_tools 警示.

让 selector LLM prompt 真看到"此 directive 必须真调 X 工具" · 不再只看 directive 文字.
Patch /tmp/v5-local-v2/nautilus_v5/runtime/daemon.py  · funded_directives query +
directive_text 构建 2 处.
"""
from __future__ import annotations
import ast
import pathlib
import sys

DAEMON = pathlib.Path("/tmp/v5-local-v2/nautilus_v5/runtime/daemon.py")

# Patch 1 · funded_directives 真带 metadata
OLD1 = '''                    for r in await cur.fetchall():
                        funded_directives.append({
                            "stake_id": r[0], "staker": r[1],
                            "nau": r[2], "directive": r[3][:200],
                            "deadline": r[4].isoformat() if r[4] else None,
                        })'''

# 注:不改 SQL · 用 metadata 列名为 5 · 但要先看 SELECT 几列
# 直接在原行后追加 metadata · 改 SELECT 加列
# 改 SELECT 真复杂 · 改成事后 SELECT metadata 单独取
NEW1 = '''                    for r in await cur.fetchall():
                        # 2026-05-06 Day 3 · 真加载 metadata 用于 directive_text 警示
                        _md = {}
                        try:
                            await cur.execute(
                                "SELECT metadata FROM platform_agent_stakes WHERE stake_id=%s",
                                (r[0],),
                            )
                            _mr = await cur.fetchone()
                            _md = (_mr[0] or {}) if _mr else {}
                        except Exception:
                            pass
                        _rt = []
                        if isinstance(_md, dict):
                            _rt_raw = _md.get("requires_tools") or _md.get("requires_tool") or []
                            if isinstance(_rt_raw, list):
                                _rt = [str(x) for x in _rt_raw if x]
                            elif isinstance(_rt_raw, str):
                                _rt = [_rt_raw]
                        funded_directives.append({
                            "stake_id": r[0], "staker": r[1],
                            "nau": r[2], "directive": r[3][:200],
                            "deadline": r[4].isoformat() if r[4] else None,
                            "requires_tools": _rt,
                        })'''

# Patch 2 · directive_text 真注入 requires_tools 警示
OLD2 = '''        directive_text = ""
        if funded_directives:
            lines = ["━━ 💰 Pearl-funded directives (有人给你钱要你做) ━━"]
            for d in funded_directives:
                lines.append(
                    f"  · stake {d['stake_id']} · {d['staker']} 投 {d['nau']} NAU · "
                    f"directive: {d['directive']}"
                )
            lines.append("⚠️ 这是真外部需求 · 优先级最高 · 选 fulfill_directive 用 deep_research 完成它")
            directive_text = "\\n".join(lines)'''

NEW2 = '''        directive_text = ""
        if funded_directives:
            lines = ["━━ 💰 Pearl-funded directives (有人给你钱要你做) ━━"]
            for d in funded_directives:
                lines.append(
                    f"  · stake {d['stake_id']} · {d['staker']} 投 {d['nau']} NAU · "
                    f"directive: {d['directive']}"
                )
                # 2026-05-06 Day 3 · 真醒目显示 requires_tools
                if d.get("requires_tools"):
                    lines.append(
                        f"    🔴 此 directive 必须真调用工具: {d['requires_tools']} · "
                        f"evidence gate 拦无调用 · 不调真没 NAU · 系统会兜底但不奖励作弊"
                    )
            lines.append("⚠️ 真外部需求 · 选 fulfill_directive · 真要求工具时按 metadata 调真工具(不只 deep_research)")
            directive_text = "\\n".join(lines)'''


def main():
    src = DAEMON.read_text()
    if OLD1 not in src:
        print("FAIL · OLD1 anchor missing", file=sys.stderr)
        sys.exit(2)
    if OLD2 not in src:
        print("FAIL · OLD2 anchor missing", file=sys.stderr)
        sys.exit(2)
    src = src.replace(OLD1, NEW1).replace(OLD2, NEW2)
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"FAIL · ast: {e}", file=sys.stderr)
        sys.exit(3)
    DAEMON.write_text(src)
    print(f"ok · daemon.py · size={len(src)}")


if __name__ == "__main__":
    main()
