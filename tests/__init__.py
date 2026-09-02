# v3.0.12 · tests 必须是包:`from tests.eval_recall import ...` 依赖此文件。
# 无 __init__.py 时 pytest importmode=prepend 只把 tests/ 本身入 sys.path,
# 包式导入全部 ModuleNotFoundError(2026-09-02 全量测试复活时实证)。
