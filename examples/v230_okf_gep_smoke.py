"""v2.3.0 OKF + GEP 真实库 smoke — 对真实 compass memory 跑各功能(打磨验证·非单元测试)。

跑: python examples/v230_okf_gep_smoke.py
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from okf.exporter import build_okf_bundle  # noqa: E402
from okf.validator import validate_okf_bundle  # noqa: E402
from gep.poi_rerank import rerank_by_impact  # noqa: E402
from gep.capsule_schema import StructuredCapsule, from_content  # noqa: E402

MEM = os.path.expanduser("~/.claude/projects/C--Users-chunx/memory")


def main():
    print(f"memory_root = {MEM}  exists={os.path.isdir(MEM)}")

    print("\n=== OKF exporter (真实库) ===")
    bundle = build_okf_bundle(MEM)
    edges = sum(len(v) for v in bundle["link_graph"].values())
    print(f"concepts={len(bundle['concepts'])} link_edges={edges} backlinks={len(bundle['backlinks'])}")

    print("\n=== OKF validator (真实库) ===")
    errs = validate_okf_bundle(bundle)
    print(f"total errors={len(errs)}")
    names = {c["name"] for c in bundle["concepts"]}
    dangling = sorted({t for ts in bundle["link_graph"].values() for t in ts if t not in names})
    no_type = [c["name"] for c in bundle["concepts"] if not c.get("type")]
    asym = [e for e in errs if "backlink" in e.lower() or "对称" in e]
    print(f"  distinct dangling targets={len(dangling)} sample={dangling[:6]}")
    print(f"  concepts missing type={len(no_type)} sample={no_type[:5]}")
    print(f"  backlink-asymmetry errors={len(asym)}")
    # dangling 根因:是 [[name]] 指向库外/MEMORY.md 索引项,还是 name 口径不一致?
    mem_md_present = any(c["name"] == "MEMORY" or c["name"].upper() == "MEMORY" for c in bundle["concepts"])
    print(f"  MEMORY.md as concept? {mem_md_present}")

    print("\n=== GEP P3 rerank (真实样例) ===")
    hits = [
        {"item_id": "low", "reward": 1.0, "cumulative_impact": 0.1},
        {"item_id": "high", "reward": 1.0, "cumulative_impact": 0.9},
        {"item_id": "nofield", "reason": "missing impact"},
    ]
    order = [h["item_id"] for h in rerank_by_impact(hits)]
    print(f"  rerank order = {order}  (expect high > low > nofield)")
    print(f"  empty list safe = {rerank_by_impact([]) == []}")

    print("\n=== GEP capsule schema (round-trip) ===")
    c = StructuredCapsule(learning="avoid X", triggers=["when Y"],
                          env_fingerprint="py3.12", confidence=0.8, when_not_to_use=["if Z"])
    content = c.to_content()
    print(f"  to_content keys = {sorted(content.keys())}")
    print(f"  backward-compat learning key = {content.get('learning')!r}")
    print(f"  round-trip ok = {from_content(content) == c}")

    print("\n=== SUMMARY ===")
    print(f"OKF export: {len(bundle['concepts'])} concepts OK | "
          f"validator: {len(errs)} errs ({len(dangling)} dangling, {len(no_type)} no-type, {len(asym)} asym) | "
          f"GEP rerank: {'OK' if order[0] == 'high' else 'FAIL'} | "
          f"capsule round-trip: {'OK' if from_content(content) == c else 'FAIL'}")


if __name__ == "__main__":
    main()
