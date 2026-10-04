#!/usr/bin/env python3
"""人类抽检标定 60 题材料包·抽样脚本(JUDGE_UPGRADE_PREP_20261004 §三协议)。

分层:主包 498 帧按 3B v4 定版判读(goldpack_main_J2.csv)dim3 三层(高/中/低)各 20。
层内选择:seed 洗牌后,7B/3B dim2 分歧帧(判据二义点主场)优先,一致帧补足。
双盲纪律:产出作答表不含任何判官读数;判官读数只进 SAMPLING.md 的层标记账(供汇总期对表)。
seed=202610042 冻结,重跑零漂移。
"""
import csv
import json
import random
import shutil
import hashlib
from collections import Counter
from pathlib import Path

BASE = Path("runtime/e1_judge_pack")
OUT = BASE / "calib60"
SEED = 202610042
PER_LAYER = 20


def load_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


j3 = load_csv(BASE / "goldpack_main_J2.csv")      # 3B v4 定版(2842 收讫)
j7 = load_csv(BASE / "upgrade_7b" / "goldpack_main_J2_7b.csv")  # 7B 首跑
cards = json.loads((BASE / "main_judge_taskcard_map_498.json").read_text(encoding="utf-8"))["cards"]
print(f"[data] 3B n={len(j3)} 7B n={len(j7)} cards n={len(cards)}")

# 分层(3B dim3)——实测 高0/中452/低46:协议"各20"高层不可行,
# 高层 20 配额按协议 oversample 条款方向并入低层(中20/低40,难题多=更保守),如实注记不私改层轴
QUOTA = {"高": 0, "中": 20, "低": 40}
layers = {"高": [], "中": [], "低": []}
for c in cards:
    r = j3.get(c["id"])
    if r:
        layers[r["dim3"]].append(c["id"])
print("[layers]", {k: len(v) for k, v in layers.items()})

rng = random.Random(SEED)
picked, meta = [], []
for layer, ids in layers.items():
    if QUOTA[layer] == 0:
        continue
    rng.shuffle(ids)
    # 层内:分歧帧(7B dim2 != 3B dim2)优先,同层内保持洗牌序
    dis = [i for i in ids if j7.get(i, {}).get("dim2") != j3[i]["dim2"]]
    con = [i for i in ids if j7.get(i, {}).get("dim2") == j3[i]["dim2"]]
    take = (dis + con)[:QUOTA[layer]]
    picked += take
    meta += [(i, layer, j3[i]["dim2"], j7.get(i, {}).get("dim2", "?"),
              j7.get(i, {}).get("dim2") != j3[i]["dim2"]) for i in take]

print(f"[picked] n={len(picked)} 分歧帧={sum(1 for m in meta if m[4])}/60")
print("[dim1 3B层内分布]", Counter(j3[i]["dim1"] for i, *_ in meta))

# 帧+任务卡
card_by_id = {c["id"]: c for c in cards}
OUT.mkdir(exist_ok=True)
(OUT / "frames_calib60").mkdir(exist_ok=True)
rows = []
for k, (qid, layer, d2_3b, d2_7b, dis) in enumerate(sorted(meta), 1):
    c = card_by_id[qid]
    src = BASE / "main_pack" / "frames" / (qid + ".jpg")
    dst = OUT / "frames_calib60" / (qid + ".jpg")
    shutil.copyfile(src, dst)
    rows.append({
        "q": k, "id": qid, "layer_3b_dim3": layer, "task": c["task_zh_fixed"],
        "progress_pct": c["progress_pct"],
        "frame_sha16": sha16(dst),
        "判官读数区_汇总期填": f"3B_dim2={d2_3b} 7B_dim2={d2_7b} 分歧={dis}",
    })

# SAMPLING.md(抽样账,含判官读数区——标定人不读此件)
sampling = [
    "# calib60 抽样账(标定人不读;汇总期判读方对表用)",
    f"- seed={SEED} 冻结,脚本 tools/e1_calib60_sample.py 重跑零漂移",
    "- 分层=3B v4 定版 dim3;实测 高0/中452/低46,协议\"各20\"高层不可行→高层配额按协议 oversample 条款方向并入低层(中20/低40),层轴不改如实注记",
    "- 层内 7B/3B dim2 分歧帧优先(判据二义点主场),一致帧补足",
    f"- 实抽分歧帧 {sum(1 for m in meta if m[4])}/60;dim1 3B 分布 {dict(Counter(j3[i]['dim1'] for i, *_ in meta))}",
    "- 双盲:ANSWER_SHEET.md 不含判官读数;本件与 frames 同发判读方留档,标定人只持须知+作答表+帧",
    "",
    "| q | id | 3B_dim3层 | 3B_dim2 | 7B_dim2 | 分歧 | frame_sha16 |",
    "|---|---|---|---|---|---|---|",
]
for r in rows:
    d = r["判官读数区_汇总期填"]
    d2_3b = d.split("3B_dim2=")[1].split()[0]
    d2_7b = d.split("7B_dim2=")[1].split()[0]
    dis = d.split("分歧=")[1]
    sampling.append(f"| {r['q']} | {r['id']} | {r['layer_3b_dim3']} | {d2_3b} | {d2_7b} | {dis} | {r['frame_sha16']} |")
(OUT / "SAMPLING.md").write_text("\n".join(sampling), encoding="utf-8")

# ANSWER_SHEET.md(标定人唯一作答面,零判官读数)
sheet = [
    "# 标定作答表(60 题)",
    "",
    "作答判据=《判官须知》原文(随包);每题看帧作答五组:完成度(完成/部分/未动)/",
    "执行质量(正常/异常/无法判断)/置信(高/中/低)/正问(是/否)/反问(是/否)。",
    "独立作答;看不清→无法判断+低置信;不看任何 AI 判读输出。",
    "",
    "| q | 任务 | 进度 | 完成度 | 执行质量 | 置信 | 正问 | 反问 |",
    "|---|---|---|---|---|---|---|---|",
]
for r in sorted(rows, key=lambda x: x["q"]):
    sheet.append(f"| {r['q']} | {r['task']} | {r['progress_pct']}% |  |  |  |  |  |")
(OUT / "ANSWER_SHEET.md").write_text("\n".join(sheet), encoding="utf-8")

# 须知原文拷贝
shutil.copyfile(BASE / "判官须知.txt", OUT / "判官须知.txt")
(OUT / "sample_manifest.json").write_text(
    json.dumps({"seed": SEED, "n": len(rows), "rows": rows,
                "须知_sha16": sha16(BASE / "判官须知.txt")},
               ensure_ascii=False, indent=1), encoding="utf-8")
print(f"[out] {OUT}/ frames={len(rows)} SAMPLING/ANSWER_SHEET/须知/manifest 四件齐")
