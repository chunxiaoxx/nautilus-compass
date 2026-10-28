# -*- coding: utf-8 -*-
"""ephem.ingest · 观测数据摄入。

修复(OBS-772 复盘): 摄入保留完整 Time 对象(precision=7 的 ISO 快照),
单 jd 浮点不再出模块边界。
"""
from astropy.time import Time


def ingest_observation(obs_id: str, t_iso: str, band: str, flux: float) -> dict:
    """摄入一条观测: 时间戳以 precision=7 ISO 快照随记录流转。"""
    t = Time(t_iso, scale="utc")
    t.precision = 7
    return {"obs_id": obs_id, "t_iso": t.isot, "band": band, "flux": flux}
