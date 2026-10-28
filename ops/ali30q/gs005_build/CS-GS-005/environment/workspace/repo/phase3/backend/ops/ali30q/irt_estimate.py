# -*- coding: utf-8 -*-
"""IRT 2PL 粗估器(阿里30q·判读层配套,平台产)。

输入:每题五模型×4轮二值读数(全过=1)→输出(难度b,区分度a)粗估+达标判读。
样本小(5考生×4轮),用矩估计+网格搜索粗估,方向性足够(精确化候五模型全量后)。
用法:
    python irt_estimate.py --scores CS-007=opus:1,1,0,0;qwen:0,0,1,0;...
    python irt_estimate.py --jev ops/ali30q/jev/  # 批量读JEV包(格式候compass)
锚点:CS-007 实测参数即标准锚坐标,其余题向其对齐。
"""
from __future__ import annotations

import argparse
import json
import math
import sys

# 模型能力先验(θ,粗校准自 A 批/公开口径,可随全量数据重估)
THETA_PRIOR = {"opus": 1.5, "gpt": 1.3, "glm": 0.8, "kimi": 0.7, "qwen": 0.5}
SOTA_GROUP = {"opus", "gpt"}

# 模型名别名→先验键(judge总线用全名如glm5.3/kimi-k3)
ALIAS = {}
for full, short in [("glm5.3","glm"),("glm-5.3","glm"),("kimi-k3","kimi"),("k3","kimi"),
                    ("qwen3.8-max","qwen"),("qwen3.8-max-0902","qwen"),("claude-opus-5-5","opus"),
                    ("gpt-6-astra","gpt"),("opus-5-5","opus")]:
    ALIAS[full] = short

def norm_model(name: str) -> str:
    n = name.strip().lower()
    for full, short in ALIAS.items():
        if n == full or n.startswith(full):
            return short
    for short in THETA_PRIOR:
        if short in n:
            return short
    return n


def prob2pl(theta: float, a: float, b: float) -> float:
    return 1.0 / (1.0 + math.exp(-a * (theta - b)))


def parse_scores(spec: str) -> dict[str, list[int]]:
    out = {}
    for model_runs in spec.split(";"):
        model, runs = model_runs.split(":")
        out[model.strip()] = [int(x) for x in runs.split(",")]
    return out


def norm_model(name: str) -> str:
    n = name.strip().lower()
    aliases = {'glm5.3':'glm','glm-5.3':'glm','kimi-k3':'kimi','k3':'kimi',
               'qwen3.8-max':'qwen','qwen3.8-max-0902':'qwen',
               'claude-opus-5-5':'opus','opus-5-5':'opus','gpt-6-astra':'gpt'}
    for full, short in aliases.items():
        if n == full or n.startswith(full): return short
    for short in ['opus','gpt','glm','kimi','qwen']:
        if short in n: return short
    return n

def estimate(scores: dict[str, list[int]]) -> dict:
    """网格搜索 (a,b):最大化观测似然。a∈[0.3,4.0] b∈[-2,3]。"""
    best = {"a": 0.3, "b": 0.0, "ll": -1e9}
    obs = []
    for m, runs in scores.items():
        m_norm = norm_model(m)
        if m_norm in THETA_PRIOR:
            obs.extend((m_norm, r) for r in runs)
    if not obs:
        raise ValueError("无有效观测(模型须在 THETA_PRIOR 内)")
    a = 0.3
    while a <= 4.001:
        b = -2.0
        while b <= 3.001:
            ll = sum(
                math.log(max(prob2pl(THETA_PRIOR[m], a, b), 1e-9) if r == 1
                         else max(1 - prob2pl(THETA_PRIOR[m], a, b), 1e-9))
                for m, r in obs
            )
            if ll > best["ll"]:
                best = {"a": round(a, 2), "b": round(b, 2), "ll": round(ll, 2)}
            b += 0.1
        a += 0.1
    # 达标判读(13门表口径的参数化表达)
    dom = [r for m, runs in scores.items() if m not in SOTA_GROUP for r in runs]
    sota = [r for m, runs in scores.items() if m in SOTA_GROUP for r in runs]
    dom_mean = sum(dom) / len(dom) if dom else 0.0
    sota_mean = sum(sota) / len(sota) if sota else 0.0
    gap_pp = round((sota_mean - dom_mean) * 100, 1)
    best.update({
        "domestic_mean": round(dom_mean, 3), "sota_mean": round(sota_mean, 3),
        "gap_pp": gap_pp,
        "verdict": (
            # 甲方三反口径(2026-10-25):qwen passrate 25%/50%档+SOTA>qwen+差≥20pp
            "OK(25%档)" if dom_mean <= 0.30 and gap_pp >= 20 else
            "OK(50%档)" if dom_mean <= 0.60 and gap_pp >= 20 else
            "过浅(国内反超或差不足)" if gap_pp < 20 else "过深(国内全灭)"
        ),
    })
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", help="题=模型:轮次;模型:轮次")
    args = ap.parse_args()
    if args.scores:
        qid, _, spec = args.scores.partition("=")
        r = estimate(parse_scores(spec))
        print(json.dumps({qid: r}, ensure_ascii=False, indent=1))




def run_batch(jev_dir: str) -> str:
    """批量模式:遍历 JEV 目录逐题出(b,a)参数表。JEV 文件格式候 compass
    (ops/ali30q/jev/*.json,含 per-model 二值轮次)。S3 数据到即一键全池。"""
    import glob
    out = []
    for path in sorted(glob.glob(os.path.join(jev_dir, "*.json"))):
        qid = os.path.basename(path).replace(".json", "")
        try:
            data = json.load(open(path, encoding="utf-8"))
            scores = {m: data[m]["runs"] for m in data if isinstance(data.get(m), dict) and "runs" in data[m]}
            out.append({qid: estimate(scores)})
        except Exception as e:
            out.append({qid: {"error": str(e)[:60]}})
    return json.dumps(out, ensure_ascii=False, indent=1)


if "batch" in str(sys.argv):
    # python irt_estimate.py batch <jev_dir>  → 全池参数表(stdout)
    import os
    print(run_batch(sys.argv[sys.argv.index("batch") + 1]))
    sys.exit(0)


if __name__ == "__main__":
    main()
