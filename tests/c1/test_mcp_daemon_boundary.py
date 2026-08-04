from __future__ import annotations

import pytest

from mcp_server import _daemon_port_from_environment


def test_daemon_port_defaults_to_existing_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMPASS_DAEMON_PORT", raising=False)

    assert _daemon_port_from_environment() == 9876


def test_daemon_port_can_be_isolated_without_changing_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMPASS_DAEMON_PORT", "43123")

    assert _daemon_port_from_environment() == 43123


@pytest.mark.parametrize("value", ["", "0", "65536", "not-a-port"])
def test_invalid_daemon_port_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    monkeypatch.setenv("COMPASS_DAEMON_PORT", value)

    with pytest.raises(ValueError, match="invalid COMPASS_DAEMON_PORT"):
        _daemon_port_from_environment()
