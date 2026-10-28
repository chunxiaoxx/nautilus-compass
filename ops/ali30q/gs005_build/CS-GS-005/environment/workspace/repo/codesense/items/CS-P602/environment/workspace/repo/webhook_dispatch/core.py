"""webhook_dispatch.core — webhook 分发(骨架:由实现者填充)。"""
from __future__ import annotations


def dispatch(cfg: dict, event: dict, http_post=None, delivered=None) -> dict:
    """分发事件到 webhook(§1-§4)。骨架待实现。

    http_post(url, headers, body) -> int(status_code):可注入的 HTTP 客户端。
    delivered: 已成功投递的 event_id 集合(set)。
    """
    raise NotImplementedError("WH-2026-1025-P602: implement me")
