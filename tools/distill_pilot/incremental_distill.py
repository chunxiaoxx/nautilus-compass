#!/usr/bin/env python3
"""Distill stable session revisions and record completion after publication readback.

The existing J1 threshold and patrol filter apply. The legacy mtime watermark is
retained as a diagnostic. Per-session content hashes select incremental work.
"""
from __future__ import annotations

import argparse
from collections import Counter
import fcntl
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).parent))
from anchor_check import CJK_RE, check, collect_anchors
from compress_arm import compress_session
from extract_sample import extract_file
from publish_to_memory import MEMORY_DIR, atomic_write, preserve_previous, sha256

REPO = Path(__file__).resolve().parents[2]
RUNTIME = REPO / "runtime/scratch_distill_pilot_20261104"
BUCKET = Path.home() / ".claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass"
PATROL_RE = re.compile(r"值守|轮值|LOOP 轮|loop 轮指令", re.IGNORECASE)
MIN_SIZE = 10_000
WRITING_WINDOW = 1800
SERVER_CMD = [
    "/opt/homebrew/bin/llama-server", "-m", str(Path.home() / "models/distill/Qwen3.5-9B-Q4_K_M.gguf"),
    "--host", "127.0.0.1", "--port", "8765", "-c", "32768", "-ngl", "99",
    "--chat-template-kwargs", '{"enable_thinking": false}',
]


def light_first_user(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for _ in range(400):
                line = handle.readline()
                if not line:
                    break
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict) or obj.get("type") != "user" or obj.get("isMeta"):
                    continue
                message = obj.get("message") or {}
                content = message.get("content") if isinstance(message, dict) else None
                if isinstance(content, str):
                    texts = [content]
                elif isinstance(content, list):
                    texts = [block.get("text", "") for block in content
                             if isinstance(block, dict) and block.get("type") == "text"]
                else:
                    texts = []
                text = " ".join(item for item in texts if isinstance(item, str) and item).strip()
                if text:
                    return text[:200]
    except OSError:
        return ""
    return ""


def source_revision(path: Path) -> dict:
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    if any(getattr(before, field) != getattr(after, field) for field in fields):
        raise RuntimeError("Session changed while its revision was read")
    return {"sha256": sha256(data), "bytes": len(data), "mtime_ns": after.st_mtime_ns}


def server_up() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/v1/models", timeout=3) as response:
            return response.status == 200
    except OSError:
        return False


def stop_server(proc: subprocess.Popen) -> None:
    """Stop only the process started by this invocation."""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def ensure_server(runtime: Path) -> subprocess.Popen | None:
    if server_up():
        return None
    with (runtime / "llama_server_incr.log").open("a") as log:
        proc = subprocess.Popen(SERVER_CMD, stdout=log, stderr=log, start_new_session=True)
    try:
        for _ in range(90):
            if server_up():
                return proc
            if proc.poll() is not None:
                raise RuntimeError("llama-server exited during startup")
            time.sleep(2)
        raise RuntimeError("llama-server did not become ready within 180 seconds")
    except BaseException:
        stop_server(proc)
        raise


def version_paths(runtime: Path, session_id: str, source_sha: str) -> dict[str, Path]:
    directory = runtime / "incremental_versions" / session_id / source_sha
    return {
        "source": directory / "extracted" / (session_id + ".txt"),
        "summary": directory / "summaries" / (session_id + ".md"),
        "narrative": directory / "prod" / (session_id + ".md"),
        "anchors": directory / "prod" / (session_id + ".anchors.txt"),
    }


def cache_valid(record: dict, paths: dict[str, Path]) -> bool:
    expected = record.get("artifact_sha256", {})
    if set(expected) != set(paths):
        return False
    return all(path.is_file() and sha256(path.read_bytes()) == expected[name]
               for name, path in paths.items())


def publication_valid(record: dict, memory_dir: Path) -> bool:
    receipt = record.get("publication", {})
    if receipt.get("source_sha256") != record.get("source_sha256"):
        return False
    try:
        path = Path(receipt["path"])
        if path.parent.resolve() != memory_dir.resolve():
            return False
        return path.is_file() and sha256(path.read_bytes()) == receipt["sha256"]
    except (KeyError, TypeError, OSError):
        return False


def collect_pending(bucket: Path, runtime: Path, state: dict) -> list[tuple[Path, dict]]:
    pending = []
    now = time.time()
    for path in sorted(bucket.glob("*.jsonl")):
        stat = path.stat()
        if stat.st_size < MIN_SIZE or now - stat.st_mtime < WRITING_WINDOW:
            continue
        if PATROL_RE.search(light_first_user(path)):
            continue
        revision = source_revision(path)
        record = state["sessions"].get(path.stem, {})
        paths = version_paths(runtime, path.stem, revision["sha256"])
        if record.get("source_sha256") == revision["sha256"] and cache_valid(record, paths):
            if record.get("status") == "review":
                continue
            if record.get("status") == "published" and publication_valid(record, Path(state["memory_dir"])):
                continue
        pending.append((path, revision))
    return pending


def update_latest(runtime: Path, paths: dict[str, Path], include_production: bool) -> None:
    destinations = {
        "source": runtime / "extracted" / paths["source"].name,
        "summary": runtime / "summaries_9b" / paths["summary"].name,
    }
    if include_production:
        destinations.update({
            "narrative": runtime / "summaries_9b_prod" / paths["narrative"].name,
            "anchors": runtime / "summaries_9b_prod" / paths["anchors"].name,
        })
    for name, destination in destinations.items():
        data = paths[name].read_bytes()
        if destination.exists() and destination.read_bytes() == data:
            continue
        preserve_previous(destination, runtime / "incremental_history" / destination.parent.name / destination.name)
        atomic_write(destination, data)


def publish_revision(paths: dict[str, Path], memory_dir: Path, source_sha: str) -> dict:
    result = subprocess.run([
        sys.executable, str(Path(__file__).with_name("publish_to_memory.py")),
        "--prod-dir", str(paths["narrative"].parent), "--memory-dir", str(memory_dir),
        "--only", paths["narrative"].stem, "--source-sha256", source_sha,
    ], check=True, capture_output=True, text=True, timeout=60)
    output = json.loads(result.stdout)
    publications = output.get("publications", [])
    if output.get("errors") or len(publications) != 1:
        raise ValueError("Publisher did not return one successful publication")
    receipt = publications[0]
    if receipt.get("status") == "review_required":
        if (receipt.get("changed") is not False or receipt.get("source_sha256") != source_sha
                or receipt.get("session_id") != paths["narrative"].stem
                or receipt.get("summary_sha256") != sha256(paths["narrative"].read_bytes())
                or receipt.get("anchors_sha256") != sha256(paths["anchors"].read_bytes())):
            raise ValueError("Review-required receipt does not bind the pending candidate")
        existing = receipt.get("existing", {})
        current = Path(existing["path"])
        if (current.parent.resolve() != memory_dir.resolve()
                or sha256(current.read_bytes()) != existing["sha256"]):
            raise ValueError("Protected memory changed during review-required readback")
        return receipt
    expected = {
        "status": "published", "session_id": paths["narrative"].stem,
        "source_sha256": source_sha,
        "summary_sha256": sha256(paths["narrative"].read_bytes()),
        "anchors_sha256": sha256(paths["anchors"].read_bytes()),
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise ValueError("Publisher receipt does not bind the requested revision")
    if not publication_valid({"source_sha256": source_sha, "publication": receipt}, memory_dir):
        raise ValueError("Published document failed independent file readback")
    return receipt


def save_state(runtime: Path, state: dict) -> None:
    atomic_write(runtime / "watermark.json", (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode())


def run_batch(args: argparse.Namespace, state: dict, pending: list[tuple[Path, dict]]) -> int:
    runtime, memory_dir = args.runtime, args.memory_dir
    proc = None
    server_checked = False
    failures = 0
    try:
        for path, revision in pending:
            source_sha = revision["sha256"]
            previous = state["sessions"].get(path.stem, {})
            record = dict(previous) if previous.get("source_sha256") == source_sha else {}
            if not record and previous.get("publication"):
                record["previous_publication"] = previous["publication"]
            record.update({"source_sha256": source_sha, "source_bytes": revision["bytes"],
                           "source_mtime_ns": revision["mtime_ns"]})
            paths = version_paths(runtime, path.stem, source_sha)
            try:
                if not cache_valid(record, paths):
                    if not server_checked:
                        proc = ensure_server(runtime)
                        server_checked = True
                    for destination in paths.values():
                        destination.parent.mkdir(parents=True, exist_ok=True)
                    extract_file(path, paths["source"])
                    stat = compress_session(paths["source"], paths["summary"],
                                            "http://127.0.0.1:8765/v1", "local", 14000)
                    source_text = paths["source"].read_text(encoding="utf-8")
                    summary_text = paths["summary"].read_text(encoding="utf-8")
                    checked = check(summary_text, source_text)
                    gate = "ok" if (checked["traceable_rate"] or 0) >= 0.95 else "review"
                    counts = Counter(anchor["value"] for anchor in collect_anchors(source_text)
                                     if anchor["type"] in ("path", "date", "tag_id", "url")
                                     and not CJK_RE.search(anchor["value"]))
                    atomic_write(paths["narrative"], summary_text.split("## 附")[0].encode())
                    atomic_write(paths["anchors"], "\n".join(sorted(value for value, count in counts.items() if count >= 3)).encode())
                    record.update({"status": "ready" if gate == "ok" else "review",
                                   "gate": gate, "j1": checked["traceable_rate"], "compression": stat,
                                   "artifact_sha256": {name: sha256(p.read_bytes()) for name, p in paths.items()}})
                if source_revision(path)["sha256"] != source_sha:
                    raise RuntimeError("Session changed before publication")
                # Save the generated revision before publishing, so a failed
                # publication can be retried without repeating model work.
                state["sessions"][path.stem] = record
                save_state(runtime, state)
                update_latest(runtime, paths, include_production=False)
                if record["gate"] == "ok":
                    publication = publish_revision(paths, memory_dir, source_sha)
                    if source_revision(path)["sha256"] != source_sha:
                        raise RuntimeError("Session changed during publication")
                    if publication["status"] == "review_required":
                        record["pending_publication"] = publication
                        record["semantic_status"] = "review_required"
                        record["status"] = "review"
                    else:
                        record["publication"] = publication
                        record.pop("pending_publication", None)
                        record["semantic_status"] = publication.get("semantic_status", "unreviewed_j1_only")
                        record["status"] = "published"
                        update_latest(runtime, paths, include_production=True)
                else:
                    record["status"] = "review"
                record.pop("error", None)
            except Exception as error:
                failures += 1
                record["status"] = "failed"
                record["error"] = {"type": type(error).__name__, "message": str(error)}
                if isinstance(error, subprocess.CalledProcessError):
                    record["error"]["returncode"] = error.returncode
                    record["error"]["stderr"] = error.stderr
            state["sessions"][path.stem] = record
            state["mtime"] = max(state.get("mtime", 0), revision["mtime_ns"] / 1_000_000_000)
            save_state(runtime, state)
            with (runtime / "incremental_stats.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"session_id": path.stem, **record}, ensure_ascii=False) + "\n")
            print(f"[incr] {path.stem[:8]} {record['status']}", file=sys.stderr)
    finally:
        if proc is not None:
            stop_server(proc)
    return 1 if failures else 0


def load_state(runtime: Path, memory_dir: Path) -> dict:
    watermark_path = runtime / "watermark.json"
    state = json.loads(watermark_path.read_text()) if watermark_path.exists() else {"mtime": 0}
    state.setdefault("sessions", {})
    if not isinstance(state["sessions"], dict):
        raise ValueError("watermark.sessions must be an object")
    state.update({"version": 2, "memory_dir": str(memory_dir.resolve())})
    return state


def select_pending(args: argparse.Namespace, state: dict) -> list[tuple[Path, dict]]:
    pending = collect_pending(args.bucket, args.runtime, state)
    requested = {name for name in args.only.split(",") if name}
    if requested:
        pending = [(path, revision) for path, revision in pending if path.stem in requested]
    pending.sort(key=lambda item: (
        state["sessions"].get(item[0].stem, {}).get("status") == "failed",
        -item[1]["mtime_ns"],
    ))
    if args.max_sessions:
        pending = pending[:args.max_sessions]
    return pending


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--runtime", type=Path, default=RUNTIME)
    parser.add_argument("--bucket", type=Path, default=BUCKET)
    parser.add_argument("--memory-dir", type=Path, default=MEMORY_DIR)
    parser.add_argument("--only", default="", help="Comma-separated complete session IDs")
    parser.add_argument("--max-sessions", type=int, default=0,
                        help="Maximum sessions in this invocation; zero processes the full queue")
    args = parser.parse_args(argv)
    if args.max_sessions < 0:
        parser.error("--max-sessions must be zero or a positive integer")
    requested = {name for name in args.only.split(",") if name}
    missing = requested - {path.stem for path in args.bucket.glob("*.jsonl")}
    if missing:
        parser.error("Requested sessions are missing: " + ", ".join(sorted(missing)))
    if not ((args.runtime / "DISTILL_GREEN").exists() or args.force):
        print("GATED: DISTILL_GREEN 不在(D5 未定谳),本轮跳过", file=sys.stderr)
        return 0
    if args.dry_run:
        state = load_state(args.runtime, args.memory_dir)
        pending = select_pending(args, state)
        print(f"新增或待发布版本 {len(pending)}", file=sys.stderr)
        return 0
    args.runtime.mkdir(parents=True, exist_ok=True)
    with (args.runtime / ".incremental.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("BUSY: another incremental writer owns the runtime", file=sys.stderr)
            return 75
        state = load_state(args.runtime, args.memory_dir)
        pending = select_pending(args, state)
        print(f"新增或待发布版本 {len(pending)}", file=sys.stderr)
        if not pending:
            return 0
        return run_batch(args, state, pending)


if __name__ == "__main__":
    sys.exit(main())
