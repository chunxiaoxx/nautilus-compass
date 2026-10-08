#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""delta_0004 回填生成器(2026-10-08 · 7B 语料第二段)。

把仓内已成文的判定档案升格为结构化 delta registry 条目(棘轮式:交付即入册)。
每条 truth_label 均来自已有档案的定谳判定(可溯源坐标),本脚本只做 schema 组装
+content_hash+qid 防撞校验——不做任何新判定(判据零放宽)。

输入源(全部仓内正本):
  docs/metering/C_VERDICT_LEDGER_20261007.md      冲正台账
  docs/metering/A2_RECOMPUTE_VERDICT_20261007.md  A2 复算判定
  docs/metering/PRECOR_ENACRE1_VERDICT_20261007.md E-NACRE-1 负结果
  docs/metering/PRECOR_BC_VERDICT_20261007.md     部署精度判定表
  docs/metering/PRECOR_JUDGE_ROBUST_20261006.md   预注册判据档
  runtime/loop/queue.md R301-R305/R347-R348       运维定谳案
输出:runtime/verdict_corpus/delta/delta_0004.jsonl(+manifest)
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runtime/verdict_corpus/delta/delta_0004.jsonl"
EXPORTED = "2026-10-08"


def case(id_: str, source: str, qid: str, artifact_ref: str,
         original_verdict: str, recompute_verdict: str, judge_reason: str,
         truth_label: str, label_origin: str, reason: str,
         domain: str = "artifact_judgment", fuel_eligible: bool = True) -> dict:
    body = {
        "id": id_,
        "exported_at": EXPORTED,
        "source": source,
        "criteria_ref": "档案定谳判定(坐标见 source;判据零放宽,本条无新判)",
        "artifact": {
            "qid": qid,
            "artifact_ref": artifact_ref,
            "original_verdict": original_verdict,
            "domain": domain,
            "fuel_eligible": fuel_eligible,
        },
        "judge_output": {
            "recompute_verdict": recompute_verdict,
            "judge_reason": judge_reason,
        },
        "truth_label": truth_label,
        "label_origin": label_origin,
        "reason": reason,
    }
    body["content_hash"] = hashlib.sha256(
        json.dumps(body, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()[:16]
    return body


CASES = [
    # —— C 冲正台账(docs/metering/C_VERDICT_LEDGER_20261007.md)——
    case("cverdict_dedup_1019rows", "docs/metering/C_VERDICT_LEDGER_20261007.md §1019 去重行",
         "cverdict-dedup-1019rows", "C 账 1019 行重复读数(SQL 可验)",
         "平台侧账面 1019 行重复(+2/row 常数)", "去重后 -30,413 账面读数",
         "A1 写入器常数 +2/行重复释放(根因已定谳)", "fail",
         "independent_recompute", "冲正案:重复坐实,去重定谳,fuel_eligible=True"),
    case("cverdict_merge_702", "docs/metering/C_VERDICT_LEDGER_20261007.md §702 合并",
         "cverdict-merge-702", "C 账 702 行跨源合并案",
         "702 行跨表口径分叉", "合并归一(验证 SQL 在档)",
         "跨源主键口径不一致,合并键已冻结", "pass",
         "independent_recompute", "冲正案:合并完成并过验证 SQL"),
    case("cverdict_gap_refill_3", "docs/metering/C_VERDICT_LEDGER_20261007.md §3 补缺",
         "cverdict-gap-refill-3", "C 账 3 行缺口回填",
         "3 行缺口(字段级缺失)", "全部回填(坐标在档)",
         "缺口=写入器段间丢行,已回填", "pass",
         "independent_recompute", "冲正案:缺口关闭,10/9 apply 复读窗在排"),
    case("cverdict_seeds_13", "docs/metering/C_VERDICT_LEDGER_20261007.md §13 seeds",
         "cverdict-seeds-13", "C 账 13 条 seed 转正",
         "13 条 seed 悬置", "全部转正入册",
         "seed 悬置=来源待认,平台已认领", "pass",
         "independent_recompute", "冲正案:seeds 转正,审计触发器留痕"),
    # —— A2 复算(docs/metering/A2_RECOMPUTE_VERDICT_20261007.md)——
    case("a2_recompute_425rows", "docs/metering/A2_RECOMPUTE_VERDICT_20261007.md",
         "a2-recompute-425rows", "A2 账 425 行复算",
         "A1 侧读数(含常数 +2 系统偏差)", "match 354 / mismatch 71(与平台逐位对齐)",
         "mismatch 71 全部落常数 +2 模式=A1 写入器根因", "pass",
         "independent_recompute", "A2 复算与平台侧逐位对齐;三权分立(生成/复算/终审)成立"),
    # —— E-NACRE-1(docs/metering/PRECOR_ENACRE1_VERDICT_20261007.md)——
    case("enacre1_negative_result", "docs/metering/PRECOR_ENACRE1_VERDICT_20261007.md",
         "enacre1-domain-routing-lora", "E-NACRE-1 域路由 LoRA(三 shard 451+451+500)",
         "假设:域路由 shard 提升判分", "Δ=-36.6pp,三域全回归(负结果)",
         "域 shard 过拟合(loss 0.0004)+训练量不足;动态权重悬置至语料≥3000", "fail",
         "preregistered_gate", "负结果照报入册;升级路径=先攒语料(本 delta 回填即该路线)"),
    # —— PRECOR BC 精度门(docs/metering/PRECOR_BC_VERDICT_20261007.md,预注册判据档 PRECOR_JUDGE_ROBUST_20261006.md)——
    case("precor_bc_fp16", "docs/metering/PRECOR_BC_VERDICT_20261007.md + PRECOR_JUDGE_ROBUST_20261006.md",
         "precor-bc-fp16", "fp16 对 bf16 锚一致率(291 held-out)",
         "预注册门 ≥99%", "1.0000(零翻转)过门",
         "fp16 数值噪声未跨判读阈值", "pass",
         "preregistered_gate", "fp16 可部署(与 bf16 同档);判定表上模型卡"),
    case("precor_bc_int8", "docs/metering/PRECOR_BC_VERDICT_20261007.md",
         "precor-bc-int8", "int8-bnb 对 bf16 锚一致率(291 held-out)",
         "预注册门 ≥99%", "0.9828(2 flips)未过门",
         "低概率边界案被量化噪声翻转", "fail",
         "preregistered_gate", "int8 禁生产部署;两翻转案坐标在判定表"),
    case("precor_bc_int4", "docs/metering/PRECOR_BC_VERDICT_20261007.md",
         "precor-bc-int4", "int4-nf4 对 bf16 锚一致率(291 held-out)",
         "预注册门 ≥99%", "0.9416(17 flips)未过门",
         "量化强度↑漂移单调↑(与 3B 独立观察同向)", "fail",
         "preregistered_gate", "int4 禁用;单调性=系统性属性非个例"),
    # —— 运维定谳(queue.md R301-R305 / R347-R348)——
    case("ops_daemon_uselesswork_verdict", "runtime/loop/queue.md R302(py-spy 取证)",
         "ops-daemon-uselesswork-storm", "云 daemon 过载风暴(19.5 万拒连)",
         "初诊 socket 泄漏(R256)", "py-spy 实证=无用功风暴(僵尸白算占满 32 槽),初诊推翻",
         "Liveness probe(MSG_PEEK)+GPU 嵌入代理根治,过载归零", "pass",
         "independent_recompute", "运维定谳:初诊推翻案——探针先证伪自己原则的正例"),
    case("ops_a100_key_leak_closure", "runtime/loop/queue.md 安全事件段(10/8)",
         "ops-a100-key-leak-3layer", "A100 凭据公开仓泄漏 6 天",
         "泄露实存(PUBLIC 仓 40 文件)", "三层闭环:树脱敏+机内轮换(chpasswd)+git filter-repo 历史清除",
         "泄漏 6 天+GPU 实例曾活跃→按已利用处置,全层闭环", "fail",
         "independent_recompute", "安全事件:事件=fail 定谳;处置闭环验证在档(md5+外网)"),
    case("ops_judge_nohup_fakeflag", "runtime/loop/queue.md R348(2026-10-08)",
         "ops-judge-rerun-fakeflag", "A100 判分 rerun DONE flag",
         "flag 生成=判分完成(表面)", "日志=python: command not found,判分零执行(假绿)",
         "nohup 非登录 shell 无 conda 别名;绝对路径 /root/venv/bin/python 重发后 GPU 41% 实跑", "fail",
         "independent_recompute", "假绿抓获案:flag≠完成,日志+GPU 双实证;环境锚入收割脚本"),
    case("ops_registry_render_metric", "runtime/loop/queue.md R339+R352(2026-10-08)",
         "ops-registry-render-metric", "终检预演 registry 仪表 WARN",
         "静态 HTML 抓不到异步渲染数字=页面问题(表面)", "口径问题:读 /corpus_stats.json 正本即 2228 正确",
         "状态≠内容≠可用三口径纪律;final_check.py 三口径固化后 11/11 PASS", "pass",
         "independent_recompute", "口径修正案:WARN 根治,终检脚本 v1 在役"),
]


def main():
    # qid 防撞:对池内既有 qid 校验
    existing = set()
    for f in ("split_train_v1", "split_dev_v1", "split_test_v1"):
        p = ROOT / f"runtime/verdict_corpus/{f}.jsonl"
        for l in p.read_text(encoding="utf-8").splitlines():
            if l.strip():
                e = json.loads(l)
                existing.add(e.get("qid") or "")
    for f in sorted((ROOT / "runtime/verdict_corpus/delta").glob("delta_*.jsonl")):
        for l in f.read_text(encoding="utf-8").splitlines():
            if l.strip():
                e = json.loads(l)
                existing.add((e.get("artifact") or {}).get("qid") or "")
    ids = {c["id"] for c in CASES}
    clash_q = [c["id"] for c in CASES if c["artifact"]["qid"] in existing]
    clash_i = ids & existing
    if clash_q or clash_i:
        raise SystemExit(f"qid/id 撞池: {clash_q} {clash_i}")

    OUT.write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in CASES) + "\n",
        encoding="utf-8")
    manifest = {
        "delta": "delta_0004.jsonl",
        "exported_at": EXPORTED,
        "n_cases": len(CASES),
        "by_label": {lb: sum(1 for c in CASES if c["truth_label"] == lb)
                     for lb in ("pass", "fail")},
        "by_origin": {o: sum(1 for c in CASES if c["label_origin"] == o)
                      for o in ("independent_recompute", "preregistered_gate")},
        "sources": sorted({c["source"].split(" ")[0] for c in CASES}),
        "note": "回填批:已成文档案升格入 registry,零新判定;判据零放宽",
    }
    (ROOT / "runtime/verdict_corpus/delta/manifest_delta_0004.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"delta_0004: {len(CASES)} cases |", manifest["by_label"], "|", manifest["by_origin"])


if __name__ == "__main__":
    main()
