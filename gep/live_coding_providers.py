"""Bounded provider transports for the Gate B coding action.

This module only transports one pre-sealed request.  It has no verifier,
promotion, journal, or suite-parsing authority.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse


class LiveCodingError(ValueError):
    """A sealed Gate B request cannot safely execute."""


class ProviderCallError(RuntimeError):
    """A redacted provider problem with a stable reason code."""


@dataclass(frozen=True)
class ProviderResult:
    """Metered output returned by one provider call; no credential is retained."""

    output_text: str
    reported_model_id: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None
    latency_ms: int

    def __post_init__(self) -> None:
        if not isinstance(self.output_text, str) or not self.output_text.strip():
            raise ProviderCallError("provider_output_missing")
        if not isinstance(self.reported_model_id, str) or not self.reported_model_id.strip():
            raise ProviderCallError("provider_identity_missing")
        for name in ("input_tokens", "output_tokens", "latency_ms"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ProviderCallError("provider_usage_invalid")
        if self.estimated_cost_usd is not None:
            _nonnegative_finite(self.estimated_cost_usd, "provider_cost_invalid")


class ProviderClient(Protocol):
    """The only capability needed by the live action adapter."""

    def invoke(self, prompt: str, *, timeout_seconds: int) -> ProviderResult: ...


@dataclass(frozen=True)
class ValueSuite:
    """Parsed immutable input to the bounded live action."""

    raw: dict[str, object]
    suite_id: str
    suite_hash: str
    loop_plan: dict[str, object]
    provider: dict[str, object]
    execution: dict[str, object]
    reuse_contract: dict[str, object]


class OpenAICompatibleProvider:
    """One fixed HTTPS chat-completions client, used only after preflight."""

    def __init__(
        self,
        suite: ValueSuite,
        *,
        environment: Mapping[str, str] | None = None,
        transport: Callable[[str, Mapping[str, str], bytes, int, int], bytes] | None = None,
    ) -> None:
        if suite.provider.get("adapter_kind") != "openai_compatible":
            raise LiveCodingError("provider_adapter_kind_invalid")
        self._suite = suite
        self._environment = os.environ if environment is None else environment
        self._transport = _urllib_post if transport is None else transport
        base_url = str(suite.provider["base_url"])
        parsed = urlparse(base_url)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise LiveCodingError("provider_base_url_invalid")
        self._base_url = base_url.rstrip("/")

    def invoke(self, prompt: str, *, timeout_seconds: int) -> ProviderResult:
        if timeout_seconds != self._suite.execution["timeout_seconds"]:
            raise ProviderCallError("provider_timeout_mismatch")
        credential = self._environment.get(str(self._suite.provider["credential_env"]))
        if not credential:
            raise ProviderCallError("provider_credential_missing")
        body = json.dumps(
            {
                "model": self._suite.provider["model_id"],
                "messages": [
                    {"role": "system", "content": self._suite.execution["system_prompt"]},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "max_completion_tokens": self._suite.execution["max_completion_tokens"],
                "stream": False,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        started = time.perf_counter()
        try:
            raw = self._transport(
                self._base_url + "/chat/completions",
                {"Authorization": f"Bearer {credential}", "Content-Type": "application/json"},
                body,
                timeout_seconds,
                int(self._suite.execution["max_output_bytes"]),
            )
        except ProviderCallError:
            raise
        except TimeoutError as exc:
            raise ProviderCallError("provider_timeout") from exc
        except Exception as exc:
            raise ProviderCallError("provider_transport_failed") from exc
        latency_ms = max(0, int(round((time.perf_counter() - started) * 1000)))
        return _parse_openai_response(raw, latency_ms)


class ClaudeCliProvider:
    """Run one configured GLM-backed Claude CLI turn without tools or persistence."""

    def __init__(
        self,
        suite: ValueSuite,
        *,
        environment: Mapping[str, str] | None = None,
        runner: Callable[..., subprocess.CompletedProcess[bytes]] | None = None,
    ) -> None:
        if suite.provider.get("adapter_kind") != "claude_cli":
            raise LiveCodingError("provider_adapter_kind_invalid")
        self._suite = suite
        self._environment = os.environ if environment is None else environment
        self._runner = subprocess.run if runner is None else runner

    def invoke(self, prompt: str, *, timeout_seconds: int) -> ProviderResult:
        if timeout_seconds != self._suite.execution["timeout_seconds"]:
            raise ProviderCallError("provider_timeout_mismatch")
        command = str(self._suite.provider["command"])
        if shutil.which(command) is None and not Path(command).is_file():
            raise ProviderCallError("provider_executable_missing")
        argv = _claude_command(self._suite)
        try:
            with tempfile.TemporaryDirectory(prefix="compass-gate-b-") as workspace:
                started = time.perf_counter()
                completed = self._runner(
                    argv,
                    cwd=workspace,
                    input=prompt.encode("utf-8"),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    env=_claude_environment(self._environment),
                    timeout=timeout_seconds,
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                latency_ms = max(0, int(round((time.perf_counter() - started) * 1000)))
        except subprocess.TimeoutExpired as exc:
            raise ProviderCallError("provider_timeout") from exc
        except FileNotFoundError as exc:
            raise ProviderCallError("provider_executable_missing") from exc
        except OSError as exc:
            raise ProviderCallError("provider_launch_failed") from exc
        stdout = completed.stdout or b""
        stderr = completed.stderr or b""
        if len(stdout) + len(stderr) > self._suite.execution["max_output_bytes"]:
            raise ProviderCallError("provider_output_too_large")
        if completed.returncode != 0:
            raise ProviderCallError("provider_nonzero_exit")
        return _parse_claude_response(stdout, latency_ms)


def _parse_openai_response(raw: bytes, latency_ms: int) -> ProviderResult:
    try:
        if len(raw) > 1024 * 1024:
            raise ValueError("response too large")
        value = json.loads(raw)
        choice = value["choices"][0]
        output_text = choice["message"]["content"]
        usage = value["usage"]
        return ProviderResult(
            output_text=output_text,
            reported_model_id=value["model"],
            input_tokens=usage["prompt_tokens"],
            output_tokens=usage["completion_tokens"],
            estimated_cost_usd=None,
            latency_ms=latency_ms,
        )
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ProviderCallError("provider_output_invalid") from exc


def _claude_command(suite: ValueSuite) -> list[str]:
    return [
        str(suite.provider["command"]),
        "-p",
        "--output-format",
        "json",
        "--model",
        str(suite.provider["command_model"]),
        "--safe-mode",
        "--tools",
        "",
        "--strict-mcp-config",
        "--mcp-config",
        '{"mcpServers":{}}',
        "--disable-slash-commands",
        "--no-session-persistence",
        "--permission-mode",
        "plan",
        "--max-budget-usd",
        str(suite.execution["max_total_cost_usd"]),
        "--effort",
        "low",
        "--system-prompt",
        str(suite.execution["system_prompt"]),
    ]


def _claude_environment(environment: Mapping[str, str]) -> dict[str, str]:
    allowed = {
        "ALL_PROXY",
        "APPDATA",
        "COMSPEC",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "LOCALAPPDATA",
        "NODE_EXTRA_CA_CERTS",
        "NO_PROXY",
        "OS",
        "PATH",
        "PATHEXT",
        "PROGRAMDATA",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMW6432",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "WINDIR",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CONFIG_DIR",
    }
    return {key: value for key, value in environment.items() if key.upper() in allowed}


def _parse_claude_response(raw: bytes, latency_ms: int) -> ProviderResult:
    try:
        value = json.loads(raw)
        if not isinstance(value, Mapping) or value.get("is_error") is True:
            raise ValueError("provider error response")
        usage = value["usage"]
        model_usage = value["modelUsage"]
        if not isinstance(usage, Mapping) or not isinstance(model_usage, Mapping):
            raise ValueError("missing usage")
        if len(model_usage) != 1:
            raise ValueError("ambiguous model usage")
        reported_model_id = next(iter(model_usage))
        return ProviderResult(
            output_text=value["result"],
            reported_model_id=reported_model_id,
            input_tokens=_usage_token(usage, "input_tokens"),
            output_tokens=_usage_token(usage, "output_tokens"),
            estimated_cost_usd=value.get("total_cost_usd"),
            latency_ms=latency_ms,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ProviderCallError("provider_output_invalid") from exc


def _usage_token(usage: Mapping[str, object], key: str) -> int:
    value = usage.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("invalid usage token count")
    return value


def _urllib_post(
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout_seconds: int,
    max_output_bytes: int,
) -> bytes:
    request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_body = response.read(max_output_bytes + 1)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise ProviderCallError("provider_timeout") from exc
        raise ProviderCallError("provider_transport_failed") from exc
    if len(response_body) > max_output_bytes:
        raise ProviderCallError("provider_output_too_large")
    return response_body


def _nonnegative_finite(value: object, reason_code: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise ProviderCallError(reason_code)
