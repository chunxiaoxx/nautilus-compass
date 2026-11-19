import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.context_capsule import build_capsule, canonical_bytes, sha256_bytes, validate_capsule


def test_capsule_has_required_binding_and_permissions():
    capsule = build_capsule("task-x", "thread-y")
    assert capsule["schema"] == "context-capsule/1"
    assert capsule["project"]["project_id"] == "nautilus-compass"
    assert capsule["project"]["memory_namespace"].startswith("-Users-")
    assert capsule["task"]["task_id"] == "task-x"
    assert capsule["task"]["thread_id"] == "thread-y"
    assert "external-send" in capsule["permissions"]["denied"]
    assert capsule["signature"]["status"] == "not_signed"


def test_capsule_hash_is_recomputable():
    capsule = build_capsule("task-x", "thread-y")
    expected = capsule["integrity"]["sha256"]
    unsigned = dict(capsule)
    unsigned.pop("signature", None)
    unsigned["integrity"] = {"algorithm": "sha256", "status": "computed"}
    assert sha256_bytes(canonical_bytes(unsigned)) == expected


def test_validation_rejects_project_mismatch():
    capsule = build_capsule("task-x", "thread-y")
    capsule["project"]["project_path"] = "/wrong/project"
    result = validate_capsule(capsule)
    assert result["status"] == "not_computable"
    assert "project_path" in result["mismatches"]
