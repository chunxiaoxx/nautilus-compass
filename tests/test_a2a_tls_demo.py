"""TLS A2A demo smoke · v1.0 (Task #55).

Black-box subprocess test: run examples/a2a_tls_demo.py end-to-end,
assert exit 0 and the PROOF line appears with (tls) + wrote≥1 + read≥1.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
DEMO = PLUGIN_ROOT / "examples" / "a2a_tls_demo.py"


def test_a2a_tls_demo_end_to_end():
    """Full mTLS A2A demo exits 0 and prints the expected PROOF line."""
    r = subprocess.run(
        [sys.executable, str(DEMO), "--quiet"],
        capture_output=True, timeout=45,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    stdout = r.stdout.decode("utf-8", errors="replace")
    stderr = r.stderr.decode("utf-8", errors="replace")
    assert r.returncode == 0, (
        f"demo exited {r.returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
    # PROOF line shape is asserted because CHANGELOG / README may point at it
    # as evidence that mTLS actually worked end-to-end.
    assert "PROOF" in stdout
    assert "(tls)" in stdout        # server banner bubbled through
    assert "over mTLS" in stdout     # client path was TLS + client cert
    assert "wrote=" in stdout


def test_a2a_tls_demo_verbose_path_works():
    """Non-quiet mode should still exit 0 · guards against log-format churn
    accidentally crashing the demo (it does a lot of print flushing)."""
    r = subprocess.run(
        [sys.executable, str(DEMO)],
        capture_output=True, timeout=45,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    assert r.returncode == 0, r.stderr.decode("utf-8", errors="replace")
    out = r.stdout.decode("utf-8", errors="replace")
    assert "[observer] connected over mTLS" in out
    assert "[reader]" in out
    assert "PROOF" in out
