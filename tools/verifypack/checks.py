"""check 引擎——七种 kind 的复算判据(SPEC §4)。verify 命令的执行体。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from . import expr
from .spec import EPISODE_FRAME_OPS, SpecError

JSON_SUFFIX = ".json"


class CheckError(RuntimeError):
    """check 无法执行(缺文件/路径坏/求值失败)——区别于 verdict=disagree。"""


def _load_doc(pack_dir: Path, ref: str):
    """'payload.json#a.b.c' → (doc, value@path)。file 相对 pack 根。"""
    file_ref, _, dotted = ref.partition("#")
    f = pack_dir / file_ref
    if not f.is_file():
        raise CheckError(f"file not in pack: {file_ref}")
    doc = json.loads(f.read_text(encoding="utf-8"))
    return expr.get_path(doc, dotted) if dotted else doc


def _rows(pack_dir: Path, ref: str) -> list[dict]:
    rows = _load_doc(pack_dir, ref)
    if not isinstance(rows, list):
        raise CheckError(f"{ref}: expected array")
    return rows


def _map_from(pack_dir: Path, ref: str, map_by: str, field: str) -> dict:
    return expr.rows_to_map(_rows(pack_dir, ref), map_by, field)


def _resolve_input(pack_dir: Path, pack: dict, dir_decl: str) -> Path:
    for inp in pack.get("inputs", []):
        if inp["name"] == dir_decl:
            return Path(inp["path"])
    raise CheckError(f"undeclared input dir: {dir_decl}")


_FILTER_OPS = {"==": lambda a, b: a == b, "!=": lambda a, b: a != b,
               ">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
               ">": lambda a, b: a > b, "<": lambda a, b: a < b}


def _apply_filter(rows: list[dict], flt) -> list[dict]:
    """check 可选 filter:[{field,op,value},…](AND)。"""
    if not flt:
        return rows
    out = rows
    for cond in flt:
        f, op, v = cond["field"], cond["op"], cond["value"]
        if op not in _FILTER_OPS:
            raise SpecError(f"filter op {op!r} not allowed")
        pred = _FILTER_OPS[op]
        out = [r for r in out if f in r and pred(r[f], v)]
    return out


def run_check(pack: dict, claim: dict, check: dict, pack_dir: Path,
              computed: dict | None = None, env_caps: set[str] | None = None) -> dict:
    """执行单条 check → {"ok": bool, "recomputed": …}。raise CheckError = 无法执行。"""
    kind = check["kind"]

    if kind == "aggregate":
        rows = _apply_filter(_rows(pack_dir, check["from"]), check.get("filter"))
        num = expr.eval_expr(check["num"], rows)
        den = expr.eval_expr(check["den"], rows) if check.get("den") is not None else 1
        val = round(num / den, check.get("ndigits", 6))
        claimed = claim["value"]
        tol = check.get("tol", 1e-6)
        ok = abs(val - claimed) <= tol if check["op"] == "ratio_eq" else val == claimed
        return {"ok": ok, "recomputed": val}

    if kind == "file_hash":
        f = pack_dir / check["file"]
        if not f.is_file():
            raise CheckError(f"file not in pack: {check['file']}")
        algo = check.get("algo", "sha256")
        got = {"sha256": _sha_file, "sha256_16": lambda p: _sha_file(p)[:16]}[algo](f)
        return {"ok": got == check["expect"], "recomputed": got}

    if kind == "file_hash_map":
        algo = check["algo"]
        hasher = {"sha256": _sha_file, "sha256_16": lambda p: _sha_file(p)[:16]}[algo]
        expect = claim["value"] if isinstance(claim["value"], dict) else json.loads(claim["value"])
        if check.get("from"):  # 行映射模式:名字字段→路径字段(支持嵌套点路径)
            rows = _rows(pack_dir, check["from"])
            key_f, path_f = check["key"], check["path"]
            got = {}
            for r in rows:
                f = pack_dir / expr.get_path(r, path_f)
                if not f.is_file():
                    raise CheckError(f"file missing: {f}")
                got[str(expr.get_path(r, key_f))] = hasher(f)
            return {"ok": got == expect, "recomputed": got}
        names = list(expect.keys()) if check.get("names_from", "claim") == "claim" \
            else [r[check["names_from"]] for r in _rows(pack_dir, check["names_from"])]
        if check.get("dir_decl"):
            root = _resolve_input(pack_dir, pack, check["dir_decl"])
        else:
            root = pack_dir / check.get("dir", ".")
        got = {}
        for n in names:
            f = root / n
            if not f.is_file():
                raise CheckError(f"input file missing: {f}")
            got[n] = hasher(f)
        return {"ok": got == expect, "recomputed": got}

    if kind == "group_count":
        rows = _apply_filter(_rows(pack_dir, check["from"]), check.get("filter"))
        by = check["by"]
        groups: dict[str, int] = {}
        for r in rows:
            groups[str(r[by])] = groups.get(str(r[by]), 0) + 1
        min_ok = all(v >= check.get("min_group", 1) for v in groups.values())
        n_ok = check.get("expect_groups") is None or len(groups) == check["expect_groups"]
        return {"ok": min_ok and n_ok, "recomputed": groups}

    if kind == "json_map_equal":
        left = _map_from(pack_dir, f"{check['file']}#{check['path']}",
                         check["map_by"], check["field"])
        expect = claim["value"] if isinstance(claim["value"], dict) else json.loads(claim["value"])
        tol = check.get("tol", 1e-4)
        ok = set(left) == set(expect) and all(
            abs(left[k] - expect[k]) <= tol if isinstance(expect[k], (int, float))
            else left[k] == expect[k] for k in expect)
        return {"ok": ok, "recomputed": len(left)}

    if kind == "text_contains":
        f = pack_dir / check["file"]
        if not f.is_file():
            raise CheckError(f"file not in pack: {check['file']}")
        text = f.read_text(encoding="utf-8")
        missing = []
        for needle in check["needles"]:
            if "claim" in needle:
                if needle["claim"] not in (computed or {}):
                    raise CheckError(f"text_contains: claim {needle['claim']!r} not yet computed")
                s = _to_text(computed[needle["claim"]])
            else:
                s = str(needle["value"])
            if s not in text:
                missing.append(s)
        return {"ok": not missing, "recomputed": f"missing={missing}" if missing else "all found"}

    if kind == "episode":
        rows = _rows(pack_dir, check["from"])
        got = _run_episode(rows, check.get("episode_by"), check["invariants"])
        # 不变量=有效性谓词:违规数必须为零,声称"吻合的违规"不构成 agree
        ok = got == claim["value"] and not any(got["violations"].values())
        return {"ok": ok, "recomputed": got}

    if kind == "script":
        if env_caps is not None and check.get("requires_env") and \
                check["requires_env"] not in env_caps:
            raise EnvRequired(check["requires_env"])
        script = pack_dir / check["repro"]
        if not script.is_file():
            raise CheckError(f"repro script not in pack: {check['repro']}")
        proc = subprocess.run([sys.executable, str(script)], capture_output=True,
                              text=True, timeout=check.get("timeout_s", 120), cwd=str(pack_dir))
        if proc.returncode != 0:
            raise CheckError(f"repro script rc={proc.returncode}: {proc.stderr[-300:]}")
        val = json.loads(proc.stdout.strip().splitlines()[-1]).get("value")
        return {"ok": val == claim["value"], "recomputed": val}

    raise SpecError(f"unknown kind {kind!r}")  # pragma: no cover


_EPS = 1e-9


def _frame_field(frame: dict, field: str):
    if field not in frame:
        raise CheckError(f"frame missing field {field!r}")
    return frame[field]


def _frame_ok(frame: dict, inv: dict) -> bool:
    v, rhs = _frame_field(frame, inv["field"]), inv["rhs"]
    return {"ge_const": v >= rhs, "le_const": v <= rhs,
            "eq_const": abs(v - rhs) <= _EPS}[inv["op"]]


def _pair_ok(prev: dict, cur: dict, inv: dict) -> bool:
    f = inv["field"]
    a, b = _frame_field(prev, f), _frame_field(cur, f)
    op = inv["op"]
    if op == "same":
        return cur[f] == prev[f]
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise CheckError(f"invariant {inv.get('name', f)!r}: field {f!r} non-numeric")
    d = b - a
    return {"incr_eq": abs(d - inv["rhs"]) <= _EPS,
            "incr_ge": d >= inv["rhs"], "incr_le": d <= inv["rhs"],
            "abs_delta_le": abs(d) <= inv["rhs"], "abs_delta_ge": abs(d) >= inv["rhs"],
            "delta_le": d <= inv["rhs"], "delta_ge": d >= inv["rhs"]}[op]


def _run_episode(rows: list[dict], by: str | None, invariants: list[dict]) -> dict:
    """帧数组 → 转移不变量核查。返回 {transitions, violations{名:数}}。"""
    groups: list[list[dict]] = []
    if by:
        buf: list[dict] = []
        for r in rows:
            if buf and _frame_field(r, by) != _frame_field(buf[-1], by):
                groups.append(buf)
                buf = []
            buf.append(r)
        if buf:
            groups.append(buf)
    else:
        groups = [rows]
    named = [(inv.get("name", f"inv{i}"), inv) for i, inv in enumerate(invariants)]
    violations = {name: 0 for name, _ in named}
    transitions = 0
    for g in groups:
        transitions += max(len(g) - 1, 0)
        for i, cur in enumerate(g):
            for name, inv in named:
                if inv["op"] in EPISODE_FRAME_OPS:
                    bad = not _frame_ok(cur, inv)
                elif i > 0:
                    bad = not _pair_ok(g[i - 1], cur, inv)
                else:
                    bad = False
                if bad:
                    violations[name] += 1
    return {"transitions": transitions, "violations": violations}


class EnvRequired(RuntimeError):
    """L2 主判据需要的环境未声明——verify 层转 fallback / degraded。"""

    def __init__(self, cap: str):
        super().__init__(f"env capability required: {cap}")
        self.cap = cap


def _sha_file(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _to_text(v) -> str:
    return json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
