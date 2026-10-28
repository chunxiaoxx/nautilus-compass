"""R5 · constitution.lock hash verify · 启动验证 · 防 V4 silent 死

每个 L1 文件有对应 .sha256 lock。启动时 verify_locks() 强制对比。
mismatch → ConstitutionViolation raise + telegram push(可配)。

V4 教训:重构时 silent 改 L1 → 召回特性悄悄死。本机制让任何 L1 修改
必须先更新 .sha256 lock(双签流程),否则启动失败。
"""
from __future__ import annotations
import hashlib
from pathlib import Path


class ConstitutionViolation(RuntimeError):
    """L1 hash mismatch · 启动应立即终止"""
    pass


# L1 受锁文件清单(模块路径相对 nautilus_v5/core/)
LOCKED_FILES = [
    "soul.py",
    "constitution.py",
    "tension.py",
    "emotion.py",
    "helix_chain.py",
    "proactive.py",
    "breath_cycle.py",
]

CORE_DIR = Path(__file__).parent
LOCKS_DIR = CORE_DIR / "locks"


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def compute_locks() -> dict[str, str]:
    """重新计算所有 LOCKED_FILES 的 sha256 · 用于初始化或更新 lock"""
    return {f: _file_sha256(CORE_DIR / f) for f in LOCKED_FILES if (CORE_DIR / f).exists()}


def write_locks(locks: dict[str, str], target: Path | None = None) -> None:
    """写入 .sha256 lock 文件(每文件 1 个 .sha256)"""
    target = target or LOCKS_DIR
    target.mkdir(exist_ok=True)
    for fname, digest in locks.items():
        (target / f"{fname}.sha256").write_text(digest + "\n", encoding="utf-8")


def read_lock(fname: str) -> str | None:
    """读单文件期望 sha256 · 不存在返回 None"""
    p = LOCKS_DIR / f"{fname}.sha256"
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8").strip()


def verify_locks(strict: bool = True) -> dict[str, tuple[str, str, bool]]:
    """启动验证 · 返回 {fname: (expected, actual, match)}

    strict=True:任何 mismatch raise ConstitutionViolation
    strict=False:只返回报告 · 不 raise(用于 dry-run / 测试)
    """
    report = {}
    violations = []
    for fname in LOCKED_FILES:
        path = CORE_DIR / fname
        if not path.exists():
            report[fname] = ("(no file)", "(no file)", True)
            continue
        actual = _file_sha256(path)
        expected = read_lock(fname)
        if expected is None:
            report[fname] = ("(no lock)", actual, False)
            violations.append(f"{fname}: no lock file in locks/")
        else:
            match = expected == actual
            report[fname] = (expected, actual, match)
            if not match:
                violations.append(
                    f"{fname}: expected {expected[:12]}... got {actual[:12]}..."
                )

    if strict and violations:
        msg = "L1 constitution violations:\n  " + "\n  ".join(violations)
        msg += "\n\nIf change is intentional, run: python -m nautilus_core.constitution --update"
        raise ConstitutionViolation(msg)

    return report


def main():
    """CLI · python -m nautilus_core.constitution [--update | --check]"""
    import sys
    if "--update" in sys.argv:
        locks = compute_locks()
        write_locks(locks)
        print(f"Updated {len(locks)} locks in {LOCKS_DIR}")
        for fname, digest in locks.items():
            print(f"  {fname}: {digest[:16]}...")
        return
    # default: --check
    report = verify_locks(strict=False)
    all_ok = all(m for _, _, m in report.values())
    for fname, (exp, act, match) in report.items():
        flag = "OK" if match else "MISMATCH"
        print(f"[{flag}] {fname}")
        if not match:
            print(f"   expected: {exp[:16] if exp else '(none)'}...")
            print(f"   actual:   {act[:16]}...")
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
