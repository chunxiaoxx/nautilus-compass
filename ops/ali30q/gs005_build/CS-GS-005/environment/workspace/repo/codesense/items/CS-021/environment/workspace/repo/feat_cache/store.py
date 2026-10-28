"""feat_cache.store — 特征缓存读写(坑版:非原子写待修)。"""
from __future__ import annotations

import pickle
from pathlib import Path


def cache_path(root: str) -> Path:
    return Path(root) / "features.pkl"


def save_cache(root: str, obj: object) -> None:
    """保存缓存(§2 必须原子落盘;§3 失败保留旧缓存并抛原始异常)。

    坑:直接以目标路径打开写入——序列化中途失败/进程被杀即留半截文件。
    """
    with open(cache_path(root), "wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_cache(root: str) -> object:
    """加载缓存;文件不存在返回 None。"""
    p = cache_path(root)
    if not p.exists():
        return None
    with open(p, "rb") as f:
        return pickle.load(f)
