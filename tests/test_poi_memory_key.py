from pathlib import Path
from proof.poi_memory_key import derive_memory_key, memory_key_from_path


def test_derive_basic():
    assert derive_memory_key("C--Users-chunx", "session_x.md") == "C--Users-chunx/session_x.md"


def test_derive_normalizes_raw_windows_project():
    # 防御 V5 传未编码路径 C:\Users\chunx
    assert derive_memory_key("C:\\Users\\chunx", "x.md") == "C--Users-chunx/x.md"


def test_derive_strips_filename_dir():
    # filename 只取 basename,防上游误传路径
    assert derive_memory_key("proj", "memory/x.md") == "proj/x.md"


def test_memory_key_from_full_path():
    p = Path.home() / ".claude" / "projects" / "C--Users-chunx" / "memory" / "session_x.md"
    assert memory_key_from_path(p) == "C--Users-chunx/session_x.md"


def test_memory_key_from_path_filename_only_returns_none():
    # 纯文件名无法定位 project → None(boost 侧据此回退 frontmatter)
    assert memory_key_from_path("session_x.md") is None
