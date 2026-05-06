"""Tests for v0.9.1 sqlite migration.

Creates a temporary projects/<proj>/memory/ with sample session_*.md ·
runs migrate_to_sqlite.py · verifies sqlite has expected rows.

Run:
  python tests/test_sqlite_migration.py
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))
sys.path.insert(0, str(PLUGIN_DIR / "tools"))


SAMPLE_SESSION_MD = """---
name: 测试 session 蒸馏
description: 用户问 v0.8 跑分进展 · AI 报告 56.6%
type: discovery
concept: trade-off
drift: green
drift_signals: []
agent_type: claude-code
---

# 测试 session 蒸馏

## 上下文
This is a test session.

## 关键发现
- v0.8 final = 56.6%
- Cross-agent federation works
"""

SAMPLE_SESSION_MD_RED = """---
name: 测试 red drift session
description: AI 找错服务器 · 重复无效尝试
type: bugfix
concept: gotcha
drift: red
drift_signals:
  - 找错服务器 cloud 而非 T4
  - 忘记 PEM 文件路径
agent_type: claude-code
---

# 测试 red drift session

## 上下文
AI made multiple errors.
"""


def setup_test_data(tmp_dir: Path) -> Path:
    """Create test projects + memory dirs."""
    projects_dir = tmp_dir / "projects"
    proj1 = projects_dir / "test_project_1"
    proj2 = projects_dir / "test_project_2"
    (proj1 / "memory").mkdir(parents=True)
    (proj2 / "memory").mkdir(parents=True)

    (proj1 / "memory" / "session_20260505-1000_test1.md").write_text(SAMPLE_SESSION_MD, encoding="utf-8")
    (proj1 / "memory" / "session_20260505-1100_test2.md").write_text(SAMPLE_SESSION_MD_RED, encoding="utf-8")
    (proj2 / "memory" / "session_20260505-1200_test3.md").write_text(SAMPLE_SESSION_MD, encoding="utf-8")
    return projects_dir


def test_parse_frontmatter():
    """parse_frontmatter extracts fields correctly."""
    from migrate_to_sqlite import parse_frontmatter
    fm, body = parse_frontmatter(SAMPLE_SESSION_MD)
    assert fm["name"] == "测试 session 蒸馏", f"got {fm['name']!r}"
    assert fm["type"] == "discovery"
    assert fm["concept"] == "trade-off"
    assert fm["drift"] == "green"
    assert fm["drift_signals"] == []
    assert "测试 session 蒸馏" in body
    print(f"  [PASS] frontmatter parsed (green · empty signals)")


def test_parse_frontmatter_with_signals():
    """drift_signals as YAML list."""
    from migrate_to_sqlite import parse_frontmatter
    fm, body = parse_frontmatter(SAMPLE_SESSION_MD_RED)
    assert fm["drift"] == "red"
    assert len(fm["drift_signals"]) == 2
    assert "找错服务器" in fm["drift_signals"][0]
    assert "PEM" in fm["drift_signals"][1]
    print(f"  [PASS] drift_signals YAML list parsed · {fm['drift_signals']}")


def test_migration_dry_run():
    """Dry run doesn't write to db · just lists."""
    from migrate_to_sqlite import load_session_files, gen_obs_id

    with tempfile.TemporaryDirectory() as tmp:
        projects_dir = setup_test_data(Path(tmp))

        files = list(load_session_files(projects_dir))
        assert len(files) == 3, f"expected 3 files · got {len(files)}"

        # obs_id should be deterministic
        for project, fp in files:
            o1 = gen_obs_id(fp)
            o2 = gen_obs_id(fp)
            assert o1 == o2, "obs_id should be deterministic"
            assert o1.startswith("ob_")
        print(f"  [PASS] dry run · {len(files)} files found · obs_id deterministic")


def test_migration_full():
    """Full migration creates rows · verifies schema."""
    from migrate_to_sqlite import init_schema, migrate_one, db, load_session_files

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        projects_dir = setup_test_data(tmp)
        db_path = tmp / "test_compass.db"

        init_schema(db_path)
        files = list(load_session_files(projects_dir))

        with db(db_path) as conn:
            results = []
            for project, fp in files:
                r = migrate_one(conn, fp, project, "u_test_user", "cn-shanghai")
                results.append(r)
            conn.commit()

        with db(db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            green = conn.execute("SELECT COUNT(*) FROM observations WHERE drift = 'green'").fetchone()[0]
            red = conn.execute("SELECT COUNT(*) FROM observations WHERE drift = 'red'").fetchone()[0]
            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            agents = conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]

        assert total == 3, f"expected 3 obs · got {total}"
        assert green == 2, f"expected 2 green · got {green}"
        assert red == 1, f"expected 1 red · got {red}"
        assert users == 1, f"expected 1 user · got {users}"
        assert agents == 1, f"expected 1 agent (claude-code) · got {agents}"
        print(f"  [PASS] migration · 3 obs (2 green · 1 red) · 1 user · 1 agent")


def test_migration_idempotent():
    """Re-running migration on same data · no duplicates."""
    from migrate_to_sqlite import init_schema, migrate_one, db, load_session_files

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        projects_dir = setup_test_data(tmp)
        db_path = tmp / "test_compass.db"

        init_schema(db_path)

        # First migration
        with db(db_path) as conn:
            for project, fp in load_session_files(projects_dir):
                migrate_one(conn, fp, project, "u_test_user", "cn-shanghai")
            conn.commit()
            n1 = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]

        # Second migration (same data)
        with db(db_path) as conn:
            for project, fp in load_session_files(projects_dir):
                migrate_one(conn, fp, project, "u_test_user", "cn-shanghai")
            conn.commit()
            n2 = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]

        assert n1 == n2 == 3, f"idempotent broken · {n1} → {n2}"
        print(f"  [PASS] idempotent · 3 → 3 (re-run safe)")


def test_migration_drift_signals_preserved():
    """drift_signals are stored as JSON · retrievable."""
    from migrate_to_sqlite import init_schema, migrate_one, db, load_session_files

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        projects_dir = setup_test_data(tmp)
        db_path = tmp / "test_compass.db"

        init_schema(db_path)
        with db(db_path) as conn:
            for project, fp in load_session_files(projects_dir):
                migrate_one(conn, fp, project, "u_test_user", "cn-shanghai")
            conn.commit()

        with db(db_path) as conn:
            row = conn.execute("SELECT drift_signals FROM observations WHERE drift = 'red'").fetchone()
            signals = json.loads(row[0])

        assert len(signals) == 2
        assert "找错服务器" in signals[0]
        print(f"  [PASS] drift_signals preserved · {signals}")


def run_all():
    tests = [
        test_parse_frontmatter,
        test_parse_frontmatter_with_signals,
        test_migration_dry_run,
        test_migration_full,
        test_migration_idempotent,
        test_migration_drift_signals_preserved,
    ]
    print("=== compass v0.9.1 sqlite migration tests ===\n")
    failed = 0
    for t in tests:
        print(f"[{t.__name__}]")
        try:
            t()
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  [ERROR] {type(e).__name__}: {e}")
            failed += 1
        print()
    print(f"=== {len(tests) - failed}/{len(tests)} passed ===")
    return failed


if __name__ == "__main__":
    sys.exit(run_all())
