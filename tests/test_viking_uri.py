"""S6 module 2 · viking_uri smoke tests · pure URL parsing."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.viking_uri import (
    parse_uri, make_uri, resolve_to_path, path_to_uri,
    SCHEME, TIER_L0, TIER_L1, TIER_L2,
)


def test_1_parse_basic():
    info = parse_uri("viking://proj-a/session_x.md")
    assert info["project"] == "proj-a"
    assert info["resource"] == "session_x.md"
    assert info["tier"] == TIER_L0
    print("OK 1 parse basic L0")


def test_2_parse_tier_query():
    info = parse_uri("viking://p/r.md?tier=L1")
    assert info["tier"] == TIER_L1
    print("OK 2 parse tier query param")


def test_3_parse_l1_suffix():
    info = parse_uri("viking://p/r.md.l1")
    assert info["tier"] == TIER_L1
    assert info["resource"] == "r.md"
    print("OK 3 parse .l1 suffix")


def test_4_parse_l2_suffix():
    info = parse_uri("viking://p/r.md.l2")
    assert info["tier"] == TIER_L2
    print("OK 4 parse .l2 suffix")


def test_5_parse_invalid_scheme():
    try:
        parse_uri("http://p/r.md")
    except ValueError:
        print("OK 5 invalid scheme rejected")
        return
    raise AssertionError("should have raised")


def test_6_parse_missing_project():
    try:
        parse_uri("viking:///just_resource.md")
    except ValueError:
        print("OK 6 missing project rejected")
        return
    raise AssertionError("should have raised")


def test_7_make_uri_l0():
    uri = make_uri("p", "r.md", tier=TIER_L0)
    assert uri == "viking://p/r.md"
    print("OK 7 make L0 URI")


def test_8_make_uri_l1():
    uri = make_uri("p", "r.md", tier=TIER_L1)
    assert uri == "viking://p/r.md.l1"
    print("OK 8 make L1 URI")


def test_9_make_uri_invalid_tier():
    try:
        make_uri("p", "r.md", tier="L99")
    except ValueError:
        print("OK 9 invalid tier rejected")
        return
    raise AssertionError("should have raised")


def test_10_resolve_to_path_l0():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        path = resolve_to_path("viking://proj/s.md", projects_root=root)
        assert path == root / "proj" / "memory" / "s.md"
    print("OK 10 resolve L0")


def test_11_resolve_to_path_l1():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        path = resolve_to_path("viking://proj/r.md.l1", projects_root=root)
        assert path == root / "proj" / "memory" / "_l1" / "r.md"
    print("OK 11 resolve L1")


def test_12_path_to_uri_roundtrip():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        p = root / "proj-x" / "memory" / "session_test.md"
        uri = path_to_uri(p, projects_root=root)
        assert uri == "viking://proj-x/session_test.md"
    print("OK 12 path → URI roundtrip L0")


def test_13_path_to_uri_l1():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        p = root / "proj" / "memory" / "_l1" / "thread.md"
        uri = path_to_uri(p, projects_root=root)
        assert uri == "viking://proj/thread.md.l1"
    print("OK 13 path → URI L1")


def test_14_path_outside_returns_empty():
    with tempfile.TemporaryDirectory() as t:
        outside = Path(t) / "elsewhere.md"
        assert path_to_uri(outside) == ""
    print("OK 14 path outside returns empty")


if __name__ == "__main__":
    tests = [test_1_parse_basic, test_2_parse_tier_query, test_3_parse_l1_suffix,
             test_4_parse_l2_suffix, test_5_parse_invalid_scheme,
             test_6_parse_missing_project, test_7_make_uri_l0, test_8_make_uri_l1,
             test_9_make_uri_invalid_tier, test_10_resolve_to_path_l0,
             test_11_resolve_to_path_l1, test_12_path_to_uri_roundtrip,
             test_13_path_to_uri_l1, test_14_path_outside_returns_empty]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} viking_uri smoke pass")
