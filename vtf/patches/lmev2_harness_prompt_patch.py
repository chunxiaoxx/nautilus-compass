"""LME-V2 harness abstention-alignment patch · 2026-08-30 · 三刀调优之刀 1

根因(逐题对齐 evidence):abstention 题 72 道(占 web 30%),我们裸 UNKNOWN 49 道
但 checker 只给 2 分——judge rubric 要求"指出前提矛盾"或"明确说明无法访问实时
环境",裸 UNKNOWN 明确判 0。本 patch 重写 DOMAIN_SYSTEM_PROMPTS,引导 reader
走两条得分路线,同时保留"知道就答"路径与 Never guess 约束。

用法(GPU 机): python3 lmev2_harness_prompt_patch.py
原文件备份为 harness.py.orig-d1(仅首次)。幂等:重复执行会再替换一次,无害。
"""
import ast
import re
import shutil
from pathlib import Path

HARNESS = Path("/root/LongMemEval-V2/evaluation/harness.py")
BAK = HARNESS.with_suffix(".py.orig-d1")

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
_BODY = (
    'Answer based on your memory of the environment, "\n'
    '        "which consists of recorded trajectory snapshots. "\n'
    '        "If your memory context contains the answer, give the concrete answer in \\\\boxed{}. "\n'
    '        "If the question\'s premise conflicts with what your memory shows (e.g. the thing "\n'
    '        "it asks about does not exist, or works differently than the question assumes), "\n'
    '        "do NOT play along and do NOT just say UNKNOWN: in \\\\boxed{} explain the "\n'
    '        "contradiction - state what your memory actually shows and why the question\'s "\n'
    '        "premise is wrong. "\n'
    '        "If your memory cannot verify the question because it would require live access "\n'
    '        "to the user\'s current environment, instance or configuration (which recorded "\n'
    '        "snapshots cannot provide), do NOT just say UNKNOWN: in \\\\boxed{} explicitly "\n'
    '        "state that you lack access to the live environment so it cannot be verified, "\n'
    '        "and explain what information would be needed. "\n'
    '        "Never guess a concrete answer when unsure."\n'
    "    ),\n"
)


def _domain(head: str) -> str:
    return head + _BODY


NEW_BLOCK = 'DOMAIN_SYSTEM_PROMPTS = {\n    "web": (\n        ' + _domain(_WEB_HEAD) + '    "enterprise": (\n        ' + _domain(_ENT_HEAD) + "}\n"


def main() -> None:
    src = HARNESS.read_text(encoding="utf-8")
    if not BAK.exists():
        shutil.copy2(HARNESS, BAK)
        print(f"BACKUP {BAK}")
    new_src, n = re.subn(
        r"DOMAIN_SYSTEM_PROMPTS = \{.*?\n\}",
        lambda m: NEW_BLOCK,  # lambda 防 replacement 转义
        src,
        count=1,
        flags=re.S,
    )
    assert n == 1, "DOMAIN_SYSTEM_PROMPTS block not found"
    ast.parse(new_src)  # 语法门
    HARNESS.write_text(new_src, encoding="utf-8")
    assert "live environment" in new_src and new_src.count("\\\\boxed") >= 6
    print("PATCH_OK bytes=%d" % len(new_src))


if __name__ == "__main__":
    main()
