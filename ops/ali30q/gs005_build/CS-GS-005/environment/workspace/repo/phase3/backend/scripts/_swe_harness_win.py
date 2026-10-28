#!/usr/bin/env python3
"""Windows launcher for SWE-bench 官方 harness(2026-06-19）。

swebench.harness 顶层 import 了 Unix-only `resource`(只用于 setrlimit(RLIMIT_NOFILE)）·
Windows 无该模块 → import 即崩。真测试在 Linux Docker 容器内跑·rlimit 与 Windows 主机无关·
故注入 no-op `resource` stub 即可让 harness 在 Windows 跑(容器执行不受影响）。

用法(swe_docker.run_evaluation 调）:
  python scripts/_swe_harness_win.py --dataset_name ... --predictions_path ... --run_id ... \
      --instance_ids ... --max_workers 1
"""
import sys
import types

if "resource" not in sys.modules:
    try:
        import resource  # noqa: F401
    except ImportError:
        stub = types.ModuleType("resource")
        stub.RLIMIT_NOFILE = 7
        stub.RLIM_INFINITY = -1

        def _noop_setrlimit(*_a, **_k):
            return None

        def _getrlimit(*_a, **_k):
            return (1024, 4096)

        stub.setrlimit = _noop_setrlimit
        stub.getrlimit = _getrlimit
        sys.modules["resource"] = stub

# resource stub 就位后·用 runpy 复用 harness 自己的 argparse + main(__main__ 块）
import runpy  # noqa: E402

if __name__ == "__main__":
    # launcher 的 argv[1:] = harness 参数 → 伪装成直接跑 run_evaluation
    sys.argv = ["swebench.harness.run_evaluation"] + sys.argv[1:]
    runpy.run_module("swebench.harness.run_evaluation", run_name="__main__")
