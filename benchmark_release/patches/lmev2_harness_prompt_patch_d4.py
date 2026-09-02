"""LME-V2 harness abstention-gate patch · 2026-08-30 · 三刀调优之刀 4

根因(d12 逐题对齐,web dynamic 3 道掉分 1.0→0.0):
- 609acb91 / 96497069:快照里有直接证据(reader 却走"lack access to the live
  environment"拒答模板)= 刀1 路线 3 被过度泛化到 dynamic 环境状态题。
- 2ee130d2:答案 False 正确,但 boxed 内附带矛盾解释文字,mc_choice_match
  严格匹配失败 = 答案格式污染。

本 patch 在刀1 基础上加两处(最小 diff,只动 _BODY 段):
1. 拒答前置 gate:fallback 路线只允许在"复查记忆后确实无任何快照含所需
   状态"时使用;快照有证据必须作答。
2. boxed 纯答案约束:框内只放最终答案,解释一律放框外。

用法(GPU 机):python3 lmev2_harness_prompt_patch_d4.py
前置:刀1 已应用(harness.py 含 "live environment")。
原文件备份为 harness.py.orig-d4(仅首次)。幂等:重复执行再替换一次,无害。
⚠️ 部署纪律:d13 双域跑完前不得执行(d13 web 进程已载入内存不受文件改动影响,
但 ent 接续是新进程会重读 harness.py —— 提前执行会造成 d13 双域 prompt 不一致)。
"""
import ast
import re
import shutil
from pathlib import Path

HARNESS = Path("/root/LongMemEval-V2/evaluation/harness.py")
BAK = HARNESS.with_suffix(".py.orig-d4")

_WEB_HEAD = (
    '"You are an experienced colleague in a web browsing environment that has "\n'
    '        "a customized magento-based shopping website, a customized magento-based "\n'
    '        "shopping admin cms website, as well as a customized forum website based "\n'
    '        "on reddit/postmill. '
)
_ENT_HEAD = (
    '"You are an experienced colleague working in a customized ServiceNow "\n'
    '        "environment. '
)
# v2 相对刀1 _BODY 的 diff:
#   + BEFORE-GATE:复查记忆,快照有证据必须作答,fallback 仅限复查后确无证据
#   + FORMAT:boxed 内只放最终答案
#   路线3 前缀改为 "Only if you have checked ..."(gate 内嵌)
_BODY = (
    'Answer based on your memory of the environment, "\n'
    '        "which consists of recorded trajectory snapshots. "\n'
    '        "Before using any fallback below, check your memory context carefully: "\n'
    '        "if any recorded snapshot shows the state or fact the question asks about, "\n'
    '        "you MUST give the concrete answer from it - do NOT fall back when your "\n'
    '        "memory contains the evidence. "\n'
    '        "If your memory context contains the answer, give the concrete answer in \\\\boxed{}, "\n'
    '        "and put ONLY the final answer inside \\\\boxed{} - keep any explanation outside the box. "\n'
    '        "If the question\'s premise conflicts with what your memory shows (e.g. the thing "\n'
    '        "it asks about does not exist, or works differently than the question assumes), "\n'
    '        "do NOT play along and do NOT just say UNKNOWN: in \\\\boxed{} explain the "\n'
    '        "contradiction - state what your memory actually shows and why the question\'s "\n'
    '        "premise is wrong. "\n'
    '        "Only if you have checked and no recorded snapshot contains the needed state - "\n'
    '        "because verifying it would require live access to the user\'s current environment, "\n'
    '        "instance or configuration which recorded snapshots cannot provide - do NOT just "\n'
    '        "say UNKNOWN: in \\\\boxed{} explicitly state that you lack access to the live "\n'
    '        "environment so it cannot be verified, and explain what information would be needed. "\n'
    '        "Never guess a concrete answer when unsure."\n'
    "    ),\n"
)


def _domain(head: str) -> str:
    return head + _BODY


NEW_BLOCK = 'DOMAIN_SYSTEM_PROMPTS = {\n    "web": (\n        ' + _domain(_WEB_HEAD) + '    "enterprise": (\n        ' + _domain(_ENT_HEAD) + "}\n"


def main() -> None:
    src = HARNESS.read_text(encoding="utf-8")
    assert "live environment" in src, "刀1 未应用,先跑 lmev2_harness_prompt_patch.py"
    if not BAK.exists():
        shutil.copy2(HARNESS, BAK)
        print(f"BACKUP {BAK}")
    new_src, n = re.subn(
        r"DOMAIN_SYSTEM_PROMPTS = \{.*?\n\}",
        lambda m: NEW_BLOCK,
        src,
        count=1,
        flags=re.S,
    )
    assert n == 1, "DOMAIN_SYSTEM_PROMPTS block not found"
    ast.parse(new_src)  # 语法门
    HARNESS.write_text(new_src, encoding="utf-8")
    assert "MUST give the concrete answer from it" in new_src  # gate 已注入
    assert "keep any explanation outside the box" in new_src  # 格式约束已注入
    print("PATCH_OK bytes=%d" % len(new_src))


if __name__ == "__main__":
    main()
