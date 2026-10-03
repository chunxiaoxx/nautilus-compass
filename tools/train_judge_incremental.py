#!/usr/bin/env python3
"""P3 S3 · 增量训练(冠军热启动+delta:replay 1:1)+双臂预测产出(喂 S4 gate)。

设计档 §三/§四:冠军 adapter 热启动(同组 LoRA 继续训,防灾难性遗忘靠 replay);
delta:replay=1:1,replay 从冻结 train1162 分层抽样,种子=delta sha16 前 8 位 hex→int;
超参承 P2v2 冻结(r16/α32/lr1e-4/wd1e-4/早停 ep5/verbalizer 三态);GPU 守门(无 CUDA
退出码 42 不静默 CPU);模型走 modelscope 通道(HF 大文件断流定谳)。

输入:--ticket runtime/judge_lora_p3/ticket_NNNN.json(pending_deltas 文件清单)
输出:out/ticket_NNNN_challenger/(adapter)+evals/ticket_NNNN_{champion,challenger}_preds.jsonl
  预测行={id,split,pred,conf}——p3_gate.py 直接消费。
本文件自包含(单文件可部署 GPU 机,与 judge 工具同模式);GPU 实测留下一轮。
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "runtime" / "verdict_corpus"
P3 = ROOT / "runtime" / "judge_lora_p3"
LABELS = ["pass", "fail", "insufficient_evidence"]
MODEL_ID = "Qwen/Qwen3-1.7B"  # GPU 机上换 modelscope 本地路径
PROMPT_TMPL = """You are a verification judge. Given the criteria, the submitted
artifact, and the official reference, decide whether the response is correct.

{content}

Verdict (one word: pass / fail / insufficient_evidence):"""


def sample_text(s: dict) -> str:  # 与 P2v2 逐字相同(防口径漂移)
    a = s.get("artifact", {})
    parts = [f"criteria: {s.get('criteria_ref', '')[:120]}"]
    for k in ("question", "response", "model_answer", "official_truth",
              "answer_gold", "reason", "rationale"):
        if a.get(k) is not None:
            parts.append(f"{k}: {str(a[k])[:400]}")
    return "\n".join(parts)[:1500]


def load_rows(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def stratified_replay(train_rows: list[dict], n: int, seed: int) -> list[dict]:
    by = defaultdict(list)
    for r in train_rows:
        by[r["truth_label"]].append(r)
    out = []
    for lab, rs in by.items():
        k = round(n * len(rs) / len(train_rows))
        out.extend(random.Random(seed + hash(lab) % 1000).sample(
            sorted(rs, key=lambda r: r["content_hash"]), k))
    return out[:n]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticket", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=P3 / "out")
    ap.add_argument("--model", default=MODEL_ID, help="GPU 机用 modelscope 本地路径")
    ap.add_argument("--champion-adapter", type=Path, default=None,
                    help="GPU 机上冠军 adapter 路径(默认读 champion.json 相对路径)")
    ap.add_argument("--epochs", type=int, default=5)
    a = ap.parse_args()
    try:
        import torch
        assert torch.cuda.is_available(), "CUDA 不可用——S3 只许 GPU 跑(守门)"
    except (ImportError, AssertionError) as e:
        print(f"[EXIT42] {e}")
        return 42
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    ticket = json.loads(a.ticket.read_text(encoding="utf-8"))
    tid = ticket["ticket_id"]
    champ = json.loads((P3 / "champion.json").read_text(encoding="utf-8"))
    delta_rows = []
    for d in ticket["pending_deltas"]:
        delta_rows.extend(load_rows(CORPUS / "delta" / d["file"]))
    seed = int(ticket["pending_deltas"][0]["sha16"][:8], 16)  # 设计档 §三 抽样种子
    replay = stratified_replay(load_rows(CORPUS / "split_train.jsonl"), len(delta_rows), seed)
    print(f"[data] delta={len(delta_rows)} replay={len(replay)} seed={seed}")

    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(
        a.model, torch_dtype="auto", device_map="cuda")
    champ_adapter = a.champion_adapter or ROOT / champ["adapter_path"]
    model = PeftModel.from_pretrained(model, champ_adapter,
                                      is_trainable=True)  # 热启动:冠军权重继续训
    label_ids = [tok.encode(l)[0] for l in LABELS]
    label_ids = [l[0] if isinstance(l, list) else l for l in label_ids]

    def encode(rows):
        out = []
        for r in rows:
            ids = tok(PROMPT_TMPL.format(content=sample_text(r)), return_tensors="pt")
            out.append((ids.input_ids[0], ids.attention_mask[0],
                        LABELS.index(r["truth_label"]), r["id"]))
        return out

    def predict(rows) -> list[dict]:
        model.eval()
        preds = []
        with torch.no_grad():
            for ids, att, _, rid in rows:
                logits = model(input_ids=ids[:-1].unsqueeze(0).cuda(),
                               attention_mask=att[:-1].unsqueeze(0).cuda()).logits[0, -1, :]
                probs = torch.softmax(logits[torch.tensor(label_ids).cuda()], dim=-1)
                p = int(probs.argmax())
                preds.append({"id": rid, "pred": LABELS[p], "conf": round(float(probs[p]), 4)})
        return preds

    # 训练前:冠军臂预测(REG-100+test149)——热启动基线读数
    reg = load_rows(CORPUS / "reg100.jsonl")
    test = load_rows(CORPUS / "split_test.jsonl")
    ev = encode(reg) + encode(test)
    champ_preds = predict(ev)
    (P3 / "evals").mkdir(exist_ok=True)
    (P3 / "evals" / f"{tid}_champion_preds.jsonl").write_text(
        "\n".join(json.dumps(p) for p in champ_preds), encoding="utf-8")

    # 训练(delta+replay 混合,承 P2v2 优化器;增量样本少,per-sample step)
    train_data = encode(delta_rows + replay)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=1e-4, weight_decay=1e-4)
    model.train()
    for ep in range(a.epochs):
        random.Random(seed + ep).shuffle(train_data)
        tot = 0.0
        for ids, att, lab, _ in train_data:
            ans = tok.encode(LABELS[lab])[0]
            ans = ans[0] if isinstance(ans, list) else ans
            inp = torch.cat([ids, torch.tensor([ans])]).unsqueeze(0).cuda()
            attx = torch.cat([att, torch.tensor([1])]).unsqueeze(0).cuda()
            logits = model(input_ids=inp[:, :-1], attention_mask=attx[:, :-1]).logits[0, -1, :]
            probs = torch.log_softmax(logits[torch.tensor(label_ids).cuda()], dim=-1)
            loss = -probs[lab]
            loss.backward()
            opt.step()
            opt.zero_grad()
            tot += float(loss)
        print(f"[ep {ep}] train_loss={tot / len(train_data):.4f}", flush=True)

    # 训练后:挑战者臂预测
    chall_preds = predict(ev)
    (P3 / "evals" / f"{tid}_challenger_preds.jsonl").write_text(
        "\n".join(json.dumps(p) for p in chall_preds), encoding="utf-8")
    out_dir = a.out / f"{tid}_challenger"
    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out_dir)
    meta = {"ticket": tid, "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "delta_n": len(delta_rows), "replay_n": len(replay), "seed": seed,
            "champion_adapter": champ["adapter_path"], "epochs": a.epochs}
    (out_dir / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    print(f"[next] python tools/p3_gate.py --champion {P3}/evals/{tid}_champion_preds.jsonl "
          f"--challenger {P3}/evals/{tid}_challenger_preds.jsonl --ticket {a.ticket} --record")
    return 0


if __name__ == "__main__":
    sys.exit(main())
