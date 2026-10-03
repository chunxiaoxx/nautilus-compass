#!/usr/bin/env python3
"""P3 前置 · G1/pusht 五演 verdict → 签名语料增量 delta_0001 导出器(2026-10-03)。

承 docs/plans/P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003.md §二(S1 白名单门)首例执行:
本批全部 label_origin=independent_recompute(compass 独立判,sha 锚定),无 rejected。

样本单位=被判工件/被裁判定(批级材料判 + 判定级假说/声称),三态标签:
  材料质量门合格 → pass;U 态 MATERIAL_INSUFFICIENT → insufficient_evidence;
  被实测否证的假说 → fail;主判据未跑/显著性不足的声称 → insufficient_evidence。

锚件来源(sha256 已核):runtime/loop/_p3_g1_verdict.json(A100 g1_verdict.json,G vs B2 终判)
  + _p3_pusht_4win_verdict.json(四窗终判)+ _p3_B_fixed_infer_summary.json(v5 B 修复批)
  + 函件锚(2407 U 态/2422 假说裁决/2459 v5 送判/2464 差分终判,commit 45184784/fe7922b5)。
用法:python tools/verdict_corpus_embodied_delta.py
输出:runtime/verdict_corpus/delta/delta_0001.jsonl + manifest_delta_0001.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
LOOP = ROOT / "runtime" / "loop"
OUT = ROOT / "runtime" / "verdict_corpus" / "delta"
OUT.mkdir(parents=True, exist_ok=True)

G1V = json.loads((LOOP / "_p3_g1_verdict.json").read_text(encoding="utf-8"))
P4V = json.loads((LOOP / "_p3_pusht_4win_verdict.json").read_text(encoding="utf-8"))
BFIX = json.loads((LOOP / "_p3_B_fixed_infer_summary.json").read_text(encoding="utf-8"))

G1_CRITERIA = ("G1 帧级判据 J1方向一致率(sign 语义)/J2幅度比带宽[0.3,3.0]/J3 sha锚定"
               "+质量门(INSUFFICIENT/THIN n_ok<20/DEGENERATE>50%);函2407三修")
PUSHT_CRITERIA = ("pusht 首案层1效度三数(冻结,主判据=rollout 成功率)+帧级辅助口径"
                  "(dir/ratio 带宽[0.3,3.0],filter≥1e-3);层3 R1/R2/R3 剔除已执行")


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()[:16]


def sample(sid, source, criteria_ref, artifact, judge_output, truth, reason):
    s = {"id": sid, "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
         "source": source, "criteria_ref": criteria_ref,
         "artifact": artifact, "judge_output": judge_output,
         "content_hash": _hash([criteria_ref, artifact, judge_output]),
         "truth_label": truth, "label_origin": "independent_recompute",
         "reason": reason}
    return s


def g1_arm_material(sid, arm_key, batch_note, source):
    a = G1V["arms"][arm_key]
    art = {"batch": batch_note, "n": a["n"], "n_ok": a["n_ok"],
           "J1_dir_rate": a["J1_dir_rate"], "J2_ratio_in_band": a["J2_ratio_in_band"],
           "ratio_median": a["ratio_median"], "rows_sha16": a["rows_sha16"],
           "per_ep_dir": a["per_ep_dir"], "ckpt": a["ckpt"]}
    return sample(sid, source, G1_CRITERIA, art,
                  {"probe_readings": "见 artifact;policy pred 逐帧材料(A100 infer_compare.jsonl)"},
                  "pass", f"材料质量门 OK(n_ok=40/40,degenerate=0);verdict ts {G1V['ts']}")


S = []
# ── G1 材料判(5)──
S.append(sample(
    "g1_G_old_batch", "函2407+commit 45184784(compass 判分机构 U 态首演)", G1_CRITERIA,
    {"batch": "G 旧批(修复前)", "n": 40, "n_ok": 8, "dir_rate": 1.0,
     "ratio_median": ">4000(静止段分母 5e-5 级所致,已实测)",
     "rows_sha16": "见函2407(旧批已被修复批覆盖,未回拉)"},
    {"probe_readings": "零增量帧未滤+dir abs 实现恒真", "note": "读数锚=函2407 原文"},
    "insufficient_evidence",
    "U 态 MATERIAL_INSUFFICIENT:8/40 帧+dir 恒真实现+ratio 数千倍=材料构造问题非模型差异"))
S.append(sample(
    "g1_B_old_batch", "函2407+commit 45184784;rows sha 前缀 413e6aba(R54 commit eae2d9b2)", G1_CRITERIA,
    {"batch": "B 旧批(30% 注入,修复前)", "n": 40, "n_ok": 8, "dir_rate": 1.0,
     "ratio_median": ">4000", "rows_sha16_prefix": "413e6aba"},
    {"probe_readings": "与 G 旧批同形态"},
    "insufficient_evidence", "U 态 MATERIAL_INSUFFICIENT(同 G 旧批三因)"))
S.append(g1_arm_material("g1_G_fixed_batch", "G", "G 修复批(三修生效)",
                         "A100 g1_verdict.json arms.G(sha eab63d7fd833d7da)"))
S.append(sample(
    "g1_B_fixed_batch", "v5 送判函2459(自报与复算零偏差)+compass 回函2464", G1_CRITERIA,
    {"batch": "B v5 修复批", "n": BFIX["n_frames"], "n_ok": BFIX["n_ok"],
     "dir_rate": BFIX["dir_rate"], "ratio_median": BFIX["ratio_median"],
     "rows_sha16_prefix": "0f845013", "frame_filter": BFIX["frame_filter"]},
    {"probe_readings": "v5 通道修复批;差分 ΔJ1=+0.025/ΔJ2=0 valid=true"},
    "pass", "材料质量门 OK;三修实测生效(函2464 差分终判)"))
S.append(g1_arm_material("g1_B2_batch", "B", "B2 flywheel 材料链批",
                         "A100 g1_verdict.json arms.B(sha 340eff115ef49e50);双链一致性实测 R59"))
# ── G1 判定级(3)──
S.append(sample(
    "g1_hyp_unnormalized", "假说对撞裁决函2422+commit fe7922b5", G1_CRITERIA,
    {"claim": "flywheel:旧批 ratio 数千倍=pred 未反归一化(差千倍)",
     "evidence": "实测 pred≈act 差 4% 非千倍;真因=静止段分母 5e-5+abs 实现恒过"},
    {"claimant": "flywheel", "claim_form": "假说"},
    "fail", "假说被实测否证(差 4% vs 声称千倍);独立复算驳倒"))
S.append(sample(
    "g1_hyp_dir_robust", "假说对撞裁决函2422+commit fe7922b5", G1_CRITERIA,
    {"claim": "方向稳健可判(dir 信号在旧材料下仍可用)",
     "evidence": "dir 实现 abs(dot)>0 恒真+零增量帧未滤=方向信号不可信"},
    {"claimant": "flywheel", "claim_form": "假说"},
    "fail", "'方向稳健可判'不成立;ep0-only 与其自述不符坐实"))
S.append(sample(
    "g1_claim_injection_conduction", "A100 g1_verdict.json findings[inferred]+差分", G1_CRITERIA,
    {"claim": "30% 视频注入传导到预测(应在读数层面可测)",
     "evidence": "双臂 pred 同形态;差分实测 ΔJ1=+0.025/ΔJ2=0≈0",
     "evidence_tier": "inferred", "upgrade_path": "注入帧 vs 干净帧 pred 逐帧对比"},
    {"claimant": "G1 实验设计", "claim_form": "设计假设"},
    "insufficient_evidence",
    "不传导特征增强但为[推断];若坐实则 G1 当前设计测不出注入效应,差分裁断无意义——升级实验未立项"))
# ── pusht 材料判(4)+判定级(2)──
for w in ("A1O", "A1N", "A2F", "A2N"):
    v = P4V["windows"][w]
    S.append(sample(
        f"pusht_{w}_material", f"A100 pusht_4win_verdict.json windows.{w}", PUSHT_CRITERIA,
        {"window": w, "n": v["n"], "n_ok": v["n_ok"], "dir_rate": v["dir_rate"],
         "ratio_in_band": v["ratio_in_band"], "ratio_median_np": v["ratio_median_np"],
         "rows_sha16": v["rows_sha16"]},
        {"probe_readings": "v5 四窗推理材料;判读归 compass 独立"},
        "pass", f"窗材料合格(n_ok=40/40);噪声底=0 三方复核 ts {P4V['ts']}"))
_c = P4V["comparisons"]["clean_A1N_vs_A2F"]
S.append(sample(
    "pusht_claim_repair_efficacy", "A100 pusht_4win_verdict.json comparisons.clean", PUSHT_CRITERIA,
    {"claim": "QC 修复提升 policy 效度(修复有效)",
     "evidence": f"A1N vs A2F Δmedian=+{_c['delta_median_np']},MWU p={_c['p_two_sided']}"
                 "(样本级显著,噪声底=0);但帧不配对=抽样混杂未隔离;层1主判据 rollout 未跑",
     "upgrade_path": "配对帧对照(~15min/对)+rollout 成功率主判据"},
    {"claimant": "首案效度实验", "claim_form": "效度声称"},
    "insufficient_evidence",
    "样本级显著≠归因≠效度终判;效度终判留预注册主判据 rollout(未跑)"))
_a = P4V["comparisons"]["adapter_A1O_vs_A1N"]
S.append(sample(
    "pusht_claim_adapter_effect", "A100 pusht_4win_verdict.json comparisons.adapter", PUSHT_CRITERIA,
    {"claim": "adapter v1→v2 变更对读数有显著效应",
     "evidence": f"Δmedian={_a['delta_median_np']},MWU p={_a['p_two_sided']}(n.s.);"
                 "n=40 不足以裁断;混杂=代码变更(时间线实证)非 run 噪声",
     "upgrade_path": "同帧配对或大样本(n≥150)重测"},
    {"claimant": "v5 披露②", "claim_form": "混杂效应声称"},
    "insufficient_evidence", "n.s.+样本不足,裁断不了;A1O 剔除处置正确(不进数据效应判读)"))

delta_path = OUT / "delta_0001.jsonl"
delta_path.write_text("\n".join(json.dumps(s, ensure_ascii=False) for s in S) + "\n",
                      encoding="utf-8")
dist = {}
for s in S:
    dist[s["truth_label"]] = dist.get(s["truth_label"], 0) + 1
manifest = {
    "delta_id": "delta_0001", "exported_at": S[0]["exported_at"],
    "exporter": "tools/verdict_corpus_embodied_delta.py",
    "n_samples": len(S), "label_distribution": dist,
    "label_origin_all": "independent_recompute",
    "whitelist_rejected": 0,
    "delta_sha16": _hash(delta_path.read_text(encoding="utf-8")),
    "anchor_files_sha256": {
        "g1_verdict.json": "0a17c8b9b4078e5aa3b19eace4a3be47dc2aa11ca9114084952dd5a836cf11d2",
        "pusht_4win_verdict.json": "93a1409c3450d8078e24be297f3d8eed7836e3aadee600fa3b3209bd9c1671f3",
        "g1_infer_B/infer_summary.json": "818846d96c4834bfcb8b5b0c5f3d7dc14330f20dc866d19ec2676482d296a92b"},
    "letter_anchors": ["函2407(U态)", "函2422(假说裁决)", "函2459(v5送判)", "函2464(差分终判)"],
    "commit_anchors": ["45184784", "fe7922b5", "eae2d9b2"],
    "note": "首个增量;P3 S2 触发门槛≥200,本批 14 → 训练单 SKIP(见 runtime/judge_lora_p3/ledger.jsonl cycle1)",
}
(OUT / "manifest_delta_0001.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=1))
