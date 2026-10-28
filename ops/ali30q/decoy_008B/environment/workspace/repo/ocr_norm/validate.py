# -*- coding: utf-8 -*-
"""ocr_norm.validate · 行号列校验(数据质检入口)。"""


def parse_line_no(text: str) -> int:
    """把行号列文本解析为整数(非数字文本由调用方保证,不在本函数处理范围)。"""
    s = text.strip()
    if s.isdigit():
        return int(s)
    raise ValueError(f"not a digit string: {text!r}")


def is_clean_digit(s: str) -> bool:
    """单字符是否为合法数据数字。"""
    return len(s) == 1 and s.isdigit()
