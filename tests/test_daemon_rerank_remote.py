"""Existing-service rerank contracts. No weights, sockets or daemons started."""
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import daemon as d


@pytest.fixture
def remote(monkeypatch):
    monkeypatch.setenv("COMPASS_RERANK_REMOTE", "127.0.0.1:8401")
    monkeypatch.setenv("COMPASS_RERANK_REMOTE_TIMEOUT", "4")
    contract = dict(model="BAAI/bge-reranker-v2-m3", revision="fixture",
                    cache_weight_blob_id="fixture", max_length=8192, activation="sigmoid")
    monkeypatch.setattr(d, "_remote_rerank_contract", lambda: contract)
    real_read = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda p, *a, **k:
                        "fixture-only" if p.name == "rerank_token" else real_read(p, *a, **k))
    monkeypatch.setattr(d, "_PROD_RERANK_USE", True)
    monkeypatch.setattr(d, "log", lambda *_: None)
    top = [(i / 100, {"path": f"d{i}", "embed_text": "x" * (600 + i)}) for i in range(30)]
    replies = [dict(ok=True, **contract, device="mps", max_length_supported=8192, batch_size_limit=4),
               dict(ok=True, **contract, device="mps", ms=100, scores=list(range(30)))]
    requests = []

    def rpc(address, request, deadline):
        requests.append((address, request, deadline))
        return replies[len(requests) - 1]

    monkeypatch.setattr(d, "_remote_rerank_rpc", rpc)
    return SimpleNamespace(top=top, replies=replies, requests=requests, contract=contract)


def test_remote_success_preserves30_inputs_dense_scores_and_model(remote, monkeypatch):
    monkeypatch.setattr(d, "_get_reranker", lambda: pytest.fail("local weights loaded"))
    out = d._rerank_top("q" * 1600, remote.top, 3)
    assert out == remote.top[-1:-4:-1]
    assert len(remote.requests[1][1]["docs"]) == 30
    assert remote.requests[1][1]["docs"] == [e["embed_text"] for _, e in remote.top]
    assert remote.requests[1][1]["query"] == "q" * 1600
    assert remote.requests[1][1]["max_length"] == 8192
    assert remote.requests[1][1]["activation"] == "sigmoid"
    assert d._RERANK_TRACE.last["backend"] == "remote_mps"
    assert d._RERANK_TRACE.last["fallback"] is False


@pytest.mark.parametrize("fault", ["auth", "wrong_model", "old_context", "wrong_count", "nan", "boolean"])
def test_remote_contract_fault_uses_explicit_original_local_fallback(remote, monkeypatch, fault):
    if fault == "auth": remote.replies[0]["ok"] = False
    elif fault == "wrong_model": remote.replies[0]["model"] = "different"
    elif fault == "old_context": remote.replies[0]["max_length_supported"] = 512
    elif fault == "wrong_count": remote.replies[1]["scores"] = [1.0]
    elif fault == "nan": remote.replies[1]["scores"][0] = float("nan")
    else: remote.replies[1]["scores"][0] = True
    calls = []
    monkeypatch.setattr(d, "_get_reranker", lambda: SimpleNamespace(
        predict=lambda pairs: calls.append(pairs) or list(range(30))))
    out = d._rerank_top("q", remote.top, 3)
    assert out == remote.top[-1:-4:-1]
    assert len(calls[0]) == 30
    assert d._RERANK_TRACE.last["fallback"] is True
    assert d._RERANK_TRACE.last["backend"] == "local_crossencoder"


def test_remote_timeout_does_not_retry_and_falls_back(remote, monkeypatch):
    calls = []
    def timeout(*args):
        calls.append(args)
        raise TimeoutError("fixture")
    monkeypatch.setattr(d, "_remote_rerank_rpc", timeout)
    monkeypatch.setattr(d, "_get_reranker", lambda: SimpleNamespace(predict=lambda pairs: [0.0]*len(pairs)))
    assert d._rerank_top("q", remote.top, 3) == remote.top[:3]
    assert len(calls) == 1
    assert d._RERANK_TRACE.last["remote_error_type"] == "TimeoutError"


def test_remote_ties_are_stable(remote, monkeypatch):
    remote.replies[1]["scores"] = [0.5] * 30
    monkeypatch.setattr(d, "_get_reranker", lambda: pytest.fail("unexpected fallback"))
    assert d._rerank_top("q", remote.top, 3) == remote.top[:3]


def test_remote_rpc_deadline_is_total_and_connection_closes(monkeypatch):
    ticks = iter([0.0, 0.1, 0.2, 1.2])
    monkeypatch.setattr(d, "time", SimpleNamespace(monotonic=lambda: next(ticks)))
    closed = []
    timeouts = []

    class Connection:
        def __enter__(self): return self
        def __exit__(self, *_): closed.append(True)
        def settimeout(self, value): timeouts.append(value)
        def sendall(self, _): pass
        def recv(self, _): return b"partial"

    monkeypatch.setattr(d.socket, "create_connection", lambda *a, **k: Connection())
    with pytest.raises(TimeoutError):
        d._remote_rerank_rpc(("127.0.0.1", 8401), {"action": "health"}, 1.0)
    assert closed == [True]
    assert timeouts and all(0 < value <= 1 for value in timeouts)


@pytest.fixture
def service(monkeypatch):
    path = Path.home() / "bge-embed/rerank_server.py"
    spec = importlib.util.spec_from_file_location("rerank_service_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "TOKEN_FILE", SimpleNamespace(read_text=lambda: "fixture-only"))
    monkeypatch.setattr(module, "model_identity", lambda: dict(
        model="BAAI/bge-reranker-v2-m3", device="mps", revision="fixture",
        cache_weight_blob_id="fixture", max_length_supported=8192, batch_size_limit=4))
    return module


def request(service, **kwargs):
    handler = object.__new__(service.Handler)
    handler.rfile = io.BytesIO(json.dumps(dict(action="rerank", token="fixture-only",
                                               query="q", docs=["d"], **kwargs)).encode()+b"\n")
    handler.wfile = io.BytesIO()
    handler.handle()
    return json.loads(handler.wfile.getvalue())


def test_service_legacy_default_preserves512(service, monkeypatch):
    seen = []
    monkeypatch.setattr(service, "score", lambda *a: seen.append(a) or [0.12345678])
    result = request(service)
    assert result["ok"] and result["max_length"] == 512
    assert seen[0][2:] == (512, 4, "identity")
    assert result["scores"] == [0.1235]


def test_service_explicit_full_context_and_precision(service, monkeypatch):
    seen = []
    monkeypatch.setattr(service, "score", lambda *a: seen.append(a) or [0.12345678])
    result = request(service, max_length=8192, activation="sigmoid")
    assert result["ok"] and result["max_length"] == 8192
    assert seen[0][2:] == (8192, 4, "sigmoid")
    assert result["scores"] == [0.12345678]


@pytest.mark.parametrize("args", [dict(max_length=8193), dict(max_length=True),
                                  dict(batch_size=5), dict(activation="unknown")])
def test_service_rejects_invalid_contract_without_scoring(service, monkeypatch, args):
    monkeypatch.setattr(service, "score", lambda *_: pytest.fail("invalid request scored"))
    assert request(service, **args)["ok"] is False


def test_service_full_input_length_bucketing_restores_order(service, monkeypatch):
    import torch
    calls = []

    class Batch(dict):
        def to(self, _): return self

    def tok(pairs, **kw):
        calls.append((pairs, kw))
        lengths = [[0] * min(len(doc), kw["max_length"]) for _, doc in pairs]
        if "return_tensors" not in kw:
            return {"input_ids": lengths}
        return Batch(values=[len(doc) for _, doc in pairs])

    def model(**kw):
        return SimpleNamespace(logits=torch.tensor(kw["values"], dtype=torch.float32))

    monkeypatch.setattr(service, "get_model", lambda: (tok, model))
    docs = ["a" * n for n in [600, 20, 1000, 300, 700, 100, 900, 40, 800]]
    scores = service.score("q", docs, 8192, 4)
    assert scores == [float(len(x)) for x in docs]
    forward_calls = [x for x in calls if "return_tensors" in x[1]]
    assert [len(pairs) for pairs, _ in forward_calls] == [4, 4, 1]
    assert all(kw["max_length"] == 8192 for _, kw in forward_calls)
    assert max(len(doc) for pairs, _ in forward_calls for _, doc in pairs) == 1000


def test_service_identity_is_bound_to_explicit_offline_snapshot(service, tmp_path, monkeypatch):
    monkeypatch.setattr(service.Path, "home", lambda: tmp_path)
    hub = tmp_path / ".cache/huggingface/hub/models--BAAI--bge-reranker-v2-m3"
    (hub / "refs").mkdir(parents=True)
    (hub / "refs/main").write_text("fixed-revision")
    snapshot = hub / "snapshots/fixed-revision"
    snapshot.mkdir(parents=True)
    (snapshot / "model.safetensors").write_bytes(b"fixture-only")
    calls = []

    class Model:
        def to(self, _): return self
        def eval(self): return self

    def loader(path, **kwargs):
        calls.append((path, kwargs))
        return Model()

    monkeypatch.setattr(service, "AutoTokenizer", SimpleNamespace(from_pretrained=loader))
    monkeypatch.setattr(service, "AutoModelForSequenceClassification", SimpleNamespace(from_pretrained=loader))
    service.get_model()
    assert len(calls) == 2
    assert all(path == str(snapshot) and kw == {"local_files_only": True} for path, kw in calls)
    assert service._loaded_revision == "fixed-revision"
    assert service._loaded_weight_blob_id == "model.safetensors"
