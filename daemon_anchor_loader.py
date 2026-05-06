"""compass v0.9 · platform_anchors layered loader · #6 fusion.

合并 3 层 anchors:
  1. anchors_platform_base.json  · 平台通用 (15 pos + 25 neg)
  2. anchors_<domain>.json       · 行业 (finance/legal/medical/vc/zenmind)
  3. anchors.json                · tenant/user 个人补充

输出: list[positive], list[negative] · 喂给 daemon BGE 索引

调用方式 (在 daemon.py 里):
  from daemon_anchor_loader import load_layered_anchors
  pos, neg = load_layered_anchors(domain="finance", tenant_anchors_path="anchors.json")

使用 base+domain+tenant 三层时:
  · base ∪ domain ∪ tenant_pos → 正样本 (anchor 数变多 · drift 模型更鲁棒)
  · base ∪ domain ∪ tenant_neg → 负样本

去重: 完全相同句子去重 · 否则保留 (允许相似表述加权)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Tuple, Optional

PLUGIN_DIR = Path(__file__).resolve().parent


def _load_json_list(path: Path, key: str) -> list[str]:
    if not path.exists():
        return []
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return list(d.get(key) or [])
    except Exception as e:
        sys.stderr.write(f"[anchor_loader] read {path.name} fail: {e}\n")
        return []


def load_layered_anchors(
    domain: Optional[str] = None,
    tenant_anchors_path: Optional[Path] = None,
    base_path: Optional[Path] = None,
) -> Tuple[list[str], list[str]]:
    """
    Returns (positive_anchors, negative_anchors) as flat de-duped lists.

    Default base_path: ~/.claude/plugins/nautilus-compass/anchors_platform_base.json
    Default tenant: anchors.json (in plugin dir)
    Domain: finance / legal / medical / vc / zenmind / None
    """
    if base_path is None:
        base_path = PLUGIN_DIR / "anchors_platform_base.json"

    pos: list[str] = []
    neg: list[str] = []

    # layer 1: platform_base
    pos.extend(_load_json_list(base_path, "positive_anchors"))
    neg.extend(_load_json_list(base_path, "negative_anchors"))

    # layer 2: domain
    if domain:
        domain_path = PLUGIN_DIR / f"anchors_{domain}.json"
        pos.extend(_load_json_list(domain_path, "positive_anchors"))
        neg.extend(_load_json_list(domain_path, "negative_anchors"))

    # layer 3: tenant/user
    if tenant_anchors_path is None:
        tenant_anchors_path = PLUGIN_DIR / "anchors.json"
    if isinstance(tenant_anchors_path, str):
        tenant_anchors_path = Path(tenant_anchors_path)
    pos.extend(_load_json_list(tenant_anchors_path, "positive_anchors"))
    neg.extend(_load_json_list(tenant_anchors_path, "negative_anchors"))

    # de-dup (preserve order)
    seen_pos = set()
    seen_neg = set()
    pos = [p for p in pos if p and not (p in seen_pos or seen_pos.add(p))]
    neg = [n for n in neg if n and not (n in seen_neg or seen_neg.add(n))]

    return pos, neg


def selftest():
    print("=== layered loader selftest ===\n")

    print("Layer 1 only (platform_base):")
    pos, neg = load_layered_anchors(domain=None, tenant_anchors_path=Path("/nonexistent.json"))
    print(f"  pos={len(pos)} neg={len(neg)}")
    print(f"  sample pos[0]: {pos[0] if pos else 'none'}")
    print(f"  sample neg[0]: {neg[0] if neg else 'none'}")
    print()

    print("Layer 1 + tenant (existing anchors.json):")
    pos, neg = load_layered_anchors(domain=None)
    print(f"  pos={len(pos)} neg={len(neg)}")
    print()

    print("Layer 1 + 2 (vc) + 3 (tenant):")
    pos, neg = load_layered_anchors(domain="vc")
    print(f"  pos={len(pos)} neg={len(neg)}")
    print()

    print("Layer 1 + 2 (zenmind) + 3 (tenant):")
    pos, neg = load_layered_anchors(domain="zenmind")
    print(f"  pos={len(pos)} neg={len(neg)}")


if __name__ == "__main__":
    selftest()
