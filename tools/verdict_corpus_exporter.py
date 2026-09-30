#!/usr/bin/env python3
"""verdict_corpus_exporter · SSI×Jev 提案 P1:verdict→训练集聚合器 v0。

目标(SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930.md P1):把仓内散落的 verdict
工件聚合成统一训练集格式,喂三态判分器(pass/fail/insufficient_evidence)。

纪律:
  · 只导出,不改判;带真值标签(label_origin 可溯)才进 train_set,
    其余诚实进 unlabelled 池——不拿判分器自报冒充标签。
  · 每条带 source 路径 + 内容 hash(可溯源,复算可对账)。
  · 输出 manifest:计数、源清单、schema 说明(报数纪律:如实报数)。

用法:python tools/verdict_corpus_exporter.py [--out runtime/verdict_corpus]
"""
from __future__ import annotations

import argparse
import glob
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

# v3 态枚举(insufficient_evidence ≡ unverifiable 等价映射,与 F15 Choice 三态对齐)
_TRUTH_MAP = {"pass": "pass", "fail": "fail",
              "unverifiable": "insufficient_evidence",
              "insufficient_evidence": "insufficient_evidence"}


def _content_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()[:16]


def _sample(sid, source, criteria_ref, artifact, judge_output,
            truth_label=None, label_origin=None, reason=""):
    """统一样本 schema。truth_label 缺失 → unlabelled 池。"""
    s = {
        "id": sid,
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "source": str(source),
        "criteria_ref": criteria_ref,
        "artifact": artifact,            # 判分输入(题面/读数/产物摘要)
        "judge_output": judge_output,    # 被检判分器的输出
        "content_hash": _content_hash([criteria_ref, artifact, judge_output]),
    }
    if truth_label is not None:
        s["truth_label"] = truth_label
        s["label_origin"] = label_origin
        s["reason"] = reason
    return s


def _loads_lenient(text: str):
    """宽容 JSON:兼容手拼件(首例 = 平衡对象 + ',\n"analysis": ...' 尾巴)。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        depth, instr, esc = 0, False, False
        for i, ch in enumerate(text):
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == '"':
                instr = not instr
                continue
            if instr:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[:i + 1])
        raise


def harvest_f15_meta(path: Path) -> list:
    """F15 meta-judge 件(两种格式):
    ① 三供应商版:顶层 compass_gates{case:三态}+ 各供应商{case:概率}
    ② 首例版:results{case:{compass:三态, jev_noul:概率}}
    compass 三态=基准真值,供应商概率=被检输出。"""
    d = _loads_lenient(path.read_text(encoding="utf-8"))
    out = []
    if isinstance(d.get("results"), dict):  # 首例版
        for case_id, cell in d["results"].items():
            truth3 = _TRUTH_MAP.get(str(cell.get("compass", "")).lower())
            if truth3 is None:
                continue
            out.append(_sample(
                sid=f"f15-{path.stem}-{case_id}",
                source=path, criteria_ref="F15-meta-judge 三态基准(choices@assay)",
                artifact={"case_id": case_id,
                          "sample_pack": "scripts/f15_meta_judge.py SAMPLES"},
                judge_output={k: v for k, v in cell.items() if k != "compass"},
                truth_label=truth3, label_origin="compass_gates(三门判分)",
                reason="F15 首例:三门判分为基准,jev_noul 概率为被检对象"))
        return out
    gates = d.get("compass_gates") or {}    # 三供应商版
    for case_id, truth in gates.items():
        truth3 = _TRUTH_MAP.get(str(truth).lower())
        if truth3 is None:
            continue
        judge_out = {k: d[k][case_id] for k in d
                     if k not in ("compass_gates", "analysis", "ts")
                     and isinstance(d[k], dict) and case_id in d[k]}
        out.append(_sample(
            sid=f"f15-{path.stem}-{case_id}",
            source=path, criteria_ref="F15-meta-judge 三态基准(choices@assay)",
            artifact={"case_id": case_id, "sample_pack": "scripts/f15_meta_judge.py SAMPLES"},
            judge_output=judge_out,
            truth_label=truth3, label_origin="compass_gates(三门判分)",
            reason="F15 抽样:三门判分为基准,供应商概率输出为被检对象"))
    return out


def harvest_judge_pack_unlabelled(path: Path) -> list:
    """BC1 考题包(task_uid+产物):v0 无逐题人工标签 → unlabelled 池。"""
    items = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        return []
    return [_sample(
        sid=f"bc1-{path.stem}-{i}",
        source=path, criteria_ref="BC1 考题(verifier_path+run_cmd)",
        artifact={"task_uid": it.get("task_uid"), "repo": it.get("repo"),
                  "verifier_path": it.get("verifier_path"),
                  "produced_output_head": str(it.get("produced_output"))[:300]},
        judge_output={"run_cmd": it.get("run_cmd")})  # 判分输出未内联,audit 侧才有
        for i, it in enumerate(items)]


def harvest_vtf_aggregated(path: Path) -> list:
    """vtf 评测 run 的 aggregated_metrics:判分器输出侧(无人工逐题标签)。"""
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    metrics = {k: d[k] for k in list(d)[:20] if isinstance(d[k], (int, float, str))}
    return [_sample(
        sid=f"vtf-{path.parts[-3] if len(path.parts) >= 3 else 'run'}-{path.parts[-2] if len(path.parts) >= 2 else 'x'}",
        source=path, criteria_ref="评测 run 汇总指标(aggregated_metrics)",
        artifact={"metrics_head": metrics},
        judge_output={"note": "run-level metrics; per-item labels not present"})]


def harvest_bc1_scorecard(bc_dir: Path) -> list:
    """BC1 v1/v2 自测成绩单 → 逐题样本(v1 的 7 FAIL 人工审计=判分器纠错金矿)。

    标签映射(源:SELFTEST_SCORECARD.md 逐题审计表 + V2 重考,2026-09-23):
      v1 11 PASS:verify=pass,truth=pass(判分器对)
      T12-0/1:verify=fail,truth=pass(真值错误——考生比真值对,判分器被坏真值骗)
      T11-0/1/2:verify=fail,truth=insufficient_evidence(题面歧义,应判 U 而非 fail)
      T31-1/2:verify=fail,truth=insufficient_evidence(边界未定义)
      v2 18/18:verify=pass,truth=pass(修题重考全对=v1 归因的反向证明)
    """
    v1_audit = {  # (verify, truth, audit_reason) —— 数据化自 scorecard 审计表
        "T12-0": ("fail", "pass", "真值错误:生成器意外产生第二处真矛盾,考生多报的那对是真的,考生比真值更对"),
        "T12-1": ("fail", "pass", "真值错误:同 T12-0"),
        "T11-0": ("fail", "insufficient_evidence", "题面歧义:due_promises 语义两读,expected 与考生采用不同但各自合理的口径"),
        "T11-1": ("fail", "insufficient_evidence", "题面歧义:同 T11-0"),
        "T11-2": ("fail", "insufficient_evidence", "题面歧义:同 T11-0"),
        "T31-1": ("fail", "insufficient_evidence", "边界未定义:「复发」是否含首见当日未声明,expected 宽口径 vs 考生严口径"),
        "T31-2": ("fail", "insufficient_evidence", "边界未定义:同 T31-1"),
    }
    out = []
    # v1 实际被考题号 = selftest_answers.json 的键(public 18;decision_set 全 30 含
    # holdout 12 未考,不可作标签源——首版曾错标,以 answers 键为准+18 题硬校验)
    try:
        ids = list(json.loads(
            (bc_dir / "selftest_answers.json").read_text(encoding="utf-8")).keys())
    except Exception:
        ids = []
    if len(ids) != 18:
        raise SystemExit(f"BC1 v1 实际考题数 {len(ids)} ≠ 18(scorecard 口径),中止防错标")
    for qid in ids:
        verify, truth, reason = v1_audit.get(qid, ("pass", "pass", "原样判分 PASS,审计无异议"))
        out.append(_sample(
            sid=f"bc1-v1-{qid}",
            source=bc_dir / "SELFTEST_SCORECARD.md",
            criteria_ref="BC1 v1 自测(verify_bc1.py 三态,U 不充正分;sha=16de925e)",
            artifact={"exam": "selftest_exam_paper.json", "qid": qid,
                      "audit_table": "SELFTEST_SCORECARD.md §逐题审计"},
            judge_output={"verify_bc1": verify},
            truth_label=truth, label_origin="BC1 v1 逐题人工审计(2026-09-23)",
            reason=reason))
    # v2 重考(修题后 18/18,含 7 缺陷题转 PASS——归因正确的反向证明)
    try:
        ids2 = list(json.loads(
            (bc_dir / "selftest_answers_v2.json").read_text(encoding="utf-8")).keys())
    except Exception:
        ids2 = []
    if len(ids2) != 18:
        raise SystemExit(f"BC1 v2 实际考题数 {len(ids2)} ≠ 18,中止防错标")
    for qid in ids2:
        out.append(_sample(
            sid=f"bc1-v2-{qid}",
            source=bc_dir / "SELFTEST_SCORECARD_V2.md",
            criteria_ref="BC1 v2 自测(五处出题缺陷已修;sha=3b9def7d)",
            artifact={"exam": "selftest_exam_paper_v2.json", "qid": qid},
            judge_output={"verify_bc1": "pass"},
            truth_label="pass", label_origin="BC1 v2 重考+非实现者复算",
            reason="修题后重考 18/18 全 PASS,7 缺陷题全部转 PASS 且无新错"))
    return out


def harvest_t3_blind(t3_dir: Path) -> list:
    """T3 jev-curate 首个外部履约 → 盲评真值样本(n=5)+ 三 findings 系统性错误样本。

    三层结构(仓内最完整的判绩账样本族):
      judge_output = jev-curate 腿判定(RESULTS.md 读数表)
      truth_label  = blind_labels.json(独立会话盲评,只读 blind_pack 未读结果)
      勘误层       = RECOMPUTE_REPORT(独立复算 RED→6 处勘误,R1 标注分歧未预披露)
    """
    bl = json.loads((t3_dir / "blind_labels.json").read_text(encoding="utf-8"))
    out = []
    for row in bl.get("labels", []):
        rid = row.get("rid", "?")
        out.append(_sample(
            sid=f"t3-jevcurate-{rid}",
            source=t3_dir / "blind_labels.json",
            criteria_ref="T3 mini jev-curate PROTOCOL.md(预注册判据)",
            artifact={"rid": rid, "probe": "jev-trust-probe-format-t3-*.jsonl",
                      "rationale": row.get("rationale", "")[:200]},
            judge_output={"delivery": "RESULTS.md 读数表(noul/depth 腿+阈值判定)",
                          "verdict": "见 RESULTS.md(逐行腿输出)"},
            truth_label=("fail" if row.get("y_circ") == 1 else "pass"),
            label_origin="T3 独立盲评(recompute-agent·只读 blind_pack·2026-09-26)",
            reason=f"y_circ={row.get('y_circ')} d_depth={row.get('d_depth')}"
                   "(1-5 标尺;复算层另证 R1 标注分歧未预披露=预注册纪律样本)"))
    # 三 findings=判分管线系统性错误+人工定性(F1 格式/F2 标尺/F3 误拒)
    for fid, desc in [
        ("F1", "score 腿 criteria dict 在真 API 必 422,生产全量拒收(格式 bug 非阈值问题)"),
        ("F2", "标尺错位:真 API 0-4 vs 阈值按 1-5 写,depth 腿真值 4 的正确行也被拒"),
        ("F3", "R3 纯断言行被 noul 腿误拒(方向对腿标签错):口径敏感点 S1"),
    ]:
        out.append(_sample(
            sid=f"t3-finding-{fid}",
            source=t3_dir / "RESULTS.md",
            criteria_ref="T3 主批 findings(生产影响排序)",
            artifact={"finding": fid, "evidence": "RESULTS.md 原文+probe jsonl"},
            judge_output={"pipeline": "jev-curate reasoning-math preset 生产路径"},
            truth_label="fail",
            label_origin="T3 主批审计+独立复算(RECOMPUTE_REPORT)",
            reason=desc))
    return out


def harvest_e5_gates_unlabelled(path: Path) -> list:
    """e5 三门判分首件(33 题):gates 自动三态+hook 实弹+签名。
    无人工逐题对照 → unlabelled(诚实处理,不拿自动判分冒充真值)。"""
    d = json.loads(path.read_text(encoding="utf-8"))
    verdicts = d.get("verdicts") or {}
    return [_sample(
        sid=f"e5gates-{qid}",
        source=path,
        criteria_ref="三门真门 G1-G3(ops/assay_gates/gates_v1.py)",
        artifact={"qid": qid, "hook_fired": d.get("hook_fired")},
        judge_output={"gates_verdict": v})
        for qid, v in verdicts.items()]


def harvest_rejudge_selfreported(path: Path) -> list:
    """arm_a 重判 500 题 → unlabelled(judge-self-reported 族)。

    🔴 证伪记录(9/30):行内 is_correct = _parse_judge(judge_raw)(harness
    L493),judge 开卷判(truth 在 prompt 里)的自报复写,非独立真值对比——
    500/500"一致"只是同源复写。**不得冒充 labelled**(报数纪律)。
    升级条件:非实现者抽样(≥10%)独立比对 question/truth/model_answer,
    一致率达标后整族升 labelled。"""
    d = json.loads(path.read_text(encoding="utf-8"))
    return [_sample(
        sid=f"rejudge-{r.get('question_id')}",
        source=path,
        criteria_ref="LME arm-a 重判(同 judge 协议 retry,judge 开卷)",
        artifact={"question": str(r.get("question"))[:200],
                  "model_answer": str(r.get("model_answer"))[:200],
                  "official_truth": r.get("truth")},
        judge_output={"judge_raw": r.get("judge_raw"),
                      "is_correct_self": r.get("is_correct")})
        for r in d.values()]


def harvest_errata_registry() -> list:
    """v5 挑战登记处(第四原语)errata → unlabelled(errata-registry·smoke 族)。

    🔴 smoke 样本(recomputer=v5-smoke 自测),非独立复算,不进 labelled;
    真实第三方 errata(独立 recomputer)到达后才是 labelled 活水——该登记处
    是 SSI×Jev 判分器 P3 动态真值供给的正式管道。"""
    reg = Path(r"C:/Users/chunx/nautilus-v5/vtf/assay_errata.jsonl")
    if not reg.exists():
        return []
    out = []
    for line in reg.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        out.append(_sample(
            sid=f"errata-{e.get('challenge_id')}",
            source=reg,
            criteria_ref="挑战登记处 18890(90 天窗·只追加不删)",
            artifact={"original_verdict_ref": e.get("original_verdict_ref"),
                      "reason": e.get("reason")},
            judge_output={"new_verdict": e.get("new_verdict"),
                          "recomputer": e.get("recomputer"),
                          "status": e.get("status")}))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runtime/verdict_corpus")
    args = ap.parse_args()
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    labelled, unlabelled = [], []
    src_summary = []

    # S1 · F15 / meta-judge 件(带 compass_gates 真值)
    for p in [ROOT / "runtime" / "f15_meta_judge_3prov.json",
              ROOT / "runtime" / "jev_meta_judge_first.json"]:
        if p.exists():
            ss = harvest_f15_meta(p)
            labelled += ss
            src_summary.append((str(p.relative_to(ROOT)), f"{len(ss)} labelled"))

    # S2 · BC1 自测成绩单逐题标签(v1 审计+v2 重考 = 最大标签增量源)
    bc_dir = ROOT / "runtime" / "assay_bc1_20260927"
    if bc_dir.exists():
        ss = harvest_bc1_scorecard(bc_dir)
        labelled += ss
        src_summary.append(("runtime/assay_bc1_20260927/SELFTEST_SCORECARD{,_V2}.md",
                            f"{len(ss)} labelled"))

    # S3 · BC1 考题包(unlabelled;判分输出未内联)
    for p in sorted((ROOT / "runtime" / "benchmarks").glob("*/judge_pack.json")):
        ss = harvest_judge_pack_unlabelled(p)
        unlabelled += ss
        src_summary.append((str(p.relative_to(ROOT)), f"{len(ss)} unlabelled"))

    # S4 · T3 jev-curate 盲评真值(外部首单三层:交付 vs 盲评 vs 复算)
    t3_dir = ROOT / "runtime" / "jev_trust_t3_jevcurate_20260924"
    if (t3_dir / "blind_labels.json").exists():
        ss = harvest_t3_blind(t3_dir)
        labelled += ss
        src_summary.append(("runtime/jev_trust_t3_jevcurate_20260924/",
                            f"{len(ss)} labelled"))

    # S5 · e5 三门判分首件(33 题自动判分,无人工对照 → unlabelled)
    e5 = ROOT / "runtime" / "e5_gates_first33.json"
    if e5.exists():
        ss = harvest_e5_gates_unlabelled(e5)
        unlabelled += ss
        src_summary.append(("runtime/e5_gates_first33.json",
                            f"{len(ss)} unlabelled"))

    # S6 · arm-a 重判 500 题(judge 自报族,待非实现者抽样复算升级)
    rj = ROOT / "vtf" / "_e2e_diag" / "arm_a_rows_rejudged.json"
    if rj.exists():
        ss = harvest_rejudge_selfreported(rj)
        unlabelled += ss
        src_summary.append(("vtf/_e2e_diag/arm_a_rows_rejudged.json",
                            f"{len(ss)} unlabelled(judge-self-reported·待复算升级)"))

    # S7 · v5 挑战登记处 errata(第四原语,smoke 族)
    ss = harvest_errata_registry()
    unlabelled += ss
    src_summary.append(("v5:18890 assay_errata.jsonl",
                        f"{len(ss)} unlabelled(errata-registry·smoke)"))

    # S3 · vtf aggregated_metrics(unlabelled;复算记录的 run 在 v1 挂标签)
    n_vtf = 0
    for p in sorted(glob.glob(str(ROOT / "vtf" / "**" / "aggregated_metrics.json"),
                              recursive=True))[:200]:
        ss = harvest_vtf_aggregated(Path(p))
        unlabelled += ss
        n_vtf += len(ss)
    src_summary.append(("vtf/**/aggregated_metrics.json", f"{n_vtf} unlabelled"))

    (out_dir / "train_set_v0.jsonl").write_text(
        "\n".join(json.dumps(s, ensure_ascii=False) for s in labelled) + "\n",
        encoding="utf-8")
    (out_dir / "unlabelled_v0.jsonl").write_text(
        "\n".join(json.dumps(s, ensure_ascii=False) for s in unlabelled) + "\n",
        encoding="utf-8")
    manifest = {
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "counts": {"labelled": len(labelled), "unlabelled": len(unlabelled),
                   "p1_target": 500},
        "schema": {"truth_label": "pass|fail|insufficient_evidence",
                   "label_origin": "真值来源(人工复核/三门判分/独立复算)",
                   "content_hash": "sha256[:16] 溯源对账"},
        "sources": src_summary,
        "v1_backlog": ["BC1 SELFTEST_SCORECARD(.sig) 逐题标签解析",
                       "T3 mini 主批 findings 挂标签",
                       "rejudge_errors 勘误样本(判绩账:评委也会错)"],
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[exporter] labelled={len(labelled)} unlabelled={len(unlabelled)} "
          f"(P1 目标 500 带标签,现距 {500 - len(labelled)})")
    for s, c in src_summary:
        print(f"  {c:<28} {s}")


if __name__ == "__main__":
    main()
