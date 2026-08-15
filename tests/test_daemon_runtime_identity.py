from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from daemon import _runtime_identity_payload


def test_runtime_identity_payload_binds_running_process_to_source() -> None:
    payload = _runtime_identity_payload()

    assert payload["ok"] is True
    assert payload["pong"] is True
    assert payload["pid"] == os.getpid()
    assert Path(payload["python_executable"]).resolve() == Path(sys.executable).resolve()
    assert Path(payload["source_root"]).resolve() == Path(__file__).parents[1].resolve()
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", payload["daemon_hash"])
