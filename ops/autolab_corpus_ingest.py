#!/usr/bin/env python3
"""compass · A 簇 eval-feedback → 避坑语料 adapter(RSI loop step-2 · A 簇 substrate).

v2(6/8):加**批次平衡警示原子** —— 首验实证:naive grounded 推激进优化→4/10 破坏正确性→ΔReward 净负;
V5 round-3(correctness-first)→9/10 correct→ΔReward 转正。把这课自动编码:批次里出现正确性失败时,
emit "优化必须先保 bit-exact" 平衡原子(放语料顶部·最高优先)。这样未来任务 grounding 自带此课(非每次手动学)。

读 autolab_eval.py 产的 reward JSON → 提 fail_reason + 批次平衡 → 写 per-task 可检索避坑语料。
deterministic·无模型·不泄 reference 解(只编码观测到的失败模式·非答案)。turf:compass=语料·V5=retrieve+注入。

用法:
  python3 autolab_corpus_ingest.py --task radix_sort reward1.json reward2.json ...
"""
import argparse, json, os, sys

CORPUS_DIR = os.environ.get("AUTOLAB_CORPUS_DIR", "/mnt/datadisk0/autolab_eval/corpus")

def atom_from_reward(r):
    cand = r.get("candidate", "?")
    reward = r.get("reward", 0.0)
    if not r.get("build", True):
        return {"cand": cand, "reward": reward, "tag": "build_fail",
                "lesson": f"编译失败 → {r.get('feedback','')[:140]}。改动需先过 gcc -O2 -std=c99 编译门"}
    if not r.get("correct", True):
        return {"cand": cand, "reward": reward, "tag": "correctness_fail",
                "lesson": "破坏正确性(输出非完全有序/checksum 变=0 分)。激进优化(prefetch/位宽/SIMD/并行)"
                          "极易破坏 bit-exact → 任何优化后必须逐位验证正确性"}
    fb = r.get("feedback", "")
    lesson = fb.split("避坑:", 1)[1].strip() if "避坑:" in fb else fb
    return {"cand": cand, "reward": reward, "median": r.get("median"),
            "lesson": lesson, "tag": "below_reference" if reward < 0.5 else "ok"}

def balance_atom(atoms):
    """批次平衡警示:correctness 失败 + correct 候选并存时,emit 'correctness-first' 课(首验实证)。"""
    n = len(atoms)
    fails = [a for a in atoms if a["tag"] in ("correctness_fail", "build_fail")]
    correct = [a for a in atoms if a["tag"] not in ("correctness_fail", "build_fail")]
    if not fails or not correct:
        return None
    rate = len(fails) / n
    return (f"⚠️ 平衡警示(批次 {len(fails)}/{n} 候选破坏正确性/编译·correct 候选 reward~"
            f"{round(sum(a['reward'] for a in correct)/len(correct),3)}): "
            f"**优化必须先保 bit-exact 正确性,再求加速**。实证:激进 grounding(prefetch/8-bit/位宽/SIMD)"
            f"会把更快候选拉破正确性门(reward=0)→ 净 ΔReward 转负。correctness-first 的 grounding 才稳赢。")

def ingest(task, reward_paths):
    os.makedirs(CORPUS_DIR, exist_ok=True)
    out = os.path.join(CORPUS_DIR, f"autolab_avoid_{task}.md")
    seen = set()
    if os.path.exists(out):
        for line in open(out, encoding="utf-8"):
            if line.startswith("- cand="):
                seen.add(line.split("cand=", 1)[1].split(" ", 1)[0])
    batch = []
    for p in reward_paths:
        try:
            r = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print(f"[skip {p}] {e}", file=sys.stderr); continue
        if r.get("task") and r["task"] != task:
            continue
        batch.append(atom_from_reward(r))
    new_atoms = [a for a in batch if a["cand"] not in seen]
    bal = balance_atom(batch)
    if not new_atoms and not bal:
        print(f"[corpus] no new atoms for {task}"); return out, 0
    fresh = os.path.getsize(out) == 0 if os.path.exists(out) else True
    with open(out, "a", encoding="utf-8") as f:
        if fresh:
            f.write(f"# 避坑语料 · autolab/{task}(compass·RSI grounded-retrieval 用)\n")
            f.write("> round-N eval 失败/低分原因 → producer 下轮 grounded 臂 retrieve 注入。\n\n")
        if bal:
            f.write(f"\n## 平衡警示(本批·最高优先)\n{bal}\n\n## 候选避坑\n")
        for a in new_atoms:
            seen.add(a["cand"])
            med = f" median={a['median']}s" if a.get("median") is not None else ""
            f.write(f"- cand={a['cand']} reward={a['reward']}{med} [{a['tag']}]: {a['lesson']}\n")
    print(f"[corpus] +{len(new_atoms)} atoms" + (" + balance警示" if bal else "") + f" → {out}")
    return out, len(new_atoms)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("rewards", nargs="+")
    a = ap.parse_args()
    ingest(a.task, a.rewards)
