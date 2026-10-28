# -*- coding: utf-8 -*-
"""ocr_norm.table · 字符清洗表(RPT-77 复盘: 清洗完整性)。

修复: 清洗后强制白名单过滤(ocr_policy §3)——translate 未映射字符会
原样静默穿透,清洗表不可枚举全部脏字符,白名单过滤是唯一完备封口。
"""
TABLE = str.maketrans({"§": None, "\x00": None, "\x1a": None, "µ": None})

_WHITELIST = set("0123456789.+- ")


def apply_table(s: str) -> str:
    """按清洗表批清洗+白名单封口(数据域字符集)。"""
    cleaned = s.translate(TABLE)
    return "".join(ch for ch in cleaned if ch in _WHITELIST)
