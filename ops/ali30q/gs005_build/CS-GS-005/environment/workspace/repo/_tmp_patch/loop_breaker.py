"""A5 · LoopBreaker · same stake 24h ≥ 3 fails → auto unstake + audit 'directive_loop_breaker'.

Patches /tmp/v5-local-v2/nautilus_v5/runtime/daemon.py · char_count fail path.
On every fail · INSERT platform_audit (action='fulfill_directive_fail').
Then COUNT 24h fails for this stake; if ≥ 3 · UPDATE stake status='unstaked' + INSERT audit 'directive_loop_breaker'.
"""
from __future__ import annotations
import ast
import pathlib
import sys

DAEMON = pathlib.Path("/tmp/v5-local-v2/nautilus_v5/runtime/daemon.py")

OLD = '''                if (res or {}).get("ok") is False or char_count < 500:
                    _err_reason = (res or {}).get("error", "")[:300] if isinstance(res, dict) else ""
                    logger.warning(
                        f"[fulfill_directive] {sid} · char={char_count} · ok={res.get('ok') if isinstance(res, dict) else '?'} · "
                        f"reason: {_err_reason or 'body<500'} · NOT marking · selector 重试"
                    )
                    return'''

NEW = '''                if (res or {}).get("ok") is False or char_count < 500:
                    _err_reason = (res or {}).get("error", "")[:300] if isinstance(res, dict) else ""
                    logger.warning(
                        f"[fulfill_directive] {sid} · char={char_count} · ok={res.get('ok') if isinstance(res, dict) else '?'} · "
                        f"reason: {_err_reason or 'body<500'} · NOT marking · selector 重试"
                    )
                    # 2026-05-06 A5 · LoopBreaker · audit fail + count 24h fails · ≥ 3 → unstake
                    try:
                        async with ag.platform_admin._pool.connection(timeout=3.0) as _lc:
                            async with _lc.cursor() as _lcu:
                                await _lcu.execute(
                                    """INSERT INTO platform_audit
                                       (actor, actor_type, action, target, target_type, outcome, output_preview)
                                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                    ("daemon", "system", "fulfill_directive_fail", sid, "stake",
                                     "fail", f"char={char_count} reason={_err_reason or 'body<500'}"[:1000]),
                                )
                                await _lcu.execute(
                                    """SELECT count(*) FROM platform_audit
                                       WHERE action='fulfill_directive_fail' AND target=%s
                                         AND ts > NOW() - interval '24 hours'""",
                                    (sid,),
                                )
                                _fail_count = (await _lcu.fetchone() or [0])[0]
                                if _fail_count >= 3:
                                    await _lcu.execute(
                                        "UPDATE platform_agent_stakes SET status='unstaked', unstaked_at=NOW() WHERE stake_id=%s AND status='active'",
                                        (sid,),
                                    )
                                    await _lcu.execute(
                                        """INSERT INTO platform_audit
                                           (actor, actor_type, action, target, target_type, outcome, output_preview)
                                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                        ("daemon", "system", "directive_loop_breaker", sid, "stake",
                                         "auto_unstaked", f"24h fail count={_fail_count} · auto-unstaked"[:1000]),
                                    )
                                    logger.warning(f"[LoopBreaker] {sid} · 24h fail={_fail_count} · auto-unstaked")
                            await _lc.commit()
                    except Exception as _le:
                        logger.debug(f"LoopBreaker fail: {_le}")
                    return'''


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
