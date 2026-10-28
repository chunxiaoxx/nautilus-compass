"""CS-021 UT:原子写——中途失败不污染旧缓存,异常原样上抛。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))


class _Boom:
    """序列化到一半失败的对象(首个属性可写、deep 属性触发 PicklingError)。"""

    def __reduce__(self):
        raise TypeError("boom-during-serialize")


def test_ut1_midwrite_failure_keeps_old_cache(tmp_path):
    """UT1[主判定] 序列化中途失败:旧缓存文件完好可加载,无半截污染。"""
    import pickle
    from feat_cache import load_cache, save_cache
    save_cache(str(tmp_path), {"v": 1})
    try:
        save_cache(str(tmp_path), _Boom())
        raise AssertionError("中途失败未上抛")
    except TypeError:
        pass
    # 旧缓存必须完好
    assert load_cache(str(tmp_path)) == {"v": 1}


def test_ut2_exception_type_passthrough(tmp_path):
    """UT2[主判定] 上抛原始异常类型(TypeError),不吞不换。"""
    from feat_cache import save_cache
    try:
        save_cache(str(tmp_path), _Boom())
        raise AssertionError("未上抛")
    except TypeError as e:
        assert "boom" in str(e)


def test_ut3_no_temp_litter(tmp_path):
    """UT3[边界] 失败后目录无 .tmp 残留(仅旧缓存一个 pkl)。"""
    from feat_cache import save_cache
    save_cache(str(tmp_path), {"v": 1})
    try:
        save_cache(str(tmp_path), _Boom())
    except TypeError:
        pass
    pkls = list(Path(tmp_path).glob("*.pkl*"))
    assert len(pkls) == 1 and pkls[0].name == "features.pkl", f"残留: {pkls}"


def test_ut4_success_path_roundtrip(tmp_path):
    """UT4[回归] 成功路径:load 读到新缓存。"""
    from feat_cache import load_cache, save_cache
    save_cache(str(tmp_path), {"v": 2, "big": list(range(1000))})
    got = load_cache(str(tmp_path))
    assert got["v"] == 2 and len(got["big"]) == 1000
