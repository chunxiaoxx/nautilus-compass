"""Soul service · shared self-modify capability over engine.ship().

Two entry points, shared by the queue consumer and (later) a sync HTTP endpoint:

- generate(): dry-run only · returns files + check result · writes nothing
- ship_to_draft_pr(): apply to a NEW branch + commit + pr_gate + `gh pr create --draft`

NEVER applies to master. NEVER auto-merges. A draft PR + human review is the
final merge gate. Dependency-injected ship/subprocess for testability.
"""
from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
from typing import Optional, Callable


def _default_engine_factory(base_dir: str, dry_run: bool):
    from engine.nautilus_engine import NautilusEngine
    return NautilusEngine(base_dir=base_dir, dry_run=dry_run)


def _loc_estimate(files_planned: list) -> int:
    # ~40 chars/line rough estimate (engine reports byte size per file)
    return sum(int(f.get("size", 0)) for f in files_planned) // 40


def generate(
    task: str,
    base_dir: str,
    cycle_id: Optional[str] = None,
    capture_content: bool = False,
    _ship: Optional[Callable] = None,
    _engine_factory: Optional[Callable] = None,
) -> dict:
    """Dry-run generation. Returns {success, files_planned, check_result, cycle_id}.

    capture_content=True applies the generation into a throwaway temp dir, reads the
    real generated file contents back (attached as a "content" key on each
    files_planned entry), then removes the temp dir. The caller's base_dir and master
    are NEVER written. Default (False) is byte-identical to the lean dry-run.
    """
    if _ship is None:
        from engine.ship import ship as _ship
    factory = _engine_factory or _default_engine_factory

    if not capture_content:
        engine = factory(base_dir, True)
        result = _ship(
            engine, task, base_dir,
            apply=False, dispatch_audit=False,
            cycle_id=cycle_id, emit_outcome_telemetry=True,
        )
        return {
            "success": bool(result.check_result.get("passed")),
            "files_planned": result.files_planned,
            "check_result": result.check_result,
            "cycle_id": cycle_id,
        }

    # capture_content: apply into an isolated temp dir to recover real generated code
    tmp = tempfile.mkdtemp(prefix="soul-capture-")
    try:
        engine = factory(tmp, False)
        result = _ship(
            engine, task, tmp,
            apply=True, dispatch_audit=False,
            cycle_id=cycle_id, emit_outcome_telemetry=True,
        )
        tmp_real = os.path.realpath(tmp)
        files = []
        for f in result.files_planned:
            content = ""
            # Containment guard: the engine silently SKIPS escaping paths on write but
            # still lists them in files_planned, so an LLM-emitted "../.." or absolute
            # path must never read a file outside tmp (arbitrary-file disclosure).
            fp = os.path.realpath(os.path.join(tmp, f.get("path", "")))
            if fp == tmp_real or fp.startswith(tmp_real + os.sep):
                try:
                    with open(fp, encoding="utf-8") as fh:
                        content = fh.read()
                except OSError:
                    pass
            files.append({**f, "content": content})
        return {
            "success": bool(result.check_result.get("passed")),
            "files_planned": files,
            "check_result": result.check_result,
            "cycle_id": cycle_id,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def ship_to_draft_pr(
    task: str,
    base_dir: str,
    branch: str,
    commit_msg: str,
    cycle_id: Optional[str] = None,
    _ship: Optional[Callable] = None,
    _engine_factory: Optional[Callable] = None,
    _runner: Callable = subprocess.run,
) -> dict:
    """Dry-run → pr_gate → apply on a NEW branch → commit → draft PR.

    Returns {success, stage?, detail?, pr_url?, branch, commit?, cycle_id}.
    Never touches master; never auto-merges.
    """
    from services.soul_pr_gate import gate

    # 1. Dry-run first to inspect the diff for the gate
    dry = generate(task, base_dir, cycle_id=cycle_id, _ship=_ship, _engine_factory=_engine_factory)
    if not dry["success"]:
        return {"success": False, "stage": "check", "detail": dry["check_result"], "cycle_id": cycle_id}

    changed = [f["path"] for f in dry["files_planned"]]
    ok, reason = gate(changed, _loc_estimate(dry["files_planned"]))
    if not ok:
        return {"success": False, "stage": "pr_gate", "detail": reason, "cycle_id": cycle_id}

    # 2. Apply on a fresh branch (NEVER master)
    if branch in ("master", "main"):
        return {"success": False, "stage": "branch", "detail": "refuse to ship to master/main", "cycle_id": cycle_id}
    self_ship = _ship
    if self_ship is None:
        from engine.ship import ship as self_ship
    factory = _engine_factory or _default_engine_factory

    def _cleanup_branch():
        _runner(["git", "-C", base_dir, "push", "origin", "--delete", branch],
                capture_output=True, text=True)
        _runner(["git", "-C", base_dir, "checkout", "master"],
                capture_output=True, text=True)
        _runner(["git", "-C", base_dir, "branch", "-D", branch],
                capture_output=True, text=True)

    _runner(["git", "-C", base_dir, "checkout", "-b", branch], capture_output=True, text=True, check=True)
    engine = factory(base_dir, False)
    result = self_ship(
        engine, task, base_dir,
        apply=True, dispatch_audit=False,
        git_commit_msg=commit_msg, cycle_id=cycle_id, emit_outcome_telemetry=True,
    )
    if not getattr(result, "applied", False):
        _cleanup_branch()
        return {"success": False, "stage": "apply", "detail": getattr(result, "errors", "apply failed"), "cycle_id": cycle_id}

    # 3. Push branch + open DRAFT PR (human review gate)
    push = _runner(["git", "-C", base_dir, "push", "-u", "origin", branch], capture_output=True, text=True)
    if getattr(push, "returncode", 1) != 0:
        _cleanup_branch()
        return {"success": False, "stage": "push", "detail": getattr(push, "stderr", "push failed"), "cycle_id": cycle_id}
    # SOUL_PR_BASE: target branch of the draft PR. Default `master` preserves
    # the pre-trunk-swap behavior; cloud units set `soul-distill-deploy` (the
    # single trunk since 2026-08-26) so PRs open against the live trunk.
    pr_base = os.getenv("SOUL_PR_BASE", "master")
    pr = _runner(
        ["gh", "pr", "create", "--draft", "--title", commit_msg[:80],
         "--body", f"Soul self-modify cycle {cycle_id}. DRAFT · human review required before merge.",
         "--base", pr_base, "--head", branch],
        cwd=base_dir, capture_output=True, text=True,
    )
    if getattr(pr, "returncode", 1) != 0:
        _cleanup_branch()
        return {
            "success": False,
            "stage": "pr_create",
            "detail": getattr(pr, "stderr", "") or "gh pr create failed",
            "branch": branch,
            "cycle_id": cycle_id,
        }
    pr_url = pr.stdout.strip() if getattr(pr, "returncode", 1) == 0 else ""
    commit_sha = getattr(result, "git_commit", None)
    # Return workspace to master so the next autonomous cycle starts clean
    _runner(["git", "-C", base_dir, "checkout", "master"], capture_output=True, text=True)
    return {
        "success": True, "pr_url": pr_url, "branch": branch,
        "commit": commit_sha, "cycle_id": cycle_id,
    }

def _llm_judge_rows(db, action, instructions):
    """裁决执行器(U34):reviewed 行→LLM 四门规则判→终态写回。平台代管件。"""
    from sqlalchemy import text as _t
    rows = db.execute(_t(
        "SELECT proposal_id, title, rationale FROM platform_proposals "
        "WHERE status='reviewed' ORDER BY created_at LIMIT 10")).fetchall()
    if not rows:
        return 'no reviewed rows'
    from agent_engine.llm.client import LLMClient
    llm = LLMClient()
    def _complete(prompt):
        for m in ('complete', 'chat', 'ask', 'generate'):
            if hasattr(llm, m):
                return getattr(llm, m)(prompt)
        raise RuntimeError('no llm method found')
    done = 0
    for pid, title, rat in rows:
        rc = str(title) + ' | ' + str(rat or '')
        prompt = ('你是组织评委。对以下治理提案给出裁决,只回一个词:'
                  'approved/rejected/archived,加一句理由。'
                  '四门规则:G-form(独白/无工件拒) G-dup(重复拒) '
                  'G-reality(已被现实超越归档) G-live(已执行归档)。'
                  '提案:' + str(rc)[:400])
        resp = _complete(prompt)
        v = str(resp).strip().lower()
        verdict = ('approved' if 'approved' in v[:20]
                   else ('archived' if 'archived' in v[:20] else 'rejected'))
        reason = str(resp).strip()[:120].replace(chr(10), ' ')
        db.execute(_t(
            'UPDATE platform_proposals SET status=:v, resolved_at=now(), '
            'resolved_by=:rb, resolution_note=:r WHERE proposal_id=:p'),
            {'v': verdict, 'rb': 'soul',
             'r': reason + ' | soul-jury-via-executor', 'p': pid})
        done += 1
    db.commit()
    return action + ': judged ' + str(done) + '/' + str(len(rows)) + ' rows'
