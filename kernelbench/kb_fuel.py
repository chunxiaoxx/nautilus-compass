"""KernelBench → 6-key 分数制燃料适配器。镜像 nautilus-v5/fde_capsule/ale_fuel_batch.py
的契约,把 KernelBench 加速比 eval 桥成蒸馏合池的 6-key record。GPU seam 后续单独加。"""
from __future__ import annotations

FUEL_KEYS = ("task_id", "problem_statement", "strong_solution",
             "strong_score", "doubao_score", "strong_verified")


def build_kb_fuel_sample(task_id, problem_statement, strong_result, doubao_speedup,
                         judge_version=None) -> dict:
    """纯:KernelBench 单题强解结果 + doubao 加速比 → 6-key 样本。
    strong_result = {"solution": str, "speedup": float, "verified": bool}。
    score_type 恒 "maximize"(加速比越大越好)。"""
    return {
        "task_id": str(task_id),
        "problem_statement": str(problem_statement),
        "strong_solution": str(strong_result.get("solution", "")),
        "strong_score": float(strong_result.get("speedup", 0.0)),
        "doubao_score": float(doubao_speedup),
        "strong_verified": bool(strong_result.get("verified", False)),
        "score_type": "maximize",
        "judge_version": str(judge_version) if judge_version else "",
    }


def is_a_class(sample: dict, rel_margin: float = 0.1) -> bool:
    """A 类(maximize·镜像 V5 ale_fuel_batch.is_a_class 语义):
    strong_verified ∧ strong>0 ∧ strong != doubao ∧ strong >= doubao*(1+rel_margin)。
    退化守卫:同分(双败)/ strong=0(没真解出)= 非 A 类(防毒燃料)。"""
    if not sample.get("strong_verified"):
        return False
    strong = float(sample["strong_score"])
    doubao = float(sample["doubao_score"])
    if strong == doubao:
        return False
    return strong > 0 and strong >= doubao * (1.0 + rel_margin)


def accumulate_kb_fuel(samples: list, existing: list) -> list:
    """纯·幂等:按 task_id dedup(同 id 取 strong_score 更高者)。不改入参。"""
    by, order = {}, []
    for s in list(existing) + list(samples):
        tid = s["task_id"]
        if tid not in by:
            by[tid] = s
            order.append(tid)
        elif float(s["strong_score"]) > float(by[tid]["strong_score"]):
            by[tid] = s
    return [by[tid] for tid in order]


# --------------------------------------------------------------------------
# GPU seam(gated · 真跑在 T4 · 调现有 kernelbench-stump-batch 工具链 + attention harness)
# 测试不覆盖此 seam(无 GPU)。所有外部 import lazy(函数体内)。
# --------------------------------------------------------------------------
def _doubao_speedup_from_summary(summary_json_path):  # pragma: no cover
    """读 build_summary.py 产的 summary.json,取 doubao 最佳过门加速比(reward 字段)。
    全员未过门=0.0(= doubao 没产出又对又快的 kernel = 最强难度信号)。"""
    import json
    with open(summary_json_path, encoding="utf-8") as f:
        s = json.load(f)
    return float(s.get("reward", 0.0))


def _eval_strong(harness_dir, candidate_path, target_speedup=1.5):  # pragma: no cover
    """调 attention harness.evaluate() 验强解 → strong_result。harness_dir 含 harness.py + reference_model.py。"""
    import importlib.util
    import sys
    sys.path.insert(0, str(harness_dir))
    spec = importlib.util.spec_from_file_location("kb_harness", str(harness_dir) + "/harness.py")
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    v = h.evaluate(str(candidate_path), target_speedup=target_speedup)
    with open(candidate_path, encoding="utf-8") as f:
        code = f.read()
    return {"solution": code, "speedup": float(v.get("speedup", 0.0)),
            "verified": bool(v.get("passed", False))}


def _run_one(task_id, problem_statement, *, harness_dir, strong_candidate_path,
             doubao_summary_json, judge_version=None):  # pragma: no cover
    """单题:验强解(harness)+ 读 doubao 加速比(summary.json)→ 6-key 样本。"""
    strong_result = _eval_strong(harness_dir, strong_candidate_path)
    doubao_speedup = _doubao_speedup_from_summary(doubao_summary_json)
    return build_kb_fuel_sample(task_id, problem_statement, strong_result,
                                doubao_speedup, judge_version=judge_version)


def main():  # pragma: no cover
    """gated seam(T4):env 驱动批量产 KernelBench 6-key records → jsonl,喂同一 ingest_fuel_records。
    env:
      KB_OUT           输出 jsonl(默认 /tmp/kb_fuel_records.jsonl)
      KB_TASK_ID       题 id(如 kb_attention)
      KB_PROBLEM_STMT  题面(或题面文件路径·见下)
      KB_HARNESS_DIR   harness.py + reference_model.py 所在目录
      KB_STRONG_CAND   强解候选 .py 路径(过 harness 的 ModelNew)
      KB_DOUBAO_SUMMARY  build_summary.py 产的 summary.json 路径
      KB_JUDGE_VERSION   审计锚(可选)
    幂等:KB_OUT 已存在 → 读回 accumulate(重跑不丢更优解)。
    单题版(批量靠外层多次调或扩 KB_TASK_ID 列表·先单题打通)。"""
    import json
    import os
    out_path = os.environ.get("KB_OUT", "/tmp/kb_fuel_records.jsonl")
    task_id = os.environ["KB_TASK_ID"]
    stmt_raw = os.environ.get("KB_PROBLEM_STMT", "")
    problem_statement = stmt_raw
    if stmt_raw and os.path.exists(stmt_raw):  # 允许传文件路径
        with open(stmt_raw, encoding="utf-8") as f:
            problem_statement = f.read()
    harness_dir = os.environ["KB_HARNESS_DIR"]
    strong_cand = os.environ["KB_STRONG_CAND"]
    doubao_summary = os.environ["KB_DOUBAO_SUMMARY"]
    judge_version = os.environ.get("KB_JUDGE_VERSION") or None

    existing = []
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            existing = [json.loads(ln) for ln in f if ln.strip()]
        print(f"[kb-fuel] 续跑:已有 {len(existing)} 条 → accumulate", flush=True)

    sample = _run_one(task_id, problem_statement, harness_dir=harness_dir,
                      strong_candidate_path=strong_cand,
                      doubao_summary_json=doubao_summary, judge_version=judge_version)
    merged = accumulate_kb_fuel([sample], existing)
    with open(out_path, "w", encoding="utf-8") as f:
        for m in merged:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    a = is_a_class(sample)
    a_count = sum(1 for m in merged if is_a_class(m))
    print(f"[kb-fuel] {task_id}: strong={sample['strong_score']} doubao={sample['doubao_score']} "
          f"verified={sample['strong_verified']} A类={a}", flush=True)
    print(f"[kb-fuel] done · {len(merged)} 条落地 · A类 {a_count} → {out_path}", flush=True)
    print(f"[kb-fuel] 下一步:喂 soul ingest_fuel_records('{out_path}') 进多基准蒸馏合池", flush=True)


if __name__ == "__main__":  # pragma: no cover
    main()
