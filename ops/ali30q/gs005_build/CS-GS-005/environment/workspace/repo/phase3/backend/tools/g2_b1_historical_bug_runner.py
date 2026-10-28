"""G2-B1: run the Protocol-V2-shaped loop on a REAL historical bug.

Task source: this repository's own git history. A real bug (fixed by commit
FIX_COMMIT) is restored in a disposable buggy worktree; the executor model must
produce a unified diff; the verifier is the repository's own pytest (fail->pass).
Evidence is written to docs/evidence/. No synthetic fixture is involved.

Budget discipline (user-approved CNY 10 pool): one completion per run, no
retries; hard refuse if usage exceeds the conservative token cap below.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import httpx

PROVIDER = os.environ.get("G2B1_PROVIDER", "deepseek")
_CONFIGS = {
    "deepseek": ("https://api.deepseek.com", "deepseek-v4-flash", "DEEPSEEK_API_KEY"),
    "ark_glm": ("https://ark.cn-beijing.volces.com/api/v3", "glm-5-2-260617", "ARK_API_KEY"),
}
API_ORIGIN, MODEL, KEY_ENV = _CONFIGS[PROVIDER]
MAX_TOKENS = 16_384
# Conservative guard: ~200k total tokens cannot exceed CNY 10 at any published
# deepseek flash pricing. Fail-closed below this.
MAX_TOTAL_TOKENS = 200_000
CANDIDATE_SCHEMA_HINT = (
    '{"artifact_version":"g2-b1-candidate-v1","claimed_test_scope":'
    '["public_behavior"],"language":"python","summary_code":"<short_snake_slug>",'
    '"unified_diff":"<unified diff>"}'
)

SYSTEM_PROMPT = (
    "You are a precise bug-fixing engine. Return ONLY one JSON object, no "
    "markdown fences, matching exactly this schema: " + CANDIDATE_SCHEMA_HINT
)


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=600)


def _one_completion(api_key: str, prompt: str) -> dict:
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "max_tokens": MAX_TOKENS,
    }
    with httpx.Client(
        base_url=API_ORIGIN,
        timeout=httpx.Timeout(900),
        follow_redirects=False,
        trust_env=False,
    ) as http:
        response = http.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
        )
    if response.status_code != 200:
        raise RuntimeError(f"http_{response.status_code}")
    document = response.json()
    usage = document.get("usage", {})
    total = usage.get("total_tokens", 0) or 0
    if total > MAX_TOTAL_TOKENS:
        raise RuntimeError("budget_cap_exceeded")
    choice = document["choices"][0]
    content = choice["message"].get("content") or ""
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()
    return {
        "content": stripped,
        "usage": usage,
        "model": document.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "content_len": len(stripped),
    }


def main(buggy_root: Path, test_id: str, source_rel: Path) -> int:
    api_key = os.environ.get(KEY_ENV)
    if not api_key:
        raise SystemExit(f"{KEY_ENV} missing")

    backend = buggy_root / "phase3" / "backend"
    source_path = backend / source_rel
    source_text = source_path.read_text(encoding="utf-8")

    red = _run(
        [sys.executable, "-m", "pytest", test_id, "-q", "--confcutdir=tests/platform_protocol"],
        cwd=backend,
    )
    red_failed = red.returncode != 0

    prompt = (
        "Fix a real bug in this repository.\n\n"
        f"Failing test (currently RED):\n{test_id}\n\n"
        "Full failing test output (read the traceback carefully before patching):\n\n"
        f"--- pytest output ---\n{red.stdout.decode('utf-8', 'replace')[-4000:]}\n--- end pytest output ---\n\n"
        "Relevant source file (contains the bug):\n"
        f"--- {source_rel} ---\n{source_text}\n\n"
        "Produce the minimal unified diff (a/... b/... headers) that makes the "
        "failing test pass. Output only the JSON object per the system schema; "
        "unified_diff must apply cleanly with git apply."
    )

    result = _one_completion(api_key, prompt)
    if not result["content"]:
        raise SystemExit(
            f"empty_content finish_reason={result['finish_reason']} usage={result['usage']}"
        )
    _content = result["content"]
    _start = _content.find("{")
    _end = _content.rfind("}")
    if _start == -1 or _end <= _start:
        (backend / "docs/evidence/.g2b1-last-content.txt").write_text(_content[:20000], encoding="utf-8")
        raise SystemExit("content_not_json")
    candidate = json.loads(_content[_start : _end + 1])
    diff = candidate["unified_diff"]

    # Apply patch in the disposable buggy worktree.
    patch_file = backend / "_g2b1.patch"
    if not diff.endswith(chr(10)):
        diff += chr(10)
    patch_file.write_text(diff, encoding="utf-8")
    applied = _run(["git", "apply", "--recount", "--whitespace=nowarn", str(patch_file)], backend)
    if applied.returncode != 0:
        # Model diffs often use backend-relative paths; git resolves from repo root.
        applied = _run(
            ["git", "apply", "--recount", "--directory=phase3/backend",
             "--whitespace=nowarn", str(patch_file)],
            buggy_root,
        )
    patch_applied = applied.returncode == 0
    apply_error = applied.stderr.decode("utf-8", "replace")[:500] if not patch_applied else ""
    if not patch_applied:  # keep local copy for offline diagnosis; never committed
        (backend / "docs/evidence/.g2b1-last-failed.patch").write_text(diff, encoding="utf-8")

    test_passed = False
    if patch_applied:
        green = _run(
            [sys.executable, "-m", "pytest", test_id, "-q", "--confcutdir=tests/platform_protocol"],
            cwd=backend,
        )
        test_passed = green.returncode == 0
        _run(["git", "checkout", "--", "."], backend)  # restore buggy state
    patch_file.unlink(missing_ok=True)

    evidence = {
        "schema_version": "g2-b1-historical-bug-run-v1",
        "context_mode": "with_traceback",
        "task_source": "nautilus-core git history (real bug, no synthetic fixture)",
        "buggy_commit": "5ea2fc32dc088db3e57b1edc0d96f7c5f8a3f172",
        "reference_fix_commit": "c7646a57f97a7182225486e7c65841b9a95f915b",
        "test_id": test_id,
        "red_confirmed_before_call": red_failed,
        "model": result["model"],
        "provider": PROVIDER,
        "usage": result["usage"],
        "patch_applied": patch_applied,
        "apply_error": apply_error,
        "test_passed_after_patch": test_passed,
        "summary_code": candidate.get("summary_code"),
    }
    out = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "evidence"
        / f"g2-b1-historical-bug-run-{PROVIDER}-20260822.json"
    )
    out.write_text(json.dumps(evidence, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=1))
    return 0 if test_passed else 1


if __name__ == "__main__":
    buggy = Path(sys.argv[1])
    raise SystemExit(
        main(
            buggy,
            "tests/platform_protocol/test_g2_a0_model_gate_v5_fail_closed.py::"
            "test_v5_live_probe_uses_only_mock_transport_and_exact_three_requests",
            Path("tests/platform_protocol/g2_a0_model_gate_v5_cli.py"),
        )
    )
