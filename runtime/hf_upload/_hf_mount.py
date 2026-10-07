#!/usr/bin/env python3
"""HF 挂载:nautilus-compass org 下两件——判分器模型卡+caliber-bench 样例包。"""
import os
from pathlib import Path

from huggingface_hub import HfApi

token = None
for line in Path.home().joinpath('.claude/.cache/compass_hf_org_token.env').read_text().splitlines():
    if line.startswith('HF_TOKEN_ORG='):
        token = line.split('=', 1)[1].strip()
api = HfApi(token=token)
ORG = 'nautilus-compass'

# ① 判分器模型卡 repo(model)
repo_id = f'{ORG}/nacre-judge-v1'
api.create_repo(repo_id, repo_type='model', exist_ok=True)
card = """---
license: apache-2.0
base_model: Qwen/Qwen3-1.7B
tags: [judge, verification, NACRE, lora]
---
# NACRE Judge Instance v1 (nacre-judge-v1)

Nautilus 独立判读侧现役判分器(LoRA on Qwen3-1.7B)。

- 三态判读 pass / fail / insufficient_evidence,J1 binary acc **88.51%**(生产评测,ECE 0.072)
- adapter sha16: dbcbab6fd1ff5821 · 判据:预注册(P2_JUDGE_TRAINING_PREREG)
- 部署纪律(PRECOR B/C 实测 291 题,2026-10-07):**只允许 bf16/fp16**——fp16 对 bf16 判定一致率 1.0000,int8 0.9828 FAIL,int4 0.9416 FAIL(禁用)
- 判定表:docs/metering/PRECOR_BC_VERDICT_20261007.md(nautilus-compass 主仓)
- 归属:NACRE 机制·判读实例 v1(机制名+实例版本号,组织对齐账 2026-10-06)
"""
p = Path('runtime/hf_upload/README_judge.md')
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(card, encoding='utf-8')
api.upload_file(path_or_fileobj=str(p), path_in_repo='README.md', repo_id=repo_id, repo_type='model')
import tempfile, shutil
tmp = Path(tempfile.mkdtemp())
for f in Path('runtime/judge_lora_p2v2/best_lora').glob('*'):
    if f.name != 'README.md':   # 自带 README 含本地路径 metadata,HF 校验不过
        shutil.copy(f, tmp / f.name)
api.upload_folder(folder_path=str(tmp), repo_id=repo_id, repo_type='model')
print('model repo done:', repo_id)

# ② caliber-bench 样例包 repo(dataset)
repo2 = f'{ORG}/caliber-bench-v0'
api.create_repo(repo2, repo_type='dataset', exist_ok=True)
api.upload_folder(folder_path='docs/benchmarks/caliber_bench_v0', repo_id=repo2, repo_type='dataset')
print('dataset repo done:', repo2)
