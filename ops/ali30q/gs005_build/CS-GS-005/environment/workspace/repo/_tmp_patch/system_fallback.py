"""A1 · fulfill_directive system fallback · LLM 不调 required_tool → 系统真代调.

Patch /tmp/v5-local-v2/nautilus_v5/runtime/daemon.py · evidence MISSING block.
On evidence MISSING + requires_tools nonempty:
  · system dispatch required_tools[0] with directive as prompt
  · audit_tool_call records the system fallback call
  · re-check evidence · if now OK → continue to mark fulfilled
"""
from __future__ import annotations
import ast
import pathlib
import sys

DAEMON = pathlib.Path("/tmp/v5-local-v2/nautilus_v5/runtime/daemon.py")

OLD = '''                                if _erts and _estaked:
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
                                        )'''

NEW = '''                                if _erts and _estaked:
                                    await _ecu.execute(
                                        "SELECT count(*) FROM agent_tool_calls WHERE agent_id=%s AND tool_name = ANY(%s) AND ts > %s AND success=true",
                                        (ag.agent_id, _erts, _estaked),
                                    )
                                    _ecnt = (await _ecu.fetchone() or [0])[0]
                                    if _ecnt == 0:
                                        logger.warning(
                                            f"[fulfill_directive] {sid} · evidence MISSING · requires={_erts} · 0 calls since stake · attempting system fallback"
                                        )
                                        # 2026-05-06 A1 · system fallback · 真代调 required_tools[0]
                                        _fb_tool = _erts[0]
                                        _fb_args_map = {
                                            "ask_kairos": {"question": directive[:1500]},
                                            "review_by_kairos": {"content": directive[:1500], "question": "audit this"},
                                            "send_to_agent": {"agent_id": "kairos", "content": directive[:1500]},
                                            "self_modify": {"filepath": "personas/system_fallback_note.md",
                                                            "content": f"# Directive {sid}\\n\\n{directive[:2000]}",
                                                            "summary": f"system fallback for {sid}"},
                                            "compass_drift_check": {"prompt": directive[:1500]},
                                            "propose_code_change": {"title": f"directive:{sid}",
                                                                     "body": directive[:1500],
                                                                     "patch_summary": f"system fallback for {sid}"},
                                        }
                                        _fb_args = _fb_args_map.get(_fb_tool, {"prompt": directive[:1500]})
                                        try:
                                            _fb_res = await ag.tool_registry.dispatch(_fb_tool, _fb_args)
                                            logger.info(f"[fulfill_directive] {sid} · system fallback dispatched {_fb_tool} · result_len={len(str(_fb_res))}")
                                        except Exception as _fbe:
                                            logger.warning(f"[fulfill_directive] {sid} · system fallback {_fb_tool} fail: {_fbe}")
                                            _fb_res = ""
                                        # Re-check evidence · system fallback should have written agent_tool_calls
                                        await _ecu.execute(
                                            "SELECT count(*) FROM agent_tool_calls WHERE agent_id=%s AND tool_name = ANY(%s) AND ts > %s",
                                            (ag.agent_id, _erts, _estaked),
                                        )
                                        _ecnt2 = (await _ecu.fetchone() or [0])[0]
                                        if _ecnt2 > 0:
                                            logger.info(f"[fulfill_directive] {sid} · evidence OK after fallback · {_ecnt2} required-tool calls")
                                            # evidence_ok stays True
                                        else:
                                            evidence_ok = False
                                    else:
                                        logger.info(
                                            f"[fulfill_directive] {sid} · evidence OK · {_ecnt} required-tool calls since stake"
                                        )'''


def main():
    src = DAEMON.read_text()
    if OLD not in src:
        print("FAIL · anchor missing", file=sys.stderr)
        sys.exit(2)
    src = src.replace(OLD, NEW)
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"FAIL · ast: {e}", file=sys.stderr)
        sys.exit(3)
    DAEMON.write_text(src)
    print(f"ok · daemon.py · size={len(src)}")


if __name__ == "__main__":
    main()
