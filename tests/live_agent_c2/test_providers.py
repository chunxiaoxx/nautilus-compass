from __future__ import annotations

import json
import os
import sys

import pytest

from benchmarks.live_agent_c2.providers import (
    OpenAICompatibleAdapter,
    ProviderCallError,
    ProviderCommand,
    SubprocessCliAdapter,
    build_claude_command,
    build_codex_command,
    build_kimi_command,
    parse_claude_json,
    parse_codex_jsonl,
    parse_kimi_jsonl,
    parse_openai_compatible_json,
)
from benchmarks.live_agent_c2.schema import provider_from_mapping


def identity(provider_id="test_provider", model_id="test-model"):
    return provider_from_mapping(
        {
            "provider_id": provider_id,
            "model_id": model_id,
            "adapter_kind": "cli",
            "adapter_version": "1.0.0",
        }
    )


def test_subprocess_adapter_uses_stdin_isolated_cwd_and_structured_usage():
    script = (
        "import json, pathlib, sys; "
        "prompt=sys.stdin.read(); "
        "assert prompt == 'return only 42'; "
        "assert not (pathlib.Path.cwd()/'.git').exists(); "
        "print(json.dumps({'type':'result','result':'42','usage':"
        "{'input_tokens':3,'output_tokens':1},'total_cost_usd':0.002}))"
    )

    def command(_prompt, _workspace):
        return ProviderCommand((sys.executable, "-c", script), "return only 42")

    adapter = SubprocessCliAdapter(
        identity=identity(),
        command_builder=command,
        output_parser=parse_claude_json,
        tool_isolation="disabled",
    )
    result = adapter.invoke("return only 42", timeout_seconds=10)

    assert adapter.admissible is True
    assert result.output_text == "42"
    assert result.input_tokens == 3
    assert result.output_tokens == 1
    assert result.estimated_cost_usd == 0.002
    assert result.latency_ms >= 0
    assert result.provider_identity == identity()


def test_provider_errors_never_echo_secret_stdout_stderr_or_command(monkeypatch):
    secret = "C2_TEST_SECRET_DO_NOT_ECHO"
    monkeypatch.setenv("C2_TEST_SECRET", secret)
    script = (
        "import os, sys; "
        "print(os.environ['C2_TEST_SECRET']); "
        "print(os.environ['C2_TEST_SECRET'], file=sys.stderr); "
        "raise SystemExit(7)"
    )
    adapter = SubprocessCliAdapter(
        identity=identity(),
        command_builder=lambda _prompt, _workspace: ProviderCommand(
            (sys.executable, "-c", script, secret), None
        ),
        output_parser=parse_claude_json,
        tool_isolation="disabled",
    )

    with pytest.raises(ProviderCallError) as captured:
        adapter.invoke("safe prompt", timeout_seconds=10)

    assert captured.value.reason_code == "provider_nonzero_exit"
    assert secret not in str(captured.value)
    assert secret not in repr(captured.value)


def test_timeout_oversize_and_missing_usage_fail_closed():
    sleeping = SubprocessCliAdapter(
        identity=identity(),
        command_builder=lambda _prompt, _workspace: ProviderCommand(
            (sys.executable, "-c", "import time; time.sleep(5)"), None
        ),
        output_parser=parse_claude_json,
        tool_isolation="disabled",
    )
    with pytest.raises(ProviderCallError, match="provider_timeout"):
        sleeping.invoke("safe", timeout_seconds=0.05)

    oversized = SubprocessCliAdapter(
        identity=identity(),
        command_builder=lambda _prompt, _workspace: ProviderCommand(
            (sys.executable, "-c", "print('x'*5000)"), None
        ),
        output_parser=parse_claude_json,
        tool_isolation="disabled",
        max_output_bytes=1024,
    )
    with pytest.raises(ProviderCallError, match="provider_output_oversize"):
        oversized.invoke("safe", timeout_seconds=10)

    missing_usage = json.dumps({"type": "result", "result": "42"})
    with pytest.raises(ProviderCallError, match="provider_usage_missing"):
        parse_claude_json(missing_usage)


def test_codex_parser_extracts_last_message_and_turn_usage():
    encoded = "\n".join(
        [
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "first"},
                }
            ),
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "42"},
                }
            ),
            json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {"input_tokens": 11, "output_tokens": 2},
                }
            ),
        ]
    )

    parsed = parse_codex_jsonl(encoded)

    assert parsed.output_text == "42"
    assert parsed.input_tokens == 11
    assert parsed.output_tokens == 2
    assert parsed.estimated_cost_usd is None


def test_real_cli_command_builders_preserve_isolation_boundaries(tmp_path):
    claude = build_claude_command("claude-fable-5", "prompt", tmp_path)
    codex = build_codex_command("gpt-5-codex", "prompt", tmp_path)
    kimi = build_kimi_command("kimi-k2", "prompt", tmp_path)

    assert claude.stdin_text == "prompt"
    assert "--safe-mode" in claude.argv
    assert "--tools" in claude.argv and "" in claude.argv
    assert "--no-session-persistence" in claude.argv
    assert '{"mcpServers":{}}' in claude.argv
    assert "--max-budget-usd" in claude.argv
    assert "--system-prompt" in claude.argv
    assert "prompt" not in claude.argv

    assert codex.stdin_text == "prompt"
    assert "--sandbox" in codex.argv and "read-only" in codex.argv
    assert "--ephemeral" in codex.argv
    assert "--ignore-user-config" in codex.argv
    assert "prompt" not in codex.argv

    assert kimi.stdin_text is None
    assert "--output-format" in kimi.argv and "stream-json" in kimi.argv
    assert "--skills-dir" in kimi.argv


def test_unverified_tool_isolation_is_pilot_only():
    adapter = SubprocessCliAdapter(
        identity=identity(provider_id="kimi"),
        command_builder=lambda _prompt, _workspace: ProviderCommand(
            (sys.executable, "-c", "print('{}')"), None
        ),
        output_parser=parse_claude_json,
        tool_isolation="unverified",
    )

    assert adapter.admissible is False


def test_kimi_parser_extracts_answer_but_fails_closed_without_usage():
    output = "\n".join(
        [
            json.dumps({"role": "assistant", "content": "42"}),
            json.dumps(
                {
                    "role": "meta",
                    "type": "session.resume_hint",
                    "session_id": "redacted-runtime-id",
                }
            ),
        ]
    )
    with pytest.raises(ProviderCallError, match="provider_usage_missing"):
        parse_kimi_jsonl(output)


def test_openai_compatible_adapter_uses_environment_secret_and_standard_usage(monkeypatch):
    monkeypatch.setenv("ARK_API_KEY", "unit-test-secret")
    captured = {}

    def transport(url, headers, body, timeout_seconds, max_output_bytes):
        captured.update(
            {
                "url": url,
                "authorization_present": headers.get("Authorization") == "Bearer unit-test-secret",
                "body": json.loads(body),
                "timeout": timeout_seconds,
                "limit": max_output_bytes,
            }
        )
        return json.dumps(
            {
                "choices": [{"message": {"content": "42"}}],
                "usage": {"prompt_tokens": 15, "completion_tokens": 1},
            }
        ).encode("utf-8")

    adapter = OpenAICompatibleAdapter(
        identity=provider_from_mapping(
            {
                "provider_id": "volcengine",
                "model_id": "doubao-seed-2-0-pro-260215",
                "adapter_kind": "openai_compatible",
                "adapter_version": "ark-v3",
            }
        ),
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        credential_env="ARK_API_KEY",
        transport=transport,
        max_tokens=64,
    )

    result = adapter.invoke("Return only 42.", timeout_seconds=30)

    assert adapter.admissible is True
    assert result.output_text == "42"
    assert result.input_tokens == 15
    assert result.output_tokens == 1
    assert result.estimated_cost_usd is None
    assert captured["url"].endswith("/chat/completions")
    assert captured["authorization_present"] is True
    assert captured["body"]["temperature"] == 0
    assert "unit-test-secret" not in repr(adapter)
    assert "unit-test-secret" not in repr(result)


def test_openai_compatible_parser_and_missing_credential_fail_closed(monkeypatch):
    parsed = parse_openai_compatible_json(
        json.dumps(
            {
                "choices": [{"message": {"content": "north"}}],
                "usage": {"input_tokens": 7, "output_tokens": 1},
            }
        )
    )
    assert parsed.output_text == "north"
    assert parsed.input_tokens == 7
    assert parsed.output_tokens == 1

    monkeypatch.delenv("ARK_API_KEY", raising=False)
    adapter = OpenAICompatibleAdapter(
        identity=provider_from_mapping(
            {
                "provider_id": "volcengine",
                "model_id": "doubao-seed-2-0-pro-260215",
                "adapter_kind": "openai_compatible",
                "adapter_version": "ark-v3",
            }
        ),
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        credential_env="ARK_API_KEY",
        transport=lambda *_args: b"{}",
    )
    with pytest.raises(ProviderCallError, match="provider_credential_missing"):
        adapter.invoke("safe", timeout_seconds=10)


def test_adapter_diagnostics_do_not_copy_environment(monkeypatch):
    monkeypatch.setenv("ARK_API_KEY", "sensitive-value")
    adapter = SubprocessCliAdapter(
        identity=identity(),
        command_builder=lambda _prompt, _workspace: ProviderCommand(
            (sys.executable, "-c", "raise SystemExit(3)"), None
        ),
        output_parser=parse_claude_json,
        tool_isolation="disabled",
    )

    with pytest.raises(ProviderCallError) as captured:
        adapter.invoke("safe", timeout_seconds=10)
    assert "sensitive-value" not in str(captured.value)
    assert os.environ["ARK_API_KEY"] == "sensitive-value"
