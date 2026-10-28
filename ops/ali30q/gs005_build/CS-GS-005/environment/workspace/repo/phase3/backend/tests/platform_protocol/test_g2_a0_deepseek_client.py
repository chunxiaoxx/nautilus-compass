from __future__ import annotations

import hashlib
import json
import socket
from collections.abc import Callable
from copy import deepcopy

import httpx
import pytest
from g2_a0_deepseek_client import (
    RESPONSE_EXAMPLE_JSON,
    DeepSeekClientViolation,
    DeepSeekTransportClientV1,
)

from platform_protocol.g2_a0_model_gate import (
    DeepSeekModelGatePolicyV1,
    canonical_json_bytes,
)

API_KEY = "test-only-placeholder"
PROMPT = (
    "Return json only. Repair the synthetic function without tools or commands. "
    f"Use this exact response example: {RESPONSE_EXAMPLE_JSON}"
)


def canonical_request(**overrides: object) -> bytes:
    body: dict[str, object] = {
        "max_tokens": 4_096,
        "messages": [{"content": PROMPT, "role": "user"}],
        "model": "deepseek-v4-flash-0731",
        "reasoning_effort": "max",
        "response_format": {"type": "json_object"},
        "stream": False,
        "thinking": {"type": "enabled"},
    }
    body.update(overrides)
    return canonical_json_bytes(body)


def candidate_document(**overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "artifact_version": "g2-a0-candidate-v1",
        "claimed_test_scope": ["public_behavior"],
        "language": "python",
        "summary_code": "bounded_repair",
        "unified_diff": "synthetic-diff-marker",
    }
    candidate.update(overrides)
    return candidate


def provider_document(**overrides: object) -> dict[str, object]:
    document: dict[str, object] = {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": json.dumps(
                        candidate_document(),
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                    "reasoning_content": "synthetic-reasoning-marker",
                    "role": "assistant",
                },
            }
        ],
        "created": 1_786_646_400,
        "id": "chatcmpl_synthetic_01",
        "model": "deepseek-v4-flash-0731",
        "object": "chat.completion",
        "system_fingerprint": "fp_synthetic_0731",
        "usage": {
            "completion_tokens": 5,
            "prompt_cache_hit_tokens": 4,
            "prompt_cache_miss_tokens": 6,
            "prompt_tokens": 10,
            "total_tokens": 15,
        },
    }
    document.update(overrides)
    return document


def provider_bytes(document: dict[str, object] | None = None) -> bytes:
    return json.dumps(
        document or provider_document(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def client_for(
    handler: Callable[[httpx.Request], httpx.Response],
) -> DeepSeekTransportClientV1:
    return DeepSeekTransportClientV1(
        policy=DeepSeekModelGatePolicyV1.default(),
        transport=httpx.MockTransport(handler),
    )


def response_handler(
    content: bytes | None = None,
    *,
    status_code: int = 200,
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            content=content or provider_bytes(),
            headers={"content-type": "application/json"},
        )

    return handler


def test_success_uses_one_exact_mocked_request_and_returns_only_approved_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []

    def deny_socket(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError("real network is prohibited")

    monkeypatch.setattr(socket, "socket", deny_socket)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.method == "POST"
        assert str(request.url) == "https://api.deepseek.com/chat/completions"
        assert request.headers["authorization"] == f"Bearer {API_KEY}"
        assert request.headers["content-type"].startswith("application/json")
        assert request.content == canonical_request()
        return httpx.Response(
            200,
            content=provider_bytes(),
            headers={"content-type": "application/json"},
        )

    client = client_for(handler)
    result = client.complete_once(
        canonical_request=canonical_request(),
        api_key=API_KEY,
    )

    assert len(requests) == 1
    assert result.returned_model == "deepseek-v4-flash-0731"
    assert (
        result.reasoning_sha256
        == hashlib.sha256(b"synthetic-reasoning-marker").hexdigest()
    )
    assert (
        result.response_content_sha256
        == hashlib.sha256(
            provider_document()["choices"][0]["message"]["content"].encode()
        ).hexdigest()
    )
    assert (
        result.system_fingerprint_sha256
        == hashlib.sha256(b"fp_synthetic_0731").hexdigest()
    )
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.cache_hit_input_tokens == 4
    assert result.cache_miss_input_tokens == 6
    assert result.calculated_cost_micros_cny == 17
    assert result.provider_call_count == 1
    assert result.candidate.artifact_version == "g2-a0-candidate-v1"
    assert result.candidate.unified_diff == "synthetic-diff-marker"
    assert API_KEY not in repr(client)
    assert API_KEY not in repr(result)
    assert "synthetic-reasoning-marker" not in repr(result)


def test_client_explicitly_disables_environment_and_redirect_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    real_client = httpx.Client

    def client_spy(*args: object, **kwargs: object) -> httpx.Client:
        captured.update(kwargs)
        return real_client(*args, **kwargs)

    monkeypatch.setattr("g2_a0_deepseek_client.httpx.Client", client_spy)
    monkeypatch.setenv("HTTPS_PROXY", "http://prohibited.invalid:9999")
    client_for(response_handler()).complete_once(
        canonical_request=canonical_request(),
        api_key=API_KEY,
    )

    assert captured["base_url"] == "https://api.deepseek.com"
    assert captured["follow_redirects"] is False
    assert captured["trust_env"] is False
    assert isinstance(captured["timeout"], httpx.Timeout)
    assert captured["transport"].__class__ is httpx.MockTransport


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("model", "deepseek-v4-flash"),
        ("reasoning_effort", "high"),
        ("stream", True),
        ("max_tokens", 4_095),
        ("temperature", 0),
        ("top_p", 1),
        ("presence_penalty", 0),
        ("frequency_penalty", 0),
        ("tools", []),
        ("tool_choice", "none"),
        ("user", "external-account"),
        ("local_path", "C:/prohibited"),
        ("command", "prohibited-command"),
    ),
)
def test_request_policy_widening_is_rejected_before_transport(
    field_name: str,
    bad_value: object,
) -> None:
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, content=provider_bytes())

    with pytest.raises(DeepSeekClientViolation, match="policy_violation"):
        client_for(handler).complete_once(
            canonical_request=canonical_request(**{field_name: bad_value}),
            api_key=API_KEY,
        )
    assert call_count == 0


@pytest.mark.parametrize(
    "case",
    ("missing_thinking", "disabled_thinking", "extra_thinking", "bad_format"),
)
def test_nested_request_policy_is_exact(case: str) -> None:
    body = json.loads(canonical_request())
    if case == "missing_thinking":
        del body["thinking"]
    elif case == "disabled_thinking":
        body["thinking"]["type"] = "disabled"
    elif case == "extra_thinking":
        body["thinking"]["budget"] = 1
    else:
        body["response_format"] = {"type": "text"}

    with pytest.raises(DeepSeekClientViolation, match="policy_violation"):
        client_for(response_handler()).complete_once(
            canonical_request=canonical_json_bytes(body),
            api_key=API_KEY,
        )


@pytest.mark.parametrize(
    "bad_prompt",
    (
        "Return an object only.",
        "Return json only without the approved response example.",
        "x" * 24_577,
    ),
    ids=("missing-json", "missing-example", "over-byte-limit"),
)
def test_prompt_must_be_bounded_json_instruction_with_exact_example(
    bad_prompt: str,
) -> None:
    messages = [{"content": bad_prompt, "role": "user"}]
    with pytest.raises(DeepSeekClientViolation, match="policy_violation"):
        client_for(response_handler()).complete_once(
            canonical_request=canonical_request(messages=messages),
            api_key=API_KEY,
        )


@pytest.mark.parametrize(
    "payload",
    (
        b'{"model":"deepseek-v4-flash-0731","model":"other"}',
        b'{ "model":"deepseek-v4-flash-0731"}',
        b"not-json",
    ),
)
def test_request_must_be_duplicate_free_canonical_json(payload: bytes) -> None:
    with pytest.raises(DeepSeekClientViolation, match="policy_violation"):
        client_for(response_handler()).complete_once(
            canonical_request=payload,
            api_key=API_KEY,
        )


@pytest.mark.parametrize("case", ("oversized_integer", "excessive_depth"))
def test_request_parser_failures_are_fixed_and_never_reach_transport(
    case: str,
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=provider_bytes())

    if case == "oversized_integer":
        payload = canonical_request().replace(
            b'"max_tokens":4096',
            b'"max_tokens":' + (b"9" * 5_000),
            1,
        )
    else:
        payload = b'{"nested":' + (b"[" * 1_100) + b"0" + (b"]" * 1_100) + b"}"

    with pytest.raises(DeepSeekClientViolation, match="policy_violation") as error:
        client_for(handler).complete_once(
            canonical_request=payload,
            api_key=API_KEY,
        )

    assert str(error.value) == "policy_violation"
    assert calls == 0


@pytest.mark.parametrize(
    "status_code",
    (301, 302, 307, 308, 400, 401, 402, 422, 429, 500, 503),
)
def test_http_failure_is_fixed_and_never_retried(status_code: int) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            status_code,
            content=b"API_KEY raw-prompt raw-response raw-reasoning",
            headers={"location": "https://prohibited.invalid"},
        )

    with pytest.raises(DeepSeekClientViolation, match="policy_violation") as error:
        client_for(handler).complete_once(
            canonical_request=canonical_request(),
            api_key=API_KEY,
        )

    assert calls == 1
    assert API_KEY not in str(error.value)
    assert "raw-prompt" not in str(error.value)
    assert "raw-response" not in str(error.value)
    assert "raw-reasoning" not in str(error.value)


def test_timeout_is_redacted_and_never_retried() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout(
            f"{API_KEY} raw-prompt raw-response raw-reasoning",
            request=request,
        )

    with pytest.raises(
        DeepSeekClientViolation, match="provider_call_ambiguous"
    ) as error:
        client_for(handler).complete_once(
            canonical_request=canonical_request(),
            api_key=API_KEY,
        )

    assert calls == 1
    assert str(error.value) == "provider_call_ambiguous"


def test_unexpected_transport_failure_is_redacted_and_never_retried() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise RuntimeError(
            f"{request.headers['authorization']} {request.content.decode('utf-8')}"
        )

    with pytest.raises(
        DeepSeekClientViolation, match="provider_call_ambiguous"
    ) as error:
        client_for(handler).complete_once(
            canonical_request=canonical_request(),
            api_key=API_KEY,
        )

    assert calls == 1
    assert str(error.value) == "provider_call_ambiguous"
    assert API_KEY not in str(error.value)
    assert PROMPT not in str(error.value)


def mutate_response(case: str) -> dict[str, object]:
    document = deepcopy(provider_document())
    choices = document["choices"]
    message = choices[0]["message"]
    if case == "wrong_model":
        document["model"] = "deepseek-v4-flash"
    elif case == "missing_model":
        del document["model"]
    elif case == "missing_fingerprint":
        del document["system_fingerprint"]
    elif case == "empty_fingerprint":
        document["system_fingerprint"] = ""
    elif case == "whitespace_fingerprint":
        document["system_fingerprint"] = " \t"
    elif case == "missing_reasoning":
        del message["reasoning_content"]
    elif case == "empty_reasoning":
        message["reasoning_content"] = ""
    elif case == "whitespace_reasoning":
        message["reasoning_content"] = " \t"
    elif case == "multiple_choices":
        choices.append(deepcopy(choices[0]))
    elif case == "missing_content":
        del message["content"]
    elif case == "bad_finish":
        choices[0]["finish_reason"] = "length"
    elif case == "extra_top":
        document["service_tier"] = "default"
    elif case == "extra_message":
        message["tool_calls"] = []
    else:
        raise AssertionError(case)
    return document


@pytest.mark.parametrize(
    ("case", "reason_code"),
    (
        ("wrong_model", "model_identity_unproven"),
        ("missing_model", "model_identity_unproven"),
        ("missing_fingerprint", "model_identity_unproven"),
        ("empty_fingerprint", "model_identity_unproven"),
        ("whitespace_fingerprint", "model_identity_unproven"),
        ("missing_reasoning", "thinking_evidence_missing"),
        ("empty_reasoning", "thinking_evidence_missing"),
        ("whitespace_reasoning", "thinking_evidence_missing"),
        ("multiple_choices", "structured_output_invalid"),
        ("missing_content", "structured_output_invalid"),
        ("bad_finish", "structured_output_invalid"),
        ("extra_top", "structured_output_invalid"),
        ("extra_message", "structured_output_invalid"),
    ),
)
def test_provider_envelope_is_fail_closed(case: str, reason_code: str) -> None:
    with pytest.raises(DeepSeekClientViolation, match=reason_code):
        client_for(
            response_handler(provider_bytes(mutate_response(case)))
        ).complete_once(
            canonical_request=canonical_request(),
            api_key=API_KEY,
        )


@pytest.mark.parametrize("duplicate_depth", ("top", "candidate"))
def test_provider_json_rejects_duplicate_keys_at_each_boundary(
    duplicate_depth: str,
) -> None:
    if duplicate_depth == "top":
        raw = provider_bytes().replace(
            b'"model":"deepseek-v4-flash-0731"',
            b'"model":"deepseek-v4-flash-0731","model":"other"',
            1,
        )
    else:
        document = provider_document()
        document["choices"][0]["message"]["content"] = (
            '{"artifact_version":"g2-a0-candidate-v1","artifact_version":"other"}'
        )
        raw = provider_bytes(document)

    with pytest.raises(DeepSeekClientViolation, match="structured_output_invalid"):
        client_for(response_handler(raw)).complete_once(
            canonical_request=canonical_request(),
            api_key=API_KEY,
        )


def test_provider_json_rejects_non_utf8_reasoning_without_leaking() -> None:
    document = provider_document()
    document["choices"][0]["message"]["reasoning_content"] = "\ud800"
    raw = json.dumps(
        document,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")

    with pytest.raises(
        DeepSeekClientViolation, match="thinking_evidence_missing"
    ) as error:
        client_for(response_handler(raw)).complete_once(
            canonical_request=canonical_request(),
            api_key=API_KEY,
        )

    assert str(error.value) == "thinking_evidence_missing"


def test_provider_json_rejects_oversized_integer_without_leaking() -> None:
    raw = provider_bytes().replace(
        b'"created":1786646400',
        b'"created":' + (b"9" * 5_000),
        1,
    )

    with pytest.raises(
        DeepSeekClientViolation, match="structured_output_invalid"
    ) as error:
        client_for(response_handler(raw)).complete_once(
            canonical_request=canonical_request(),
            api_key=API_KEY,
        )

    assert str(error.value) == "structured_output_invalid"


@pytest.mark.parametrize(
    "candidate_content",
    (
        "not-json",
        '```json\n{"artifact_version":"g2-a0-candidate-v1"}\n```',
        json.dumps(candidate_document(extra="not-allowed")),
        json.dumps(candidate_document(language="javascript")),
        json.dumps(candidate_document(claimed_test_scope="public_behavior")),
    ),
)
def test_candidate_content_uses_the_exact_structured_allowlist(
    candidate_content: str,
) -> None:
    document = provider_document()
    document["choices"][0]["message"]["content"] = candidate_content

    with pytest.raises(DeepSeekClientViolation, match="structured_output_invalid"):
        client_for(response_handler(provider_bytes(document))).complete_once(
            canonical_request=canonical_request(),
            api_key=API_KEY,
        )


def mutate_usage(case: str) -> dict[str, object]:
    document = deepcopy(provider_document())
    usage = document["usage"]
    if case == "bool":
        usage["completion_tokens"] = True
    elif case == "negative":
        usage["prompt_tokens"] = -1
    elif case == "missing":
        del usage["prompt_cache_hit_tokens"]
    elif case == "missing_usage":
        del document["usage"]
    elif case == "unknown":
        usage["reasoning_tokens"] = 5
    elif case == "total_mismatch":
        usage["total_tokens"] = 16
    elif case == "cache_mismatch":
        usage["prompt_cache_miss_tokens"] = 5
    elif case == "output_over_limit":
        usage["completion_tokens"] = 4_097
        usage["total_tokens"] = 4_107
    elif case == "budget":
        usage["prompt_cache_hit_tokens"] = 0
        usage["prompt_cache_miss_tokens"] = 6_000_000
        usage["prompt_tokens"] = 6_000_000
        usage["total_tokens"] = 6_000_005
    else:
        raise AssertionError(case)
    return document


@pytest.mark.parametrize(
    ("case", "reason_code"),
    (
        ("bool", "usage_invalid"),
        ("negative", "usage_invalid"),
        ("missing", "usage_invalid"),
        ("missing_usage", "usage_invalid"),
        ("unknown", "usage_invalid"),
        ("total_mismatch", "usage_invalid"),
        ("cache_mismatch", "usage_invalid"),
        ("output_over_limit", "usage_invalid"),
        ("budget", "budget_exceeded"),
    ),
)
def test_usage_and_cost_are_exact(case: str, reason_code: str) -> None:
    with pytest.raises(DeepSeekClientViolation, match=reason_code):
        client_for(response_handler(provider_bytes(mutate_usage(case)))).complete_once(
            canonical_request=canonical_request(),
            api_key=API_KEY,
        )


@pytest.mark.parametrize("api_key", ("", "contains whitespace", None, False))
def test_api_key_shape_is_rejected_before_transport(api_key: object) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=provider_bytes())

    with pytest.raises(DeepSeekClientViolation, match="policy_violation"):
        client_for(handler).complete_once(
            canonical_request=canonical_request(),
            api_key=api_key,
        )
    assert calls == 0
