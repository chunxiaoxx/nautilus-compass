#!/usr/bin/env python3
"""P2 v1 · verdict-judge 基线训练(bge-m3 冻结 + 三态头)。

预注册:docs/metering/P2_JUDGE_TRAINING_PREREG_20260930.md
  J1 test 二值 acc ≥85% · J2 ECE ≤0.10 · J3 U 态探索性
  J4 训练禁读 test(仅最终评估一次) · J5 split sha 校验 · J6 读数原样落盘

用法:python tools/train_judge_baseline.py
产出:runtime/judge_baseline/{features.npy,head.pt,eval_report.json,run_log.txt}
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "runtime" / "verdict_corpus"
OUT = ROOT / "runtime" / "judge_baseline"
OUT.mkdir(parents=True, exist_ok=True)

SHA_EXPECTED = {  # J5 冻结值(P2_JUDGE_TRAINING_PREREG)
    "split_train.jsonl": "35683198dd3c4992",
    "split_dev.jsonl": "942e4daeaedca2fb",
    "split_test.jsonl": "4bcaf1c9b551f336",
}
LABEL2ID = {"pass": 0, "fail": 1, "insufficient_evidence": 2}
SEED = 20260930
BATCH = 16


def sample_text(s: dict) -> str:
    """判分输入表示 v2:只含工件本体(question/response/官方真值)。

    v1 缺陷(首跑 64.9% FAIL 诊断):输入含 judge_output=被检判分器自报的
    作弊通道——判分器本意是从工件独立判对错,不是读另一个判分器的答案;
    且 bge 语义空间对该信号稀释(连抄都没学会,dev@ep0 即 best)。
    v2 剔除 judge_output,字段结构化标注。
    """
    a = s.get("artifact", {})
    parts = [f"criteria: {s.get('criteria_ref', '')[:120]}"]
    for k in ("question", "response", "model_answer", "official_truth",
              "answer_gold", "reason", "rationale"):
        if a.get(k) is not None:
            parts.append(f"{k}: {str(a[k])[:400]}")
    return "\n".join(parts)[:1500]


def load_split(name):
    rows = [json.loads(l) for l in
            (CORPUS / name).read_text(encoding="utf-8").splitlines() if l.strip()]
    return [(sample_text(r), LABEL2ID[r["truth_label"]], r["id"], r["truth_label"])
            for r in rows]


def verify_sha():  # J5
    for name, want in SHA_EXPECTED.items():
        got = hashlib.sha256((CORPUS / name).read_bytes()).hexdigest()[:16]
        assert got == want, f"J5 FAIL: {name} sha {got} ≠ 冻结 {want}"
    print("[J5] split sha 校验 PASS(三折与预注册冻结一致)")


def main():
    verify_sha()
    random.seed(SEED)
    import numpy as np
    import torch
    import torch.nn as nn
    torch.manual_seed(SEED)

    # ── 特征:bge-m3 冻结 encode ──
    from sentence_transformers import SentenceTransformer
    model_path = (Path.home() / ".cache/modelscope/hub/models/BAAI/bge-m3")
    model_path = str(model_path) if model_path.exists() else "BAAI/bge-m3"
    enc = SentenceTransformer(model_path, device="cpu")
    enc.max_seq_length = 512
    t0 = time.time()
    feats, labels, ids, labs = {}, {}, {}, {}
    for split in ("train", "dev", "test"):
        data = load_split(f"split_{split}.jsonl")  # J4:test 只在最终评估用
        texts = [d[0] for d in data]
        X = enc.encode(texts, batch_size=BATCH, show_progress_bar=False,
                       normalize_embeddings=False)
        feats[split] = torch.tensor(np.asarray(X), dtype=torch.float32)
        labels[split] = torch.tensor([d[1] for d in data], dtype=torch.long)
        ids[split] = [d[2] for d in data]
        labs[split] = [d[3] for d in data]
        print(f"[feat] {split}: {len(texts)} 条 ({time.time()-t0:.0f}s)")

    # ── 三态头(1024→256→3)· class weight 补 U 稀缺 ──
    head = nn.Sequential(nn.Linear(1024, 256), nn.ReLU(),
                         nn.Dropout(0.1), nn.Linear(256, 3))
    cnt = torch.bincount(labels["train"], minlength=3).float()
    w = (cnt.sum() / (3 * cnt.clamp(min=1))).clamp(max=20)
    print(f"[head] train 分布={cnt.tolist()} class_weight={w.tolist()}")
    opt = torch.optim.AdamW(head.parameters(), lr=1e-3, weight_decay=1e-4)
    lossf = nn.CrossEntropyLoss(weight=w)

    Xtr, ytr = feats["train"], labels["train"]
    best_dev, best_state, log = -1.0, None, []
    for ep in range(60):
        head.train()
        perm = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), 64):
            idx = perm[i:i + 64]
            opt.zero_grad()
            loss = lossf(head(Xtr[idx]), ytr[idx])
            loss.backward()
            opt.step()
        head.eval()
        with torch.no_grad():
            dv = (head(feats["dev"]).argmax(1) == labels["dev"]).float().mean().item()
        log.append(f"epoch {ep}: dev_acc={dv:.4f}")
        if dv > best_dev:
            best_dev, best_state, best_ep = dv, {k: v.clone() for k, v in head.state_dict().items()}, ep
        if ep - best_ep >= 8:
            break
    head.load_state_dict(best_state)
    print(f"[train] best dev_acc={best_dev:.4f} @epoch {best_ep}")

    # ── test 最终一次(J1/J2/J3)──
    head.eval()
    with torch.no_grad():
        logits = head(feats["test"])
        prob = torch.softmax(logits, dim=1)
        pred = prob.argmax(1)
    binary_mask = labels["test"] != 2  # 二值口径:U 排除
    j1 = ((pred == labels["test"])[binary_mask]).float().mean().item()
    # ECE 10 桶(置信度=max prob)
    conf, pmax = prob.max(1)
    ece, bins = 0.0, 10
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        m = (conf >= lo) & (conf < hi + (1e-9 if b == bins - 1 else 0))
        if m.sum() > 0:
            acc_b = (pred[m] == labels["test"][m]).float().mean().item()
            ece += m.float().sum().item() / len(conf) * abs(acc_b - conf[m].mean().item())
    u_mask = labels["test"] == 2
    u_hit = ((pred == 2) & u_mask).sum().item() if u_mask.sum() else None
    u_pred = (pred == 2).sum().item()
    report = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "seed": SEED, "best_dev_acc": round(best_dev, 4),
        "J1_test_binary_acc": round(j1, 4),
        "J1_pass": j1 >= 0.85,
        "J2_test_ece_10bin": round(ece, 4), "J2_pass": ece <= 0.10,
        "J3_U": {"test_U_true": int(u_mask.sum()), "test_U_pred": int(u_pred),
                 "test_U_hit": u_hit},
        "per_class": {c: {"n": int((labels['test'] == i).sum()),
                          "pred_n": int((pred == i).sum())}
                      for c, i in LABEL2ID.items()},
        "epochs": best_ep + 1,
    }
    (OUT / "eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "head.pt").write_bytes(b"")
    torch.save(head.state_dict(), OUT / "head.pt")
    (OUT / "run_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
