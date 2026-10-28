# -*- coding: utf-8 -*-
"""ephem.ingest · 观测数据摄入。

上游地面站推送 ISO 字符串;摄入时转 JD 供管线内部流转。
"""
from astropy.time import Time


def ingest_observation(obs_id: str, t_iso: str, band: str, flux: float) -> dict:
    """摄入一条观测: 转 JD 后交由管线内部流转(见 store.save_observation)。"""
    t = Time(t_iso, scale="utc")
    return {"obs_id": obs_id, "jd": t.jd, "band": band, "flux": flux}
