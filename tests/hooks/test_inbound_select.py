"""B4 · 跨框入站选择逻辑 · 修 watermark surface-once 丢未消费消息.

本 session 亲踩: 早期漏了一批 20260623 _TO_COMPASS_ 入站(prior session 已 mark-read·
surface-once 丢失)。纯函数 select_inbound 把"近期未消费"的也二次 surface(floor)。
导入全局 hook 文件(~/.claude/hooks/inbound_outbound_surface.py)测其 select_inbound。
"""
import sys
import importlib.util
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_HOOK = Path.home() / ".claude" / "hooks" / "inbound_outbound_surface.py"
_spec = importlib.util.spec_from_file_location("inbound_outbound_surface", _HOOK)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
select_inbound = _mod.select_inbound


def _entries():
    now = 1_000_000.0
    return now, [
        (now - 100,        "_OUTBOUND_FROM_PLATFORM_SOUL_TO_COMPASS_20260623_x.md"),   # new inbound
        (now - 100_000,    "_OUTBOUND_FROM_V5_TO_COMPASS_20260623_old_unread.md"),       # old but recent (within floor)
        (now - 100,        "_OUTBOUND_FROM_COMPASS_TO_V5_SOUL_20260623_own.md"),         # own (FROM_COMPASS) → exclude
        (now - 100,        "_OUTBOUND_FROM_V5_TO_V5_20260623_other.md"),                 # to V5 → exclude
        (now - 50,         "_OUTBOUND_FROM_V5_BROADCAST_20260623_b.md"),                 # broadcast → include
        (now - 9_000_000,  "_OUTBOUND_FROM_V5_TO_COMPASS_20260601_ancient.md"),          # too old → drop
    ]


def test_new_inbound_above_watermark():
    now, ents = _entries()
    watermark = now - 1000  # 100k-old is below watermark
    new_hits, recent_hits, new_wm = select_inbound(ents, "COMPASS", watermark, now, recent_hours=48)
    names = [n for _, n in new_hits]
    assert any("SOUL_TO_COMPASS" in n for n in names), "fresh inbound must be in new_hits"
    assert any("BROADCAST" in n for n in names), "broadcast must be in new_hits"
    print("✅ new inbound + broadcast surfaced")


def test_own_and_other_excluded():
    now, ents = _entries()
    new_hits, recent_hits, _ = select_inbound(ents, "COMPASS", 0.0, now, recent_hours=48)
    allnames = [n for _, n in new_hits + recent_hits]
    assert not any("FROM_COMPASS_TO_V5" in n for n in allnames), "own outbound excluded"
    assert not any("_TO_V5_" in n for n in allnames), "other-dialog inbound excluded"
    print("✅ own + other-dialog excluded")


def test_recent_floor_resurfaces_unconsumed():
    # 关键修复: 老于 watermark 但在 48h floor 内的未消费消息 → recent_hits(不丢)
    now, ents = _entries()
    watermark = now - 1000  # the 100k-old (≈27h) is BELOW watermark
    new_hits, recent_hits, _ = select_inbound(ents, "COMPASS", watermark, now, recent_hours=48)
    rnames = [n for _, n in recent_hits]
    assert any("old_unread" in n for n in rnames), \
        f"unconsumed-but-recent must re-surface (this is the bug fix) · got {rnames}"
    print("✅ recent floor re-surfaces unconsumed (surface-once bug fixed)")


def test_ancient_dropped():
    now, ents = _entries()
    new_hits, recent_hits, _ = select_inbound(ents, "COMPASS", 0.0, now, recent_hours=48)
    allnames = [n for _, n in new_hits + recent_hits]
    assert not any("ancient" in n for n in allnames), "beyond floor must be dropped"
    print("✅ ancient (beyond floor) dropped")


def test_watermark_advances_only_to_newest_new():
    # watermark 只推进到真 surface 的 new 消息 mt · 不跳 now(否则又丢未来)
    now, ents = _entries()
    watermark = now - 1000
    _, _, new_wm = select_inbound(ents, "COMPASS", watermark, now, recent_hours=48)
    assert new_wm <= now, "watermark must not jump beyond now"
    assert new_wm == now - 50, f"watermark = newest new hit (broadcast at now-50) · got {new_wm}"
    print("✅ watermark advances to newest-new only")


if __name__ == "__main__":
    tests = [
        test_new_inbound_above_watermark,
        test_own_and_other_excluded,
        test_recent_floor_resurfaces_unconsumed,
        test_ancient_dropped,
        test_watermark_advances_only_to_newest_new,
    ]
    failures = []
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failures.append((t.__name__, str(e)))
            print(f"❌ {t.__name__}: {e}")
    if failures:
        print(f"\n❌ {len(failures)}/{len(tests)} failures")
        sys.exit(1)
    print(f"\n✅ {len(tests)}/{len(tests)} inbound-select tests pass")
