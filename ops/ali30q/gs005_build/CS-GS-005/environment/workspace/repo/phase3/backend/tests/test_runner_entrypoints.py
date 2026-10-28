"""webhook 入口脚本冒烟 · 验 env→argv 构造正确 + 复用现有 runner main(不重写逻辑)."""
import importlib.util
import os
import sys

import pytest

_BASE = os.path.join(os.path.dirname(__file__), "..", "runner", "platform_soul")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_BASE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_s2_entry_builds_argv_from_env(monkeypatch):
    captured = {}
    # stub 现有 S2 runner main:只截 argv,不真跑飞书
    import services.fde_qc_feedback_runner as r
    monkeypatch.setattr(r, "main", lambda: captured.update(argv=list(sys.argv)))
    monkeypatch.setenv("FDE_BASE_TOKEN", "RGDK_x")
    monkeypatch.setenv("PAIHUO_TABLE_ID", "tbl_paihuo")
    monkeypatch.delenv("DRY_RUN", raising=False)
    monkeypatch.setenv("PLATFORM_BASE", "https://nautilus.social")
    _load("s2_auto_qc").main()
    a = captured["argv"]
    assert a[1:] == ["--base", "https://nautilus.social",
                     "--app-token", "RGDK_x", "--table-id", "tbl_paihuo"]


def test_s2_entry_dry_run_flag(monkeypatch):
    captured = {}
    import services.fde_qc_feedback_runner as r
    monkeypatch.setattr(r, "main", lambda: captured.update(argv=list(sys.argv)))
    monkeypatch.setenv("FDE_BASE_TOKEN", "RGDK_x")
    monkeypatch.setenv("PAIHUO_TABLE_ID", "tbl_paihuo")
    monkeypatch.setenv("DRY_RUN", "1")
    _load("s2_auto_qc").main()
    assert "--dry-run" in captured["argv"]


def test_s3_entry_builds_argv_with_isolated_delivery_base(monkeypatch):
    captured = {}
    import services.fde_delivery_runner as r
    monkeypatch.setattr(r, "main", lambda: captured.update(argv=list(sys.argv)))
    monkeypatch.setenv("FDE_BASE_TOKEN", "RGDK_x")
    monkeypatch.setenv("PAIHUO_TABLE_ID", "tbl_paihuo")
    monkeypatch.delenv("DRY_RUN", raising=False)
    # deliver/settle 用默认(我 Dx2qb 机密隔离)
    monkeypatch.delenv("DELIVER_APP_TOKEN", raising=False)
    _load("s3_delivery_settlement").main()
    a = captured["argv"]
    assert "--assign-app" in a and a[a.index("--assign-app") + 1] == "RGDK_x"
    assert "--deliver-app" in a and a[a.index("--deliver-app") + 1] == "Dx2qb1fjhaJadSs0ZeMc0teVn49"
    assert a[a.index("--settle-table") + 1] == "tblFL7y3DejBQUvm"


def test_s2_entry_missing_required_env_raises(monkeypatch):
    monkeypatch.delenv("FDE_BASE_TOKEN", raising=False)
    monkeypatch.delenv("PAIHUO_TABLE_ID", raising=False)
    with pytest.raises(KeyError):
        _load("s2_auto_qc").main()
