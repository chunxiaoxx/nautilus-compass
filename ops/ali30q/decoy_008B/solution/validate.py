# -*- coding: utf-8 -*-
"""ocr_norm.validate · 行号列校验(金标: ASCII 数据数字判定,版式拒收)。

修复: isdigit 对上标类字符('²'.isdigit()==True)误判放行,违反 §1
版式标记非数据——判定收窄为 ASCII [0-9]。
"""


def parse_line_no(text: str) -> int:
    """把行号列文本解析为整数;非 ASCII 数字串(含版式标记)一律拒收(§1)。"""
    s = text.strip()
    if s.isascii() and s.isdecimal():
        return int(s)
    raise ValueError(f"not an ascii digit string: {text!r}")


def is_clean_digit(s: str) -> bool:
    """单字符是否为合法数据数字(仅 ASCII [0-9];'²'等版式标记为 False)。"""
    return len(s) == 1 and s.isascii() and s.isdecimal()
