"""CPU-only fake-model concurrency checks; never bind or stress a live service."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace, ModuleType

import pytest
import torch


def module(name, monkeypatch):
    path = Path.home() / "bge-embed" / f"{name}.py"
    if name == "embed_server":
        path = Path(os.environ.get("MPS_EMBED_TEST_SOURCE", str(path)))
        # These tests cover the model boundary; HTTP readiness is a separate live check.
        fake_api = ModuleType("fastapi")
        class App:
            def __init__(self, **_): pass
            def get(self, *_): return lambda fn: fn
            def post(self, *_): return lambda fn: fn
        fake_api.FastAPI = App
        monkeypatch.setitem(sys.modules, "fastapi", fake_api)
    spec = importlib.util.spec_from_file_location(f"isolated_{name}", path)
    service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service)
    service.DEV = "cpu"  # all tensors below are tiny CPU fixture values
    return service


class Batch(dict):
    def to(self, _): return self


class Meter:
    def __init__(self):
        self.lock = threading.Lock()
        self.active = self.peak = self.loads = 0
        self.batches = []

    def enter(self, texts):
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.batches.append(list(texts))
        time.sleep(0.01)  # deterministic overlap opportunity in the broken version

    def leave(self):
        with self.lock: self.active -= 1


@pytest.fixture
def embedding(monkeypatch):
    service = module("embed_server", monkeypatch)
    meter = Meter()
    tokenizer_calls = []

    def tokenizer(texts, **kwargs):
        tokenizer_calls.append(kwargs)
        return Batch(texts=list(texts))

    class Model:
        def to(self, _): return self
        def eval(self): return self
        def __call__(self, texts):
            meter.enter(texts)
            try:
                return SimpleNamespace(last_hidden_state=torch.tensor(
                    [[[float(len(text)), 1.0]] for text in texts]))
            finally: meter.leave()

    def load_model(*_, **__):
        with meter.lock: meter.loads += 1
        time.sleep(0.01)
        return Model()

    monkeypatch.setattr(service, "AutoTokenizer", SimpleNamespace(
        from_pretrained=lambda *a, **k: tokenizer))
    monkeypatch.setattr(service, "AutoModel", SimpleNamespace(from_pretrained=load_model))
    return SimpleNamespace(service=service, meter=meter, tokenizer_calls=tokenizer_calls)


def test_embedding_concurrent_first_requests_load_once_and_infer_one_at_a_time(embedding):
    e = embedding
    barrier = threading.Barrier(3)
    inputs = [["x" * (i + 1) for i in range(9)] for _ in range(3)]

    def request(texts):
        barrier.wait(timeout=5)
        return e.service._embed(texts)

    with ThreadPoolExecutor(max_workers=3) as pool:
        outputs = list(pool.map(request, inputs))
    assert e.meter.loads == 1
    assert e.meter.peak == 1
    assert len(outputs) == 3 and all(len(x) == 9 for x in outputs)
    assert all(len(batch) <= 4 for batch in e.meter.batches)


def test_embedding_bounded_batches_preserve_full_input_order_and_normalized_outputs(embedding):
    e = embedding
    texts = ["x" * i for i in [2, 7, 1, 9, 3, 8, 4, 6, 5]]
    actual = torch.tensor(e.service._embed(texts))
    expected = torch.nn.functional.normalize(torch.tensor(
        [[float(len(text)), 1.0] for text in texts]), dim=-1)
    assert torch.allclose(actual, expected, atol=1e-7, rtol=0)
    assert [len(batch) for batch in e.meter.batches] == [4, 4, 1]
    assert [text for batch in e.meter.batches for text in batch] == texts
    assert all(x["max_length"] == 512 and x["truncation"] is True for x in e.tokenizer_calls)


def test_existing_reranker_already_serializes_model_forward(monkeypatch):
    service = module("rerank_server", monkeypatch)
    meter = Meter()

    def tokenizer(pairs, **kwargs):
        if "return_tensors" not in kwargs:
            return {"input_ids": [[0]*len(doc) for _, doc in pairs]}
        return Batch(texts=[doc for _, doc in pairs])

    def model(texts):
        meter.enter(texts)
        try: return SimpleNamespace(logits=torch.tensor([float(len(t)) for t in texts]))
        finally: meter.leave()

    monkeypatch.setattr(service, "get_model", lambda: (tokenizer, model))
    barrier = threading.Barrier(3)
    docs = ["x"*n for n in [20, 70, 10, 90, 30, 80, 40, 60, 50]]

    def request(_):
        barrier.wait(timeout=5)
        return service.score("q", docs, 8192, 4)

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(request, range(3)))
    assert meter.peak == 1
    assert all(result == [float(len(t)) for t in docs] for result in results)
    assert all(len(batch) <= 4 for batch in meter.batches)
