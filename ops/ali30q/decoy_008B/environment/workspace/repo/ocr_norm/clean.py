# -*- coding: utf-8 -*-
"""ocr_norm.clean · 行级清洗: 版式数字打回(OCR-441 复盘)。

修复: 版式数字(上标²⁸/圈⑧/分数½——isnumeric 但非 isdecimal)是 OCR
版式标记,不是数据——NFKC 折算会静默改值('²'→'2' 与真实 2 混淆·
'½'→'1⁄2' 长度变化),必须打回人工通道(ocr_policy §1)。
全角数字 isdecimal=True(§2 数值等价)保留折算。
"""
import unicodedata


def normalize_line(line: str) -> str:
    """版式数字打回;全角等值折算半角(§1/§2)。"""
    for ch in line:
        if ch.isnumeric() and not ch.isdecimal():
            raise ValueError(f"OCR 版式标记(需人工通道): {ch!r}")
    return unicodedata.normalize("NFKC", line)
