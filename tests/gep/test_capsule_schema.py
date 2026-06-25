import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from gep.capsule_schema import StructuredCapsule, from_content


def test_capsule_to_content_has_boundary_fields():
    c = StructuredCapsule(learning="do X", triggers=["when Y"],
                          env_fingerprint="py3.11", confidence=0.8,
                          when_not_to_use=["if Z"])
    d = c.to_content()
    assert d["learning"] == "do X"          # 向后兼容:裸 learning 键在
    assert d["triggers"] == ["when Y"]
    assert d["env_fingerprint"] == "py3.11"
    assert d["confidence"] == 0.8
    assert d["when_not_to_use"] == ["if Z"]


def test_capsule_defaults():
    c = StructuredCapsule(learning="x")
    assert c.triggers == [] and c.when_not_to_use == [] and c.confidence == 1.0
    assert c.env_fingerprint == ""


def test_capsule_roundtrip():
    c = StructuredCapsule(learning="x", triggers=["t"], when_not_to_use=["n"])
    assert from_content(c.to_content()) == c


def test_capsule_roundtrip_full():
    c = StructuredCapsule(learning="do X", triggers=["a", "b"],
                          env_fingerprint="py3.11", confidence=0.42,
                          when_not_to_use=["c"])
    assert from_content(c.to_content()) == c


def test_from_content_missing_fields_use_defaults():
    # 老消费者/旧裸 learning 行只有 learning 键
    c = from_content({"learning": "legacy bare row"})
    assert c.learning == "legacy bare row"
    assert c.triggers == [] and c.when_not_to_use == []
    assert c.env_fingerprint == "" and c.confidence == 1.0


def test_two_capsules_independent_lists():
    a = StructuredCapsule(learning="a"); b = StructuredCapsule(learning="b")
    a.triggers.append("x")
    assert b.triggers == []                  # 默认 list 不共享(default_factory)
