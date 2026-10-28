#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CS-507 v1 达标交付包一键组装(打包闸·2026-10-28 预演就绪)。

判分产物落盘约定(回函后按此放,组装零改动):
  <judged_dir>/<model>__run<k>.json   # 每次 run 的 score.py 输出
  <judged_dir>/answers/<model>__run<k>/*   # 对应答卷(assets 用)

用法:
  python3 assemble.py --base /path/CS-507_v1_deep_1028.tar.gz \
      --judged /path/judged_dir --metrics <flywheel>/codesense_discrimination_metrics.py \
      --out /path/out_dir [--force]

流程: 达标门(五条件+三指标, 任一不过拒打包) → 组包(题本体+文档证据层)
      → 判分报告生成 → tar.gz+md5 → 输出核对单路径。
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

# ── 判据常量(1012 终极口径·ALI_REQ_STANDARD_MAP_V1) ──
M1_MIN, M2_MAX, M3_MIN = 0.50, 0.50, 1.25
MODELS = ["opus5.5", "qwen3.8max", "gpt6-astra", "kimi-k3", "glm5.3"]
# 模型名归一(防 gate5 同款双命名双计缺陷:compass #23159 实证 kimi-k3-ark/kimi-k3 双计可出>100%)
ALIAS = {
    "kimi-k3-ark": "kimi-k3", "kimi-k3-ark_": "kimi-k3", "kimi": "kimi-k3",
    "qwen3.8-max": "qwen3.8max", "qwen3.8max_": "qwen3.8max", "qwen": "qwen3.8max",
    "qwen3.8": "qwen3.8max", "glm-5.3": "glm5.3", "glm": "glm5.3",
    "gpt6-astra": "gpt6-astra", "gpt-6-astra": "gpt6-astra", "gpt6": "gpt6-astra",
    "opus5.5": "opus5.5", "opus-5.5": "opus5.5", "opus": "opus5.5",
}
# gating UT(甲方口径:通过 case 计数不含 gating·task.toml badpatterns[].ut 声明)
GATING_UTS = {"test_extract_text_not_dict_serialized",
              "test_extract_text_bad_str_returns_empty",
              "test_e2e_no_garbage_output"}


def norm_model(name: str) -> str:
    n = name.strip().lower()
    if n in MODELS:
        return n
    if n in ALIAS:
        return ALIAS[n]
    # 未登记变体:去后缀再试
    for cand in (n.split("_")[0], n.replace("-", ""), n.split("-ark")[0]):
        if cand in MODELS or cand in ALIAS:
            return cand if cand in MODELS else ALIAS[cand]
    return name  # 原样保留——由 C1 的 len(by_model)==5 兜底报警


def load_runs(judged: Path) -> list:
    runs = []
    for f in sorted(judged.glob("*__run*.json")):
        m = re.match(r"(?P<model>.+)__run(?P<round>\d+)\.json", f.name)
        if not m:
            continue
        d = json.loads(f.read_text())
        per_ut = d.get("per_ut") or {}
        # gating UT 剔除(甲方口径:case 计数不含 gating UT)
        per_ut = {k: v for k, v in per_ut.items() if k not in GATING_UTS}
        all_pass = bool(d.get("all_pass")) and not any(v == 0 for v in per_ut.values())
        runs.append({
            "model": norm_model(m.group("model")),
            "round": int(m.group("round")),
            "all_pass": all_pass,
            "passrate_ut": (sum(1 for v in per_ut.values() if v == 1) / len(per_ut)) if per_ut else 0.0,
            "ut_results": {k: (1 if v == 1 else 0) for k, v in per_ut.items()},
            "_src": f.name,
        })
    return runs


def five_conditions(runs: list) -> dict:
    by_model = {}
    for r in runs:
        by_model.setdefault(r["model"], []).append(r)
    checks, detail = {}, {}
    detail["rounds"] = {m: len(v) for m, v in by_model.items()}
    checks["C1_五模型各4轮"] = all(len(v) == 4 for v in by_model.values()) and len(by_model) == 5

    full = {m: sum(1 for r in v if r["all_pass"]) for m, v in by_model.items()}
    total_full = sum(full.values())
    detail["全过轮"] = full
    checks["C2_整体<70%"] = total_full / 20.0 < 0.70

    opus = full.get("opus5.5", 0)
    checks["C3_opus全过轮∈[1,3]"] = 1 <= opus <= 3

    q = by_model.get("qwen3.8max", [])
    q_rate = (sum(1 for r in q if r["all_pass"]) / len(q)) if q else 0.0
    opus_rate = (full.get("opus5.5", 0) / len(by_model.get("opus5.5", [1]))) if by_model.get("opus5.5") else 0.0
    gpt_rate = (full.get("gpt6-astra", 0) / len(by_model.get("gpt6-astra", [1]))) if by_model.get("gpt6-astra") else 0.0
    q_failed_at_least_once = any(not r["all_pass"] for r in q)
    detail["qwen主分带"] = q_rate
    checks["C4_qwen双低"] = q_failed_at_least_once and q_rate < opus_rate and q_rate < gpt_rate
    checks["C5_qwen∈{25,50}"] = q_rate in (0.25, 0.50)
    return {"checks": checks, "detail": detail, "all_pass": all(checks.values())}


def three_metrics(runs: list, metrics_script: Path) -> dict:
    matrix = {"task": "CS-507", "runs": [
        {"model": r["model"], "round": r["round"], "ut_results": r["ut_results"]}
        for r in runs]}
    tmp = Path("/tmp/_metrics_input.json")
    tmp.write_text(json.dumps(matrix, ensure_ascii=False))
    p = subprocess.run([sys.executable, str(metrics_script), "--matrix", str(tmp)],
                       capture_output=True, text=True)
    # 注意: metrics 脚本 FAIL 时 exit 1 但 stdout 仍有完整 JSON——按 stdout 解析, rc 仅记录
    if not p.stdout.strip():
        return {"verdict": "ERROR", "stderr": (p.stderr or "no stdout")[-500:], "rc": p.returncode}
    out = json.loads(p.stdout)
    # flywheel 脚本 schema: checks.M{1,2}_<中文名>.value/pass —— 拍平为 m1/m2/m3
    flat = {"verdict": out.get("verdict")}
    for key, alias in (("M1", "m1"), ("M2", "m2"), ("M3", "m3")):
        node = next((v for k, v in (out.get("checks") or {}).items() if k.startswith(key)), None)
        flat[alias] = node.get("value") if node else None
        flat[f"{alias}_pass"] = bool(node.get("pass")) if node else False
    flat["_raw"] = out
    return flat


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assemble(base_tgz: Path, judged: Path, out_dir: Path) -> Path:
    work = out_dir / "_assemble_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    with tarfile.open(base_tgz) as t:
        t.extractall(work)
    pkg = work / "CS-507"

    # 文档证据层替换(v1 修正件,以 kit 内为准)
    kit = Path(__file__).resolve().parent
    src_equiv = kit / "equivalent_v1_fixed.md"
    if src_equiv.exists():
        shutil.copy(src_equiv, pkg / "tests/calibration/equivalent.md")
    shutil.copy(kit / "model_failure_modes.md", pkg / "tests/assets/model_failure_modes.md")

    # 混时代数据清除: 21UT 旧答卷与旧矩阵全部清出(红线)
    assets = pkg / "tests/assets"
    removed = 0
    for f in list(assets.iterdir()):
        if f.name.startswith(("opus5.5_run", "qwen3.8max_run", "gpt-6-astra_run",
                              "kimi-k3-ark_run", "glm5.3_run")) or f.name == "ut_results.json":
            f.unlink()
            removed += 1
    # 新答卷入位
    new_answers = judged / "answers"
    if new_answers.exists():
        for f in new_answers.rglob("*"):
            if f.is_file():
                rel = f.relative_to(new_answers)
                dst = assets / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(f, dst)

    out_pkg = out_dir / "CS-507"
    if out_pkg.exists():
        shutil.rmtree(out_pkg)
    shutil.move(str(pkg), str(out_pkg))
    shutil.rmtree(work)
    return out_pkg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="判分发车版 tar.gz")
    ap.add_argument("--judged", required=True, help="判分产物目录(约定见 docstring)")
    ap.add_argument("--metrics", required=True, help="flywheel 三指标脚本路径")
    ap.add_argument("--out", required=True)
    ap.add_argument("--force", action="store_true", help="跳过达标门(仅预演用)")
    a = ap.parse_args()

    judged, out_dir = Path(a.judged), Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in ("GATE_FAIL.json", "judge_data_five_conditions.json",
                  "judge_data_three_metrics.json", "CS-507", "CS-507_v1_delivery.tar.gz"):
        p = out_dir / stale
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    runs = load_runs(judged)
    if len(runs) < 20:
        print(f"❌ 判分 run 不足 20(实得 {len(runs)}), 拒绝组装")
        return 1

    fc = five_conditions(runs)
    tm = three_metrics(runs, Path(a.metrics))
    print("== 五条件 ==", json.dumps(fc["checks"], ensure_ascii=False, indent=1))
    print("== 三指标 ==", json.dumps({k: tm.get(k) for k in ("m1", "m2", "m3", "verdict")},
                                     ensure_ascii=False))

    tm_ok = (tm.get("m1") is not None and tm.get("m1") >= M1_MIN
             and tm.get("m2") is not None and tm.get("m2") <= M2_MAX
             and tm.get("m3") is not None and tm.get("m3") >= M3_MIN)
    if not (fc["all_pass"] and tm_ok) and not a.force:
        print("❌ 达标门未过——不出包。差距已列上方, 回到判分迭代。")
        (out_dir / "GATE_FAIL.json").write_text(json.dumps(
            {"five_conditions": fc, "three_metrics": tm}, ensure_ascii=False, indent=1))
        return 2

    pkg = assemble(Path(a.base), judged, out_dir)
    (pkg.parent / "judge_data_five_conditions.json").write_text(
        json.dumps(fc, ensure_ascii=False, indent=1))
    (pkg.parent / "judge_data_three_metrics.json").write_text(
        json.dumps(tm, ensure_ascii=False, indent=1))
    tgz = out_dir / "CS-507_v1_delivery.tar.gz"
    with tarfile.open(tgz, "w:gz") as t:
        for f in sorted(pkg.rglob("*")):
            if f.is_file() and not f.name.startswith("._") and f.name != ".DS_Store" \
                    and "__pycache__" not in f.parts:
                t.add(f, arcname=str(f.relative_to(pkg.parent)))
    print(f"✅ 交付包: {tgz}\n   sha256={sha256(tgz)}\n   核对单: ASSEMBLY_CHECKLIST.md 第四节起逐项勾")
    return 0


if __name__ == "__main__":
    sys.exit(main())
