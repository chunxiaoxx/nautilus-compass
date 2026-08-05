"""Isolated, fail-closed provider boundaries for Compass C2."""

from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from .schema import ProviderIdentity


_ADMISSIBLE_ISOLATION = frozenset({"disabled", "read_only"})
_ALL_ISOLATION = frozenset({"disabled", "read_only", "unverified"})
LIVE_PROVIDER_NAMES = ("minimax-claude", "volcengine-ark")
_MINIMAX_COMMAND_MODEL = "MiniMax-M3[1m]"


class ProviderCallError(RuntimeError):
    """A redacted provider failure carrying only a stable reason code."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


@dataclass(frozen=True, slots=True)
class ProviderCommand:
    argv: tuple[str, ...]
    stdin_text: Optional[str]

    def __post_init__(self) -> None:
        if not isinstance(self.argv, tuple) or not self.argv:
            raise TypeError("argv must be a non-empty tuple")
        if any(not isinstance(value, str) or "\x00" in value for value in self.argv):
            raise ValueError("argv values must be strings without null bytes")
        if not self.argv[0]:
            raise ValueError("argv executable must not be blank")
        if self.stdin_text is not None and not isinstance(self.stdin_text, str):
            raise TypeError("stdin_text must be a string or None")


@dataclass(frozen=True, slots=True)
class ParsedProviderOutput:
    output_text: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Optional[float]
    reported_model_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.output_text, str) or not self.output_text.strip():
            raise ProviderCallError("provider_output_missing")
        _token_count("input_tokens", self.input_tokens)
        _token_count("output_tokens", self.output_tokens)
        if self.estimated_cost_usd is not None:
            _cost(self.estimated_cost_usd)
        if self.reported_model_id is not None and (
            not isinstance(self.reported_model_id, str) or not self.reported_model_id.strip()
        ):
            raise ProviderCallError("provider_identity_missing")


@dataclass(frozen=True, slots=True)
class ProviderCallResult:
    provider_identity: ProviderIdentity
    output_text: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Optional[float]
    latency_ms: int


CommandBuilder = Callable[[str, Path], ProviderCommand]
OutputParser = Callable[[str], ParsedProviderOutput]
HttpTransport = Callable[[str, Mapping[str, str], bytes, float, int], bytes]


class SubprocessCliAdapter:
    """Invoke one CLI in a fresh temporary directory without a shell."""

    def __init__(
        self,
        *,
        identity: ProviderIdentity,
        command_builder: CommandBuilder,
        output_parser: OutputParser,
        tool_isolation: str,
        max_output_bytes: int = 1024 * 1024,
    ) -> None:
        if not isinstance(identity, ProviderIdentity) or identity.adapter_kind != "cli":
            raise TypeError("identity must describe a CLI ProviderIdentity")
        if not callable(command_builder) or not callable(output_parser):
            raise TypeError("command_builder and output_parser must be callable")
        if tool_isolation not in _ALL_ISOLATION:
            raise ValueError("tool_isolation is unsupported")
        if isinstance(max_output_bytes, bool) or not isinstance(max_output_bytes, int):
            raise TypeError("max_output_bytes must be an integer")
        if max_output_bytes < 256:
            raise ValueError("max_output_bytes must be at least 256")
        self.identity = identity
        self._command_builder = command_builder
        self._output_parser = output_parser
        self.tool_isolation = tool_isolation
        self.max_output_bytes = max_output_bytes

    @property
    def admissible(self) -> bool:
        return self.tool_isolation in _ADMISSIBLE_ISOLATION

    def invoke(self, prompt: str, *, timeout_seconds: float) -> ProviderCallResult:
        _validate_invocation(prompt, timeout_seconds)
        with tempfile.TemporaryDirectory(prefix="compass-c2-provider-") as directory:
            workspace = Path(directory)
            command = self._build_command(prompt, workspace)
            started = time.perf_counter()
            completed = _run_command(command, workspace, timeout_seconds)
            latency_ms = max(0, int(round((time.perf_counter() - started) * 1000)))
        encoded = _validated_stdout(completed, self.max_output_bytes)
        try:
            parsed = self._output_parser(encoded)
        except ProviderCallError:
            raise
        except Exception as exc:
            raise ProviderCallError("provider_output_invalid") from exc
        if not isinstance(parsed, ParsedProviderOutput):
            raise ProviderCallError("provider_output_invalid")
        return ProviderCallResult(
            provider_identity=self.identity,
            output_text=parsed.output_text,
            input_tokens=parsed.input_tokens,
            output_tokens=parsed.output_tokens,
            estimated_cost_usd=parsed.estimated_cost_usd,
            latency_ms=latency_ms,
        )

    def _build_command(self, prompt: str, workspace: Path) -> ProviderCommand:
        try:
            command = self._command_builder(prompt, workspace)
        except Exception as exc:
            raise ProviderCallError("provider_configuration_invalid") from exc
        if not isinstance(command, ProviderCommand):
            raise ProviderCallError("provider_configuration_invalid")
        return command


class OpenAICompatibleAdapter:
    """Call one fixed HTTPS chat-completions endpoint using an environment credential."""

    def __init__(
        self,
        *,
        identity: ProviderIdentity,
        base_url: str,
        credential_env: str,
        transport: HttpTransport = None,
        max_tokens: int = 64,
        max_output_bytes: int = 1024 * 1024,
    ) -> None:
        if not isinstance(identity, ProviderIdentity) or identity.adapter_kind != "openai_compatible":
            raise TypeError("identity must describe an openai_compatible ProviderIdentity")
        parsed = urlparse(base_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("base_url must be an HTTPS origin without credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("base_url must not contain query or fragment components")
        if not isinstance(credential_env, str) or not credential_env.isidentifier():
            raise ValueError("credential_env must be a safe environment variable name")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or not 1 <= max_tokens <= 4096:
            raise ValueError("max_tokens must be between 1 and 4096")
        if isinstance(max_output_bytes, bool) or not isinstance(max_output_bytes, int):
            raise TypeError("max_output_bytes must be an integer")
        if max_output_bytes < 256:
            raise ValueError("max_output_bytes must be at least 256")
        self.identity = identity
        self.base_url = base_url.rstrip("/")
        self.credential_env = credential_env
        self.max_tokens = max_tokens
        self.max_output_bytes = max_output_bytes
        self._transport = _urllib_post if transport is None else transport

    @property
    def admissible(self) -> bool:
        return True

    def invoke(self, prompt: str, *, timeout_seconds: float) -> ProviderCallResult:
        _validate_invocation(prompt, timeout_seconds)
        credential = os.environ.get(self.credential_env)
        if not credential:
            raise ProviderCallError("provider_credential_missing")
        body = json.dumps(
            {
                "model": self.identity.model_id,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a benchmark subject. Follow the user task and return only "
                            "the requested value. Do not use tools."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "max_tokens": self.max_tokens,
                "stream": False,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {credential}",
            "Content-Type": "application/json",
        }
        started = time.perf_counter()
        try:
            encoded = self._transport(
                self.base_url + "/chat/completions",
                headers,
                body,
                timeout_seconds,
                self.max_output_bytes,
            )
        except ProviderCallError:
            raise
        except Exception as exc:
            raise ProviderCallError("provider_transport_failed") from exc
        latency_ms = max(0, int(round((time.perf_counter() - started) * 1000)))
        if not isinstance(encoded, bytes) or len(encoded) > self.max_output_bytes:
            raise ProviderCallError("provider_output_oversize")
        try:
            parsed = parse_openai_compatible_json(encoded.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise ProviderCallError("provider_output_invalid") from exc
        if parsed.reported_model_id != self.identity.model_id:
            raise ProviderCallError("provider_identity_mismatch")
        return ProviderCallResult(
            provider_identity=self.identity,
            output_text=parsed.output_text,
            input_tokens=parsed.input_tokens,
            output_tokens=parsed.output_tokens,
            estimated_cost_usd=parsed.estimated_cost_usd,
            latency_ms=latency_ms,
        )


def parse_claude_json(encoded: str) -> ParsedProviderOutput:
    try:
        payload = json.loads(encoded)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ProviderCallError("provider_output_invalid") from exc
    if not isinstance(payload, Mapping):
        raise ProviderCallError("provider_output_invalid")
    if payload.get("is_error") is True or payload.get("subtype") == "error":
        raise ProviderCallError("provider_response_error")
    output_text = payload.get("result")
    usage = payload.get("usage")
    if not isinstance(output_text, str) or not isinstance(usage, Mapping):
        reason = "provider_usage_missing" if not isinstance(usage, Mapping) else "provider_output_missing"
        raise ProviderCallError(reason)
    input_tokens, output_tokens = _usage_tokens(usage)
    cost = payload.get("total_cost_usd")
    if cost is not None:
        cost = _cost(cost)
    model_usage = payload.get("modelUsage")
    reported_model_id = None
    if isinstance(model_usage, Mapping) and len(model_usage) == 1:
        reported_model_id = next(iter(model_usage))
    return ParsedProviderOutput(
        output_text,
        input_tokens,
        output_tokens,
        cost,
        reported_model_id,
    )


def parse_minimax_claude_json(encoded: str) -> ParsedProviderOutput:
    parsed = parse_claude_json(encoded)
    if parsed.reported_model_id != _MINIMAX_COMMAND_MODEL:
        raise ProviderCallError("provider_identity_mismatch")
    return parsed


def parse_codex_jsonl(encoded: str) -> ParsedProviderOutput:
    events = _json_lines(encoded)
    messages: list[str] = []
    usage: Optional[Mapping[str, Any]] = None
    for event in events:
        if event.get("type") == "item.completed":
            item = event.get("item")
            if isinstance(item, Mapping) and item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    messages.append(text)
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), Mapping):
            usage = event["usage"]
    if not messages:
        raise ProviderCallError("provider_output_missing")
    if usage is None:
        raise ProviderCallError("provider_usage_missing")
    input_tokens, output_tokens = _usage_tokens(usage)
    return ParsedProviderOutput(messages[-1], input_tokens, output_tokens, None)


def parse_kimi_jsonl(encoded: str) -> ParsedProviderOutput:
    events = _json_lines(encoded)
    messages = [
        event.get("content")
        for event in events
        if event.get("role") == "assistant" and isinstance(event.get("content"), str)
    ]
    if not messages:
        raise ProviderCallError("provider_output_missing")
    usage = next(
        (event.get("usage") for event in reversed(events) if isinstance(event.get("usage"), Mapping)),
        None,
    )
    if usage is None:
        raise ProviderCallError("provider_usage_missing")
    input_tokens, output_tokens = _usage_tokens(usage)
    return ParsedProviderOutput(messages[-1], input_tokens, output_tokens, None)


def parse_openai_compatible_json(encoded: str) -> ParsedProviderOutput:
    try:
        payload = json.loads(encoded)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ProviderCallError("provider_output_invalid") from exc
    if not isinstance(payload, Mapping):
        raise ProviderCallError("provider_output_invalid")
    choices = payload.get("choices")
    usage = payload.get("usage")
    reported_model_id = payload.get("model")
    if not isinstance(reported_model_id, str) or not reported_model_id.strip():
        raise ProviderCallError("provider_identity_missing")
    if not isinstance(choices, list) or not choices or not isinstance(usage, Mapping):
        reason = "provider_usage_missing" if not isinstance(usage, Mapping) else "provider_output_missing"
        raise ProviderCallError(reason)
    first = choices[0]
    if not isinstance(first, Mapping) or not isinstance(first.get("message"), Mapping):
        raise ProviderCallError("provider_output_missing")
    content = first["message"].get("content")
    if not isinstance(content, str) or not content.strip():
        raise ProviderCallError("provider_output_missing")
    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    return ParsedProviderOutput(
        content,
        _token_count("input_tokens", input_tokens),
        _token_count("output_tokens", output_tokens),
        None,
        reported_model_id,
    )


def build_live_adapters(
    names: Optional[Sequence[str]] = None,
) -> tuple[SubprocessCliAdapter | OpenAICompatibleAdapter, ...]:
    selected = LIVE_PROVIDER_NAMES if names is None else tuple(names)
    if len(selected) != len(set(selected)):
        raise ValueError("providers must not contain duplicates")
    unknown = set(selected) - set(LIVE_PROVIDER_NAMES)
    if unknown:
        raise ValueError(f"unsupported live provider: {', '.join(sorted(unknown))}")
    return tuple(_live_adapter(name) for name in selected)


def _live_adapter(name: str) -> SubprocessCliAdapter | OpenAICompatibleAdapter:
    if name == "minimax-claude":
        identity = ProviderIdentity(
            provider_id="minimax",
            model_id="minimax-m3-1m",
            adapter_kind="cli",
            adapter_version="2.1.220",
        )
        return SubprocessCliAdapter(
            identity=identity,
            command_builder=lambda prompt, workspace: build_claude_command(
                _MINIMAX_COMMAND_MODEL, prompt, workspace
            ),
            output_parser=parse_minimax_claude_json,
            tool_isolation="disabled",
        )
    if name == "volcengine-ark":
        identity = ProviderIdentity(
            provider_id="volcengine",
            model_id="doubao-seed-2-0-pro-260215",
            adapter_kind="openai_compatible",
            adapter_version="ark-v3",
        )
        return OpenAICompatibleAdapter(
            identity=identity,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            credential_env="ARK_API_KEY",
            max_tokens=64,
        )
    raise ValueError("unsupported live provider")


def build_claude_command(model_id: str, prompt: str, workspace: Path) -> ProviderCommand:
    _command_inputs(model_id, prompt, workspace)
    return ProviderCommand(
        (
            "claude",
            "-p",
            "--output-format",
            "json",
            "--model",
            model_id,
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
            "0.03",
            "--system-prompt",
            (
                "You are a benchmark subject. Follow the user task and return only the "
                "requested value. Do not use tools."
            ),
        ),
        prompt,
    )


def build_codex_command(model_id: str, prompt: str, workspace: Path) -> ProviderCommand:
    _command_inputs(model_id, prompt, workspace)
    return ProviderCommand(
        (
            "codex",
            "exec",
            "-",
            "--model",
            model_id,
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--ignore-user-config",
            "--skip-git-repo-check",
            "--json",
            "--color",
            "never",
            "--cd",
            str(workspace),
        ),
        prompt,
    )


def build_kimi_command(model_id: str, prompt: str, workspace: Path) -> ProviderCommand:
    _command_inputs(model_id, prompt, workspace)
    skills_directory = workspace / "empty-skills"
    skills_directory.mkdir()
    return ProviderCommand(
        (
            "kimi",
            "--prompt",
            prompt,
            "--model",
            model_id,
            "--output-format",
            "stream-json",
            "--skills-dir",
            str(skills_directory),
        ),
        None,
    )


def _run_command(
    command: ProviderCommand,
    workspace: Path,
    timeout_seconds: float,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            command.argv,
            cwd=workspace,
            input=b"" if command.stdin_text is None else command.stdin_text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=_provider_environment(),
            timeout=timeout_seconds,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired as exc:
        raise ProviderCallError("provider_timeout") from exc
    except FileNotFoundError as exc:
        raise ProviderCallError("provider_executable_missing") from exc
    except OSError as exc:
        raise ProviderCallError("provider_launch_failed") from exc


def _validated_stdout(
    completed: subprocess.CompletedProcess[bytes], max_output_bytes: int
) -> str:
    stdout = completed.stdout or b""
    stderr = completed.stderr or b""
    if len(stdout) + len(stderr) > max_output_bytes:
        raise ProviderCallError("provider_output_oversize")
    if completed.returncode != 0:
        raise ProviderCallError("provider_nonzero_exit")
    try:
        return stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProviderCallError("provider_output_invalid") from exc


def _provider_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "NO_COLOR": "1",
            "TERM": "dumb",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    return environment


def _urllib_post(
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout_seconds: float,
    max_output_bytes: int,
) -> bytes:
    request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            encoded = response.read(max_output_bytes + 1)
    except urllib.error.HTTPError as exc:
        reason = "provider_http_client_error" if 400 <= exc.code < 500 else "provider_http_server_error"
        raise ProviderCallError(reason) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderCallError("provider_transport_failed") from exc
    if len(encoded) > max_output_bytes:
        raise ProviderCallError("provider_output_oversize")
    return encoded


def _usage_tokens(usage: Mapping[str, Any]) -> tuple[int, int]:
    if "input_tokens" not in usage or "output_tokens" not in usage:
        raise ProviderCallError("provider_usage_missing")
    return _token_count("input_tokens", usage["input_tokens"]), _token_count(
        "output_tokens", usage["output_tokens"]
    )


def _token_count(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProviderCallError("provider_usage_invalid")
    return value


def _cost(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProviderCallError("provider_cost_invalid")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        raise ProviderCallError("provider_cost_invalid")
    return normalized


def _json_lines(encoded: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(encoded, str):
        raise ProviderCallError("provider_output_invalid")
    events: list[Mapping[str, Any]] = []
    try:
        for line in encoded.splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, Mapping):
                raise ProviderCallError("provider_output_invalid")
            events.append(event)
    except json.JSONDecodeError as exc:
        raise ProviderCallError("provider_output_invalid") from exc
    if not events:
        raise ProviderCallError("provider_output_invalid")
    return tuple(events)


def _validate_invocation(prompt: str, timeout_seconds: float) -> None:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-blank string")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
        raise TypeError("timeout_seconds must be a finite positive number")
    if not math.isfinite(float(timeout_seconds)) or not 0 < float(timeout_seconds) <= 600:
        raise ValueError("timeout_seconds must be between 0 and 600")


def _command_inputs(model_id: str, prompt: str, workspace: Path) -> None:
    if not isinstance(model_id, str) or not model_id.strip() or "\x00" in model_id:
        raise ValueError("model_id must be a safe non-blank string")
    if not isinstance(prompt, str) or not prompt.strip() or "\x00" in prompt:
        raise ValueError("prompt must be a safe non-blank string")
    if not isinstance(workspace, Path) or not workspace.is_dir():
        raise ValueError("workspace must be an existing directory")


__all__ = [
    "LIVE_PROVIDER_NAMES",
    "ParsedProviderOutput",
    "OpenAICompatibleAdapter",
    "ProviderCallError",
    "ProviderCallResult",
    "ProviderCommand",
    "SubprocessCliAdapter",
    "build_claude_command",
    "build_codex_command",
    "build_kimi_command",
    "build_live_adapters",
    "parse_claude_json",
    "parse_codex_jsonl",
    "parse_kimi_jsonl",
    "parse_minimax_claude_json",
    "parse_openai_compatible_json",
]
