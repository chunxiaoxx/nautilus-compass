# -*- coding: utf-8 -*-
"""ephem.catalog · 批量历元聚合(CAT-11)。

§2/§3 贯穿聚合层: 均值历元不得以单 JD 浮点越持久化边界;
空集不得报有效历元; 缺时间戳不得静默跳过当全通过。
"""
import json
from pathlib import Path

from astropy.time import Time
import astropy.units as u

_CATALOG = Path(__file__).parent / "_catalog.json"


def _to_time(obs) -> Time:
    if isinstance(obs, Time):
        return obs
    if isinstance(obs, str):
        return Time(obs, scale="utc")
    if isinstance(obs, dict):
        if "t_iso" in obs:
            return Time(obs["t_iso"], scale="utc")
        if "jd1" in obs and "jd2" in obs:
            t = Time(0, format="jd", scale="utc")
            t.jd1 = obs["jd1"]
            t.jd2 = obs["jd2"]
            return t
        if "t" in obs:
            return _to_time(obs["t"])
        if "start" in obs:
            return _to_time(obs["start"])
        raise ValueError("observation missing lossless timestamp")
    raise ValueError(f"unsupported observation form: {type(obs)}")


def mean_epoch(observations: list) -> dict:
    """批量均值历元。空集拒绝;缺时间戳拒绝。全程 Time 对象运算。"""
    if not observations:
        raise ValueError("empty catalog has no valid epoch")
    times = Time([_to_time(o) for o in observations])
    mean = times.mean()
    mean.precision = 7
    return {"t_iso": mean.isot, "n": int(times.size)}


def export_catalog(observations: list, path=None) -> dict:
    rec = mean_epoch(observations)
    dest = Path(path) if path else _CATALOG
    dest.write_text(json.dumps({"t_iso": rec["t_iso"], "n": rec["n"]}), encoding="utf-8")
    return rec


def span_us(observations: list) -> float:
    if len(observations) < 2:
        raise ValueError("span requires at least two observations")
    times = [_to_time(o) for o in observations]
    return abs((max(times) - min(times)).to_value(u.us))
