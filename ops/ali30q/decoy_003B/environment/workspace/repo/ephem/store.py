# -*- coding: utf-8 -*-
"""ephem.store · 观测数据存取层。

存储约定(docs/data_policy.md §2): 时间戳持久化必须无损。
OBS-772 修复记录: ingest 侧发现观测时刻落库后微秒位丢失,已将
save_observation 的时间戳参数与存储格式改为字符串 ISO(无损)。
"""
import json
from pathlib import Path

from astropy.time import Time

_STORE = Path(__file__).parent / "_obs.jsonl"


def save_observation(obs_id: str, jd: float, band: str, flux: float) -> None:
    """落一条观测。OBS-772 后: jd 以 ISO 字符串形式持久化(无损)。"""
    t = Time(jd, format="jd", scale="utc")
    rec = {"obs_id": obs_id, "t_iso": t.isot, "band": band, "flux": flux}
    with _STORE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_observations() -> list:
    with _STORE.open("r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
