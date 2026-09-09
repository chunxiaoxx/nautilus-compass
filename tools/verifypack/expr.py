"""受限表达式求值器——VerifyPack aggregate check 的 num/den 用。

只允许:数字、字段名(对行数组取列)、sum/len/min/max/round/count 调用、
+ - * /、一元 -。AST 白名单,其余节点一律拒绝——不 eval 任意代码。
"""
from __future__ import annotations

import ast

_ALLOWED_CALLS = {"sum", "len", "min", "max", "round", "count"}
_ALLOWED_BINOPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
                   ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b}


class ExprError(ValueError):
    """表达式越出白名单(含语法错误)。"""


def eval_expr(expr: str, rows: list[dict]) -> float | int:
    """对行数组求受限表达式。字段名 → 该列的值列表(sum/min/max)或行数(len)。"""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ExprError(f"bad expr {expr!r}: {e}") from e
    return _eval(tree.body, rows)


def _eval(node: ast.AST, rows: list[dict]):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](_eval(node.left, rows), _eval(node.right, rows))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval(node.operand, rows)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fname = node.func.id
        if fname not in _ALLOWED_CALLS or node.keywords:
            raise ExprError(f"call {fname!r} not allowed")
        if fname == "count":
            if node.keywords:
                raise ExprError("count() takes no keywords")
            if not node.args:
                return len(rows)
            return _count_pred(node.args[0], rows)
        if not node.args:
            raise ExprError(f"{fname}() needs an argument")
        vals = [_eval(a, rows) for a in node.args]
        return {"sum": sum, "len": len, "min": min, "max": max, "round": round}[fname](*vals)
    if isinstance(node, ast.Name):
        name = node.id
        if not rows:
            raise ExprError(f"field {name!r}: no rows")
        if name not in rows[0]:
            raise ExprError(f"unknown field {name!r}")
        return [r[name] for r in rows]
    raise ExprError(f"node {type(node).__name__} not allowed")


_CMP = {ast.Eq: lambda a, b: a == b, ast.Gt: lambda a, b: a > b,
        ast.GtE: lambda a, b: a >= b, ast.Lt: lambda a, b: a < b,
        ast.LtE: lambda a, b: a <= b, ast.NotEq: lambda a, b: a != b}


def _count_pred(node: ast.AST, rows: list[dict]) -> int:
    """仅支持受限形态 count(field <op> constant)。"""
    if not (isinstance(node, ast.Compare) and len(node.ops) == 1
            and isinstance(node.left, ast.Name)
            and len(node.comparators) == 1
            and isinstance(node.comparators[0], ast.Constant)
            and type(node.ops[0]) in _CMP):
        raise ExprError("count() predicate must be: field <cmp> constant")
    field, const = node.left.id, node.comparators[0].value
    if not rows:
        return 0
    if field not in rows[0]:
        raise ExprError(f"unknown field {field!r}")
    pred = _CMP[type(node.ops[0])]
    return sum(1 for r in rows if pred(r[field], const))


def get_path(doc, dotted: str):
    """按 a.b.c 取嵌套值;缺失即 KeyError。"""
    cur = doc
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(f"path {dotted!r}: missing {part!r}")
        cur = cur[part]
    return cur


def rows_to_map(rows: list[dict], key_field: str, value_field: str) -> dict:
    """行数组 → {key_field: value_field} 映射。"""
    out = {}
    for r in rows:
        if key_field not in r or value_field not in r:
            raise KeyError(f"rows missing {key_field!r}/{value_field!r}")
        out[r[key_field]] = r[value_field]
    return out
