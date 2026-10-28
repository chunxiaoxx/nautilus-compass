# -*- coding: utf-8 -*-
"""CS-003 判分 UT · Time 高精度 JD 持久化(改一查十·大范围同类改动)。

约定来源: docs/data_policy.md §1-§4。
判分原则: 行为断言(往返漂移数值),不锁实现方式(ISO 字符串/jd1-jd2 双值/
Time 对象传递皆可·等价门)。gating: test_chain_full_lossless。
"""
import json
import subprocess
import sys
from pathlib import Path

from astropy.time import Time
import astropy.units as u

REPO = Path(__file__).resolve().parent.parent / "environment" / "workspace" / "repo"
sys.path.insert(0, str(REPO))

from ephem import store, predict, ingest, format as efmt  # noqa: E402

T_US = "2026-10-15T12:00:00.123456"       # 微秒级样本
T_100NS = "2026-10-15T12:00:00.1234567"   # 0.1μs 级样本(astropy 上限)


def _as_time(v) -> Time:
    """兼容多种返回形态(Time/ISO str/单jd float/dict)。"""
    if isinstance(v, Time):
        return v
    if isinstance(v, str):
        return Time(v, scale="utc")
    if isinstance(v, (int, float)):
        return Time(v, format="jd", scale="utc")
    if isinstance(v, dict):
        if "jd1" in v and "jd2" in v:   # §2 合法载体之二
            return Time(v["jd1"], v["jd2"], format="jd", scale="utc")
        for k in ("start", "t", "t_iso", "start_iso", "start_jd", "jd"):
            if k in v:
                return _as_time(v[k])
    raise AssertionError(f"无法解析时间形态: {type(v)} {str(v)[:80]}")


def _drift_us(a: Time, b: Time) -> float:
    return abs((a - b).to_value("us"))


# ───────────────────── predict(修复点1·双 jd 边界) ─────────────────────
def test_predict_window_lossless():
    """窗口起点经 next_window 后微秒不丢(初始实现 ~33μs 漂移)。"""
    t0 = Time(T_US, scale="utc")
    w = predict.next_window(t0, 92.8)
    start = _as_time(w["start"] if "start" in w else w)
    expect = t0 + 92.8 * 60 * u.s
    assert start.scale == "utc"
    assert _drift_us(start, expect) < 0.1, f"漂移 {_drift_us(start, expect)}μs"


def test_predict_window_value_correct():
    """轨道外推数值正确(时长大口径)。"""
    t0 = Time(T_US, scale="utc")
    w = predict.next_window(t0, 92.8)
    start = _as_time(w["start"] if "start" in w else w)
    assert _drift_us(start, t0 + 92.8 * 60 * u.s) < 1.0


def test_predict_multiple_orbits_no_amplification():
    """多轨道(10 圈)累计不放大精度损失。"""
    t0 = Time(T_US, scale="utc")
    w = predict.next_window(t0, 92.8 * 10)
    start = _as_time(w["start"] if "start" in w else w)
    assert _drift_us(start, t0 + 928 * 60 * u.s) < 0.1


def test_predict_end_after_start():
    w = predict.next_window(Time(T_US, scale="utc"), 92.8)
    keys = [k for k in w.keys() if "end" in k]
    if keys:
        assert _as_time(w[keys[0]]) > _as_time(w["start"] if "start" in w else w)


def test_predict_two_envs_consistent():
    """同输入在 TZ=UTC 子进程与本地一致(行为与运行环境解耦)。"""
    t0 = Time(T_US, scale="utc")
    w_local = predict.next_window(t0, 92.8)
    s_local = _as_time(w_local["start"] if "start" in w_local else w_local).isot
    code = (
        "import sys, os, time, json\n"
        "os.environ['TZ'] = 'UTC'\n"
        "if hasattr(time, 'tzset'):\n"
        "    time.tzset()\n"
        f"sys.path.insert(0, r'{REPO}')\n"
        "from astropy.time import Time\n"
        "from ephem import predict\n"
        "w = predict.next_window(Time('2026-10-15T12:00:00.123456', scale='utc'), 92.8)\n"
        "def _as_time(v):\n"
        "    from astropy.time import Time as T\n"
        "    if isinstance(v, T): return v\n"
        "    if isinstance(v, str): return T(v, scale='utc')\n"
        "    if isinstance(v, (int, float)): return T(v, format='jd', scale='utc')\n"
        "    if isinstance(v, dict):\n"
        "        for k in ('start', 't', 't_iso', 'start_iso', 'start_jd', 'jd'):\n"
        "            if k in v: return _as_time(v[k])\n"
        "    raise ValueError\n"
        "print(json.dumps({'result': _as_time(w['start'] if 'start' in w else w).isot}))"
    )
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-200:]
    assert json.loads(r.stdout)["result"] == s_local


# ───────────────────── ingest(修复点2·单 jd 摄入) ─────────────────────
def test_ingest_lossless():
    """摄入链微秒不丢(初始实现 19.49μs)。"""
    r = ingest.ingest_observation("OBS-X", T_US, "V", 1.0)
    t = _as_time(r)
    assert _drift_us(t, Time(T_US, scale="utc")) < 0.1


def test_ingest_fields_preserved():
    r = ingest.ingest_observation("OBS-Y", T_US, "R", 2.5)
    assert r.get("obs_id") == "OBS-Y" and r.get("band") == "R" and r.get("flux") == 2.5


def test_ingest_100ns_edge():
    """0.1μs 级样本(astropy 表达上限)不劣化。"""
    r = ingest.ingest_observation("OBS-Z", T_100NS, "V", 1.0)
    t = _as_time(r)
    assert _drift_us(t, Time(T_100NS, scale="utc")) < 0.2


def test_ingest_json_roundtrip_lossless():
    """摄入结果经 json 持久化往返无损(模拟落库,§2 持久化边界)。"""
    r = ingest.ingest_observation("OBS-J", T_US, "V", 1.0)
    r2 = json.loads(json.dumps(r, default=str))
    t = _as_time(r2)
    assert _drift_us(t, Time(T_US, scale="utc")) < 0.1


def test_ingest_two_envs_consistent():
    code = (
        "import sys, os, time, json\n"
        "os.environ['TZ'] = 'UTC'\n"
        "if hasattr(time, 'tzset'):\n"
        "    time.tzset()\n"
        f"sys.path.insert(0, r'{REPO}')\n"
        "from ephem import ingest\n"
        "r = ingest.ingest_observation('OBS-X', '2026-10-15T12:00:00.123456', 'V', 1.0)\n"
        "print(json.dumps({'result': r}, default=str))"
    )
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-200:]
    d = json.loads(r.stdout)["result"]
    t = _as_time(d)
    assert _drift_us(t, Time(T_US, scale="utc")) < 0.1


# ───────────────────── store(对照·保持) ─────────────────────
def test_store_roundtrip_lossless(tmp_path):
    """store 已修参照: 存取往返无损(回归保护)。"""
    store._STORE = tmp_path / "_obs.jsonl"
    t = Time(T_US, scale="utc")
    store.save_observation("OBS-S", t, "V", 3.0)
    rows = store.load_observations()
    assert len(rows) == 1
    t_back = Time(rows[0]["t_iso"], scale="utc")
    assert _drift_us(t_back, t) < 0.1


def test_store_keeps_fields(tmp_path):
    store._STORE = tmp_path / "_obs.jsonl"
    store.save_observation("OBS-S2", Time(T_US, scale="utc"), "R", 4.0)
    rows = store.load_observations()
    assert rows[0]["band"] == "R" and rows[0]["flux"] == 4.0


# ───────────────────── format(对照·保持) ─────────────────────
def test_format_stays_compliant():
    out = efmt.render({"obs_id": "O", "t_iso": T_US, "band": "V", "flux": 1.0})
    assert T_US in out


# ───────────────────── 端到端链与 gating ─────────────────────
def test_chain_full_lossless():
    """[gating] 端到端: ingest→(json 持久化)→store→predict 全链无损。"""
    r = ingest.ingest_observation("OBS-C", T_US, "V", 1.0)
    r2 = json.loads(json.dumps(r, default=str))
    t = _as_time(r2)
    w = predict.next_window(t, 92.8)
    start = _as_time(w["start"] if "start" in w else w)
    expect = Time(T_US, scale="utc") + 92.8 * 60 * u.s
    assert _drift_us(start, expect) < 0.5, "端到端链路精度损失超阈"


def test_chain_microsecond_edge():
    """尾数 999999 的边界时刻全链无损(进位敏感)。"""
    edge = "2026-10-15T23:59:59.999999"
    r = ingest.ingest_observation("OBS-E", edge, "V", 1.0)
    t = _as_time(r)
    assert _drift_us(t, Time(edge, scale="utc")) < 0.2


# ───────────────────── 扩量(§2 无损 ISO 的精度位语义) ─────────────────────
def test_ingest_precision7_roundtrip():
    """precision=7 的 ISO 字符串摄入无损(高精度字符串形态)。"""
    t = Time(T_100NS, scale="utc")
    t.precision = 7
    r = ingest.ingest_observation("OBS-P7", t.isot, "V", 1.0)
    t2 = _as_time(r)
    assert _drift_us(t2, t) < 0.2


def test_format_preserves_microseconds():
    """render 输出含微秒位(§2 无损·对照模块回归)。"""
    out = efmt.render({"obs_id": "O", "t_iso": T_US, "band": "V", "flux": 1.0})
    assert "123456" in out


def test_predict_iso_output_microseconds():
    """predict 对外 ISO 接口含微秒位(window_start_iso)。"""
    t0 = Time(T_US, scale="utc")
    s = predict.window_start_iso(t0, 92.8)
    t_back = Time(s, scale="utc")
    assert _drift_us(t_back, t0 + 92.8 * 60 * u.s) < 0.1


def test_ingest_scale_stays_utc():
    r = ingest.ingest_observation("OBS-U", T_US, "V", 1.0)
    assert _as_time(r).scale == "utc"


def test_store_two_entries_independent(tmp_path):
    store._STORE = tmp_path / "_obs.jsonl"
    store.save_observation("A", Time(T_US, scale="utc"), "V", 1.0)
    store.save_observation("B", Time(T_100NS, scale="utc"), "R", 2.0)
    rows = store.load_observations()
    assert len(rows) == 2 and rows[0]["obs_id"] == "A" and rows[1]["obs_id"] == "B"


def test_chain_microsecond_edge_day_rollover():
    """跨日 0.1μs 边界(进位链最深点)。"""
    edge = "2026-10-15T23:59:59.9999999"
    r = ingest.ingest_observation("OBS-E2", edge, "V", 1.0)
    t = _as_time(r)
    # 整数 JD 处浮点精确·阈收紧(0.05μs):宽松阈会让"round 对齐整日"混过
    assert _drift_us(t, Time(edge, scale="utc")) < 0.05


# ───────────────────── catalog 聚合层(CAT-11·515B 第二层) ─────────────────────
from ephem import catalog  # noqa: E402


def test_catalog_mean_lossless():
    """[gating] 微秒级两时刻均值历元无损(单 JD 浮点均值会漂 ~20μs)。"""
    a = {"obs_id": "A", "t_iso": T_US, "band": "V", "flux": 1.0}
    b = {"obs_id": "B", "t_iso": "2026-10-15T12:00:00.173456", "band": "V", "flux": 1.0}
    rec = catalog.mean_epoch([a, b])
    got = _as_time(rec)
    expect = Time(T_US, scale="utc") + 25000 * u.us
    assert _drift_us(got, expect) < 0.1, f"均值历元漂移 {_drift_us(got, expect)}μs"


def test_catalog_empty_not_valid():
    """[gating] 空聚合不得报有效历元(空集≠占位 JD 0/假 ISO)。"""
    try:
        rec = catalog.mean_epoch([])
    except Exception:
        return
    t = None
    try:
        t = _as_time(rec)
    except Exception:
        t = None
    assert t is None, f"空集不得还原为有效历元: {rec}"


def test_catalog_export_no_float_jd(tmp_path):
    """[gating] 汇总落盘不得含裸浮点 JD(§2 贯穿聚合导出)。"""
    a = {"obs_id": "A", "t_iso": T_US, "band": "V", "flux": 1.0}
    dest = tmp_path / "_catalog.json"
    catalog.export_catalog([a], path=dest)
    text = dest.read_text(encoding="utf-8")
    payload = json.loads(text)
    assert "mean_jd" not in payload
    assert "jd" not in payload
    assert "t_iso" in payload
    assert _drift_us(_as_time(payload), Time(T_US, scale="utc")) < 0.1


def test_catalog_span_lossless():
    """微秒级跨度用 Time 差值,单 JD 差换算会漂。"""
    a = {"obs_id": "A", "t_iso": T_US, "band": "V", "flux": 1.0}
    b = {"obs_id": "B", "t_iso": "2026-10-15T12:00:00.173456", "band": "V", "flux": 1.0}
    got = catalog.span_us([a, b])
    assert abs(got - 50000.0) < 1.0, f"跨度 {got}μs 偏离 50000μs"


def test_catalog_mean_two_times_midpoint():
    """日级两时刻均值落在中点(功能正确性,不锁微秒)。"""
    a = {"obs_id": "A", "t_iso": "2026-10-15T00:00:00", "band": "V", "flux": 1.0}
    b = {"obs_id": "B", "t_iso": "2026-10-17T00:00:00", "band": "V", "flux": 1.0}
    rec = catalog.mean_epoch([a, b])
    got = _as_time(rec)
    expect = Time("2026-10-16T00:00:00", scale="utc")
    assert _drift_us(got, expect) < 1.0  # 1μs 宽限,日级算术本不漂


def test_catalog_missing_not_skipped():
    """缺时间戳条目不得静默跳过当全通过。"""
    good = {"obs_id": "A", "t_iso": T_US, "band": "V", "flux": 1.0}
    bad = {"obs_id": "B", "band": "V", "flux": 1.0}
    try:
        rec = catalog.mean_epoch([good, bad])
    except Exception:
        return
    # 若未拒绝,n 必须计入全部输入(不得把缺失当没看见)
    assert rec.get("n") == 2, f"缺时间戳被跳过: {rec}"
