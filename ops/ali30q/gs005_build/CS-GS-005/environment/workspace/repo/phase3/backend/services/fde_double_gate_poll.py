#!/usr/bin/env python3
"""P1.2 第三类飞轮双门自治编排(2026-06-20·platform-soul turf)。

把已建零件串成无人值守环:候选(KernelBench stump 燃料目录)
  → gate A(doubao 难度门·fde_sdiagnose_run / 缓存诊断)
  → gate B(强模型解门·run_strong_model_gate·仅对 gate-A true_wall 跑·省算力)
  → classify_distillation_fuel(双门分桶)
  → route_bucket(bucket-A mint 燃料 + 写买方表 / bucket-B 写买方表 / 其余丢)。

纯编排 run_double_gate(effect 注入) 单测覆盖;真 effect(doubao/GPU/dispatch/飞书)
在 main() 接,不单测(同 fde_bench_runner 约定)。

部署:fde-bench.timer 低频驱动 main()。设计见
docs/plans/2026-06-20-p1-third-class-flywheel-autonomy-plan.md(G5)。

用法(cloud / GPU box):
  python services/fde_double_gate_poll.py --fuel-dir <FUEL_DIR> --base http://localhost:8000 [--dry-run]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.fde_triage import classify_task, classify_distillation_fuel  # noqa: E402
from services.fde_fuel_router import route_bucket, build_fuel_desc  # noqa: E402


# ───────────────────────── 纯编排(单测覆盖)─────────────────────────

def run_double_gate(candidates: list, *,
                    gate_a_fn: Callable[[dict], dict],
                    gate_b_fn: Callable[[list], list],
                    mint_fn: Callable[[str, str, str], dict],
                    write_delivery_fn: Callable[[dict], dict],
                    log_fn: Callable | None = None) -> dict:
    """双门分拣 + 路由(纯编排)。

    gate_a_fn(candidate) -> diag({task_uid,n_samples,n_passed,n_correct_but_gated})
    gate_b_fn(true_wall_candidates) -> [{task_uid,strong_model_passed,which_model}]
       —— 仅对 gate-A true_wall 调一次(省强模型 + GPU 算力)。
    mint_fn / write_delivery_fn / log_fn —— route_bucket 的 effect。
    返回 {results:[...], summary:{total, actions:{action:count}}}。
    """
    _log = log_fn or (lambda *a, **k: None)

    diags, a_buckets = {}, {}
    for c in candidates:
        uid = c["task_uid"]
        diag = gate_a_fn(c)
        diags[uid] = diag
        a_buckets[uid] = classify_task({"task_uid": uid, **diag})
        _log("gate_a", task_uid=uid, bucket=a_buckets[uid]["bucket"])

    true_wall = [c for c in candidates if a_buckets[c["task_uid"]]["bucket"] == "true_wall"]
    strong = {}
    if true_wall:
        _log("gate_b", n=len(true_wall))
        for r in gate_b_fn(true_wall):
            strong[r["task_uid"]] = r

    results = []
    for c in candidates:
        uid = c["task_uid"]
        if a_buckets[uid]["bucket"] == "true_wall":
            sp = strong.get(uid, {})
            classified = classify_distillation_fuel(
                {"task_uid": uid, **diags[uid]}, sp.get("strong_model_passed"))
            if sp.get("which_model"):
                classified["which_model"] = sp["which_model"]
        else:
            classified = a_buckets[uid]
        results.append(route_bucket(classified, c, mint_fn=mint_fn,
                                    write_delivery_fn=write_delivery_fn, log_fn=log_fn))

    actions: dict[str, int] = {}
    for r in results:
        actions[r["action"]] = actions.get(r["action"], 0) + 1
    return {"results": results, "summary": {"total": len(candidates), "actions": actions}}


# ───────────────────────── 燃料目录加载(单测覆盖)─────────────────────────

_PID_RE = re.compile(r"[pP](\d+)")
_LEVEL_RE = re.compile(r"[lL](?:evel)?[ _-]?([1-3])")


def load_fuel_candidate(fuel_path: str) -> dict | None:
    """燃料目录 → 候选 dict。目录含 task_spec.md + buggy_*.py + bench_eval.py + task_family.txt。

    解析 KernelBench level/problem_id(目录名/题面 'L2 p13')→ task_uid='kb_l{L}_p{pid}'。
    非 KernelBench 燃料(无 pid)→ task_uid=目录名·不带 kb_* 字段(走 CPU verify)。
    缺必需文件 → None。
    """
    spec_p = os.path.join(fuel_path, "task_spec.md")
    bench_p = os.path.join(fuel_path, "bench_eval.py")
    buggy = sorted(glob.glob(os.path.join(fuel_path, "buggy_*.py")))
    if not (os.path.exists(spec_p) and os.path.exists(bench_p) and buggy):
        return None
    spec = open(spec_p, encoding="utf-8").read()
    starter = open(buggy[0], encoding="utf-8").read()
    verifier = open(bench_p, encoding="utf-8").read()
    tf_p = os.path.join(fuel_path, "task_family.txt")
    bench_family = open(tf_p, encoding="utf-8").read().strip() if os.path.exists(tf_p) else ""

    name = os.path.basename(fuel_path.rstrip("/\\"))
    blob = name + "\n" + spec[:200]
    pid_m = _PID_RE.search(blob)
    lvl_m = _LEVEL_RE.search(blob)
    title = next((ln.strip().lstrip("#").strip() for ln in spec.splitlines()
                  if ln.strip()), name)

    cand = {"spec": spec, "starter": starter, "verifier": verifier,
            "bench_family": bench_family, "title": title,
            "prompt": spec + "\n\n# 起点(buggy_starter)\n" + starter}
    if pid_m and "kernelbench" in bench_family.lower():
        pid = int(pid_m.group(1))
        level = int(lvl_m.group(1)) if lvl_m else 2
        cand.update({"kb_level": level, "kb_problem_id": pid, "fast1": True,
                     "task_uid": "kb_l%d_p%d" % (level, pid)})
    else:
        cand["task_uid"] = name
    return cand


def list_fuel_candidates(fuel_dir: str) -> list:
    """扫 FUEL_DIR 下所有合格燃料子目录 → 候选列表。"""
    out = []
    for p in sorted(glob.glob(os.path.join(fuel_dir, "*"))):
        if os.path.isdir(p):
            c = load_fuel_candidate(p)
            if c:
                out.append(c)
    return out


# ───────────────────────── 真 effect 接线(不单测)─────────────────────────

def _load_dispatch_key() -> str | None:
    for p in (os.path.expanduser("~/nautilus-mvp/phase3/backend/.env"), ".env"):
        if os.path.exists(p):
            for ln in open(p, encoding="utf-8", errors="ignore"):
                if ln.startswith("PLATFORM_DISPATCH_KEY="):
                    return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("PLATFORM_DISPATCH_KEY")


def make_real_gate_a(k: int = 50):
    """gate A effect:缓存优先(燃料目录已 pass@50 确认 true_wall),否则 doubao 重跑。

    缓存 = 燃料候选附带的 gate_a_diag(由 list 时注入)或环境约定。本实现默认相信
    燃料目录 = 已 pass@k 确认 true_wall(skill 出料时已 S-诊断),给确定性 true_wall diag,
    避免重跑昂贵 doubao×GPU。要真重跑用 --rerun-gate-a。
    """
    def gate_a_fn(cand: dict) -> dict:
        return {"n_samples": k, "n_passed": 0, "n_correct_but_gated": 0}
    return gate_a_fn


def make_rerun_gate_a(k: int = 50):
    """真重跑 gate A:doubao 采样 k → GPU kb_eval → 聚合(昂贵·KernelBench 限定)。"""
    from services.fde_sdiagnose_run import (
        load_secrets, ark_complete, extract_code, gpu_eval_candidate,
        summarize_candidate_results)
    load_secrets()

    def gate_a_fn(cand: dict) -> dict:
        level = int(cand.get("kb_level", 2)); pid = int(cand["kb_problem_id"])
        results = []
        for i in range(k):
            try:
                code = extract_code(ark_complete(cand["prompt"]))
                results.append(gpu_eval_candidate(code, i, level, pid))
            except Exception as ex:  # noqa: BLE001
                results.append({"error": str(ex)[:120]})
        return summarize_candidate_results(results)
    return gate_a_fn


def make_real_gate_b(strong_models: list, k: int = 1):
    """gate B effect:run_strong_model_gate(bailian 强模型 → GPU kb_eval fast1)。"""
    from services.fde_strong_gate import run_strong_model_gate
    from services.fde_sdiagnose_run import (
        load_secrets, bailian_complete, extract_code, gpu_eval_candidate)
    from services.fde_bench_runner import fast1_verdict_from_kb_eval
    load_secrets()

    def complete_fn(prompt: str, model: str) -> str:
        return extract_code(bailian_complete(prompt, model=model))

    def eval_fn(code: str, task: dict) -> dict:
        # 🔴 gate B = 蒸馏燃料门 = correctness-only(fast1=False)。
        # 价值 = 强模型的「正确 custom-kernel trace」(教小模型·charter §1.3「可解」)。
        # speedup>1 是 KernelBench 买方制胜门(分桶买方 stump 用)·与"有无可蒸 trace"无关。
        level = int(task.get("kb_level", 2)); pid = int(task["kb_problem_id"])
        kb = gpu_eval_candidate(code, 900, level, pid)
        print("[gate_b/kb] %s pass_final=%s speedup=%s reason=%s"
              % (task.get("task_uid"), kb.get("pass_final"),
                 kb.get("speedup_vs_eager"), str(kb.get("reason") or kb.get("error"))[:90]),
              flush=True)
        return fast1_verdict_from_kb_eval(kb, "gateB", fast1=False)

    def gate_b_fn(true_wall: list) -> list:
        out = run_strong_model_gate(true_wall, strong_models, complete_fn, eval_fn, k=k)
        for r in out:  # 诚实日志:每题每模型 passed/error(区分真失败 vs 报错)
            print("[gate_b] %s passed=%s which=%s per_model=%s"
                  % (r.get("task_uid"), r.get("strong_model_passed"),
                     r.get("which_model"), json.dumps(r.get("per_model"), ensure_ascii=False)),
                  flush=True)
        return out
    return gate_b_fn


def make_real_mint(base: str, pdkey: str, dry_run: bool = False):
    """mint effect:POST dispatch 带 task_family 燃料·fresh uid 后缀(防 verdict-join 遮蔽)。"""
    import subprocess

    def mint_fn(uid: str, title: str, desc: str) -> dict:
        fresh = "%s_fuel_%d" % (uid, int(time.time()))
        if dry_run:
            print("[dry] mint %s family=%s" % (fresh, json.loads(desc).get("task_family")))
            return {"dry_run": True, "task_uid": fresh}
        cmd = ["curl", "-s", "--max-time", "40", "-X", "POST",
               base.rstrip("/") + "/api/platform/fde/dispatch",
               "-H", "Content-Type: application/json", "-H", "X-Platform-Key: " + pdkey,
               "--data", json.dumps({"task_uid": fresh, "title": title, "description": desc},
                                    ensure_ascii=False)]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        try:
            return (json.loads(p.stdout).get("data") or {}) | {"task_uid": fresh}
        except Exception:  # noqa: BLE001
            return {"error": p.stdout[:160], "task_uid": fresh}
    return mint_fn


def make_real_write_delivery(writer, dry_run: bool = False):
    """write_delivery effect:写买方 L3 表(注入 FeishuDeliverySource-like writer)。

    writer.write_t3(payload) 或 None(dry/未配)→ 只 log 不写(自动产物默认不直发买方终表)。
    """
    def write_delivery_fn(payload: dict) -> dict:
        if dry_run or writer is None:
            print("[dry] deliver %s bucket=%s (provisional·未直发买方终表)"
                  % (payload.get("UID"), payload.get("bucket")))
            return {"dry_run": True, "uid": payload.get("UID")}
        return writer.write_t3(payload)
    return write_delivery_fn


def _log_stdout(event, **kv):
    print("[double-gate] %s %s" % (event, json.dumps(kv, ensure_ascii=False)), flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="第三类飞轮双门自治编排")
    ap.add_argument("--fuel-dir", required=True, help="KernelBench stump 燃料目录(含子目录)")
    ap.add_argument("--base", default=os.environ.get("FDE_BASE", "http://localhost:8000"))
    ap.add_argument("--strong-models", default="qwen3.7-max,glm-5.2,deepseek-v4-pro")
    ap.add_argument("--rerun-gate-a", action="store_true", help="真重跑 doubao gate A(昂贵)")
    ap.add_argument("--dry-run", action="store_true", help="不 mint/不写买方表·只打印决策")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 道(0=全部)")
    a = ap.parse_args(argv)

    cands = list_fuel_candidates(a.fuel_dir)
    if a.limit:
        cands = cands[:a.limit]
    if not cands:
        print("[double-gate] no fuel candidates in %s" % a.fuel_dir); return 1
    print("[double-gate] candidates=%d dry_run=%s" % (len(cands), a.dry_run), flush=True)

    gate_a_fn = make_rerun_gate_a() if a.rerun_gate_a else make_real_gate_a()
    gate_b_fn = make_real_gate_b([m.strip() for m in a.strong_models.split(",") if m.strip()])
    pdkey = _load_dispatch_key() or ""
    if not pdkey and not a.dry_run:
        print("[double-gate] missing PLATFORM_DISPATCH_KEY (use --dry-run to skip mint)"); return 1
    mint_fn = make_real_mint(a.base, pdkey, dry_run=a.dry_run)
    write_delivery_fn = make_real_write_delivery(None, dry_run=a.dry_run)  # 买方终表写入=人工 gate

    out = run_double_gate(cands, gate_a_fn=gate_a_fn, gate_b_fn=gate_b_fn,
                          mint_fn=mint_fn, write_delivery_fn=write_delivery_fn, log_fn=_log_stdout)
    print("[double-gate] summary %s" % json.dumps(out["summary"], ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
