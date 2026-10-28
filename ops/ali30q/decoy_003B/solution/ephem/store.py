# -*- coding: utf-8 -*-
"""ephem.store · 观测数据存取层。

存储约定(docs/data_policy.md §2): 时间戳持久化必须无损。
OBS-772 修复 v2: 初版 isot 只到毫秒(astropy 默认 precision=3)——
持久化统一 precision=7(0.1μs 级)。
"""
import json
from pathlib import Path

from astropy.time import Time

_STORE = Path(__file__).parent / "_obs.jsonl"


def save_observation(obs_id: str, t, band: str, flux: float) -> None:
    """落一条观测。t 接受 Time 对象或 ISO 字符串;持久化 precision=7。"""
    t = Time(t, scale="utc") if not isinstance(t, Time) else t
    t.precision = 7
    rec = {"obs_id": obs_id, "t_iso": t.isot, "band": band, "flux": flux}
    with _STORE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_observations() -> list:
    with _STORE.open("r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
