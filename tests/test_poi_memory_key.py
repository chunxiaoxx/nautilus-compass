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


def test_memory_key_from_nonstandard_path_returns_none():
    # 无 'memory' 段的路径无法可靠定位 project · 锚定 'memory' 段而非盲取 parts[-3]
    # 防 silent-mislabel(如云端 /var/lib/compass/poi/... 旧逻辑会错标 'poi/...')
    assert memory_key_from_path("/var/lib/compass/poi/cycle-1/ingest_a.md") is None
    assert memory_key_from_path("/a/b/c.md") is None  # 无 'memory' 段


def test_memory_key_anchors_on_memory_segment_not_position():
    # 即使 project 前后还有目录层级,仍锚定 'memory' 段取其前一级
    p = "/home/u/.claude/projects/cycle-59717-auto/memory/session_y.md"
    assert memory_key_from_path(p) == "cycle-59717-auto/session_y.md"


def test_memory_key_memory_as_last_segment_returns_none():
    # 'memory' 是末段(目录路径无文件)→ None
    assert memory_key_from_path("/a/proj/memory") is None
