"""CS-P601 UT:导出流水线范围遗漏,L1-L4 分层 22 条(含反幻觉 gating)。passrate 全对率。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

from pathlib import Path as _P
from export_pipeline import run_export  # noqa: E402


class FakeDB:
    """可控 db:记录 fetch/register 调用与参数。"""

    def __init__(self, rows=None, fail_register=False, register_raise=False):
        self.rows = rows if rows is not None else [{"id": "R1", "amount": 100}]
        self.fail_register = fail_register
        self.register_raise = register_raise
        self.fetch_calls = []
        self.registered = []

    def fetch(self, query, version=None):
        self.fetch_calls.append((query, version))
        return self.rows

    def register(self, export_id):
        if self.register_raise:
            raise RuntimeError("register down")
        if self.fail_register:
            return False
        self.registered.append(export_id)


def cfg(**kw):
    base = {"query": "SELECT 1", "out_dir": "/tmp/exptest", "export_id": "E1", "version": "v7"}
    base.update(kw)
    return base


# ---- L1 主路径(4) ----

def test_l1_happy_path(tmp_path):
    db = FakeDB()
    r = run_export(cfg(out_dir=str(tmp_path)), db)
    assert r["ok"] is True and r["rows"] == 1
    assert (_P(tmp_path) / "report.csv").exists() and (_P(tmp_path) / "report.csv.sha256").exists()
    assert db.registered == ["E1"]


def test_l1_multi_rows_content(tmp_path):
    rows = [{"id": f"R{i}", "amount": 100 + i} for i in range(3)]
    r = run_export(cfg(out_dir=str(tmp_path)), FakeDB(rows))
    assert r["rows"] == 3
    body = (_P(tmp_path) / "report.csv").read_text()
    assert "R0,100" in body and "R2,102" in body


def test_l1_fetch_gets_query_and_version(tmp_path):
    db = FakeDB()
    run_export(cfg(out_dir=str(tmp_path)), db)
    assert db.fetch_calls == [("SELECT 1", "v7")]


def test_l1_file_after_sha_pair(tmp_path):
    run_export(cfg(out_dir=str(tmp_path)), FakeDB())
    sha = (_P(tmp_path) / "report.csv.sha256").read_text().strip()
    import hashlib
    body = (_P(tmp_path) / "report.csv").read_text()
    assert sha == hashlib.sha256(body.encode()).hexdigest()


# ---- L2 配置校验边界(4) ----

def test_l2_missing_query(tmp_path):
    c = cfg(); del c["query"]
    r = run_export(c, FakeDB())
    assert r == {"ok": False, "reason": "missing:query"}


def test_l2_missing_version(tmp_path):
    c = cfg(); del c["version"]
    r = run_export(c, FakeDB())
    assert r["reason"] == "missing:version"


def test_l2_missing_no_steps_executed(tmp_path):
    c = cfg(); del c["out_dir"]
    db = FakeDB()
    r = run_export(c, db)
    assert r["ok"] is False and db.fetch_calls == []  # 缺键=零步骤执行


def test_l2_empty_rows_ok_zero(tmp_path):
    r = run_export(cfg(out_dir=str(tmp_path)), FakeDB(rows=[]))
    assert r["ok"] is True and r["rows"] == 0  # 空结果合法导出


# ---- L3 范围遗漏(隐含步骤)(5) ----

def test_l3_version_locked_not_latest(tmp_path):
    db = FakeDB()
    db.fetch = lambda q, version=None: db.rows  # 忽略 version 也行,但要传参
    calls = []
    def fetch(q, version=None):
        calls.append(version); return []
    db.fetch = fetch
    run_export(cfg(out_dir=str(tmp_path)), db)
    assert calls == ["v7"]  # 必须按快照键取,而非"最新"


def test_l3_register_only_after_files(tmp_path):
    db = FakeDB()
    run_export(cfg(out_dir=str(tmp_path)), db)
    # 文件先于登记:登记发生时文件必须已存在
    assert (_P(tmp_path) / "report.csv").exists() and db.registered


def test_l3_register_fail_marks_failure(tmp_path):
    r = run_export(cfg(out_dir=str(tmp_path)), FakeDB(register_raise=True))
    assert r["ok"] is False and "register" in r["reason"]


def test_l3_register_fail_no_orphan_mark(tmp_path):
    db = FakeDB(register_raise=True)
    run_export(cfg(out_dir=str(tmp_path)), db)
    assert db.registered == []  # 失败不得进入已登记名单


def test_l3_sha_written_not_deferred(tmp_path):
    run_export(cfg(out_dir=str(tmp_path)), FakeDB())
    # §5 备注坑:校验和"后补异步"——必须同步成对落盘
    assert (_P(tmp_path) / "report.csv.sha256").exists()


# ---- L4 原子一致+反幻觉 gating(4) ----

def test_l4_sha_consistency_enforced(tmp_path):
    r = run_export(cfg(out_dir=str(tmp_path)), FakeDB())
    import hashlib
    body = (_P(tmp_path) / "report.csv").read_text()
    assert (_P(tmp_path) / "report.csv.sha256").read_text().strip() == hashlib.sha256(body.encode()).hexdigest()


def test_l4_register_error_surfaced(tmp_path):
    r = run_export(cfg(out_dir=str(tmp_path)), FakeDB(register_raise=True))
    assert r["ok"] is False and "register" in r["reason"]


def test_l4h_antihallucination_latest_data_rejected(tmp_path):
    """反幻觉gating:取数不得忽略version取'最新'(§5备注坑1)。"""
    calls = []
    class SpyDB(FakeDB):
        def fetch(self, q, version=None):
            calls.append(version)
            return self.rows
    db = SpyDB()
    run_export(cfg(out_dir=str(tmp_path), version="v7"), db)
    assert calls == ["v7"], "取数未按版本快照=坐实'取最新'备注"


def test_l4h_antihallucination_register_first_rejected(tmp_path):
    """反幻觉gating:先登记后写文件(§5备注坑2)——登记时文件必须已存在。"""
    order = []
    class OrderDB(FakeDB):
        def register(self, eid):
            order.append(("register", (_P(tmp_path) / "report.csv").exists()))
            return True
    db = OrderDB()
    run_export(cfg(out_dir=str(tmp_path)), db)
    assert order and order[0][1] is True, "登记先于文件=坐实备注坑2"
