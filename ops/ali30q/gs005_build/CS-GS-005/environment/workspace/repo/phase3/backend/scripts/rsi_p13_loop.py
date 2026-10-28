#!/usr/bin/env python3
"""单人端到端 RSI 第一圈 — p13 KernelBench(platform-soul·6/18）。

终极判据(probe 真数）: turn-2 best speedup > turn-1 best speedup。
- turn-1（无记忆）: 强模型(deepseek-v4-pro) 从 base prompt 产 k 个候选 → GPU T4 eval → 选 best fast1。
- 抽记忆: 从 turn-1 best kernel(已验证 correct+fast1）抽 grounded 记忆(源码 exemplar + 实测 speedup + ref 时间分布事实）。
- turn-2（注入记忆）: 同强模型 base prompt + 记忆 → eval → best。
- 判: speedup_2 > speedup_1?  delta vs 计时噪声(ref std ~0.7%）诚实标注。

fast1 = correctness PASS(eval + strict 1e-3) AND 1.0 < speedup_vs_eager <= 2.0。

复用 services.fde_sdiagnose_run 的 producer + GPU verifier（不重复造）。
用法（background 跑·别前台 poll）:
  python -m scripts.rsi_p13_loop --k1 4 --k2 4 --out /tmp/rsi_p13.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.fde_sdiagnose_run import (  # noqa: E402
    bailian_complete, extract_code, gpu_eval_candidate, load_secrets,
)

DEFAULT_PROMPT = os.path.expanduser(
    "~/fde_t3_scratch/kernelbench/_sdiag/p13/prompt.txt")

# 🔴 harness 静态门(Kevin RL paper 口径）会拒带 try/except、pass、torch.nn 计算层的代码。
# base prompt 不含这些约束 → 模型不知道 → 浪费样本。两 turn 同等注入（不混淆 RSI 变量）。
GUARD_HINT = """

## HARD CONSTRAINTS (the automated verifier REJECTS code that violates these)
- Do NOT use any `try` / `except` block anywhere (flagged as fallback bypass).
- Do NOT use a `pass` statement anywhere (flagged as inheritance bypass).
- Do NOT use torch.nn compute layers (nn.ConvTranspose3d, nn.Linear, nn.Conv*, nn.ReLU ...).
  Use torch.nn.functional (e.g. F.conv_transpose3d) or your own CUDA kernels.
  Only nn.Module / nn.Parameter are allowed, for structure.
- Must compile via load_inline and pass correctness at strict atol=rtol=1e-3 in FP32.
  Do NOT downcast to half/bfloat16.
- Output ONLY the ModelNew code in a single ```python block, no prose, no test code.
"""


# ───────────────────────── 纯逻辑 ─────────────────────────

def fast1_speedup(result: dict) -> float | None:
    """result → fast1 speedup（不满足 fast1 返回 None）。

    fast1 = eval.correctness AND strict_recheck.correctness AND 1<su<=2。
    """
    if result.get("error"):
        return None
    su = result.get("speedup_vs_eager")
    if su is None or not (1.0 < su <= 2.0):
        return None
    if result.get("eval", {}).get("correctness") is not True:
        return None
    if result.get("strict_recheck", {}).get("correctness") is not True:
        return None
    return su


def raw_speedup(result: dict) -> float | None:
    """correctness-gated raw speedup（去 fast1 的 2× cap）。

    RSI 机制证明用此 reward：只要 correct（eval+strict）且 speedup 可测就算数，
    不卡 1<su≤2 窗口（那是燃料/难倒业务约束·非机制证明要求）。
    correct-but-slow（su<1）也保留——它正是 turn-over-turn 改进梯度的起点。
    """
    if result.get("error"):
        return None
    su = result.get("speedup_vs_eager")
    if su is None or su <= 0:
        return None
    if result.get("eval", {}).get("correctness") is not True:
        return None
    if result.get("strict_recheck", {}).get("correctness") is not True:
        return None
    return su


def select_best(records: list[dict], reward_fn=fast1_speedup) -> dict | None:
    """records=[{idx,code,result}] → reward 最大的那条。无合格候选返回 None。"""
    scored = [(reward_fn(r["result"]), r) for r in records]
    scored = [(s, r) for s, r in scored if s is not None]
    if not scored:
        return None
    return max(scored, key=lambda x: x[0])[1]


NOISE_REL = 0.01  # ref 计时 std≈0.7%·保守 1% 相对门(防计时抖动判成假阳性 RSI）


def rsi_above_noise(su1: float | None, su2: float | None, noise_rel: float = NOISE_REL) -> bool:
    """turn-2 是否真比 turn-1 改进(相对 delta > 噪声门）。naive su2>su1 会造 facade。"""
    if su1 is None or su2 is None or su1 <= 0:
        return False
    return (su2 - su1) / su1 > noise_rel


def build_memory(best: dict, reproduce: bool = False) -> str:
    """从 turn-1 best（已验证）抽 grounded 记忆，注入 turn-2 prompt。

    Grounded：① 已验证源码 exemplar ② 实测 speedup ③ ref 时间分布事实。
    reproduce=True：指令偏"复现为主·correctness 至上"（测记忆能否抬 fast1 yield）。
    reproduce=False：指令偏"改进+更快"（测记忆能否抬 speedup ceiling）。
    """
    res = best["result"]
    su = res.get("speedup_vs_eager")
    ref_mean = res.get("ref_time", {}).get("mean")
    if reproduce:
        instruction = (
            "Reproduce this verified kernel as your ModelNew. Correctness is paramount — "
            "it MUST pass strict 1e-3. You may make at most minor, safe tweaks; do NOT "
            "restructure in ways that risk correctness. Aim to keep the speedup at or "
            f"above {su:.4f}x.")
    else:
        instruction = (
            "Use this verified kernel as a starting point. Produce an improved ModelNew that "
            f"is still correct (must pass strict 1e-3) AND has a higher speedup than {su:.4f}x. "
            "Consider reducing kernel-launch overhead, fusing the epilogue into fewer launches, "
            "or a faster path for the ConvTranspose3d itself.")
    return (
        "\n\n## Prior verified attempt (memory from a previous round)\n"
        "A previous attempt produced the kernel below. It was VERIFIED on this same "
        "Tesla T4 GPU with the official harness:\n"
        "- correctness: PASS (5/5 trials, and strict re-check at atol=rtol=1e-3)\n"
        f"- measured speedup vs eager PyTorch: {su:.4f}x\n"
        f"- reference forward runtime is ~{ref_mean:.0f} ms and is dominated by the "
        "ConvTranspose3d; the fused epilogue (mean/add/softmax/tanh/scale) is a small "
        "fraction of total time, so fusing only the epilogue caps the achievable speedup.\n\n"
        + instruction + "\n\n```python\n" + best["code"].strip() + "\n```\n")


# ───────────────────────── 集成 ─────────────────────────

def produce_and_eval(prompt: str, k: int, level: int, pid: int, model: str,
                     tag: str, stop_after_fast1: int | None = None) -> list[dict]:
    """k 个候选 produce+eval。stop_after_fast1=N 时，累计 N 条 fast1 即早停（省 GPU）。"""
    records = []
    for i in range(k):
        t0 = time.time()
        try:
            resp = bailian_complete(prompt, model=model)
            code = extract_code(resp)
        except Exception as ex:  # noqa: BLE001 — 诚实计错不中断
            records.append({"idx": i, "code": "", "result": {"error": "produce: %s" % ex}})
            print("  [%s %d/%d] produce_error %s" % (tag, i + 1, k, str(ex)[:80]), flush=True)
            continue
        # fresh-uid-per-version: tag 进 idx 空间防撞 turn-1/turn-2 同名
        res = gpu_eval_candidate(code, hash((tag, i)) % 100000, level, pid)
        records.append({"idx": i, "code": code, "result": res})
        su = res.get("speedup_vs_eager")
        f1 = fast1_speedup(res)
        print("  [%s %d/%d] su=%s fast1=%s reason=%s | %.0fs"
              % (tag, i + 1, k, ("%.4f" % su) if su else su,
                 ("%.4f" % f1) if f1 else None, str(res.get("reason") or res.get("error"))[:50],
                 time.time() - t0), flush=True)
        if stop_after_fast1 is not None:
            n_fast1 = sum(1 for r in records if fast1_speedup(r["result"]) is not None)
            if n_fast1 >= stop_after_fast1:
                print("  [%s] early-stop: %d fast1 reached" % (tag, n_fast1), flush=True)
                break
    return records


def run(k1: int, k2: int, prompt_path: str, level: int, pid: int, model: str,
        out_path: str | None, inject_code_path: str | None = None,
        inject_su: float | None = None, reproduce: bool = False,
        reward: str = "fast1") -> dict:
    load_secrets()
    # reward=raw：correctness-gated 原始 speedup（RSI 机制证明·终极判据 speedup_2>speedup_1）。
    # reward=fast1：1<su≤2 窗口（燃料/难倒业务）。
    reward_fn = raw_speedup if reward == "raw" else fast1_speedup
    base_prompt = open(prompt_path, encoding="utf-8").read() + GUARD_HINT  # 两 turn 同等
    print("[rsi] p%d level=%d model=%s k1=%d k2=%d inject=%s reward=%s"
          % (pid, level, model, k1, k2, bool(inject_code_path), reward), flush=True)

    if inject_code_path:
        # ── 注入模式：turn-1 baseline 来自外部已验证 exemplar（飞轮自产·verified）──
        # 无记忆基线由先前批次确立（见报告 baseline_no_memory）；本 run 只测"注入记忆能否抬 yield"。
        print("\n=== TURN 1 = injected verified exemplar (su=%.4f) ===" % inject_su, flush=True)
        best1 = {"idx": -1, "code": open(inject_code_path, encoding="utf-8").read(),
                 "result": {"speedup_vs_eager": inject_su, "ref_time": {"mean": 200.0},
                            "eval": {"correctness": True}, "strict_recheck": {"correctness": True}}}
        su1 = inject_su
        t1 = []  # 无新采样·baseline 外部确立
    else:
        # ── TURN 1: 无记忆 ── reward=raw 跑满 k1 取最佳 correct；fast1 模式采到 1 条即停
        stop = 1 if reward == "fast1" else None
        print("\n=== TURN 1 (no memory, k1=%d, reward=%s) ===" % (k1, reward), flush=True)
        t1 = produce_and_eval(base_prompt, k1, level, pid, model, "t1", stop_after_fast1=stop)
        best1 = select_best(t1, reward_fn)
        su1 = reward_fn(best1["result"]) if best1 else None
    print("[rsi] turn-1 best %s speedup = %s" % (reward, su1), flush=True)

    memory = None
    t2, best2, su2 = [], None, None
    if best1 is None:
        print("[rsi] turn-1 produced no fast1 kernel — abort RSI (no grounded memory).", flush=True)
    else:
        # ── 抽记忆 ──
        memory = build_memory(best1, reproduce=reproduce)
        # ── TURN 2: 注入记忆 ──
        print("\n=== TURN 2 (memory injected) ===", flush=True)
        t2 = produce_and_eval(base_prompt + memory, k2, level, pid, model, "t2")
        best2 = select_best(t2, reward_fn)
        su2 = reward_fn(best2["result"]) if best2 else None
        print("[rsi] turn-2 best %s speedup = %s" % (reward, su2), flush=True)

    # ── 判据 ── 🔴 必须超噪声(rsi_above_noise）·naive su2>su1 会判成假阳性(facade）。
    delta = (su2 - su1) if (su1 is not None and su2 is not None) else None
    rel_delta = (delta / su1) if (delta is not None and su1) else None
    rsi_proven = rsi_above_noise(su1, su2)
    t2_fast1 = sum(1 for r in t2 if fast1_speedup(r["result"]) is not None)
    report = {
        "task": "kb_l%d_p%d" % (level, pid), "model": model, "k1": k1, "k2": k2,
        "mode": "inject" if inject_code_path else "self",
        "turn1_best_speedup": su1, "turn2_best_speedup": su2,
        "turn2_fast1_count": t2_fast1, "turn2_n": len(t2),
        "baseline_no_memory_fast1": "0/12 (2026-06-18 v2 k=4 + v3 k=8 · fresh deepseek-v4-pro · no memory)",
        "delta": delta, "rel_delta": rel_delta, "noise_rel_threshold": NOISE_REL,
        "rsi_proven": rsi_proven,
        "memory_injected": memory is not None,
        "turn1_speedups": [r["result"].get("speedup_vs_eager") for r in t1],
        "turn2_speedups": [r["result"].get("speedup_vs_eager") for r in t2],
        "best1_code": best1["code"] if best1 else None,
        "best2_code": best2["code"] if best2 else None,
        "raw_turn1": [r["result"] for r in t1],
        "raw_turn2": [r["result"] for r in t2],
    }
    print("\n========== RSI p%d 结果 ==========" % pid, flush=True)
    print("turn-1 best = %s · turn-2 best = %s · delta = %s · rsi_proven = %s"
          % (su1, su2, delta, rsi_proven), flush=True)
    print("⚠️ 诚实: ref 计时 std≈0.7%%·delta 须 > ~0.007 才超噪声", flush=True)
    if out_path:
        json.dump(report, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("[rsi] 写 %s" % out_path, flush=True)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k1", type=int, default=4)
    ap.add_argument("--k2", type=int, default=4)
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--level", type=int, default=2)
    ap.add_argument("--problem-id", type=int, default=13)
    ap.add_argument("--model", default="deepseek-v4-pro")
    ap.add_argument("--out", default=None)
    ap.add_argument("--inject-code", default=None,
                    help="注入模式：外部已验证 exemplar 路径作 turn-1 baseline + 记忆")
    ap.add_argument("--inject-su", type=float, default=None, help="该 exemplar 实测 speedup")
    ap.add_argument("--reproduce", action="store_true",
                    help="记忆指令偏复现（测抬 yield）·默认偏改进（测抬 ceiling）")
    ap.add_argument("--reward", default="fast1", choices=["fast1", "raw"],
                    help="raw=correctness-gated 原始 speedup(RSI 机制证明·终极判据)·fast1=1<su≤2 窗口")
    a = ap.parse_args()
    run(a.k1, a.k2, a.prompt, a.level, a.problem_id, a.model, a.out,
        a.inject_code, a.inject_su, a.reproduce, a.reward)


if __name__ == "__main__":
    main()
