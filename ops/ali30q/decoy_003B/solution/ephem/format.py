# -*- coding: utf-8 -*-
"""ephem.format · 输出格式化。

OBS-772 复盘 v2: 渲染链同样受 astropy isot 默认精度(3 位毫秒)限制——
合规实现必须显式 precision=7 后再输出。
"""
from astropy.time import Time


def render(obs: dict) -> str:
    """观测记录渲染为对外文本(时间戳全精度)。"""
    t = Time(obs["t_iso"], scale="utc") if "t_iso" in obs else Time(obs["jd"], format="jd", scale="utc")
    t.precision = 7
    return f"{obs['obs_id']} {t.isot} {obs['band']} {obs['flux']}"
