"""feat_cache.store — 特征缓存读写(金标修复版:tmp+rename 原子落盘)。"""
from __future__ import annotations

import os
import pickle
import tempfile
from pathlib import Path


def cache_path(root: str) -> Path:
    return Path(root) / "features.pkl"


def save_cache(root: str, obj: object) -> None:
    """保存缓存——原子写:先写同目录临时文件,fsync 后 os.replace 落位。

    中断/失败时既有缓存保持完好(§2),原始异常向上抛(§3)。
    """
    root_p = Path(root)
    root_p.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(root_p), suffix=".pkl.tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, cache_path(root))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise  # §3:不吞不换类型


def load_cache(root: str) -> object:
    """加载缓存;文件不存在返回 None。"""
    p = cache_path(root)
    if not p.exists():
        return None
    with open(p, "rb") as f:
        return pickle.load(f)
