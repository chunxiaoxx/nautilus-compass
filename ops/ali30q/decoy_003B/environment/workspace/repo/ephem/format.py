# -*- coding: utf-8 -*-
"""ephem.format · 输出格式化(合规对照: 全链 ISO 字符串)。"""
from astropy.time import Time


def render(obs: dict) -> str:
    """观测记录渲染为对外文本。"""
    t = Time(obs["t_iso"], scale="utc") if "t_iso" in obs else Time(obs["jd"], format="jd", scale="utc")
    return f"{obs['obs_id']} {t.isot} {obs['band']} {obs['flux']}"
