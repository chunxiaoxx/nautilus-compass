"""LME-V2 刀3 附带修复 · judge 瞬时空响应重试 patch · 2026-08-30

根因(d12 web 全量实测):第 17 题 judge(doubao)偶发返回空 content,
_parse_llm_binary_judgement 抛 ValueError 后整个 harness 进程崩,
web 240 题只出 16 行(ent 同参数 211 题未崩 = 瞬时失败非系统性)。

修复三层:
1. _call_chat_completion 内部 retry 3 次(异常或空内容都重试,指数退避)
2. 两个 judge 调用点(abstention/gotchas checker)包 try-except:
   3 次全败 → 该题记 0 分 + stderr 警告,run 继续(局部失败不放大为全局失败)
3. ast.parse 语法门 + 幂等(重复执行前检测 retry 标记)

用法(GPU 机): python3 lmev2_evaluator_retry_patch.py
原文件备份 qa_eval_metrics.py.orig-d3(仅首次)。
"""
import ast
import re
import shutil
from pathlib import Path

TARGET = Path("/root/LongMemEval-V2/evaluation/qa_eval_metrics.py")
BAK = TARGET.with_suffix(".py.orig-d3")
MARK = "judge-retry"

NEW_CALL = '''def _call_chat_completion(
    *,
    client: Any,
    model: str,
    messages: list[dict[str, str]],
    max_completion_tokens: int,
    reasoning_effort: str | None,
    temperature: float | None,
    top_p: float | None,
    timeout_seconds: float,
) -> str:
    request: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": max_completion_tokens,
        "timeout": timeout_seconds,
    }
    if reasoning_effort is not None:
        request["reasoning_effort"] = reasoning_effort
    if temperature is not None:
        request["temperature"] = temperature
    if top_p is not None:
        request["top_p"] = top_p

    import sys as _sys
    import time as _time

    last_exc: Exception | None = None
    for _attempt in range(3):
        try:
            response = client.chat.completions.create(**request)
            message_content = response.choices[0].message.content
            text = ""
            if isinstance(message_content, str):
                text = message_content.strip()
            elif isinstance(message_content, list):
                parts = []
                for item in message_content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        parts.append(item["text"])
                text = chr(10).join(parts).strip()
            if text:
                return text
            last_exc = ValueError("Evaluator model returned empty response content.")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
        print(
            f"[judge-retry] evaluator attempt {_attempt + 1}/3 failed: {last_exc}",
            file=_sys.stderr,
        )
        _time.sleep(5 * (_attempt + 1))
    raise last_exc if last_exc else ValueError("Evaluator model failed after retries.")
'''

NEW_CALLSITE = '''    import sys as _sys
    import time as _time

    judge_text = ""
    for _attempt in range(3):
        try:
            judge_text = _call_chat_completion(
{sig}
            )
            label, _reason = _parse_llm_binary_judgement(judge_text)
            return label == 1
        except Exception as exc:  # noqa: BLE001
            print(
                f"[judge-retry] judge attempt {_attempt + 1}/3 failed: {exc}",
                file=_sys.stderr,
            )
            _time.sleep(5 * (_attempt + 1))
    print(f"[judge-retry] giving up; scoring 0 for this question", file=_sys.stderr)
    return False'''


def main() -> None:
    src = TARGET.read_text(encoding="utf-8")
    if MARK in src:
        print("ALREADY_PATCHED")
        return
    if not BAK.exists():
        shutil.copy2(TARGET, BAK)
        print(f"BACKUP {BAK}")

    # 1) 整函数替换 _call_chat_completion
    new_src, n1 = re.subn(
        r'def _call_chat_completion\(.*?raise ValueError\("Evaluator model returned empty response content\."\)\n',
        NEW_CALL,
        src,
        count=1,
        flags=re.S,
    )
    assert n1 == 1, "call-completion function not matched"

    # 2) 两个 judge 调用点包 retry(参数签名原样保留)
    def _sites(text: str) -> tuple[str, int]:
        pat = re.compile(
            r"    judge_text = _call_chat_completion\(\n(.*?)\n    \)\n"
            r"    label, _reason = _parse_llm_binary_judgement\(judge_text\)\n"
            r"    return label == 1\n",
            flags=re.S,
        )

        def _repl(m: re.Match) -> str:
            return NEW_CALLSITE.replace("{sig}", m.group(1)) + "\n"

        return pat.subn(_repl, text)

    new_src, n2 = _sites(new_src)
    assert n2 == 2, f"expected 2 judge callsites, got {n2}"

    ast.parse(new_src)  # 语法门
    assert new_src.count("judge-retry") >= 3  # f-string 运行时插值,源码里只查占位符
    TARGET.write_text(new_src, encoding="utf-8")
    print(f"PATCH_OK bytes={len(new_src)} callsites={n2}")


if __name__ == "__main__":
    main()
