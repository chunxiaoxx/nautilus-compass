#!/usr/bin/env python3
"""Bounded Compass service probe.

The probe checks the local daemon's authentication boundary and, when present,
the local OpenAI-compatible model endpoint. It never prints the daemon token.
The output is a diagnostic receipt, not a semantic or production-acceptance
claim.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import socket
import time
import urllib.request


def rpc(host: str, port: int, payload: dict, timeout: float) -> tuple[dict, float]:
    started = time.perf_counter()
    with socket.create_connection((host, port), timeout=timeout) as conn:
        conn.settimeout(timeout)
        conn.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode())
        data = b""
        while b"\n" not in data:
            chunk = conn.recv(65536)
            if not chunk:
                break
            data += chunk
    return json.loads(data.split(b"\n", 1)[0].decode()), round((time.perf_counter() - started) * 1000, 1)


def read_token(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def safe_response(response: dict) -> dict:
    result = dict(response)
    recall = result.get("recall")
    if isinstance(recall, list):
        result["recall"] = [
            {key: item.get(key) for key in ("score", "path", "project", "age")}
            for item in recall
        ]
    elif isinstance(recall, dict):
        result["recall"] = {
            key: recall.get(key) for key in ("p9_cache", "sliding_5min", "inotify")
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daemon-host", default="127.0.0.1")
    parser.add_argument("--daemon-port", type=int, default=9876)
    parser.add_argument("--model-url", default="http://127.0.0.1:8765")
    parser.add_argument("--project", default="-Users-chunxiao-wang-Projects-nautilus-compass")
    parser.add_argument("--query", default="history compression semantic review")
    parser.add_argument("--token-file", type=pathlib.Path,
                        default=pathlib.Path.home() / ".claude/.cache/compass_daemon_token")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    token = read_token(args.token_file)
    checks: list[dict] = []
    requests = [
        ("daemon_ping_no_token", {"action": "ping"}),
        ("daemon_status_no_token", {"action": "status"}),
        ("daemon_recall_no_token", {
            "action": "recall", "query": args.query, "project": args.project, "top_k": 3,
        }),
        ("daemon_status_authorized", {"action": "status", "token": token}),
        ("daemon_recall_authorized", {
            "action": "recall", "query": args.query, "project": args.project,
            "top_k": 3, "token": token,
        }),
    ]
    for name, payload in requests:
        try:
            response, latency_ms = rpc(args.daemon_host, args.daemon_port, payload, 30)
            checks.append({"name": name, "latency_ms": latency_ms,
                           "response": safe_response(response)})
        except Exception as error:  # diagnostic receipt must retain failures
            checks.append({"name": name, "error": f"{type(error).__name__}: {error}"})

    model = {}
    try:
        started = time.perf_counter()
        with urllib.request.urlopen(args.model_url.rstrip("/") + "/v1/models", timeout=10) as response:
            models = json.loads(response.read().decode())
        model["models_ok"] = True
        model["model_id"] = (models.get("data") or [{}])[0].get("id")
        model["models_latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    except Exception as error:
        model["models_ok"] = False
        model["error"] = f"{type(error).__name__}: {error}"

    receipt = {
        "schema": "compass-service-probe/1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "daemon": {"host": args.daemon_host, "port": args.daemon_port},
        "model_url": args.model_url,
        "project": args.project,
        "checks": checks,
        "model": model,
        "token_values_recorded": False,
        "interpretation": {
            "service_boundary": "ping is public; status/recall require the local token",
            "semantic_boundary": "recall success is transport evidence, not semantic approval",
            "acceptance_boundary": "this probe does not establish production or customer acceptance",
        },
    }
    encoded = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    receipt["receipt_sha256"] = hashlib.sha256(encoded).hexdigest()
    encoded = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
    print(json.dumps({"receipt_sha256": receipt["receipt_sha256"],
                      "checks": [(item["name"], item.get("response", {}).get("ok"),
                                  item.get("response", {}).get("error"))
                                 for item in checks],
                      "models_ok": model.get("models_ok")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
