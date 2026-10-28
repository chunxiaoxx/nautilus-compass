"""Deterministic static check pipeline · Nautilus Engine cycle 3.

Four checks against engine-generated Python file(s):
  1. py_compile  · stdlib syntax-level validation (always available)
  2. import      · attempt to load the module (catches missing deps · runtime err)
  3. ruff        · linting (skipped if ruff exe not on PATH)
  4. pytest      · opt-in target invocation (separate · slower · not part of default)

All four return CheckResult objects · run_pipeline() aggregates to {passed, checks}.

Designed to be called by NautilusEngine after writing files in --apply mode
so the audit + commit step (cycle 4) only sees code that survives the pipeline.
"""
from __future__ import annotations

import ast
import importlib.util
import py_compile
import re
import shutil
import subprocess
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from .text_utils import truncate


@dataclass
class CheckResult:
    name: str
    passed: bool
    skipped: bool = False
    message: str = ""
    duration_ms: int = 0


def _is_py(path: str) -> bool:
    return path.lower().endswith(".py")


def _elapsed_ms(t0: float) -> int:
    return int((time.time() - t0) * 1000)


def check_py_compile(path: str) -> CheckResult:
    """Syntax-level compile via stdlib py_compile."""
    if not _is_py(path):
        return CheckResult(name="py_compile", passed=True, skipped=True, message="not a .py file")
    t0 = time.time()
    try:
        py_compile.compile(path, doraise=True)
        return CheckResult(name="py_compile", passed=True, duration_ms=_elapsed_ms(t0))
    except py_compile.PyCompileError as e:
        return CheckResult(
            name="py_compile",
            passed=False,
            message=str(e)[:500],
            duration_ms=_elapsed_ms(t0),
        )
    except Exception as e:
        return CheckResult(
            name="py_compile",
            passed=False,
            message=f"{type(e).__name__}: {e}"[:500],
            duration_ms=_elapsed_ms(t0),
        )


def check_import(path: str, pythonpath: Optional[str] = None) -> CheckResult:
    """Load module via importlib · catches import-time errors (missing deps, etc).

    pythonpath: if provided, prepend to sys.path for the duration of the check so
    that internal imports (e.g. ``from engine.text_utils import truncate``) resolve
    against the real backend package tree rather than failing in the isolated staging
    directory.  The original sys.path is restored after the check.
    """
    if not _is_py(path):
        return CheckResult(name="import", passed=True, skipped=True, message="not a .py file")
    t0 = time.time()
    p = Path(path)
    # 2026-09-10 · subprocess isolation (was same-process importlib).
    # Same-process exec_module silently inherits the checker's sys.modules: in
    # the consumer process `utils` / `agent_engine` are already bound to the
    # real backend packages, so a staged tests/test_x.py doing
    # `from utils.x import ...` resolved against the live package and failed
    # with "No module named utils.x" no matter what we prepended to sys.path.
    # A fresh interpreter per file gives a clean module namespace,
    # honours PYTHONPATH, and contains any import-time side effects.
    code = (
        "import importlib.util, sys\n"
        "spec = importlib.util.spec_from_file_location('_staged_mod', sys.argv[1])\n"
        "assert spec is not None and spec.loader is not None, 'cannot create import spec'\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "sys.modules['_staged_mod'] = mod\n"
        "spec.loader.exec_module(mod)\n"
    )
    env = dict(os.environ)
    if pythonpath:
        env["PYTHONPATH"] = pythonpath + os.pathsep + env.get("PYTHONPATH", "")
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code, str(p)],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            cwd=str(p.parent),
        )
        if proc.returncode == 0:
            return CheckResult(name="import", passed=True, duration_ms=_elapsed_ms(t0))
        err = (proc.stderr or "").strip().splitlines()
        tail = "\n".join(err[-6:]) if err else f"exit code {proc.returncode}"
        return CheckResult(
            name="import",
            passed=False,
            message=tail[:500],
            duration_ms=_elapsed_ms(t0),
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="import",
            passed=False,
            message="import check timed out after 30s",
            duration_ms=_elapsed_ms(t0),
        )
    except Exception as e:
        return CheckResult(
            name="import",
            passed=False,
            message=f"{type(e).__name__}: {e}"[:500],
            duration_ms=_elapsed_ms(t0),
        )


def check_ruff(paths: list[str], command: str = "ruff") -> CheckResult:
    """Run `<ruff> check` on .py files · skipped silently if ruff exe missing."""
    t0 = time.time()
    ruff_exe = shutil.which(command)
    if not ruff_exe:
        return CheckResult(
            name="ruff",
            passed=True,
            skipped=True,
            message=f"ruff not found in PATH (command={command})",
        )
    py_paths = [p for p in paths if _is_py(p)]
    if not py_paths:
        return CheckResult(
            name="ruff",
            passed=True,
            skipped=True,
            message="no .py files to check",
        )
    try:
        result = subprocess.run(
            [ruff_exe, "check", "--quiet", *py_paths],
            capture_output=True,
            text=True,
            timeout=30,
        )
        passed = result.returncode == 0
        msg = (result.stdout + result.stderr).strip()[:500]
        if not msg:
            msg = "ruff: clean" if passed else "ruff: violations"
        return CheckResult(
            name="ruff",
            passed=passed,
            message=msg,
            duration_ms=_elapsed_ms(t0),
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="ruff",
            passed=False,
            message="ruff timeout (30s)",
            duration_ms=_elapsed_ms(t0),
        )
    except Exception as e:
        return CheckResult(
            name="ruff",
            passed=False,
            message=f"{type(e).__name__}: {e}"[:500],
            duration_ms=_elapsed_ms(t0),
        )


_TRACEBACK_MARKER = "Traceback (most recent call last)"
# SyntaxError / IndentationError print without the "Traceback" header · catch
# them via the error type name + colon pattern as a backup signal.
_ERROR_MARKERS = (
    "SyntaxError:",
    "IndentationError:",
    "TabError:",
)


def _has_runtime_failure(stderr: str) -> bool:
    if not stderr:
        return False
    if _TRACEBACK_MARKER in stderr:
        return True
    return any(m in stderr for m in _ERROR_MARKERS)


def check_runtime(path: str, timeout: int = 10) -> CheckResult:
    """Subprocess `python <path>` smoke · catches import + top-level runtime errors.

    SECURITY: executes arbitrary code in `path` via subprocess. Use only on trusted
    or staged-but-not-applied LLM output. Subprocess provides timeout isolation
    but no further sandboxing.

    LIMIT: invokes with NO args. Bugs gated behind argv parsing (e.g. main() that
    only fails when a task arg is provided) are NOT caught. See
    tests/test_runtime_check.py::test_runtime_does_NOT_catch_main_only_bug for
    the canonical example (cycle 5 bug class).
    """
    if not _is_py(path):
        return CheckResult(name="runtime", passed=True, skipped=True, message="not a .py file")
    t0 = time.time()
    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stderr = result.stderr or ""
        passed = not _has_runtime_failure(stderr)
        msg = stderr.strip()[-400:] if stderr else f"exit {result.returncode}"
        return CheckResult(
            name="runtime",
            passed=passed,
            message=msg,
            duration_ms=_elapsed_ms(t0),
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="runtime",
            passed=False,
            message=f"runtime timeout ({timeout}s)",
            duration_ms=_elapsed_ms(t0),
        )
    except Exception as e:
        return CheckResult(
            name="runtime",
            passed=False,
            message=f"{type(e).__name__}: {str(e)[:200]}",
            duration_ms=_elapsed_ms(t0),
        )


def _detect_sample_args(file_path: str) -> list[str]:
    """Heuristic: infer the most likely sample args to invoke `python <file>`.

    - argparse-based scripts → ["--help"] (always exits 0 cleanly)
    - sys.argv[1] / sys.argv[1:] usage → ["nautilus_engine_smoke"] (one positional)
    - otherwise → [] (no args · same as check_runtime)
    """
    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    if "argparse.ArgumentParser" in content or "ArgumentParser(" in content:
        return ["--help"]
    if (
        "sys.argv[1]" in content
        or "sys.argv[1:]" in content
        or "argv[1:]" in content
        or "len(sys.argv)" in content
    ):
        return ["nautilus_engine_smoke"]
    return []


def check_runtime_with_sample_args(path: str, timeout: int = 10) -> CheckResult:
    """Runtime smoke that auto-detects + passes sample args to trigger main() body.

    Closes the cycle 6 gap (main()-only bugs hidden behind argv parsing).
    Heuristics in _detect_sample_args:
      - argparse imports → invoke with --help (always exits 0)
      - sys.argv[1] access → invoke with single dummy positional
      - otherwise → no args (falls back to check_runtime behavior)

    Pass criterion: no Traceback in stderr. Exit code is NOT enforced because
    legitimate scripts may exit non-zero on dummy input.

    SECURITY: executes arbitrary code · only use on staged/trusted output.
    """
    if not _is_py(path):
        return CheckResult(name="runtime_args", passed=True, skipped=True, message="not a .py file")
    args = _detect_sample_args(path)
    t0 = time.time()
    try:
        result = subprocess.run(
            [sys.executable, path, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stderr = result.stderr or ""
        has_failure = _has_runtime_failure(stderr)
        # When we provided sample args, the file's entry path was triggered ·
        # a non-zero exit signals the bug surfaced (even if a try/except
        # caught the exception and reformatted it to "Error: ..." in stderr).
        # Without args, exit code is unreliable (lib-style files exit 0 by
        # default) so we only check for tracebacks.
        if args:
            passed = (result.returncode == 0) and not has_failure
        else:
            passed = not has_failure
        prefix = f"args={args} · exit={result.returncode} · "
        body = stderr.strip()[-280:] if stderr else "(no stderr)"
        return CheckResult(
            name="runtime_args",
            passed=passed,
            message=(prefix + body)[:500],
            duration_ms=_elapsed_ms(t0),
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="runtime_args",
            passed=False,
            message=f"runtime_args timeout ({timeout}s) · args={args}",
            duration_ms=_elapsed_ms(t0),
        )
    except Exception as e:
        return CheckResult(
            name="runtime_args",
            passed=False,
            message=f"{type(e).__name__}: {str(e)[:200]}",
            duration_ms=_elapsed_ms(t0),
        )


# ---------- cycle 12 P1 · semantic-preservation diff (Layer 5 BUDDHA gap) ----------

SEMANTIC_PRESERVE_TRIGGER_PHRASES = (
    "keep all other code identical",
    "only add",
    "only change line",
    "minimal diff",
    "do not refactor",
)


# ---------- Gap 1 · line count + docstring + size-trigger guards ----------

SHRINK_FLOOR = 0.85          # always strict (truncation is the failure mode)
GROWTH_CEILING = 2.0         # default
GROWTH_CEILING_ALLOW_ADD = 4.0  # when allow_additions=True

_DOCSTRING_CHANGE_KEYWORDS = (
    # EN
    "update docstring",
    "rewrite docstring",
    "change docstring",
    "modify docstring",
    "docstring change",
    # 中文
    "改 docstring",
    "重写 docstring",
    "更新 docstring",
    "修改 docstring",
)

_EXISTING_FILE_LOC_TRIGGER = 50


def should_apply_semantic_check(task: str | None) -> bool:
    """Auto-detect whether the semantic-preservation check should fire.

    Returns True when the task wording contains any MINIMAL CHANGE MODE trigger
    phrase (cycle 12 P0 prompt). Mirrors the LLM-side triggers so the deterministic
    check fires in the same situations the prompt is meant to constrain.
    """
    if not task:
        return False
    lower = task.lower()
    return any(phrase in lower for phrase in SEMANTIC_PRESERVE_TRIGGER_PHRASES)


_ADDITIVE_VERB_RE = re.compile(
    r"\b(?:add|adding|adds|new|introduce|introduces|append|appends|insert|inserts)\b",
    re.IGNORECASE,
)


def should_allow_additions(task: str | None) -> bool:
    """Cycle 16 · auto-detect whether intentional additions should be tolerated.

    Returns True when the task is in MINIMAL CHANGE MODE (cycle 12 trigger
    phrase) AND explicitly asks to ADD something (add/new/introduce/append/insert).
    Closes the cycle 15 gap where strict semantic check correctly detected
    SPEC'd additions as diff and falsely blocked apply.

    The conjunction is important: "rewrite cache.py" alone doesn't trigger
    additions tolerance · only "add a logger · keep ALL other code identical"
    (or similar) does.
    """
    if not should_apply_semantic_check(task):
        return False
    return bool(_ADDITIVE_VERB_RE.search(task))


def should_apply_preservation_checks(
    task: Optional[str],
    blocks: list,
    base_dir,
) -> bool:
    """OR trigger for the preservation check family (Gap 1).

    Fires when:
        - task contains any MINIMAL CHANGE phrase (existing should_apply_semantic_check), OR
        - any target file in blocks already exists on disk with > 50 LOC.

    `blocks` is the engine.parse_file_blocks() output: list of dicts each with a "path" key
    relative to base_dir.
    """
    if should_apply_semantic_check(task):
        return True
    if isinstance(base_dir, Path):
        base = base_dir.resolve()
    else:
        base = Path(base_dir).resolve()
    for b in blocks:
        rel = b.get("path", "")
        if not rel:
            continue
        target = (base / rel).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            continue  # path escape · ignore
        if not target.is_file():
            continue
        try:
            with target.open(encoding="utf-8", errors="ignore") as f:
                lines = sum(1 for _ in f)
            if lines > _EXISTING_FILE_LOC_TRIGGER:
                return True
        except OSError:
            continue
    return False


def _extract_top_level_signatures(tree: ast.Module) -> dict:
    """Pull out top-level imports / function sigs / class names from an AST."""
    imports: list[str] = []
    functions: list[tuple[str, str]] = []
    classes: list[tuple[str, list[str]]] = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                spec = alias.name + (f" as {alias.asname}" if alias.asname else "")
                imports.append(f"import {spec}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = "." * node.level
            for alias in node.names:
                spec = alias.name + (f" as {alias.asname}" if alias.asname else "")
                imports.append(f"from {level}{module} import {spec}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append((node.name, ast.unparse(node.args)))
        elif isinstance(node, ast.ClassDef):
            base_names = [ast.unparse(b) for b in node.bases]
            classes.append((node.name, base_names))

    return {"imports": imports, "functions": functions, "classes": classes}


def check_semantic_preservation(
    original_path: str,
    new_path: str,
    strict: bool = True,
    allow_additions: bool = False,
) -> CheckResult:
    """AST-based diff of top-level semantic elements between two Python files.

    Catches the Layer 5 BUDDHA-A.1 class of regression: the engine LLM generates
    syntactically valid code that PASSES all 4 default checks but has different
    imports / functions / classes than the original (over-rewrite). Used in
    conjunction with the cycle 12 P0 MINIMAL CHANGE MODE prompt as defense in depth.

    Args:
        original_path: file as it exists before the engine ships
        new_path: LLM-generated replacement (staged or applied)
        strict: when True · ANY semantic diff fails. When False · only function
                signature changes fail; added/removed imports and classes are
                surfaced in the message but treated as warnings.
        allow_additions: cycle 16 · when True · intentional additions
                (added imports / functions / classes) DO NOT fail the check.
                Removed elements and signature changes still fail. Use this
                for tasks that explicitly ask to ADD something while preserving
                everything else (closes cycle 15 spec'd-add false-positive).

    Returns:
        CheckResult(name="semantic", ...) with the concrete diff in `message`
        on failure so the engine retry loop can re-prompt with the exact gap.
    """
    if not _is_py(original_path) or not _is_py(new_path):
        return CheckResult(
            name="semantic", passed=True, skipped=True, message="not a .py file"
        )
    t0 = time.time()
    try:
        original_src = Path(original_path).read_text(encoding="utf-8")
        new_src = Path(new_path).read_text(encoding="utf-8")
    except OSError as e:
        return CheckResult(
            name="semantic",
            passed=False,
            message=truncate(f"read error: {e}", 300),
            duration_ms=_elapsed_ms(t0),
        )
    try:
        orig_tree = ast.parse(original_src)
        new_tree = ast.parse(new_src)
    except SyntaxError as e:
        return CheckResult(
            name="semantic",
            passed=False,
            message=truncate(f"parse error: {e}", 300),
            duration_ms=_elapsed_ms(t0),
        )

    orig = _extract_top_level_signatures(orig_tree)
    new = _extract_top_level_signatures(new_tree)

    removals: list[str] = []
    additions: list[str] = []
    sig_changes: list[str] = []

    orig_imports = set(orig["imports"])
    new_imports = set(new["imports"])
    if (removed := sorted(orig_imports - new_imports)):
        removals.append(f"imports removed: {removed}")
    if (added := sorted(new_imports - orig_imports)):
        additions.append(f"imports added: {added}")

    orig_funcs = dict(orig["functions"])
    new_funcs = dict(new["functions"])
    if (removed_f := sorted(set(orig_funcs) - set(new_funcs))):
        removals.append(f"functions removed: {removed_f}")
    if (added_f := sorted(set(new_funcs) - set(orig_funcs))):
        additions.append(f"functions added: {added_f}")
    for name in set(orig_funcs) & set(new_funcs):
        if orig_funcs[name] != new_funcs[name]:
            sig_changes.append(
                f"function {name!r} sig {orig_funcs[name]!r} → {new_funcs[name]!r}"
            )

    orig_classes = dict(orig["classes"])
    new_classes = dict(new["classes"])
    if (removed_c := sorted(set(orig_classes) - set(new_classes))):
        removals.append(f"classes removed: {removed_c}")
    if (added_c := sorted(set(new_classes) - set(orig_classes))):
        additions.append(f"classes added: {added_c}")

    differences = removals + additions + sig_changes
    if not differences:
        return CheckResult(name="semantic", passed=True, duration_ms=_elapsed_ms(t0))

    # Pass/fail policy (cycle 16 · 3 modes):
    # - allow_additions: pass unless removals OR sig changes (additions OK)
    # - strict (default): pass only when zero diff
    # - non-strict (no flags): pass unless sig changes (most permissive)
    if allow_additions:
        violations = removals + sig_changes
    elif strict:
        violations = differences
    else:
        violations = sig_changes

    return CheckResult(
        name="semantic",
        passed=(not violations),
        message=truncate(" · ".join(differences), 500),
        duration_ms=_elapsed_ms(t0),
    )


def check_line_count(
    original_path: str,
    new_path: str,
    allow_additions: bool = False,
) -> CheckResult:
    """Reject when new file line count drifts from original outside bounds.

    Bounds (per design doc 2026-05-26-gap1-semantic-guard-design.md):
        shrink_floor = 0.85 * orig_lines (always strict · truncate is the failure mode)
        growth_ceiling = 2.0 * orig_lines default · 4.0 when allow_additions=True

    Skipped:
        - original not on disk (new file): vacuous
        - original empty (ratio undefined)
    """
    t0 = time.time()
    orig = Path(original_path)
    if not orig.is_file():
        return CheckResult(
            name="line_count",
            passed=True,
            skipped=True,
            message="original not on disk (new file)",
            duration_ms=_elapsed_ms(t0),
        )
    try:
        with open(original_path, encoding="utf-8", errors="ignore") as f:
            orig_lines = sum(1 for _ in f)
        with open(new_path, encoding="utf-8", errors="ignore") as f:
            new_lines = sum(1 for _ in f)
    except OSError as e:
        return CheckResult(
            name="line_count",
            passed=False,
            message=f"read error: {e}"[:300],
            duration_ms=_elapsed_ms(t0),
        )
    if orig_lines == 0:
        return CheckResult(
            name="line_count",
            passed=True,
            skipped=True,
            message="original empty (ratio undefined)",
            duration_ms=_elapsed_ms(t0),
        )
    ratio = new_lines / orig_lines
    ceiling = GROWTH_CEILING_ALLOW_ADD if allow_additions else GROWTH_CEILING
    if ratio < SHRINK_FLOOR:
        return CheckResult(
            name="line_count",
            passed=False,
            message=f"shrink {new_lines}/{orig_lines}={ratio:.2f} < {SHRINK_FLOOR} floor",
            duration_ms=_elapsed_ms(t0),
        )
    if ratio > ceiling:
        return CheckResult(
            name="line_count",
            passed=False,
            message=(
                f"growth {new_lines}/{orig_lines}={ratio:.2f} > {ceiling} ceiling "
                f"(allow_additions={allow_additions})"
            ),
            duration_ms=_elapsed_ms(t0),
        )
    return CheckResult(
        name="line_count",
        passed=True,
        message=f"ok {new_lines}/{orig_lines}={ratio:.2f}",
        duration_ms=_elapsed_ms(t0),
    )


def _extract_module_docstring(src: str) -> Optional[str]:
    """Return the module-level docstring (first AST string expression) · None if absent."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    if not tree.body:
        return None
    first = tree.body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return first.value.value
    return None


def check_docstring_preserve(
    original_path: str,
    new_path: str,
    task: str,
) -> CheckResult:
    """Reject when module-level docstring text differs byte-for-byte.

    Skip when task lowercased contains any keyword in _DOCSTRING_CHANGE_KEYWORDS
    (5 EN + 4 中文 · supports bilingual task wording).

    Skipped: new file (no original) · or both sides have no module docstring.
    """
    t0 = time.time()
    orig = Path(original_path)
    if not orig.is_file():
        return CheckResult(
            name="docstring_preserve",
            passed=True,
            skipped=True,
            message="original not on disk (new file)",
            duration_ms=_elapsed_ms(t0),
        )
    if task and any(kw in task.lower() for kw in _DOCSTRING_CHANGE_KEYWORDS):
        return CheckResult(
            name="docstring_preserve",
            passed=True,
            skipped=True,
            message="task signals docstring change · escape",
            duration_ms=_elapsed_ms(t0),
        )
    try:
        orig_src = Path(original_path).read_text(encoding="utf-8")
        new_src = Path(new_path).read_text(encoding="utf-8")
    except OSError as e:
        return CheckResult(
            name="docstring_preserve",
            passed=False,
            message=f"read error: {e}"[:300],
            duration_ms=_elapsed_ms(t0),
        )
    orig_doc = _extract_module_docstring(orig_src)
    new_doc = _extract_module_docstring(new_src)
    if orig_doc is None and new_doc is None:
        return CheckResult(
            name="docstring_preserve",
            passed=True,
            skipped=True,
            message="neither side has module docstring",
            duration_ms=_elapsed_ms(t0),
        )
    if orig_doc == new_doc:
        return CheckResult(
            name="docstring_preserve",
            passed=True,
            duration_ms=_elapsed_ms(t0),
        )
    return CheckResult(
        name="docstring_preserve",
        passed=False,
        message=truncate(
            f"docstring changed · orig={orig_doc!r} → new={new_doc!r}",
            300,
        ),
        duration_ms=_elapsed_ms(t0),
    )


def check_pytest(target: str, timeout: int = 120) -> CheckResult:
    """Run `python -m pytest -x` against target · opt-in (not part of default pipeline)."""
    t0 = time.time()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-x", "--no-header", target],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        passed = result.returncode == 0
        tail = (result.stdout + result.stderr).strip()
        return CheckResult(
            name="pytest",
            passed=passed,
            message=tail[-500:],
            duration_ms=_elapsed_ms(t0),
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="pytest",
            passed=False,
            message=f"pytest timeout ({timeout}s)",
            duration_ms=_elapsed_ms(t0),
        )
    except Exception as e:
        return CheckResult(
            name="pytest",
            passed=False,
            message=f"{type(e).__name__}: {e}"[:500],
            duration_ms=_elapsed_ms(t0),
        )


def run_pipeline(
    paths: list[str],
    run_py_compile: bool = True,
    run_import: bool = True,
    run_ruff: bool = True,
    run_runtime: bool = False,
    run_runtime_args: bool = False,
    pytest_target: Optional[str] = None,
    runtime_timeout: int = 10,
    pythonpath: Optional[str] = None,
) -> dict:
    """Run check pipeline against the given files · aggregate to {passed, checks}.

    Note: run_runtime defaults False (security · executes arbitrary code).
    Only enable for trusted / staged LLM output.

    pythonpath: if provided, forwarded to check_import so staged files with
    internal imports (e.g. ``from engine.text_utils import truncate``) resolve
    against the real backend tree.  Default None preserves existing behaviour.

    Returns:
        {"passed": bool, "checks": [dict, ...]} · checks list dicts via asdict.
    """
    checks: list[CheckResult] = []
    if not paths:
        return {"passed": True, "checks": []}

    if run_py_compile:
        checks.extend(check_py_compile(p) for p in paths)
    if run_import:
        checks.extend(check_import(p, pythonpath=pythonpath) for p in paths)
    if run_ruff:
        checks.append(check_ruff(paths))
    if run_runtime:
        checks.extend(check_runtime(p, timeout=runtime_timeout) for p in paths)
    if run_runtime_args:
        checks.extend(
            check_runtime_with_sample_args(p, timeout=runtime_timeout) for p in paths
        )
    if pytest_target:
        checks.append(check_pytest(pytest_target))

    return {
        "passed": all(c.passed for c in checks),
        "checks": [asdict(c) for c in checks],
    }
