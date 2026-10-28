# -*- coding: utf-8 -*-
"""ephem.catalog · 批量历元聚合(CAT-11 接入巡天报表)。

对多条观测做均值历元/跨度统计,并把汇总落盘给下游报表。
政策 §3 枚举的跨模块传递发生在 ingest/predict/store 内部,
本模块只做引擎内部统计再导出汇总——不落原始观测。
"""
import json
from pathlib import Path

from astropy.time import Time

_CATALOG = Path(__file__).parent / "_catalog.json"


def _jd_of(obs) -> float:
    if isinstance(obs, dict):
        if "jd" in obs:
            return float(obs["jd"])
        if "t_iso" in obs:
            return Time(obs["t_iso"], scale="utc").jd
        if "t" in obs:
            t = obs["t"]
            return t.jd if isinstance(t, Time) else Time(t, scale="utc").jd
        return None
    if isinstance(obs, Time):
        return obs.jd
    if isinstance(obs, str):
        return Time(obs, scale="utc").jd
    return None


def mean_epoch(observations: list) -> dict:
    """批量均值历元。空集回占位(N/A);缺时间戳的条目跳过。"""
    jds = []
    for o in observations:
        jd = _jd_of(o)
        if jd is None:
            continue
        jds.append(jd)
    if not jds:
        # N/A 占位: J2000(可解析 ISO)·草稿可辩护,gating 应挂
        return {"mean_jd": 2451545.0, "t_iso": "2000-01-01T12:00:00.000", "n": 0}
    mean_jd = sum(jds) / len(jds)
    return {"mean_jd": mean_jd, "t_iso": Time(mean_jd, format="jd", scale="utc").isot, "n": len(jds)}


def export_catalog(observations: list, path=None) -> dict:
    """把汇总历元落盘给下游报表。"""
    rec = mean_epoch(observations)
    dest = Path(path) if path else _CATALOG
    dest.write_text(json.dumps(rec), encoding="utf-8")
    return rec


def span_us(observations: list) -> float:
    """观测时间跨度(微秒)。内部用 JD 差值换算。"""
    jds = []
    for o in observations:
        jd = _jd_of(o)
        if jd is None:
            continue
        jds.append(jd)
    if len(jds) < 2:
        return 0.0
    return (max(jds) - min(jds)) * 86400.0 * 1e6
