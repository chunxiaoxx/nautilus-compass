"""Hindsight memory adapter · LongMemEval-S 独立评测用(预注册档 V1 + V1.1 附录)。

状态:RUN-FREEZE 2026-11-07(官方 hindsight-client 实测端点校正;冻结后禁改——预注册 §三.1)。
集成纪律:**不修改 tests/eval_longmemeval_accuracy.py 冻结面**;hindsight 臂跑法在
tests/eval_hindsight_arm.py,本模块只提供 retain/recall 封装与 recall→context 装配。

设计(2026-10-31 侦察 + 2026-11-07 run-freeze 实测):
- hindsight 自托管 = Docker(ghcr.io/vectorize-io/hindsight · API 8888)
- 官方 python 客户端 hindsight-client(PyPI · MIT),retain=batch items / recall=query
- bank 协议:每题一个 bank(= LongMemEval 每题独立 haystack 的自然映射),
  bank_id = "lme2-" + sha1(sorted haystack_session_ids)[:12]
- 公平性:retain 内容 = eval 同款 session_to_text(max_chars=600),不做我方偏好预处理;
  时间信号走其原生 timestamp 参数(官方接口,非我方调优)
- document_id = session_id(recall 结果可回溯命中会话 → truth_in_top 次级指标)

错误纪律(预注册 §一):recall/retain 基础设施失败 → HindsightError 显式抛出(fail loud,
eval 必须中止留证);"recall 返回空"是数据不是错误(照报 0 分)。
"""
from __future__ import annotations

import hashlib
import os

# === RUN-FREEZE(2026-11-07 实测)·冻结后禁改 ===
DEFAULT_BASE_URL = os.environ.get("HINDSIGHT_BASE_URL", "http://127.0.0.1:8888")
CLIENT_TIMEOUT = float(os.environ.get("HINDSIGHT_CLIENT_TIMEOUT", "600"))


class HindsightError(RuntimeError):
    """基础设施级失败(连接/HTTP 非 2xx/响应不可解析)——fail loud,禁静默吞。"""


def bank_id_for(session_ids: list[str]) -> str:
    """同 haystack 同 bank(500 题实测全互异,此函数仍是确定性映射的单一事实源)。"""
    digest = hashlib.sha1("|".join(sorted(session_ids)).encode()).hexdigest()[:12]
    return f"lme2-{digest}"


class HindsightMemory:
    """一次评测 run 的 hindsight bank 封装(官方 hindsight-client 包裹)。"""

    def __init__(self, bank_id: str, base_url: str | None = None, client=None):
        self.bank_id = bank_id
        if client is None:
            from hindsight_client import Hindsight  # 官方客户端(PyPI hindsight-client)
            client = Hindsight(base_url=base_url or DEFAULT_BASE_URL,
                               timeout=CLIENT_TIMEOUT)
        self._client = client
        self.retained = 0

    # --- write side ---
    def retain_corpus(self, sessions: list, session_ids: list[str],
                      dates: list | None = None,
                      session_to_text=None, max_chars: int = 600) -> int:
        """LongMemEval haystack 逐会话 retain·单 batch 提交(内容与 eval 管线同源)。

        session_to_text 由调用方注入(eval.session_to_text),避免本模块反向依赖冻结脚本。
        timestamp 传 haystack 原始日期(其原生时间接口);document_id=session_id。
        """
        if session_to_text is None:
            raise HindsightError("retain_corpus 需注入 session_to_text(同源公平性纪律)")
        items = []
        for i, sess in enumerate(sessions):
            date = dates[i] if dates and i < len(dates) else None
            text = session_to_text(sess, max_chars=max_chars, date=None)
            item = {"content": text, "document_id": session_ids[i]}
            if date:
                item["timestamp"] = date
            items.append(item)
        try:
            resp = self._client.retain_batch(bank_id=self.bank_id, items=items)
        except Exception as e:  # noqa: BLE001 — 统一转显式错误(fail loud 纪律)
            raise HindsightError(f"retain_batch bank={self.bank_id} failed: {e}") from e
        self.retained += len(items)
        return len(items)

    # --- read side ---
    def recall_memory(self, query: str) -> list[dict]:
        """官方默认参数 recall · 返回 [{text, type, document_id, occurred_start, scores}]。

        空列表=合法数据(照报 0 分),不抛错。
        """
        try:
            resp = self._client.recall(bank_id=self.bank_id, query=query)
        except Exception as e:  # noqa: BLE001
            raise HindsightError(f"recall bank={self.bank_id} failed: {e}") from e
        out = []
        for r in (resp.results or []):
            text = getattr(r, "text", None) or ""
            if not text:
                raise HindsightError(f"recall 条目缺 text: {str(r)[:200]}")
            out.append({
                "text": text,
                "type": getattr(r, "type", None),
                "document_id": getattr(r, "document_id", None),
                "occurred_start": getattr(r, "occurred_start", None),
                "scores": str(getattr(r, "scores", None)),
            })
        return out


def build_recall_context(results: list[dict]) -> str:
    """recall 结果 → subject prompt 的 context 块(等价于 compass 臂的 build_context 位)。

    每个 memory 一块:序号 + 日期(其 occurred_start 原生返回)+ 原文。
    空结果返回显式占位(不抛错——空是数据)。
    """
    if not results:
        return "(no memories recalled)"
    blocks = []
    for i, r in enumerate(results, 1):
        d = (r.get("occurred_start") or "")[:10]
        head = f"--- Memory {i}{f' (date {d})' if d else ''} ---"
        blocks.append(f"{head}\n{r['text']}")
    return "\n\n".join(blocks)
