"""S_GBrain modules 3+4 · skill_evaluator + skill_cron_emitter smoke."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills_pkg.skill_evaluator import run_smoke, evaluate
from skills_pkg.skill_cron_emitter import (
    validate_crontab, emit_cron_script, emit_crontab_line, emit_for_skill,
)


def _scaffold_skill(skills_root: Path, name: str, status: str = "codified",
                    smoke_body: str = "if __name__ == '__main__':\n    print('OK')\n",
                    cron_schedule: str = "null") -> Path:
    d = skills_root / status / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\nstatus: {status}\nhandler_path: handler.py\n"
        f"cron_schedule: {cron_schedule}\nreview_count: 0\n---\n",
        encoding="utf-8",
    )
    (d / "handler.py").write_text("def execute(p, c):\n    return {'ok': True}\n",
                                    encoding="utf-8")
    tests = d / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "test_smoke.py").write_text(smoke_body, encoding="utf-8")
    return d


def test_1_run_smoke_pass():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        d = _scaffold_skill(root, "ok-skill")
        r = run_smoke(d)
        assert r["pass"]
        assert r["returncode"] == 0
    print("OK 1 run_smoke pass")


def test_2_run_smoke_fail():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        d = _scaffold_skill(root, "fail-skill",
                             smoke_body="import sys\nsys.exit(1)\n")
        r = run_smoke(d)
        assert not r["pass"]
        assert r["returncode"] == 1
    print("OK 2 run_smoke fail")


def test_3_run_smoke_timeout():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        d = _scaffold_skill(root, "slow",
                             smoke_body="import time\ntime.sleep(10)\n")
        r = run_smoke(d, walltime_max_sec=1)
        assert not r["pass"]
        assert "timeout" in r["stderr"].lower()
    print("OK 3 run_smoke timeout")


def test_4_run_smoke_no_test_file():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "ghost"
        d.mkdir()
        r = run_smoke(d)
        assert not r["pass"]
        assert "not found" in r["stderr"]
    print("OK 4 no smoke file returns fail")


def test_5_evaluate_bumps_review_count():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        d = _scaffold_skill(root, "rev-test")
        r = evaluate(d, skills_root=root)
        assert r["pass"]
        assert r.get("review_count_new") == 1
    print("OK 5 evaluate bumps review_count")


def test_6_validate_crontab_valid():
    assert validate_crontab("0 9 * * *")
    assert validate_crontab("*/15 * * * *")
    assert validate_crontab("0 0,12 * * 1-5")
    print("OK 6 valid crontab accepted")


def test_7_validate_crontab_invalid():
    assert not validate_crontab("")
    assert not validate_crontab("0 9 * * * extra")
    assert not validate_crontab("0 9 * * * ; rm -rf /")
    assert not validate_crontab("$(whoami) 9 * * *")
    print("OK 7 invalid crontab rejected (injection)")


def test_8_emit_cron_script():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        d = _scaffold_skill(root, "scheduled", cron_schedule="0 9 * * *")
        out_dir = root / "cron"
        script = emit_cron_script(d, "0 9 * * *", output_dir=out_dir)
        assert script is not None
        assert script.exists()
        content = script.read_text(encoding="utf-8")
        assert "0 9 * * *" in content
        assert "set -euo pipefail" in content
    print("OK 8 emit_cron_script writes valid wrapper")


def test_9_emit_crontab_line():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        d = _scaffold_skill(root, "x")
        line = emit_crontab_line(d, "0 9 * * *", output_dir=root / "cron")
        assert "0 9 * * *" in line
        assert "skill_x_cron.sh" in line
    print("OK 9 crontab line format")


def test_10_emit_for_skill_no_schedule():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        d = _scaffold_skill(root, "no-cron", cron_schedule="null")
        r = emit_for_skill(d)
        assert not r["ok"]
    print("OK 10 no schedule declared → skip")


def test_11_emit_for_skill_with_schedule():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        d = _scaffold_skill(root, "daily", cron_schedule="0 9 * * *")
        r = emit_for_skill(d, output_dir=root / "cron")
        assert r["ok"]
        assert "skill_daily_cron.sh" in r["script_path"]
    print("OK 11 emit_for_skill with valid schedule")


if __name__ == "__main__":
    tests = [test_1_run_smoke_pass, test_2_run_smoke_fail, test_3_run_smoke_timeout,
             test_4_run_smoke_no_test_file, test_5_evaluate_bumps_review_count,
             test_6_validate_crontab_valid, test_7_validate_crontab_invalid,
             test_8_emit_cron_script, test_9_emit_crontab_line,
             test_10_emit_for_skill_no_schedule, test_11_emit_for_skill_with_schedule]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} skill_evaluator+cron smoke pass")
