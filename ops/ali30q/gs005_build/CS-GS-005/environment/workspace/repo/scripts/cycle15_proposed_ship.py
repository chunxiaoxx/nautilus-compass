"""Ship orchestrator · Nautilus Engine cycle 4.

Bridges generate → staging → check → audit → optional commit. Used by:
- `nautilus code <task>` CLI command (phase3/cli/nautilus_cli/__main__.py)
- Programmatic: ship(engine, task, base_dir, apply=False) → ShipResult

Pipeline:
    1. engine.generate(task) → raw LLM text
    2. engine.parse_file_blocks(raw) → blocks (lang, path, content)
    3. Write blocks to a tempdir "staging" copy
    4. Run check_pipeline (py_compile + import + ruff) on staged files
    5. Optional: POST to /api/v1/audit/dispatch for cert signal
    6. Gate apply on check_passed AND (fidelity_score >= threshold OR no audit)
    7. If apply: copy staged files to base_dir; optional git add + commit

Default is dry-run · explicit apply=True writes + commits.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from engine.checks import (
    check_semantic_preservation,
    run_pipeline,
    should_apply_semantic_check,
)

DEFAULT_AUDIT_URL = "https://www.nautilus.social/api/v1/audit/dispatch"


@dataclass
class ShipResult:
    task: str
    files_planned: list[dict] = field(default_factory=list)
    check_result: dict = field(default_factory=lambda: {"passed": False, "checks": []})
    audit: Optional[dict] = None
    git_commit: Optional[str] = None
    applied: bool = False
    errors: list[str] = field(default_factory=list)
    # cycle 8 retry · per-attempt trace from self-healing retry loop
    attempts: list[dict] = field(default_factory=list)
    # v5agent cycle 8 a2a wiring · optional council review counts + opinions
    a2a_review: Optional[dict] = None


def ship(
    engine: Any,
    task: str,
    base_dir: str,
    apply: bool = False,
    fidelity_threshold: float = 0.7,
    dispatch_audit: bool = True,
    audit_url: str = DEFAULT_AUDIT_URL,
    api_key: Optional[str] = None,
    git_commit_msg: Optional[str] = None,
    run_runtime_check: bool = False,
    run_runtime_args_check: bool = False,
    runtime_timeout: int = 10,
    max_retries: int = 0,
    request_a2a_review: bool = False,
    a2a_targets: Optional[tuple] = None,
    a2a_timeout: int = 30,
    a2a_db_engine: Any = None,
) -> ShipResult:
    """Run the full ship pipeline. See module docstring for details.

    cycle 8 · max_retries controls the self-healing retry loop. Default 0 = a
    single attempt. With max_retries=N, on check failure the engine is
    re-prompted with error context + previous attempt file paths · up to N
    additional tries. The audit / apply / commit steps use the final attempt.
    """
    base = Path(base_dir).resolve()
    task = _inject_file_context(task, base)
    attempts: list[dict] = []  # private records · include _blocks for retry/apply
    last_blocks: list[dict] = []
    last_check: dict = {"passed": False, "checks": []}
    last_files_planned: list[dict] = []

    total_tries = max(1, 1 + max_retries)
    for attempt_num in range(1, total_tries + 1):
        retry_ctx = attempts[-1] if attempts else None
        att = _try_once(
            engine,
            task,
            retry_ctx,
            run_runtime_check=run_runtime_check,
            run_runtime_args_check=run_runtime_args_check,
            runtime_timeout=runtime_timeout,
            base_dir=base,
        )
        attempts.append({
            "attempt_number": attempt_num,
            "raw_response_chars": att["raw_response_chars"],
            "files_planned": att["files_planned"],
            "check_result": att["check_result"],
            "_blocks": att["blocks"],
        })
        last_blocks = att["blocks"]
        last_check = att["check_result"]
        last_files_planned = att["files_planned"]
        if att["check_result"]["passed"]:
            break

    public_attempts = [{k: v for k, v in a.items() if k != "_blocks"} for a in attempts]

    if not last_blocks:
        return ShipResult(
            task=task,
            attempts=public_attempts,
            errors=[
                f"LLM output had no parseable file blocks (after {len(attempts)} attempt(s))"
            ],
        )

    audit = _maybe_dispatch_audit(
        task, last_blocks, dispatch_audit, audit_url, api_key
    )
    a2a_review = _maybe_request_a2a_review(
        task, last_blocks, request_a2a_review, a2a_targets, a2a_timeout, a2a_db_engine
    )

    errors: list[str] = []
    if not last_check["passed"]:
        errors.append(f"static check pipeline failed after {len(attempts)} attempts")
    fid = (audit or {}).get("fidelity_score")
    if fid is not None and fid < fidelity_threshold:
        errors.append(
            f"fidelity {fid:.2f} below threshold {fidelity_threshold:.2f}"
        )

    if errors or not apply:
        return ShipResult(
            task=task,
            files_planned=last_files_planned,
            check_result=last_check,
            audit=audit,
            attempts=public_attempts,
            a2a_review=a2a_review,
            applied=False,
            errors=errors,
        )

    applied_paths = _apply_files(last_blocks, base)
    commit_sha: Optional[str] = None
    if git_commit_msg and applied_paths:
        commit_sha, git_err = _git_add_commit(applied_paths, base, git_commit_msg)
        if git_err:
            errors.append(git_err)

    return ShipResult(
        task=task,
        files_planned=last_files_planned,
        check_result=last_check,
        audit=audit,
        attempts=public_attempts,
        a2a_review=a2a_review,
        applied=True,
        git_commit=commit_sha,
        errors=errors,
    )


def _try_once(
    engine: Any,
    task: str,
    retry_ctx: Optional[dict],
    run_runtime_check: bool,
    run_runtime_args_check: bool,
    runtime_timeout: int,
    base_dir: Optional[Path] = None,
) -> dict:
    """One generate-stage-check cycle · returns dict with raw/files/blocks/check_result.

    If retry_ctx provided · builds an augmented prompt referencing the prior
    attempt's failed checks and file paths.

    If base_dir provided AND task wording triggers MINIMAL CHANGE MODE
    (per cycle 12 P0 prompt phrases) · runs check_semantic_preservation on
    each staged file that has an existing original at base_dir/path.
    """
    prompt = task if retry_ctx is None else _build_retry_prompt(task, retry_ctx)
    raw = engine.generate(prompt)
    blocks = engine.parse_file_blocks(raw)

    files_planned = [
        {"path": b["path"], "size": len(b["content"]), "lang": b.get("lang", "")}
        for b in blocks
    ]
    if not blocks:
        return {
            "raw_response_chars": len(raw),
            "files_planned": [],
            "blocks": [],
            "check_result": {"passed": False, "checks": []},
        }

    staging = Path(tempfile.mkdtemp(prefix="nautilus_engine_staging_"))
    try:
        staged = _write_staging(blocks, staging)
        check_result = run_pipeline(
            staged,
            run_runtime=run_runtime_check,
            run_runtime_args=run_runtime_args_check,
            runtime_timeout=runtime_timeout,
        )
        if base_dir is not None and should_apply_semantic_check(task):
            extra = _run_semantic_checks(blocks, staging, base_dir)
            if extra:
                check_result["checks"].extend(extra)
                check_result["passed"] = check_result["passed"] and all(
                    c["passed"] for c in extra
                )
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    return {
        "raw_response_chars": len(raw),
        "files_planned": files_planned,
        "blocks": blocks,
        "check_result": check_result,
    }


def _run_semantic_checks(
    blocks: list[dict], staging: Path, base_dir: Path
) -> list[dict]:
    """For each block whose target file already exists under base_dir, run
    check_semantic_preservation (staged vs original) and return asdict results.

    New files (no original on disk) are skipped · semantic preservation is
    vacuous when there is nothing to preserve.
    """
    out: list[dict] = []
    for b in blocks:
        original = (base_dir / b["path"]).resolve()
        try:
            original.relative_to(base_dir)
        except ValueError:
            continue  # path escape (already filtered by _write_staging too)
        if not original.is_file():
            continue
        staged = (staging / b["path"]).resolve()
        if not staged.is_file():
            continue
        out.append(asdict(check_semantic_preservation(str(original), str(staged))))
    return out


def _inject_file_context(
    task: str, base_dir: Path, max_chars_per_file: int = 8000
) -> str:
    """Read every file mentioned in `task` that exists under base_dir and
    prepend its content to the prompt as a CONTEXT block. Returns the task
    unchanged when no matches resolve.

    Karpathy Fix 1 · gives the LLM ground truth so MINIMAL CHANGE MODE
    (cycle 12 P0) has real lines to preserve.
    """
    pattern = re.compile(r"[\w/\-_.\\]+\.(?:py|js|ts|tsx|md|sql|yaml|yml|json|sh|go|rs)\b")
    found = sorted(set(pattern.findall(task)))
    blocks: list[str] = []
    for rel in found:
        target = (base_dir / rel).resolve()
        try:
            target.relative_to(base_dir)
        except ValueError:
            continue
        if not target.is_file():
            continue
        try:
            content = target.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if len(content) > max_chars_per_file:
            continue
        blocks.append(
            f"CONTEXT for {rel} (preserve unless task explicitly says otherwise):\n"
            f"```\n{content}\n```\n"
        )
    if not blocks:
        return task
    return "\n".join(blocks) + "\n" + task


def _build_retry_prompt(task: str, prev: dict) -> str:
    """Compose retry prompt from original task + failed-check details."""
    failed = [c for c in prev.get("check_result", {}).get("checks", []) if not c.get("passed")]
    err_lines = "\n".join(
        f"- [{c['name']}] {((c.get('message') or '').strip())[:240]}"
        for c in failed
    ) or "- (no specific check messages · static pipeline reported failure)"
    file_lines = "\n".join(
        f"- {f['path']} ({f['size']} chars)" for f in prev.get("files_planned", [])
    ) or "- (no files emitted on previous attempt)"
    return (
        f"Original task: {task}\n\n"
        f"Your previous attempt produced these files:\n{file_lines}\n\n"
        f"But these checks FAILED:\n{err_lines}\n\n"
        f"Please re-generate the COMPLETE file(s) addressing every failure above. "
        f"Emit each file using the strict code-block convention from your system prompt."
    )


# ---------- internals ----------

def _write_staging(blocks: list[dict], staging: Path) -> list[str]:
    paths: list[str] = []
    for b in blocks:
        stage = (staging / b["path"]).resolve()
        try:
            stage.relative_to(staging)
        except ValueError:
            continue  # skip path escapes even in staging
        stage.parent.mkdir(parents=True, exist_ok=True)
        stage.write_text(b["content"], encoding="utf-8")
        paths.append(str(stage))
    return paths


def _apply_files(blocks: list[dict], base: Path) -> list[str]:
    written: list[str] = []
    for b in blocks:
        target = (base / b["path"]).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            continue  # reject path escape
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(b["content"], encoding="utf-8")
        written.append(b["path"])
    return written


def _git_add_commit(
    rel_paths: list[str], cwd: Path, msg: str
) -> tuple[Optional[str], Optional[str]]:
    """Stage + commit rel_paths in cwd · return (sha, error_or_None)."""
    try:
        for rp in rel_paths:
            subprocess.run(
                ["git", "-C", str(cwd), "add", rp],
                check=True, capture_output=True, text=True,
            )
        subprocess.run(
            ["git", "-C", str(cwd), "commit", "-q", "-m", msg],
            check=True, capture_output=True, text=True,
        )
        sha = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        return sha, None
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e))[:300]
        return None, f"git commit failed: {err}"
    except Exception as e:
        return None, f"git error: {type(e).__name__}: {str(e)[:200]}"


def _maybe_request_a2a_review(
    task: str,
    blocks: list[dict],
    request: bool,
    targets: Optional[tuple],
    timeout_s: int,
    db_engine: Any,
) -> Optional[dict]:
    """Optionally call engine.a2a_review.request_review() · returns asdict(result)."""
    if not request:
        return None
    try:
        from engine.a2a_review import request_review, DEFAULT_TARGETS
        from dataclasses import asdict
    except Exception as e:
        return {"error": f"a2a_review import failed: {type(e).__name__}: {e}"[:200]}

    # Engine emits full files · build a synthetic 'diff' for review message
    diff_lines: list[str] = []
    for b in blocks[:5]:
        diff_lines.append(f"--- file: {b['path']} ({len(b['content'])} chars) ---")
        diff_lines.append(b["content"][:600])
    code_diff = "\n".join(diff_lines)[:2000]

    targets = targets or DEFAULT_TARGETS
    # Review fix Important #3 · was abs(hash()) · Python's hash is salted per
    # process (PYTHONHASHSEED) · same task produced different IDs across runs.
    # Use hashlib for a stable, cross-process correlatable ID.
    import hashlib as _hashlib
    task_id = "engineship_" + _hashlib.sha256(task.encode("utf-8")).hexdigest()[:16]
    try:
        result = request_review(
            task_id=task_id,
            code_diff=code_diff,
            repo_map_snippet="",
            target_agents=targets,
            timeout_s=timeout_s,
            poll_interval_s=2,
            db_engine=db_engine,
        )
        return asdict(result)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:200]}"}


def _maybe_dispatch_audit(
    task: str,
    blocks: list[dict],
    dispatch: bool,
    url: str,
    api_key: Optional[str],
) -> Optional[dict]:
    if not dispatch:
        return None
    if not api_key:
        return {"skipped": True, "reason": "no API key (set NAUTILUS_API_KEY)"}

    spec_lines = [f"Task: {task}", "", "Generated files:"]
    for b in blocks:
        spec_lines.append(
            f"- {b['path']} ({len(b['content'])} chars · {b.get('lang', '')})"
        )
    spec = "\n".join(spec_lines)[:9000]

    body = {
        "task_spec": spec,
        "budget_nau": 10,
        "deadline_hours": 1,
        "title": f"engine-ship · {task[:100]}",
        "task_type": "general",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "nautilus-engine-ship/0.1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return payload.get("data", {}) or {}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "skipped": False}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:200]}", "skipped": False}