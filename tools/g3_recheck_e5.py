#!/usr/bin/env python3
"""G3 抽检 10% 首次实跑 · e5_gates_first33(seed=20260930 抽 4)。

预注册:seed=20260930 · 抽检名单固定 · 读数原样落盘。
范围声明(诚实):原始判分请求未归档(gates detail 只存结论),G2/G3 判分
输入不可完整重放 → 本次抽检=G1 层(注入核验+可解析,可独立重放)+工件
完整性;G2/G3 重放缺口=抽检发现,记档并给出修复项。
"""
from __future__ import annotations

import importlib.util
import json
import random
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "gates_v1", ROOT / "ops" / "assay_gates" / "gates_v1.py")
g1mod = importlib.util.module_from_spec(_spec)
sys.modules["gates_v1"] = g1mod
_spec.loader.exec_module(g1mod)

SRC = ROOT / "runtime" / "e5_gates_first33.json"
WORKDIRS = Path(r"C:/Users/chunx/nautilus-v5/tools/uni_agent_bridge/e5_workdirs")
OUT = ROOT / "runtime" / "recheck_e5_g3"
OUT.mkdir(exist_ok=True)
SEED = 20260930


def qid_to_dir(qid: str) -> Path:
    # e5_20260929_131955_1 → task_1_20260929_131955
    m = re.match(r"e5_(\d{8})_(\d{6})_(\d+)", qid)
    if not m:
        return WORKDIRS / qid
    return WORKDIRS / f"task_{m.group(3)}_{m.group(1)}_{m.group(2)}"


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    qids = sorted(d["verdicts"])
    n_sample = max(1, round(len(qids) * 0.10))
    sample = random.Random(SEED).sample(qids, n_sample)
    print(f"[sample] seed={SEED} {n_sample}/{len(qids)}: {sample}")
    results = []
    for qid in sample:
        rec = {"qid": qid, "recorded": d["verdicts"][qid]}
        td = qid_to_dir(qid)
        tj = td / "trajectory.json"
        rec["artifact_exists"] = tj.exists()
        if tj.exists():
            try:
                text = tj.read_text(encoding="utf-8")
                rec["artifact_parsable"] = True
                # G1 独立重放:可寻址+注入核验(用 gates_v1 同一正则集)
                t = {"artifacts_ref": str(tj), "text": text}
                g1, why = g1mod.gate_g1(t)
                rec["g1_replay"] = g1
                rec["g1_replay_why"] = why
                rec["artifact_bytes"] = len(text)
            except Exception as e:
                rec["artifact_parsable"] = False
                rec["g1_replay"] = "unverifiable"
                rec["g1_replay_why"] = f"read/parse fail: {e}"
        else:
            rec["artifact_parsable"] = None
            rec["g1_replay"] = "unverifiable"
            rec["g1_replay_why"] = "artifact missing"
        # G2/G3 原始输入不可重放(请求未归档)→ 记缺口
        rec["g2_replayable"] = False
        rec["g3_replayable"] = False
        results.append(rec)
        print(json.dumps(rec, ensure_ascii=False))
    # 判定:G1 重放全部与记录一致(pass 且无注入)= 抽检 PASS(G1 层)
    g1_ok = all(r.get("g1_replay") == "pass" and r.get("artifact_exists")
                for r in results)
    print(f"[verdict] G1 层抽检 {'PASS(' + str(len(results)) + '/' + str(len(results)) + ' 一致,无注入,工件齐)' if g1_ok else 'FAIL'};"
          f" G2/G3 重放缺口=原始判分请求未归档(修复项:请求件随 verdict 落盘)")
    (OUT / "recheck_report.json").write_text(
        json.dumps({"seed": SEED, "sample": sample, "results": results,
                    "g1_layer_pass": g1_ok,
                    "gap": "原始判分请求未归档,G2/G3 判分输入不可重放"},
                   ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
