# -*- coding: utf-8 -*-
"""lint-report 判据测试(预注册 L1-L5,docs/plans/NARRATIVE_DRIFT_LINT_CHARTER_20261002.md)。

L1 昨晚事故回放必 RED / L2 勘误后必 GREEN / L3 六数字复现 / L4 措辞改动不报红 /
L5 CLI 一条命令端到端。
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "runtime" / "typesafe_jev_cvscreen" / "pack"
REPORT = PACK / "mini_report.md"
ASSERTIONS = PACK / "report.assertions.json"
DATA = PACK / "measure_report.json"
LINT = ROOT / "tools" / "verifypack" / "lint_report.py"


def _run(report: Path):
    """L2-L4 用 in-process(覆盖率);L1/L5 保留真 CLI 子进程(端到端)。"""
    sys.path.insert(0, str(ROOT / "tools"))
    import io
    from contextlib import redirect_stdout
    from verifypack.lint_report import run_lint
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = run_lint(str(report), str(ASSERTIONS), str(DATA))
    return rc, buf.getvalue()


def _run_cli(report: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LINT), "--report", str(report),
         "--assertions", str(ASSERTIONS), "--data", str(DATA)],
        capture_output=True, text=True, encoding="utf-8", timeout=60)


@pytest.fixture(scope="module")
def pre_erratum(tmp_path_factory) -> Path:
    """勘误前版本(git 历史原件)回放到临时文件。"""
    out = tmp_path_factory.mktemp("l1") / "mini_report_pre.md"
    r = subprocess.run(["git", "show", "dda96982:runtime/typesafe_jev_cvscreen/pack/mini_report.md"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0 and "Erratum" not in r.stdout, "勘误前版本回放失败"
    out.write_text(r.stdout, encoding="utf-8")
    return out


def test_L1_pre_erratum_must_be_RED(pre_erratum):
    """昨晚事故回放:divergence 散文臆造类别互换 → D1 必 FAIL,exit=1。"""
    r = _run_cli(pre_erratum)
    assert r.returncode == 1, f"L1 应 RED,实 exit={r.returncode}\n{r.stdout}"
    assert "[FAIL] D1" in r.stdout and "job_hopping" in r.stdout


def test_L2_post_erratum_must_be_GREEN():
    """勘误后 v1.1 现版:同断言全过,exit=0。"""
    rc, out = _run(REPORT)
    assert rc == 0, f"L2 应 GREEN\n{out}"
    assert "[FAIL]" not in out


def test_L3_numbers_recomputed():
    """六数字断言逐条 PASS 且与 measure_report 重导出一致(L2 已含,单列计数)。"""
    rc, out = _run(REPORT)
    for nid in ("N1", "N2", "N3", "N4", "N5", "D1"):
        assert f"[PASS] {nid}" in out, f"{nid} 未过\n{out}"


def test_L4_wording_change_no_false_positive(tmp_path):
    """L4 误报控制:纯措辞替换(不动断言词与数字)不报红。"""
    t = REPORT.read_text(encoding="utf-8")
    t2 = t.replace("the interesting output", "the notable output").replace("good", "fine")
    assert t2 != t
    v = tmp_path / "wording_only.md"
    v.write_text(t2, encoding="utf-8")
    rc, out = _run(v)
    assert rc == 0, f"L4 应 GREEN\n{out}"


def test_L5_cli_end_to_end():
    """L5:python -m verifypack lint 一条命令(模块路径)。"""
    r = subprocess.run(
        [sys.executable, "-m", "verifypack", "lint",
         "--report", str(REPORT), "--assertions", str(ASSERTIONS), "--data", str(DATA)],
        cwd=ROOT / "tools", capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    assert "GREEN" in r.stdout


def test_main_entrypoint_inprocess(capsys):
    """CLI main() 入口 in-process(L5 真子进程之外补覆盖)。"""
    sys.path.insert(0, str(ROOT / "tools"))
    from verifypack.lint_report import main
    rc = main(["--report", str(REPORT), "--assertions", str(ASSERTIONS), "--data", str(DATA)])
    out = capsys.readouterr().out
    assert rc == 0 and "GREEN" in out
    with pytest.raises(KeyError):
        main(["--report", str(REPORT), "--assertions", str(DATA), "--data", str(DATA)])
    # 断言文件结构错 = 配置错误,以异常暴露而非伪装成报告 RED


def test_enum_set_catches_drift_directly():
    """单元:enum_set 核心逻辑(数据值域外词 → FAIL)。"""
    sys.path.insert(0, str(ROOT / "tools"))
    from verifypack.lint_report import check_enum_set
    data = {"divergence_rows": [{"pred": "unclear"}, {"pred": "unclear"}]}
    a = {"id": "X", "kind": "enum_set", "severity": "hard", "source": "#/divergence_rows/*/pred",
         "prose_scope": {"whole": True}, "expect": ["unclear"],
         "vocab_all": ["job_hopping", "lateral_moves", "unclear"]}
    ok_clean, _ = check_enum_set(a, data, "Both rows are unclear abstentions.")
    ok_drift, msg = check_enum_set(a, data, "job_hopping predicted where lateral moves written.")
    assert ok_clean and not ok_drift and "job_hopping" in msg
