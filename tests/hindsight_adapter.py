"""Hindsight memory adapter · LongMemEval-S 独立评测用(预注册档 V1 · docs/metering/HINDSIGHT_EVAL_PREREG_V1_20261031.md)。

状态:SKELETON(候 vectorize-io/hindsight 答复 version/tag 后按其实测端点校正,冻结后禁改——预注册 §三.1)。
集成纪律:**不修改 tests/eval_longmemeval_accuracy.py 冻结面**;--pipeline=hindsight 集成补丁在
判据冻结 commit 里随批过审落位。本模块只提供与 top_sessions 契约兼容的伪会话视图。

设计(2026-10-31 侦察):
- hindsight 自托管 = Docker(ghcr.io/vectorize-io/hindsight · API 8888)+ LLM key(retain 提取用)
- API 面:retain(bank_id, content, context, timestamp) / recall(bank_id, query) / reflect(...)
- bank 隔离:每次评测 run 独立 bank(longmemeval-s-<run_tag>),run 后可整体丢弃
- 公平性:retain 内容 = eval 同款 session_to_text(max_chars=600),不做我方偏好预处理

错误纪律(预注册 §一):recall/retain 基础设施失败 → HindsightError 显式抛出(fail loud,
eval 必须中止留证);"recall 返回空"是数据不是错误(照报 0 分)。
"""
from __future__ import annotations

import json
import os
import urllib.request

# === 冻结点(RUN-FREEZE)·候对方答复后按实测校正,冻结后禁改 ===
DEFAULT_BASE_URL = os.environ.get("HINDSIGHT_BASE_URL", "http://127.0.0.1:8888")
RETAIN_PATH = "/api/v1/{bank}/retain"      # TODO(run-freeze): 以实测 swagger 为准
RECALL_PATH = "/api/v1/{bank}/recall"      # TODO(run-freeze): 同上
RECALL_TOP_K = 5                            # = eval TOP_K_CONTEXT 同口径


class HindsightError(RuntimeError):
    """基础设施级失败(连接/HTTP 非 2xx/响应不可解析)——fail loud,禁静默吞。"""


def _default_transport(method: str, url: str, payload: dict | None) -> dict:
    """stdlib 传输(仓纪律:eval 面依赖保持零第三方);测试经 inject transport 替换。"""
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:  # noqa: BLE001 — 统一转显式错误(fail loud 纪律)
        raise HindsightError(f"{method} {url} failed: {e}") from e


class HindsightMemory:
    """一次评测 run 的 hindsight bank 封装(伪会话视图兼容 top_sessions 契约)。"""

    def __init__(self, bank_id: str, base_url: str | None = None,
                 transport=None):
        self.bank_id = bank_id
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._transport = transport or _default_transport
        self.retained = 0

    # --- write side ---
    def retain_text(self, content: str, context: str | None = None) -> dict:
        url = f"{self.base_url}{RETAIN_PATH.format(bank=self.bank_id)}"
        payload: dict = {"content": content}
        if context:
            payload["context"] = context
        try:
            resp = self._transport("POST", url, payload)
        except HindsightError:
            raise
        except Exception as e:  # noqa: BLE001 — 任何 transport 异常统一包显式错误
            raise HindsightError(f"retain {url} failed: {e}") from e
        if not isinstance(resp, dict):
            raise HindsightError(f"retain 非对象响应: {type(resp).__name__}")
        self.retained += 1
        return resp

    def retain_corpus(self, sessions: list, dates: list | None = None,
                      session_to_text=None, max_chars: int = 600) -> int:
        """LongMemEval haystack 逐会话 retain(内容与 eval 管线同源=公平性 §三.1)。

        session_to_text 由调用方注入(eval.session_to_text),避免本模块反向依赖冻结脚本。
        """
        if session_to_text is None:
            raise HindsightError("retain_corpus 需注入 session_to_text(同源公平性纪律)")
        n = 0
        for i, sess in enumerate(sessions):
            date = dates[i] if dates and i < len(dates) else None
            text = session_to_text(sess, max_chars=max_chars, date=date)
            # 时间锚语义经 context 透传给 hindsight(haystack_dates 与 eval 同款信号)
            self.retain_text(text, context=str(date) if date else None)
            n += 1
        return n

    # --- read side ---
    def recall_memory(self, query: str, top_k: int = RECALL_TOP_K) -> list[dict]:
        """返回原始 recall 结果列表 [{text, score, ...}]——空列表=合法数据(照报 0 分)。"""
        url = f"{self.base_url}{RECALL_PATH.format(bank=self.bank_id)}"
        try:
            resp = self._transport("POST", url, {"query": query, "top_k": top_k})
        except HindsightError:
            raise
        except Exception as e:  # noqa: BLE001 — 任何 transport 异常统一包显式错误
            raise HindsightError(f"recall {url} failed: {e}") from e
        items = resp.get("results") if isinstance(resp, dict) else None
        if items is None:
            raise HindsightError(f"recall 响应缺 results 键: {str(resp)[:200]}")
        out = []
        for it in items[:top_k]:
            text = it.get("text") or it.get("content") or ""
            if not text:
                raise HindsightError(f"recall 条目缺 text/content: {str(it)[:200]}")
            out.append({"text": text, "score": it.get("score")})
        return out

    @staticmethod
    def to_pseudo_sessions(results: list[dict]) -> list[list[dict]]:
        """recall 结果 → top_sessions 兼容伪会话。

        每个伪会话=单 turn 列表(session_to_text 渲染为 '[memory] <text>'),
        外层形状与 eval 的 sessions(list-of-turn-lists)同构,build_context 直接消费。
        """
        return [[{"role": "memory", "content": r["text"]}] for r in results]
