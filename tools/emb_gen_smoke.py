#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tokenizers 直编绕 AutoTokenizer(5.16 兼容坑)· 单条生成烟测。"""
import torch
from tokenizers import Tokenizer
from transformers import AutoModelForCausalLM

M = "/root/vdd4/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master"
tok = Tokenizer.from_file(M + "/tokenizer.json")
print("tok ok, vocab", tok.get_vocab_size())
model = AutoModelForCausalLM.from_pretrained(M, torch_dtype=torch.float16).to("cuda").eval()
print("model loaded")

im_start = tok.token_to_id("<|im_start|>")
im_end = tok.token_to_id("<|im_end|>")
sys_msg = "你是评测集构建器。根据过去的工作记忆记录,写出 agent 再次遇到相同情况时会输入的一句话情境查询(中文为主≤60字,保留英文错误码)。只输出查询。"
usr = "记忆记录:\nGitHub 三通知已分类无新回应;值守 quiet(ts 08:01,B 材料仍未出);判读管线 rehearsal 通过。"
prompt = f"<|im_start|>system\n{sys_msg}<|im_end|>\n<|im_start|>user\n{usr}<|im_end|>\n<|im_start|>assistant\n"
ids = tok.encode(prompt) + [im_start]
enc = torch.tensor([ids]).to("cuda")
with torch.no_grad():
    gen = model.generate(enc, max_new_tokens=80, do_sample=True, temperature=0.7, top_p=0.9)
resp = tok.decode(gen[0][len(ids):].tolist(), skip_special_tokens=True)
print("RESP:", resp.split("</think>")[-1].strip()[:120])
