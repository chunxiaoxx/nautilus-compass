# -*- coding: utf-8 -*-
"""ephem.predict · 星历预报计算。

可见光与射电波段的过境预报。时间基准: UTC。
"""
from astropy.time import Time


def next_window(t0: Time, orbit_minutes: float = 92.8) -> dict:
    """下一个观测窗口: 起点为 t0 起整轨道数后的时刻。

    内部以 JD 数值做轨道外推与窗口比较(引擎口径)。
    """
    start_jd = t0.jd + orbit_minutes / 1440.0
    end_jd = start_jd + 8.0 / 1440.0
    return {"start_jd": start_jd, "end_jd": end_jd}


def window_start_iso(t0: Time, orbit_minutes: float = 92.8) -> str:
    """对外接口: 窗口起点的 ISO 字符串。"""
    w = next_window(t0, orbit_minutes)
    return Time(w["start_jd"], format="jd", scale="utc").isot
