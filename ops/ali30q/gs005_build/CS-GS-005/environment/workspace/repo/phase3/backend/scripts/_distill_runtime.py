"""distill_eval 的 GPU/env 实现层(2026-06-22·env 就位后建·非 facade)。

distill_eval.py import 的 4 函数的真实现:
  load_models / generate_solution / doubao_solution = 推理 + 读分(已用 1.5B 实测验证)。
  score_solution = subprocess 调 ale_eval(跨 venv·全链锁 judge_version=202301)。

✅ score_solution UNGATED(2026-06-22):V5 在此盒(43.166.8.20)装好 python-202301 judge
   镜像(chmod 1777 /workdir 套 compass 经验)。真探针 4/4 PASS:ahc008/009 reward 精确
   复现 V5 strong_score → 真判题集成验通(非 mock)。judge_version 全链锁 202301(燃料同版)。
盒拓扑:训练+推理+judge 镜像 co-located 在 43.166.8.20(T4)。

dtype:_compute_dtype 用 is_bf16_supported()(T4 Turing emulated bf16)→ 与 distill_qlora
   一致(绕 fp16+bitsandbytes GradScaler "not implemented for BFloat16" 坑)。
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys

# instruction 单一来源(训练/eval 同源·防 train/eval skew)。_distill_runtime 经 distill_eval
# import(BACKEND 已在 sys.path);直接 import 时下面 guard 补 path。
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)
from services.distill_fuel import instruction_for   # noqa: E402

# ale_eval(compass scorer)在独立 venv·subprocess 跨 venv 调(职责分离·不污染训练 venv)
ALE_VENV = os.environ.get("ALE_VENV_PY", "/mnt/datadisk0/ale-bench/.venv/bin/python")
ALE_DIR = os.environ.get("ALE_DIR", "/mnt/datadisk0/ale-bench")
JUDGE_VERSION = os.environ.get("ALE_JUDGE_VERSION", "202301")   # 全链锁同版(燃料同版)
ALE_LANGUAGE = os.environ.get("ALE_LANGUAGE", "python")          # qwen 写 python 解

# 🔧 SWE 二元打分(2026-06-26·同质料 held-out eval 使能):distilled 出的 diff → 官方
# swebench docker harness 判 resolved。与 ALE 同架构=subprocess 跨 venv 调(swe-rsi 的
# services.swe_docker 与 nautilus services 同名包·subprocess 隔离避命名冲突·复用
# verify_pathA_one 同款 run_candidate_docker)。
SWE_VENV = os.environ.get("SWE_VENV_PY", "/mnt/datadisk0/swe-rsi/venv/bin/python")
SWE_BACKEND = os.environ.get("SWE_BACKEND", "/mnt/datadisk0/swe-rsi/backend")
SWE_HARNESS = os.environ.get("SWE_HARNESS_WORKDIR", "/mnt/datadisk0/swe-rsi/harness")
SWE_EVAL_TIMEOUT = int(os.environ.get("SWE_EVAL_TIMEOUT", "1800"))


def _compute_dtype():
    import torch
    # is_bf16_supported():T4(Turing emulated)+A100(原生)均 True→bf16(与训练 adapter dtype 一致)
    return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16


def load_models(base_model: str, adapter: str | None = None):
    """加载**单** base(4bit QLoRA)·可选挂 adapter。返回 (model, tok)。

    🔴 单模型省显存(2026-06-22 修 OOM):base/distilled 共享同一 base 权重·用
    `disable_adapter()` context 切换(adapter 旁路=base 视图·adapter on=distilled)。
    两独立模型会 OOM——尤其 7B 首证(2×7B 4bit ~8GB + compass 4.9GB 撞 16GB)·单模型
    +adapter 切换才可行。附带更可比(消除两次加载差异·base/distilled 唯一变量=adapter)。
    adapter=None → 纯 base(烟雾测试·generate use_adapter 参数无 adapter 时 no-op)。
    """
    import torch  # noqa
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    dt = _compute_dtype()
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=dt, bnb_4bit_use_double_quant=True)
    tok = AutoTokenizer.from_pretrained(base_model)
    tok.pad_token = tok.pad_token or tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_model, quantization_config=bnb, device_map="auto", dtype=dt)
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter)   # 单模型·adapter 可 disable 切换
    return model, tok


# 🔴 训练 prompt 模板(与 distill_qlora._PROMPT_TMPL 完全一致·2026-06-23 修 train/eval skew):
# 训练用 "### Instruction/Problem/Solution" + completion-only·eval 之前误用 Qwen chat
# template + 不同措辞 → 模型条件分布对不上 → 吐不出记住的解(train_loss~0.0003 却 eval=0
# 的根因·第 4 个 confound)。instruction 是燃料 builder(distill_fuel)的常量·held 记录暂
# 不带 instruction → 此处用同常量(后续硬化:把 instruction 串进 held_out_eval_record)。
_GEN_INSTRUCTION = ("Solve the following algorithm engineering / optimization problem. "
                    "Produce a correct, high-scoring solution.")
_GEN_PROMPT_TMPL = "### Instruction:\n{instruction}\n\n### Problem:\n{input}\n\n### Solution:\n"


def generate_solution(model, tok, problem: str, kind: str = "ale",
                      max_new_tokens: int = 4096, use_adapter: bool = True) -> str:
    """模型对 problem 产解(greedy·确定性·held-out 公平对比)。

    🔴 prompt 必须与训练完全一致(### Instruction/Problem/Solution·非 chat template)·
    否则 train/eval skew → 吐不出记住的解(KILLED 假象根因·2026-06-23)。instruction 按
    kind 取(instruction_for·与 build_distill_sample 训练写端同源)——SWE 题用 SWE 措辞·
    否则用 ALE instruction 跑 SWE 题=另一种 skew。
    max_new_tokens=4096 容长解(ALE 解可 >2k token·之前 2048 截断 ahc001/008)。
    use_adapter=False 且模型有 adapter → `disable_adapter()` 旁路 adapter 跑 base 视图
    (单模型 base/distilled 对比·同 base 权重·唯一变量=adapter)。无 adapter 时 no-op。
    """
    import contextlib
    import torch
    text = _GEN_PROMPT_TMPL.format(instruction=instruction_for(kind), input=problem)
    ins = tok(text, return_tensors="pt").to(model.device)
    ctx = (model.disable_adapter() if (not use_adapter and hasattr(model, "disable_adapter"))
           else contextlib.nullcontext())
    with torch.no_grad(), ctx:
        out = model.generate(**ins, max_new_tokens=max_new_tokens, do_sample=False)
    return tok.decode(out[0][ins.input_ids.shape[1]:], skip_special_tokens=True)


def _extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else text.strip()


def _extract_diff(text: str) -> str:
    """模型输出 → unified diff。优先 ```diff/patch fence·否则从首个 diff 标记起取。

    无 fence 且无 diff 标记(纯 prose·模型没产 patch)→ 返回 ""(不是 diff·_score_swe
    据此跳过 docker·省一次无效 build)。
    """
    m = re.search(r"```(?:diff|patch)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    for marker in ("diff --git", "--- a/", "--- "):
        idx = text.find(marker)
        if idx != -1:
            return text[idx:].strip()
    return ""


def _score_swe(task: dict, solution: str) -> float:
    """SWE 二元打分:distilled 出的 diff → 官方 swebench docker → resolved(1.0/0.0)。

    subprocess 跨 venv 调 swe-rsi 的 run_candidate_docker(与 verify_pathA_one 同款·避
    services 同名包冲突)。docker/harness 缺或失败 → 保守 0(eval 端诚实·不假装解出)。
    """
    diff = _extract_diff(solution)
    if not diff:
        return 0.0
    tid = task["task_id"]
    payload = base64.b64encode(json.dumps({"tid": tid, "diff": diff}).encode()).decode()
    runner = (
        "import json,base64,sys\n"
        f'sys.path.insert(0,"{SWE_BACKEND}")\n'
        "from services.swe_docker import run_candidate_docker\n"
        f'd=json.loads(base64.b64decode("{payload}").decode())\n'
        f'rr=run_candidate_docker(d["tid"],d["diff"],run_id="evalheld",'
        f'workdir="{SWE_HARNESS}",timeout={SWE_EVAL_TIMEOUT})\n'
        'rep=rr.get("report",{}) if isinstance(rr,dict) else {}\n'
        'print("RESOLVED="+str(bool(rep.get("resolved"))))\n'
    )
    try:
        proc = subprocess.run([SWE_VENV, "-c", runner],
                              capture_output=True, text=True, timeout=SWE_EVAL_TIMEOUT + 120)
        for line in proc.stdout.splitlines():
            if line.startswith("RESOLVED="):
                return 1.0 if line.split("=", 1)[1].strip() == "True" else 0.0
    except Exception:
        pass
    return 0.0


def score_solution(task: dict, solution: str) -> float:
    """解 → 分数。kind=swe → docker resolved 二元(1/0);否则 ALE 绝对分。

    ALE:subprocess 调 ale_eval.eval_fn(全链锁 judge_version=202301)·镜像缺/失败→0。
    SWE:见 _score_swe(官方 swebench docker)。
    """
    if task.get("kind") == "swe":
        return _score_swe(task, solution)
    code = _extract_code(solution)
    if os.environ.get("ALE_MOCK_SCORE"):
        # dry-run hook(env-gated·生产不触发):judge 镜像未到时用合成分验证整条
        # ingest→train→eval→verdict 管线串通。非真 judge·按解内容变化让 delta 有信号。
        return float(len(code) % 997) + 1.0
    pid = task["task_id"]
    payload = base64.b64encode(json.dumps({"c": code, "p": pid}).encode()).decode()
    runner = (
        "import json,base64,ale_eval\n"
        f'd=json.loads(base64.b64decode("{payload}").decode())\n'
        f'r=ale_eval.eval_fn(d["c"],d["p"],language="{ALE_LANGUAGE}",'
        f'judge_version="{JUDGE_VERSION}",lite_version=False)\n'
        'print("REWARD="+str(r["reward"]))\n'
    )
    try:
        proc = subprocess.run([ALE_VENV, "-c", runner], cwd=ALE_DIR,
                              capture_output=True, text=True, timeout=600)
        for line in proc.stdout.splitlines():
            if line.startswith("REWARD="):
                return float(line.split("=", 1)[1])
    except Exception:
        pass
    return 0.0   # judge 镜像缺 / 失败 → 保守 0(eval 端诚实·不假装有分)


def doubao_solution(task: dict) -> float:
    """held-out 题已含 doubao_score(燃料 record)→ 直接读·不重打分(省一次 doubao 调用)。"""
    return float(task.get("doubao_score") or 0.0)
