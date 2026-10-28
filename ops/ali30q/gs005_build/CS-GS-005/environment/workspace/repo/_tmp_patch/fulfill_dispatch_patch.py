"""
Fulfill_directive 真重写 · 真按 metadata.requires_tools 派 · 让 LLM 在 respond 路径自由选工具.

真背景:
  当前 fulfill_directive hardcoded dispatch deep_research · 不管 directive 真要求啥
  agent LLM 写 reason "必须用 self_modify" · 但路径锁死它没 agency
  iter 1-7 累积:0 真 self_modify · 0 真 ask_kairos · 0 真 PR 闭环

真修法:
  在 deep_research dispatch 前 · 真 query stake.metadata.requires_tools
  真要求时:走 ag.respond(prompt) · LLM ReAct 真自选工具(self_modify / ask_kairos / send_to_agent ...)
  evidence gate 已存(我加过)· 但 .singleton-ready 备份是 cutover 时 · 没我后面加的 evidence gate
  这次真 patch 同时:加 evidence gate + dispatch 路径

兜底:
  1. metadata 没 requires_tools → 走旧 deep_research 路径(不破坏现有)
  2. respond 失败 → return 空 res · selector 重试
  3. 真 ast 验证 · syntax check 通过才落地

Usage:
  scp fulfill_dispatch_patch.py cloud:/tmp/
  ssh cloud "python3 /tmp/fulfill_dispatch_patch.py"
"""
from __future__ import annotations
import pathlib
import sys

DAEMON_PY = pathlib.Path("/home/ubuntu/nautilus-v5/nautilus_v5/runtime/daemon.py")

# ─────────────────────────────────────────────────────
# Anchor 1 · dispatch deep_research(replace 真路径选择)
# ─────────────────────────────────────────────────────

OLD_DISPATCH = '''                logger.info(f"[fulfill_directive] {sid} · '{directive[:60]}' for {staker} ({nau} NAU)")
                res_json = await ag.tool_registry.dispatch("deep_research", {
                    "question": enhanced_question,
                    "max_subqueries": 5,
                    "publish": True,
                })'''

NEW_DISPATCH = '''                logger.info(f"[fulfill_directive] {sid} · '{directive[:60]}' for {staker} ({nau} NAU)")
                # 2026-05-06 · 真按 metadata.requires_tools 派 · 不再 hardcoded deep_research
                # 真要求工具时 · 走 ag.respond(prompt) · LLM ReAct 真自选工具
                _required_tools = []
                try:
                    async with ag.platform_admin._pool.connection(timeout=3.0) as _c:
                        async with _c.cursor() as _cu:
                            await _cu.execute("SELECT metadata FROM platform_agent_stakes WHERE stake_id=%s", (sid,))
                            _md = (await _cu.fetchone() or [None])[0] or {}
                            if isinstance(_md, dict):
                                _rt = _md.get("requires_tools") or _md.get("requires_tool")
                                if isinstance(_rt, list):
                                    _required_tools = [str(t) for t in _rt if t]
                                elif isinstance(_rt, str) and _rt:
                                    _required_tools = [_rt]
                except Exception as _e:
                    logger.debug(f"[fulfill_directive] metadata read fail: {_e}")
                if _required_tools:
                    # 真走 LLM ReAct · agent 自由选工具
                    logger.info(f"[fulfill_directive] {sid} · requires_tools={_required_tools} · respond path · LLM auto-pick")
                    _orch_prompt = (
                        f"{enhanced_question}\\n\\n"
                        f"[平台规则] 此 directive 必须真调用以下工具至少一次: {_required_tools}\\n"
                        f"[evidence gate] 你必须真用工具 · 不能只写文字描述 · 否则 fulfillment 不计\\n"
                        f"[stake_id] {sid} · {nau} NAU 已质押 · 完成则 80% 归你"
                    )
                    _chunks = []
                    try:
                        async for _ck in ag.respond(_orch_prompt, user_id=f"directive:{sid}"):
                            _chunks.append(_ck)
                    except Exception as _re:
                        logger.warning(f"[fulfill_directive] respond fail: {_re}")
                    _resp_text = "".join(_chunks).strip()
                    res = {"ok": bool(_resp_text), "body": _resp_text[:5000]}
                    res_json = __import__("json").dumps(res)
                else:
                    res_json = await ag.tool_registry.dispatch("deep_research", {
                        "question": enhanced_question,
                        "max_subqueries": 5,
                        "publish": True,
                    })'''

# ─────────────────────────────────────────────────────
# Anchor 2 · evidence gate before mark fulfilled
# (重新加我之前丢失的 evidence gate)
# ─────────────────────────────────────────────────────

OLD_MARK = '''                # 标 stake fulfilled · 加 race-condition 防护 · 同 stake 只 push 1 次
                # WHERE fulfilled_at IS NULL · 已被别的 cycle 抢先标了 → rowcount=0 → skip webhook
                row_count = 0
                try:
                    async with ag.platform_admin._pool.connection(timeout=5.0) as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """UPDATE platform_agent_stakes
                                   SET fulfilled_at = NOW(), fulfilled_url = %s
                                   WHERE stake_id = %s
                                     AND fulfilled_at IS NULL""",
                                (url, sid),
                            )'''

NEW_MARK = '''                # 2026-05-06 · evidence gate · stake.metadata.requires_tools 真要求时验工具调用
                # 防 agent 写文字当 fulfillment 跑路
                evidence_ok = True
                try:
                    async with ag.platform_admin._pool.connection(timeout=3.0) as _ec:
                        async with _ec.cursor() as _ecu:
                            await _ecu.execute(
                                "SELECT metadata, staked_at FROM platform_agent_stakes WHERE stake_id=%s",
                                (sid,),
                            )
                            _er = await _ecu.fetchone()
                            if _er:
                                _emeta = _er[0] or {}
                                _estaked = _er[1]
                                _erts = []
                                if isinstance(_emeta, dict):
                                    _ert = _emeta.get("requires_tools") or _emeta.get("requires_tool")
                                    if isinstance(_ert, list):
                                        _erts = [str(t) for t in _ert if t]
                                    elif isinstance(_ert, str) and _ert:
                                        _erts = [_ert]
                                if _erts and _estaked:
                                    await _ecu.execute(
                                        "SELECT count(*) FROM agent_tool_calls WHERE agent_id=%s AND tool_name = ANY(%s) AND ts > %s AND success=true",
                                        (ag.agent_id, _erts, _estaked),
                                    )
                                    _ecnt = (await _ecu.fetchone() or [0])[0]
                                    if _ecnt == 0:
                                        logger.warning(
                                            f"[fulfill_directive] {sid} · evidence MISSING · requires={_erts} · 0 calls since stake · NOT marking"
                                        )
                                        evidence_ok = False
                                    else:
                                        logger.info(
                                            f"[fulfill_directive] {sid} · evidence OK · {_ecnt} required-tool calls since stake"
                                        )
                except Exception as _ee:
                    logger.debug(f"[fulfill_directive] evidence check fail: {_ee}")
                if not evidence_ok:
                    return   # 不 mark · selector 下 cycle 真重试

                # 标 stake fulfilled · 加 race-condition 防护 · 同 stake 只 push 1 次
                # WHERE fulfilled_at IS NULL · 已被别的 cycle 抢先标了 → rowcount=0 → skip webhook
                row_count = 0
                try:
                    async with ag.platform_admin._pool.connection(timeout=5.0) as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """UPDATE platform_agent_stakes
                                   SET fulfilled_at = NOW(), fulfilled_url = %s
                                   WHERE stake_id = %s
                                     AND fulfilled_at IS NULL""",
                                (url, sid),
                            )'''


def main():
    src = DAEMON_PY.read_text()
    backup = DAEMON_PY.with_suffix(".py.bak.fulfill_dispatch")
    backup.write_text(src)
    print(f"backup → {backup}")

    if OLD_DISPATCH not in src:
        print("ERROR · OLD_DISPATCH anchor missing", file=sys.stderr)
        sys.exit(2)
    if OLD_MARK not in src:
        print("ERROR · OLD_MARK anchor missing", file=sys.stderr)
        sys.exit(2)

    src = src.replace(OLD_DISPATCH, NEW_DISPATCH)
    src = src.replace(OLD_MARK, NEW_MARK)

    # 真 ast 验证
    import ast
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"ERROR · ast parse fail: {e}", file=sys.stderr)
        sys.exit(3)

    DAEMON_PY.write_text(src)
    print(f"OK · daemon.py patched · size={len(src)}")
    print("  · dispatch path: requires_tools → ag.respond LLM auto-pick")
    print("  · evidence gate: 0 required-tool calls → reject")


if __name__ == "__main__":
    main()
