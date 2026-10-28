"""函数即记忆实验(diff 文本 vs 可调用函数形态注入)· 预注册 2026-09-08。

假设(理论总账 T6 机制推论):自家矿 diff 注入无增益(L2:B=C<A)的机制之一
是"diff 文本在模型分布内"(模型见过大量 diff),而"可调用函数+调用接口"改变
了任务的表征形态。预测:**函数形态注入的首轮通过 > diff 文本注入**。

预注册判据(冻结,跑前写定):
- 复用 L2 holdout 同 8 题(同题同模型同单轮,k3);A/C 引用 L2 既有读数
  (A 无注入 5/8;C=diff 注入 3/8),本实验只新跑 B'=函数形态注入臂(8 次)
- 主门:B' 首轮通过 > C'(diff 形态,3/8)——机制差异成立
- 强门:B' > A(5/8)——净增益成立(超过裸考才算真有用)
- 次门:token 均值不失控(<2× A 臂 15046)
- 停机:2026-09-15;改写器 prompt 冻结于本文件 REWRITE_PROMPT

方法:B' 注入物 = L2 arm_b 记忆的 winning_diff 经冻结 prompt 改写为
"可调用修复函数 + 何时调用 + 参数"形态;改写产物落盘供审计。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import g2_b1_agentic_runner as runner  # noqa: E402
import g2_b1_executor_agent as ex  # noqa: E402
from g2_b1_l2_memory_experiment import _infer_repo  # noqa: E402

BACKEND = TOOLS.parent
L2_DIR = BACKEND / "docs/evidence/g2b1_l2_20260908"
EXT_DIR = BACKEND / "docs/evidence/g2b1_funcmem_20260908"
HOLDOUT = L2_DIR / "l2_holdout_20260908.jsonl"
PROVIDER = "chunxiao_k3"

REWRITE_PROMPT = (
    "You convert a git patch into a reusable Python FIX FUNCTION. Output ONLY "
    "one Python code block: a function named fix_<topic> that, when applied to "
    "the affected module's inputs/state, implements the FIXED behavior shown "
    "in the patch. Include a one-line docstring: WHEN to call it (the bug "
    "symptom) and WHAT it fixes. No explanation outside the code block.\n\n"
    f"Patch:\n```diff\n{{diff}}\n```"
)

# L2 参照读数(冻结引用,不重跑)
L2_A_FIRST_PASS, L2_C_FIRST_PASS = 5, 3  # n=8;C = 相似 diff 注入臂


def _rewrite(completer, diff: str) -> str:
    raw = completer(REWRITE_PROMPT.replace("{diff}", diff))
    return raw.get("content", "").strip()


def _arm_injector(func_text: str | None):
    orig = runner.build_prompt

    def wrapped(test_id, red_tail, source_rel, source_text, feedback):
        base = orig(test_id, red_tail, source_rel, source_text, feedback)
        if not func_text:
            return base
        return ("REUSABLE FIX FUNCTION from a similar past bug (advisory only "
                "— the repo below is at a different state; call or adapt the "
                "pattern, do NOT paste verbatim):\n"
                f"--- past fix function:\n{func_text}\n--- end reference ---\n\n"
                + base)

    return wrapped


def _run_task_retry(repo, task, completer, tag, tries: int = 3):
    for attempt in range(1, tries + 1):
        try:
            return ex.run_task(repo, task, completer, tag, EXT_DIR)
        except Exception as exc:
            print(f"  [retry {attempt}/{tries}] {exc}", flush=True)
            if attempt < tries:
                time.sleep(90)
    return None


def main() -> int:
    rows = [json.loads(l) for l in
            HOLDOUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    completer = ex.make_completer(PROVIDER)
    EXT_DIR.mkdir(parents=True, exist_ok=True)

    # Step0: rewrite every arm_b memory once (idempotent cache file)
    cache_p = EXT_DIR / "func_rewrites.json"
    cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    for i, row in enumerate(rows, 1):
        mem = row.get("arm_b")
        if not mem:
            continue
        key = mem["reference_fix_commit"][:10]
        if key in cache:
            continue
        cache[key] = _rewrite(completer, mem["winning_diff"])
        print(f"[rewrite {i}] {key}: {len(cache[key])} chars", flush=True)
        cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=1),
                           encoding="utf-8")

    # Step1: B' arm on the same 8 holdout tasks (A/C cite L2, frozen)
    results = []
    for i, row in enumerate(rows, 1):
        # _infer_repo: repo_path 为 None/失效时按 source_files 前缀兜底(L2 同款)
        task, repo = row["task"], _infer_repo(row["task"])
        mem = row.get("arm_b")
        func_text = cache.get(mem["reference_fix_commit"][:10]) if mem else None
        if repo is None:  # 兜底仍失败:跳过记数,不崩整场
            print(f"[{i}/8] B' skip: repo unresolvable", flush=True)
            continue
        runner.build_prompt = _arm_injector(func_text)
        ev = _run_task_retry(Path(repo), task, completer,
                             f"fmB-{PROVIDER}")
        if ev is None:
            print(f"[{i}/8] B' ERROR after retries", flush=True)
            continue
        turns = ev.get("turns") or [{}]
        fp = bool(turns[0].get("test_passed"))
        results.append((fp, ev.get("total_tokens", 0)))
        print(f"[{i}/8] B' first_pass={fp} tokens={ev.get('total_tokens')}",
              flush=True)

    n_pass = sum(1 for fp, _ in results if fp)  # 9/9 修:原 sum(1 for fp,_) 数的是条目数,自报 11/11 掩盖强门 FAIL(实测 4/8)
    toks = [t for _, t in results] or [0]
    print("=== 函数即记忆读数(首轮判据,n=8 holdout 复用)===", flush=True)
    print(f"  A(裸考,L2 引用): {L2_A_FIRST_PASS}/8", flush=True)
    print(f"  C(diff 注入,L2 引用): {L2_C_FIRST_PASS}/8", flush=True)
    print(f"  B'(函数注入,新跑): {n_pass}/{len(results)} "
          f"mean_tokens={sum(toks) / len(toks):.0f}", flush=True)
    gate1 = n_pass > L2_C_FIRST_PASS
    gate2 = n_pass > L2_A_FIRST_PASS
    print(f"主门 B'>C': {'PASS(机制差异成立)' if gate1 else 'FAIL'}; "
          f"强门 B'>A: {'PASS(净增益)' if gate2 else 'FAIL'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
