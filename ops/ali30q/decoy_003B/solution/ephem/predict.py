# -*- coding: utf-8 -*-
"""ephem.predict · 星历预报计算。

修复(OBS-772 复盘): 窗口计算全程 Time 对象运算(astropy 内部 jd1/jd2
双值,无损),对外输出 precision=7 的 ISO 字符串——浮点单 jd 不再跨边界。
"""
from astropy.time import Time
import astropy.units as u


def next_window(t0, orbit_minutes: float = 92.8) -> dict:
    """下一个观测窗口: 起点为 t0 起整轨道数后的时刻(Time 对象运算)。"""
    t = t0 if isinstance(t0, Time) else Time(t0, scale="utc")
    start = t + orbit_minutes * 60 * u.s
    end = start + 8 * 60 * u.s
    start.precision = 7
    end.precision = 7
    return {"start": start, "end": end}


def window_start_iso(t0, orbit_minutes: float = 92.8) -> str:
    """对外接口: 窗口起点的 ISO 字符串(precision=7)。"""
    w = next_window(t0, orbit_minutes)
    return w["start"].isot
