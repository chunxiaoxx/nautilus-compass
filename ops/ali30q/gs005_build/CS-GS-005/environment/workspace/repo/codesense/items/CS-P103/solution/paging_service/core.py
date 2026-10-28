"""paging_service.core — 分页切片(金标实现)。"""
from __future__ import annotations

import math


def list_orders(rows: list[dict], page: int, size: int) -> dict:
    """分页切片(§1-§4,以规范为准,§5 备注不采纳)。"""
    if page < 1:
        return {"error": "bad_page"}
    if size <= 0:
        return {"error": "bad_size"}
    capped = min(size, 100)  # §2 上限钳制
    start = (page - 1) * capped
    items = rows[start:start + capped]
    return {
        "items": items,
        "page": page,
        "size": capped,
        "total_rows": len(rows),
        "total_pages": math.ceil(len(rows) / capped),
    }
