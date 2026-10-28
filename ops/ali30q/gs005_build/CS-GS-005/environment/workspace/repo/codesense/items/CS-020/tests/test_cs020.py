"""CS-020 UT:管道任一步失败=整链失败且报错含步骤名与退出码。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

import tempfile  # noqa: E402

from release_pipeline import ReleaseError, run_release  # noqa: E402


def _mk(steps: dict[str, int], artifact: bool = True):
    d = tempfile.mkdtemp()
    d = Path(d)
    for name, rc in steps.items():
        (d / f"{name}.sh").write_text(f"echo {name}\nexit {rc}\n")
    if artifact:
        (d / "artifact.bin").write_text("x")
    return str(d)


def test_ut1_validate_fail_blocks_release(tmp_path=None):
    """UT1[主判定] 校验步 exit2:整链失败,报错含 validate 与退出码,产物不出库。"""
    import shutil
    d = Path(_mk({"export": 0, "validate": 2, "sign": 0}))
    art = d / "artifact.bin"
    art.write_text("x")
    try:
        run_release(str(d))
        raise AssertionError("校验失败未阻断")
    except ReleaseError as e:
        assert "validate" in str(e) and "2" in str(e), f"报错缺步骤/码: {e}"
        assert not (d / "released").exists()
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_ut2_export_fail_reported(tmp_path=None):
    """UT2[主判定] 导出步 exit1:整链失败且报 export=1。"""
    import shutil
    d = Path(_mk({"export": 1, "validate": 0, "sign": 0}))
    try:
        run_release(str(d))
        raise AssertionError("导出失败未阻断")
    except ReleaseError as e:
        assert "export" in str(e) and "1" in str(e)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_ut3_all_pass_returns_zero(tmp_path=None):
    """UT3[回归] 全步成功:返回 0。"""
    import shutil
    d = Path(_mk({"export": 0, "validate": 0, "sign": 0}))
    try:
        assert run_release(str(d)) == 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_ut4_sign_fail_also_caught(tmp_path=None):
    """UT4[边界] 末步失败同样整链失败(报 sign)。"""
    import shutil
    d = Path(_mk({"export": 0, "validate": 0, "sign": 3}))
    try:
        run_release(str(d))
        raise AssertionError("签名失败未阻断")
    except ReleaseError as e:
        assert "sign" in str(e) and "3" in str(e)
    finally:
        shutil.rmtree(d, ignore_errors=True)
