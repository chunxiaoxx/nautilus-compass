import json

from tools import local_agent_runtime as runtime
from tools import nacre_build_dataset as dataset
from tools import nacre_eval as nacre_eval
from tools import nacre_prepare_mlx_data as mlx_data
from tools import nacre_training_preflight as preflight
from tools import nacre_validate_gold_candidates as gold_validator
from tools import nacre_validate_dataset as validator


def test_local_tool_registry_has_no_external_send_tool():
    assert "send_email" not in runtime.TOOL_REGISTRY
    assert "github_comment" not in runtime.TOOL_REGISTRY
    assert "deploy" not in runtime.TOOL_REGISTRY


def test_local_model_thinking_flag_is_explicit(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": "{}"}}],
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return Response()

    monkeypatch.setattr(runtime.urllib.request, "urlopen", fake_urlopen)

    runtime._call_model([{"role": "user", "content": "分析"}], enable_thinking=True)
    assert captured["body"]["enable_thinking"] is True

    runtime._call_model([{"role": "user", "content": "值守"}], enable_thinking=False)
    assert captured["body"]["enable_thinking"] is False


def test_semantic_review_uses_thinking_without_tool_router(monkeypatch):
    captured = {}

    def fake_call(messages, max_tokens=512, *, enable_thinking=False, timeout=120):
        captured.update({
            "max_tokens": max_tokens,
            "enable_thinking": enable_thinking,
            "timeout": timeout,
            "messages": messages,
        })
        return '```json\n{"verdict":"pass","findings":[],"next_action":"none"}\n```'

    monkeypatch.setattr(runtime, "_call_model", fake_call)
    result = runtime.semantic_review("检查证据")

    assert result["parse_status"] == "pass"
    assert result["thinking_enabled"] is True
    assert captured["enable_thinking"] is True
    assert captured["max_tokens"] == 4096
    assert captured["timeout"] == 300


def test_org_continuity_read_is_bounded_and_local():
    result = runtime.org_continuity_read({})

    assert result["ok"] is True
    assert result["source"].startswith("runtime/org-continuity/")
    assert result["acceptance_boundary"] == "组织连续性文件读回，不代表外部客户验收"


def test_write_draft_is_local_only(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "DRAFT_DIR", tmp_path)

    result = runtime.write_draft({"title": "审核草稿", "body": "请审核"})

    assert result["ok"] is True
    assert result["status"] == "draft_only"
    path = tmp_path / result["path"].split("/")[-1]
    assert path.exists()
    assert "external_send: false" in path.read_text(encoding="utf-8")


def test_dataset_builder_excludes_external_events(tmp_path):
    source = tmp_path / "events.jsonl"
    source.write_text(
        json.dumps({"task": "safe", "external_model_used": False, "external_send": False})
        + "\n"
        + json.dumps({"task": "unsafe", "external_model_used": True, "external_send": False})
        + "\n",
        encoding="utf-8",
    )

    events = dataset.load_events(source)
    records = [dataset.build_record(event) for event in events if not event.get("external_model_used") and not event.get("external_send")]

    assert len(records) == 1
    assert records[0]["task"] == "safe"
    assert records[0]["safety"]["external_model_used"] is False


def test_dataset_builder_excludes_unverified_draft_claim():
    event = {
        "task": "请生成本地审核草稿",
        "final": "草稿已保存，但没有回执。",
        "steps": [{"model_output": {"tool_calls": [{"name": "local_health", "arguments": {}}]}, "results": []}],
    }

    assert dataset.contract_violation(event) == "draft_claim_without_successful_write_draft"


def test_dataset_builder_excludes_false_draft_claim_even_when_draft_was_forbidden():
    event = {
        "task": "只读检查，不要写草稿",
        "final": "检查完成，草稿已保存。",
        "steps": [],
    }

    assert dataset.contract_violation(event) == "draft_claim_without_successful_write_draft"


def test_dataset_builder_keeps_explicit_no_draft_task():
    event = {
        "task": "只读检查，不要写草稿",
        "final": "检查完成",
        "steps": [],
    }

    assert dataset.contract_violation(event) is None


def test_compass_recall_returns_bounded_evidence(monkeypatch):
    monkeypatch.setattr(
        runtime,
        "_compass_daemon_request",
        lambda request, timeout=30.0: {
            "ok": True,
            "scope": request["scope"],
            "projects_scanned": [request.get("project")],
            "recall": [{
                "path": "memory.md",
                "project": request.get("project"),
                "score": 0.91,
                "description": "verified memory",
                "fact_status": "measured",
                "body": "secret=do-not-export",
            }],
            "performance": {"total_compute_ms": 12},
        },
    )

    result = runtime.compass_recall({"query": "verified", "top_k": 1})

    assert result["ok"] is True
    assert result["recall"][0]["path"] == "memory.md"
    assert "body_excerpt" not in result["recall"][0]
    assert result["performance"]["total_compute_ms"] == 12


def test_evidence_gate_requires_source_and_success_status():
    supported = runtime.evidence_gate({
        "claim": "local model is healthy",
        "evidence": [{"source": "health.json", "status": "healthy"}],
    })
    insufficient = runtime.evidence_gate({
        "claim": "local model is healthy",
        "evidence": [{"source": "health.json", "status": "unknown"}],
    })

    assert supported["verdict"] == "supported"
    assert insufficient["verdict"] == "insufficient"
    assert "evidence[0].status" in insufficient["missing"]


def test_evidence_gate_rejects_unobserved_context_source():
    result = runtime.evidence_gate({
        "claim": "memory is verified",
        "evidence": [{"source": "compass_recall", "path": "/tmp/fake.md", "status": "verified"}],
        "_observed_evidence": [{"source": "compass_recall", "path": "real.md", "status": "inferred"}],
    })

    assert result["verdict"] == "insufficient"
    assert "evidence[0].unobserved_source" in result["missing"]


def test_evidence_gate_rejects_inferred_recall_as_verified():
    result = runtime.evidence_gate({
        "claim": "memory is verified",
        "evidence": [{"source": "compass_recall", "path": "real.md", "status": "verified"}],
        "_observed_evidence": [{"source": "compass_recall", "path": "real.md", "status": "inferred"}],
    })

    assert result["verdict"] == "insufficient"
    assert "evidence[0].observed_status" in result["missing"]


def test_memory_search_rejects_external_path():
    result = runtime.memory_search({"query": "组织连续性", "path": "/tmp/fake.md"})

    assert result["hits"] == []
    assert result["reason"] == "path_filter_not_supported"


def test_dataset_validator_detects_manifest_drift(tmp_path):
    data_path = tmp_path / "dataset.jsonl"
    manifest_path = tmp_path / "manifest.json"
    data_path.write_text(
        json.dumps({
            "schema": "nacre-sft-v0",
            "id": "one",
            "split": "train",
            "task": "safe task",
            "tool_trace": [],
            "target": "safe result",
            "safety": {"external_model_used": False, "external_send": False},
        }) + "\n",
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps({"record_count": 0, "sha256": "wrong"}), encoding="utf-8")

    report = validator.validate(data_path, manifest_path)

    assert report["ok"] is False
    assert "manifest_record_count_mismatch" in report["errors"]
    assert "manifest_sha256_mismatch" in report["errors"]


def test_mlx_converter_emits_chat_files(tmp_path):
    source = tmp_path / "dataset.jsonl"
    source.write_text(json.dumps({
        "split": "train",
        "task": "检查状态",
        "tool_trace": [{"name": "local_health", "arguments": {}}],
        "target": "状态正常",
    }, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = mlx_data.prepare(source, tmp_path / "mlx")

    assert manifest["counts"]["train"] == 1
    row = json.loads((tmp_path / "mlx" / "train.jsonl").read_text(encoding="utf-8"))
    assert row["messages"][-1]["role"] == "assistant"
    assert '"tool_calls"' in row["messages"][-1]["content"]


def test_training_preflight_blocks_tiny_dataset(tmp_path, monkeypatch):
    config = tmp_path / "config.yaml"
    config.write_text("model: /tmp/model\n", encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    (data / "manifest.json").write_text(json.dumps({"counts": {"train": 1, "validation": 0, "test": 0}}), encoding="utf-8")
    for name in ("train.jsonl", "valid.jsonl", "test.jsonl"):
        (data / name).write_text("", encoding="utf-8")
    monkeypatch.setattr(preflight, "_mlx_available", lambda _: True)

    report = preflight.preflight(config, data, min_train=2, min_valid=1, python_path=tmp_path / "python")

    assert report["ready"] is False
    assert "base_model_missing" in report["blockers"]
    assert "train_count_below_2" in report["blockers"]


def test_runtime_eval_reports_contract_failure_without_claiming_semantic_accuracy():
    report = nacre_eval.evaluate([
        {
            "external_model_used": False,
            "external_send": False,
            "task": "只读检查，不要写草稿",
            "steps": [{"model_output": {"tool_calls": [{"name": "local_health", "arguments": {}}]}}],
            "final": "状态正常",
        }
    ])

    assert report["tool_allowlist"]["rate"] == 1.0
    assert report["semantic_accuracy"] == "unscored_without_human_gold_set"


def test_gold_candidate_validator_requires_review_fields(tmp_path):
    source = tmp_path / "gold.jsonl"
    source.write_text(json.dumps({
        "id": "candidate-1",
        "category": "health",
        "task": "检查健康",
        "allowed_tools": ["local_health"],
        "expected_outcome": "返回健康状态",
        "forbidden_actions": ["send_email"],
    }) + "\n", encoding="utf-8")

    report = gold_validator.validate(source)

    assert report["ok"] is True
    assert report["approved_for_training"] is False
