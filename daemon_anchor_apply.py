"""compass v0.9.4 · daemon anchor apply · #6 fusion runtime.

把 layered anchors (platform_base + domain + tenant) 应用到 BGE 索引.
不修改 daemon.py 主代码 · 用 patch 模式: daemon import 时调本模块.

Usage in daemon.py:
  from daemon_anchor_apply import apply_layered_anchors
  pos_texts, neg_texts = apply_layered_anchors(domain="finance")
  # then index with bge-m3 as before

Or as standalone (for cache prebuild):
  python daemon_anchor_apply.py --domain finance --output anchors_merged.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

PLUGIN_DIR = Path(__file__).resolve().parent


def apply_layered_anchors(domain: Optional[str] = None,
                          tenant_anchors_path: Optional[Path] = None,
                          base_path: Optional[Path] = None) -> tuple[list[str], list[str]]:
    """
    Returns (positive_anchors, negative_anchors) · de-duped · for BGE indexing.
    Uses daemon_anchor_loader.load_layered_anchors as primary.
    """
    sys.path.insert(0, str(PLUGIN_DIR))
    from daemon_anchor_loader import load_layered_anchors
    return load_layered_anchors(domain=domain,
                                 tenant_anchors_path=tenant_anchors_path,
                                 base_path=base_path)


def write_merged_to_file(domain: Optional[str], output: Path):
    pos, neg = apply_layered_anchors(domain=domain)
    merged = {
        "comment": f"Merged anchors · platform_base + domain={domain} + tenant · v0.9.4 layered",
        "version": "1.0.0",
        "layer": "merged",
        "domain": domain,
        "positive_anchors": pos,
        "negative_anchors": neg,
    }
    output.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[anchor_apply] merged → {output} · pos={len(pos)} · neg={len(neg)}")


def patch_daemon_anchors():
    """
    Try to monkey-patch daemon.py at runtime · so daemon's anchor loader
    automatically uses layered.

    Strategy: replace `_load_anchors_file` (or whatever name daemon uses) to
    call our apply_layered_anchors instead.

    Note: this is implementation-coupled · only works if daemon.py is loaded
    in the same Python process (which it is when run as same daemon process).
    """
    try:
        sys.path.insert(0, str(PLUGIN_DIR))
        import daemon  # the actual daemon.py
        # The exact attribute name in daemon.py depends on its implementation.
        # As of 2026-05-05, daemon.py loads anchors via `_load_anchors()` or similar.
        # We expose the layered version under a stable name:
        daemon._load_anchors_layered = apply_layered_anchors
        print("[anchor_apply] daemon._load_anchors_layered installed · daemon should call this on next reload")
        return True
    except ImportError as e:
        print(f"[anchor_apply] daemon module not importable: {e}")
        return False
    except Exception as e:
        print(f"[anchor_apply] patch failed: {e}")
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--domain", default=None,
                   help="finance | legal | medical | vc | zenmind | (None=base+tenant only)")
    p.add_argument("--output", type=Path,
                   default=PLUGIN_DIR / ".cache" / "anchors_merged.json")
    p.add_argument("--patch-daemon", action="store_true",
                   help="Try to monkey-patch live daemon (requires daemon process)")
    args = p.parse_args()

    if args.patch_daemon:
        ok = patch_daemon_anchors()
        sys.exit(0 if ok else 1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_merged_to_file(args.domain, args.output)


if __name__ == "__main__":
    main()
