"""G2-B1 variant generator core (batch 1 · design docs/plans/2026-08-28-variant-generation-design.md).

OP-1 受控回注:模板=四仓真实 fix 对;变体=在 fix 版代码上回注"变换后的 bug"。
变体行携带 variant_patch(unified diff,合成 starter),无合成 commit。

变体双门(合成版,executor variant 流执行,与模板同尺):
  门A' starter 必败:worktree@reference_fix_commit + apply variant_patch + ref 测试 → FAIL
  门B' 正解必过:worktree@reference_fix_commit 干净 + ref 测试 → PASS

novelty 门(防 v4 同质废料,预注册阈值 0.3):取「行骨架距离」与
「标识符距离」的较小者——纯常量/标识符改名两维全同 → 0 → 拒收。
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ARCHIVED_REPOS = {"nautilus-v5.archived-20260827"}
NOVELTY_THRESHOLD = 0.3

_SHAPE_TOKEN = re.compile(r'"[^"]*"|\'[^\']*\'')
_SHAPE_NUM = re.compile(r"\b\d+\b")
_SHAPE_CONST = re.compile(r"\b[A-Z_][A-Z0-9_]{1,}\b")
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def select_templates(rows: list[dict], limit: int) -> list[dict]:
    """批1 模板筛选:排除归档仓;只留 fix( 语义 subject;单源文件与 core/compass 优先。"""
    pool = [r for r in rows
            if r["repo_path"].rsplit("\\", 1)[-1].rsplit("/", 1)[-1] not in ARCHIVED_REPOS
            and r.get("subject", "").startswith("fix(")
            and r.get("source_files") and r.get("test_files")]
    repo_rank = {"nautilus-core": 0, "nautilus-compass": 1,
                 "nautilus-fde-phase3": 2, "nautilus-v5": 3}
    pool.sort(key=lambda r: (len(r["source_files"]),
                             repo_rank.get(r["repo_path"].rsplit("\\", 1)[-1], 9)))
    return pool[:limit]


def _shape(line: str) -> str:
    s = _SHAPE_CONST.sub("?", _SHAPE_NUM.sub("?", _SHAPE_TOKEN.sub("'?'", line)))
    return " ".join(s.split())


def _diff_lines(diff: str):
    """diff 文本 → (原始增删行集, 行骨架集, 结构标识符集) 三元组。"""
    raw, shapes, words = set(), set(), set()
    for line in diff.splitlines():
        if line[:1] not in ("+", "-") or line.startswith(("+++", "---")):
            continue
        body = line[1:].strip()
        if not body:
            continue
        raw.add(body)
        shapes.add(_shape(body))
        for w in _WORD.findall(body):
            if not w.isdigit() and not (len(w) >= 2 and w.isupper()):
                words.add(w.lower())
    return raw, shapes, words


def _jaccard_dist(a: set, b: set) -> float:
    union = a | b
    if not union:
        return 0.0
    return 1.0 - len(a & b) / len(union)


def novelty_score(t_diff_sig, v_diff_sig) -> float:
    """二维取小:结构骨架与标识符任一同构 → 视为近克隆拒收。"""
    _, t_shape, t_words = t_diff_sig
    _, v_shape, v_words = v_diff_sig
    return min(_jaccard_dist(t_shape, v_shape), _jaccard_dist(t_words, v_words))


def variant_task_uid(ref_hash10: str, op: str, n: int) -> str:
    """合成内容哈希命名空间——不与模板 ref10 对账前缀域冲突。"""
    h = hashlib.sha1(f"{ref_hash10}|{op}|{n}".encode()).hexdigest()[:12]
    return f"g2b1:{h}"


def make_variant_row(tpl: dict, op: str, n: int, patch: str) -> dict:
    ref = tpl["reference_fix_commit"]
    return {
        "schema_version": "g2-b1-task-v1",
        "task_uid": variant_task_uid(ref[:10], op, n),
        "buggy_commit": ref,           # 变体起点=模板 fix;合成 bug 由 patch 表达
        "reference_fix_commit": ref,
        "subject": f"{tpl.get('subject', 'fix(variant)')} [variant:{op}]",
        "test_files": list(tpl["test_files"]),
        "source_files": list(tpl["source_files"]),
        "repo_path": tpl["repo_path"],
        "variant_of": f"g2b1:{ref[:12]}",
        "template_task_uid": f"g2b1:{ref[:12]}",
        "variant_op": op,
        "variant_patch": patch,
    }


# ---------- OP-1 LLM 提案 + 变体双门(批1 主流程) ----------

_DIFF_FENCE = re.compile(r"```[a-z]*\n(.*?)```", re.S)

PROMPT_TMPL = """You are synthesizing a bug-injection VARIANT of a real fix, for an SWE repair benchmark.
Given the reference fix diff (bug -> fix), output ONE unified diff (git format, a/ b/ prefixes) that re-introduces a DIFFERENT bug into the fixed code.

Op {op}:
- 1a (value variant): wrong constant / boundary / direction (off-by-one reversed, wrong default, swapped operand).
- 1b (condition variant): invert or tighten a guard, swallow an exception branch.

Rules:
- Touch ONLY these file(s): {sources}
- The patched code must stay syntactically valid and importable.
- The existing test suite must FAIL after applying your diff, and PASS after reverting it.
- Do NOT just rename identifiers or change constants cosmetically (a novelty gate rejects near-clones).
- Output the raw unified diff and nothing else, wrapped in a ```diff fence.

Reference fix diff:
```diff
{diff}```
"""


def propose_patch(completer, template_diff: str, sources: list[str],
                  op: str) -> str | None:
    """LLM 提案回注 diff;非 diff 回复返回 None(由 novelty/双门把无效提案筛掉)。

    executor completer 带 agentic SYSTEM_PROMPT,模型倾向回 JSON artifact
    ({"unified_diff": "..."}),8/28 pilot 实测 proposed=0 即此因——优先解包。"""
    prompt = PROMPT_TMPL.format(op=op, sources=", ".join(sources),
                                diff=template_diff)
    reply = completer(prompt)
    if isinstance(reply, dict):          # executor completer 形状 {content, usage, ...}
        reply = reply.get("content")
    if not reply:
        return None
    text = reply.strip()
    if text.startswith("{"):
        try:
            inner = json.loads(text).get("unified_diff")
            if inner:
                text = str(inner).strip()
        except ValueError:
            m_json = re.search(r'"unified_diff"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
            if m_json:                   # 截断 JSON 的兜底
                text = m_json.group(1).encode().decode("unicode_escape").strip()
    m = _DIFF_FENCE.search(text)
    text = (m.group(1) if m else text).strip()
    if not (text.startswith(("---", "diff --git")) and "+++ " in text
            and "@@" in text):
        return None
    return text + ("" if text.endswith("\n") else "\n")


def verify_variant(repo_path: str, row: dict, timeout: int = 600) -> dict:
    """变体双门(合成版):门A' fix树+patch 必败;门B' 干净 fix 树必过。

    测试已是 fix 版(起点=fix commit),pytest 的 cwd=tests/ 的 backend 根
    (与 executor 的 _backend_root_of 同规)。"""
    import subprocess
    import sys
    import tempfile

    ref = row["reference_fix_commit"]
    files = row.get("test_files") or []
    first = files[0] if files else ""
    parts = Path(first).parts
    backend_rel = ""
    for i, part in enumerate(parts):
        if part == "tests" and i > 0:
            backend_rel = "/".join(parts[:i])
            break

    def pytest_ok() -> bool:
        rel = [(Path(f).relative_to(backend_rel) if backend_rel else Path(f)).as_posix()
               for f in files]
        r = subprocess.run(
            [sys.executable, "-m", "pytest", *rel, "-q", "--no-header",
             "-p", "no:cacheprovider"],
            cwd=str(base), capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout)
        return r.returncode == 0 and "no tests ran" not in (r.stdout or "")

    wt = Path(tempfile.mkdtemp(prefix="g2b1_var_"))
    try:
        rc = subprocess.run(
            ["git", "-c", "core.autocrlf=false", "worktree", "add", "--detach",
             str(wt), ref], cwd=repo_path, capture_output=True, timeout=900)
        if rc.returncode != 0:
            return {"passed": False, "reason": "worktree_fail"}
        base = wt / backend_rel if backend_rel else wt
        ap = subprocess.run(["git", "apply", "--whitespace=nowarn", "-"],
                            input=row["variant_patch"].encode("utf-8"),
                            cwd=str(wt), capture_output=True, timeout=60)
        if ap.returncode != 0:
            return {"passed": False, "reason": "apply_fail"}
        gate_a = not pytest_ok()                      # starter 必败
        subprocess.run(["git", "checkout", "--", "."], cwd=str(wt),
                       capture_output=True)           # revert → 干净 fix 树
        gate_b = pytest_ok()                          # 正解(revert)必过
        return {"gate_a_starter_fails": gate_a, "gate_b_fix_passes": gate_b,
                "passed": gate_a and gate_b}
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=repo_path, capture_output=True)


def template_diff(repo_path: str, ref: str, source_files: list[str]) -> str:
    import subprocess
    r = subprocess.run(
        ["git", "show", ref, "--", *source_files],
        cwd=repo_path, capture_output=True, timeout=120)
    return r.stdout.decode("utf-8", "replace")


def run_batch(queue_path: str, out_path: str, limit: int = 30,
              ops=("1a", "1b"), completer=None) -> dict:
    """批1 主流程:模板 → LLM 提案 → novelty 门 → 变体双门 → 过门写 jsonl。"""
    import json
    rows = [json.loads(l) for l in open(queue_path, encoding="utf-8") if l.strip()]
    templates = select_templates(rows, limit=limit)
    stats = {"templates": len(templates), "proposed": 0, "novelty_rejected": 0,
             "gate_rejected": 0, "gate_error": 0, "propose_error": 0, "passed": 0}
    out_rows = []
    for tpl in templates:
        diff = template_diff(tpl["repo_path"], tpl["reference_fix_commit"],
                             tpl["source_files"])
        if not diff.strip():
            continue
        sig_t = _diff_lines(diff)
        for op in ops:
            # fail-soft:提案调用(429 重试后仍败/网络)不崩批(8/28 pilot4 实证)
            try:
                patch = propose_patch(completer, diff, tpl["source_files"], op)
            except Exception:
                import time as _time
                stats["propose_error"] += 1
                _time.sleep(5)
                continue
            if not patch:
                continue
            stats["proposed"] += 1
            if novelty_score(sig_t, _diff_lines(patch)) < NOVELTY_THRESHOLD:
                stats["novelty_rejected"] += 1
                continue
            row = make_variant_row(tpl, op=op, n=1, patch=patch)
            # fail-soft:一个模板的门(超时/仓库异常)不能崩整批(8/28 pilot 实测:
            # 满载机器上 nautilus-core worktree add >300s,整批 TimeoutExpired)
            try:
                gate = verify_variant(tpl["repo_path"], row)
            except Exception:
                stats["gate_error"] += 1
                continue
            if not gate["passed"]:
                stats["gate_rejected"] += 1
                continue
            row["gate"] = {k: v for k, v in gate.items()}
            out_rows.append(row)
            stats["passed"] += 1
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    stats["out_path"] = str(out)
    return stats


def main() -> None:
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--provider", default="ark_glm",
                        help="ark_glm(默认)| none(dry-run,无 LLM)")
    args = parser.parse_args()

    if args.provider == "none":
        completer = lambda prompt: None  # noqa: E731 — dry-run
    else:
        import g2_b1_executor_agent as ex
        completer = ex.make_completer(args.provider)
        assert os.environ.get(ex.PROVIDERS[args.provider][2]), \
            f"missing env {ex.PROVIDERS[args.provider][2]}"
    stats = run_batch(args.queue, args.out, limit=args.limit,
                      completer=completer)
    print(stats)


if __name__ == "__main__":
    main()
