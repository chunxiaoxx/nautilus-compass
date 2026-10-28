"""soul canonical verify · reward loop 第二刀的独立验证端。

职责:对一条 GenOpt 轨迹做独立于生产者的分数复现,复现一致才 PATCH
`/api/platform/fde/verdict/{verdict_id}/external-verify`(income 唯一入账门)。

防橡皮图章契约(硬):
  1. 轨迹必须携带完整 best 解(len >= 500)——160/300 字符 preview 一律拒,
     绝不 fallback。旧 H800 轨迹因此永远过不了这道门(诚实)。
  2. 轨迹带 best_solution_sha256 时必须与解文本对账。
  3. verifier 独立重跑 2 次:两次分差 > 1e-9 → NONDETERMINISTIC,拒。
  4. |reproduced - claimed| <= tolerance(默认 0.01)才 MATCH;否则 MISMATCH,拒。

stdlib only(urllib)——cloud 上零依赖直接跑。

Usage:
    python soul_canonical_verify.py --task-dir <task_root> \
        --trajectory <traj.json> --verdict-id <verdict_id> \
        --platform-url http://localhost:8000 [--tolerance 0.01] [--dry-run]

Exit codes: 0=MATCH(+PATCH ok) · 2=NotReproducible · 3=MISMATCH/NONDETERMINISTIC
            · 4=PATCH http failed
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

# 低于此长度的 "解" 视为截断产物(实测 preview=160/300 · 真解 5-15KB)。
MIN_FULL_SOURCE_LEN = 500

VERIFIER_SOURCE = "soul-canonical-verify"


class NotReproducible(Exception):
    """轨迹不携带可独立复现的完整解。"""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_best_solution(traj: dict) -> tuple[str, float]:
    """取完整 best 解 + claimed 分数;取不到完整解 → NotReproducible。"""
    claimed = traj.get("best_score")
    if claimed is None:
        raise NotReproducible("trajectory has no best_score")
    claimed = float(claimed)

    code = None
    top = traj.get("best_round_source")
    if isinstance(top, str) and len(top) >= MIN_FULL_SOURCE_LEN:
        code = top
    else:
        # 扫 rounds:score == best_score 的轮 · 兼容两种 producer 格式
        #   gpt55_local_runner: rounds[].source + rounds[].metrics.combined_score
        #   gapclosed_runner:   rounds[].candidate_code + rounds[].score
        for r in traj.get("rounds", []):
            score = r.get("score")
            if score is None:
                score = (r.get("metrics") or {}).get("combined_score")
            if score is None or abs(float(score) - claimed) > 1e-9:
                continue
            cand = r.get("source") or r.get("candidate_code")
            if isinstance(cand, str) and len(cand) >= MIN_FULL_SOURCE_LEN:
                code = cand
                break

    if code is None:
        raise NotReproducible(
            f"no full best solution in trajectory (need len >= {MIN_FULL_SOURCE_LEN}; "
            f"preview-only trajectories are rejected by design)")

    want_sha = traj.get("best_solution_sha256")
    if want_sha and _sha256(code) != want_sha:
        raise NotReproducible(
            f"best_solution_sha256 mismatch: trajectory={want_sha[:12]}… "
            f"actual={_sha256(code)[:12]}…")

    return code, claimed


def reproduce_score(task_dir: str, code: str, python_exe: str = sys.executable,
                    timeout: int = 1200) -> float:
    """独立重跑 verification/evaluate.py,返回 combined_score。"""
    eval_py = os.path.join(task_dir, "verification", "evaluate.py")
    if not os.path.isfile(eval_py):
        raise RuntimeError(f"verifier not found: {eval_py}")
    baseline = os.path.join(task_dir, "baseline", "init.py")
    # --baseline 只在该 verifier 声明了此参数时传(部分 verifier 不认,传了必炸)。
    with open(eval_py, encoding="utf-8") as f:
        accepts_baseline = "--baseline" in f.read()

    with tempfile.TemporaryDirectory(prefix="soul_verify_") as td:
        cand = os.path.join(td, "candidate.py")
        with open(cand, "w", encoding="utf-8") as f:
            f.write(code)
        cmd = [python_exe, eval_py, "--benchmark-dir", task_dir, "--candidate", cand]
        if accepts_baseline and os.path.isfile(baseline):
            cmd += ["--baseline", baseline]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, cwd=td)
        metrics_path = os.path.join(td, "metrics.json")
        if not os.path.isfile(metrics_path):
            raise RuntimeError(
                f"verifier produced no metrics.json (exit {proc.returncode}): "
                f"{proc.stderr[-300:]}")
        with open(metrics_path, encoding="utf-8") as f:
            metrics = json.load(f)

    if not metrics.get("valid"):
        raise RuntimeError(f"reproduced run invalid: {json.dumps(metrics)[:300]}")
    return float(metrics["combined_score"])


def verify(task_dir: str, traj: dict, tolerance: float = 0.01,
           python_exe: str = sys.executable) -> dict:
    """复现 + determinism 自检 + 容差判定。raises NotReproducible。"""
    code, claimed = load_best_solution(traj)
    s1 = reproduce_score(task_dir, code, python_exe=python_exe)
    s2 = reproduce_score(task_dir, code, python_exe=python_exe)
    if abs(s1 - s2) > 1e-9:
        return {"status": "NONDETERMINISTIC", "reproduced": s1, "reproduced_2nd": s2,
                "claimed": claimed}
    status = "MATCH" if abs(s1 - claimed) <= tolerance else "MISMATCH"
    return {"status": status, "reproduced": s1, "claimed": claimed,
            "tolerance": tolerance}


def patch_external_verify(platform_url: str, verdict_id: str, reproduced: float,
                          tolerance: float, timeout: int = 20) -> tuple[int, dict]:
    body = json.dumps({
        "verifier_source": VERIFIER_SOURCE,
        "reproduced_score": reproduced,
        "tolerance": tolerance,
    }).encode("utf-8")
    url = (platform_url.rstrip("/")
           + f"/api/platform/fde/verdict/{verdict_id}/external-verify")
    req = urllib.request.Request(url, data=body, method="PATCH",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            payload = {"raw": "unreadable error body"}
        return e.code, payload
    except urllib.error.URLError as e:
        return 0, {"error": f"connection failed: {e}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", required=True)
    ap.add_argument("--trajectory", required=True)
    ap.add_argument("--verdict-id", default=None,
                    help="要 PATCH 的 verdict_id;缺省 = 只复现不 PATCH")
    ap.add_argument("--platform-url",
                    default=os.environ.get("NAUTILUS_API_URL", "http://localhost:8000"))
    ap.add_argument("--tolerance", type=float, default=0.01)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    traj_path = args.trajectory
    if not os.path.isabs(traj_path):
        traj_path = os.path.join(args.task_dir, traj_path)
    with open(traj_path, encoding="utf-8") as f:
        traj = json.load(f)

    try:
        result = verify(os.path.abspath(args.task_dir), traj, tolerance=args.tolerance)
    except NotReproducible as e:
        print(json.dumps({"status": "NOT_REPRODUCIBLE", "reason": str(e)},
                         ensure_ascii=False))
        return 2

    print(json.dumps(result, ensure_ascii=False))
    if result["status"] != "MATCH":
        return 3

    if args.dry_run or not args.verdict_id:
        print("[dry-run/no-verdict-id] MATCH · skip PATCH", file=sys.stderr)
        return 0

    code, payload = patch_external_verify(
        args.platform_url, args.verdict_id, result["reproduced"], args.tolerance)
    print(json.dumps({"patch_http": code, "response": payload}, ensure_ascii=False))
    return 0 if code == 200 else 4


if __name__ == "__main__":
    sys.exit(main())
