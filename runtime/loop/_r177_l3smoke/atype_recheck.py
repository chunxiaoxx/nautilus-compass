# A 型 11 条截断修复复验(R168 建议一验收)——champion 1.7B 现役判读管线,v1 语料全文
# 判据(预注册 _r168_bothwrong_audit.md 建议一):≥7/11 转对;不回升=截断非主因,照报负结果
import json
import sys

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, "/root/vdd2/judge14b_upgrade")
from train_judge14b_upgrade import LABELS, PROMPT_TMPL, evaluate, sample_text  # noqa: E402

BASE = "/root/vdd2/models/Qwen3-1.7B"
CHAMP = "/root/vdd2/judge14b_upgrade/champion_17b_lora"

rows = [json.loads(l) for l in open("/root/vdd2/judge14b_upgrade/atype11_v1.jsonl", encoding="utf-8")]
pairs = [(PROMPT_TMPL.format(content=sample_text(r)), LABELS.index(r["truth_label"]), r["id"])
         for r in rows]

tok = AutoTokenizer.from_pretrained(BASE)
m = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map={"": 0})
m = PeftModel.from_pretrained(m, CHAMP)
label_ids = {lab: tok.encode(lab, add_special_tokens=False)[0] for lab in LABELS}
rws, _ = evaluate(m, tok, pairs, label_ids)
ok = sum(r["ok"] for r in rws)
res = {"n": len(rws), "ok": ok, "rate": round(ok / len(rws), 4),
       "gate": ">=7/11 (R168 建议一)", "pass": ok >= 7, "rows": rws}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open("/root/vdd2/judge14b_upgrade/atype_recheck_result.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
