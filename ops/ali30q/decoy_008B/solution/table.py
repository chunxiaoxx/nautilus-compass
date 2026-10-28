# -*- coding: utf-8 -*-
"""ocr_norm.table · 字符清洗表(金标: §1 打回贯穿批入口+§2 折算+§3 白名单)。

修复: 批清洗入口与行级清洗同守 §1——版式标记(isnumeric 但非 isdecimal)
不得借白名单过滤静默变形('1²3'→'13' 是静默丢位,不是清洗);全角数字
折算半角(§2);清洗后白名单封口(§3)。
"""
import unicodedata

TABLE = str.maketrans({"§": None, "\x00": None, "\x1a": None, "µ": None})

_WHITELIST = set("0123456789.+- ")


def apply_table(s: str) -> str:
    """批清洗: 版式标记打回(§1)+全角折算(§2)+白名单封口(§3)。"""
    cleaned = s.translate(TABLE)
    chars = []
    for ch in cleaned:
        if ch.isnumeric() and not ch.isdecimal():
            raise ValueError(f"OCR 版式标记(需人工通道): {ch!r}")
        if ch.isdecimal() and not ch.isascii():
            chars.append(unicodedata.normalize("NFKC", ch))
        else:
            chars.append(ch)
    return "".join(c for c in chars if c in _WHITELIST)
