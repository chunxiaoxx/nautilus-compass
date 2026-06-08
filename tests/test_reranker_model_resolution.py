"""TDD for daemon._RERANKER_MODEL resolution (2026-06-07 HF-fallback fix).

Bug: on HF-cache-only hosts the reranker path had no HF-id fallback, so it tried
to load a non-existent ModelScope path and silently fell back to dense order.
Fix mirrors EMBEDDER_MODEL: local ModelScope path if it exists, else HF repo id.

We import daemon in a subprocess with a controlled fake home so the test does not
depend on whether THIS machine happens to have a ModelScope cache.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SNIPPET = "import daemon; print(daemon._RERANKER_MODEL)"


def _run_with_home(home: Path, extra_env=None):
    env = dict(os.environ)
    env["HOME"] = str(home)          # POSIX
    env["USERPROFILE"] = str(home)   # Windows (Path.home() -> expanduser('~'))
    env.pop("ZMM_RERANKER_MODEL", None)
    if extra_env:
        env.update(extra_env)
    p = subprocess.run([sys.executable, "-c", _SNIPPET], cwd=str(ROOT),
                       capture_output=True, text=True, env=env, timeout=120)
    assert p.returncode == 0, f"daemon import failed:\n{p.stderr[-1500:]}"
    return p.stdout.strip().splitlines()[-1].strip()


def test_falls_back_to_hf_id_when_no_modelscope(tmp_path):
    # clean home, no modelscope cache -> must resolve to the HF repo id (the fix)
    assert _run_with_home(tmp_path) == "BAAI/bge-reranker-v2-m3"


def test_prefers_local_modelscope_path_when_present(tmp_path):
    ms = tmp_path / ".cache/modelscope/hub/models/BAAI/bge-reranker-v2-m3"
    ms.mkdir(parents=True)
    got = _run_with_home(tmp_path)
    assert got == str(ms), got


def test_env_override_wins(tmp_path):
    got = _run_with_home(tmp_path, {"ZMM_RERANKER_MODEL": "some/custom-reranker"})
    assert got == "some/custom-reranker"
