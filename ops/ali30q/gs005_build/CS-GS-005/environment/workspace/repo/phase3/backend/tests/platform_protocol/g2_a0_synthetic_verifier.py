from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from g2_a0_deepseek_client import CandidateArtifactV1
from g2_a0_synthetic_fixture import SyntheticRepairFixtureV1

_DIFF_BYTES_LIMIT = 65_536
_PATCHED_BYTES_LIMIT = 8_192
_SOURCE_TREE_ROOT = Path(__file__).resolve().parents[4]
_HUNK_RE = re.compile(
    r"@@ -(?P<old_start>[1-9][0-9]*)(?:,(?P<old_count>[0-9]+))? "
    r"\+(?P<new_start>[1-9][0-9]*)(?:,(?P<new_count>[0-9]+))? @@\n"
)
_FORBIDDEN_DIFF_MARKERS = (
    "```",
    "\x00",
    "diff --git",
    "git binary patch",
    "old mode ",
    "new mode ",
    "new file mode ",
    "deleted file mode ",
    "rename from ",
    "rename to ",
    "copy from ",
    "copy to ",
    "/dev/null",
    "../",
    "..\\",
    "\\\\?\\",
)
_FORBIDDEN_SOURCE_MARKERS = (
    "__",
    "://",
    "compile(",
    "delattr(",
    "eval(",
    "exec(",
    "getattr(",
    "globals(",
    "import ",
    "locals(",
    "open(",
    "setattr(",
    "subprocess",
    "socket",
)
_ALLOWED_AST_NODES = (
    ast.Module,
    ast.FunctionDef,
    ast.arguments,
    ast.arg,
    ast.If,
    ast.Raise,
    ast.Return,
    ast.BoolOp,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Compare,
    ast.Eq,
)
_ALLOWED_NAMES = {
    "TypeError",
    "bool",
    "clamp_score",
    "int",
    "isinstance",
    "max",
    "min",
    "value",
}
_ALLOWED_CALLS = {"TypeError", "isinstance", "max", "min"}
_ORACLE_SCRIPT = r"""
import importlib.util
import json
import pathlib
import sys

target = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("synthetic_target", target)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
function = module.clamp_score

def returns(value, expected):
    try:
        result = function(value)
    except BaseException:
        return False
    return type(result) is int and result == expected

def rejects(value):
    try:
        function(value)
    except TypeError:
        return True
    except BaseException:
        return False
    return False

public_passed = all((returns(-5, 0), returns(50, 50), returns(120, 100)))
hidden_passed = all(
    (
        returns(0, 0),
        returns(100, 100),
        returns(-1000000, 0),
        returns(1000000, 100),
        rejects(True),
        rejects(False),
        rejects("1"),
        rejects(None),
        rejects(1.5),
        rejects(1 + 2j),
    )
)
status = "passed" if public_passed and hidden_passed else "rejected"
sys.stdout.write(
    json.dumps(
        {
            "hidden_passed": hidden_passed,
            "public_passed": public_passed,
            "status": status,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    + "\n"
)
""".strip()


class _CandidateInvalid(ValueError):
    pass


class _OracleFailed(RuntimeError):
    def __init__(self, stdout: bytes = b"") -> None:
        super().__init__("oracle_failed")
        self.stdout = stdout


@dataclass(frozen=True, slots=True)
class SyntheticVerificationResultV1:
    status: str
    reason_code: str
    source_sha256: str
    patched_sha256: str | None
    oracle_output_sha256: str | None
    public_case_count: int
    hidden_case_count: int
    source_write_count: int
    network_call_count: int
    child_process_count: int
    fixture_cleanup_count: int


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_candidate(candidate: object) -> CandidateArtifactV1:
    if type(candidate) is not CandidateArtifactV1:
        raise _CandidateInvalid
    if (
        candidate.artifact_version != "g2-a0-candidate-v1"
        or candidate.claimed_test_scope != ("public_behavior",)
        or candidate.language != "python"
        or candidate.summary_code != "bounded_repair"
    ):
        raise _CandidateInvalid
    return candidate


def _parse_count(value: str | None) -> int:
    try:
        return 1 if value is None else int(value)
    except ValueError as error:
        raise _CandidateInvalid from error


def _apply_unified_diff(source_bytes: bytes, unified_diff: str) -> bytes:
    if not isinstance(unified_diff, str) or not unified_diff.endswith("\n"):
        raise _CandidateInvalid
    try:
        diff_bytes = unified_diff.encode("utf-8")
    except UnicodeEncodeError as error:
        raise _CandidateInvalid from error
    if len(diff_bytes) > _DIFF_BYTES_LIMIT or "\r" in unified_diff:
        raise _CandidateInvalid
    lowered = unified_diff.lower()
    if any(marker in lowered for marker in _FORBIDDEN_DIFF_MARKERS):
        raise _CandidateInvalid

    lines = unified_diff.splitlines(keepends=True)
    if len(lines) < 4:
        raise _CandidateInvalid
    if lines[:2] != ["--- a/synthetic_target.py\n", "+++ b/synthetic_target.py\n"]:
        raise _CandidateInvalid
    match = _HUNK_RE.fullmatch(lines[2])
    if match is None:
        raise _CandidateInvalid
    if _parse_count(match["old_start"]) != 1 or _parse_count(match["new_start"]) != 1:
        raise _CandidateInvalid

    old_count = _parse_count(match["old_count"])
    new_count = _parse_count(match["new_count"])
    source_lines = source_bytes.decode("utf-8").splitlines(keepends=True)
    output: list[str] = []
    old_cursor = 0
    old_seen = 0
    new_seen = 0
    removed = 0
    added = 0

    for line in lines[3:]:
        prefix = line[:1]
        content = line[1:]
        if prefix == " ":
            if old_cursor >= len(source_lines) or source_lines[old_cursor] != content:
                raise _CandidateInvalid
            output.append(content)
            old_cursor += 1
            old_seen += 1
            new_seen += 1
        elif prefix == "-":
            if old_cursor >= len(source_lines) or source_lines[old_cursor] != content:
                raise _CandidateInvalid
            old_cursor += 1
            old_seen += 1
            removed += 1
        elif prefix == "+":
            output.append(content)
            new_seen += 1
            added += 1
        else:
            raise _CandidateInvalid

    if (
        old_seen != old_count
        or new_seen != new_count
        or old_cursor != len(source_lines)
        or removed == 0
        or added == 0
    ):
        raise _CandidateInvalid
    patched = "".join(output).encode("utf-8")
    if not patched.endswith(b"\n") or len(patched) > _PATCHED_BYTES_LIMIT:
        raise _CandidateInvalid
    return patched


def _validate_repaired_source(patched_bytes: bytes) -> None:
    try:
        source = patched_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _CandidateInvalid from error
    lowered = source.lower()
    if any(marker in lowered for marker in _FORBIDDEN_SOURCE_MARKERS):
        raise _CandidateInvalid
    try:
        tree = ast.parse(source, filename="synthetic_target.py", mode="exec")
    except SyntaxError as error:
        raise _CandidateInvalid from error
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise _CandidateInvalid
    function = tree.body[0]
    if (
        function.name != "clamp_score"
        or function.decorator_list
        or function.returns is not None
        or [argument.arg for argument in function.args.args] != ["value"]
        or function.args.posonlyargs
        or function.args.kwonlyargs
        or function.args.vararg is not None
        or function.args.kwarg is not None
        or function.args.defaults
        or function.args.kw_defaults
    ):
        raise _CandidateInvalid

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_AST_NODES):
            raise _CandidateInvalid
        if isinstance(node, ast.Name) and node.id not in _ALLOWED_NAMES:
            raise _CandidateInvalid
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name)
            or node.func.id not in _ALLOWED_CALLS
            or node.keywords
        ):
            raise _CandidateInvalid
        if isinstance(node, ast.Constant):
            if type(node.value) not in {int, str}:
                raise _CandidateInvalid
            if type(node.value) is int and node.value not in {0, 100}:
                raise _CandidateInvalid
            if type(node.value) is str and node.value != "value must be an integer":
                raise _CandidateInvalid

    bool_guard = False
    integer_guard = False
    for statement in function.body:
        if not _raises_type_error(statement):
            continue
        bool_guard = bool_guard or any(
            _is_isinstance_call(node, "bool") for node in ast.walk(statement.test)
        )
        integer_guard = integer_guard or any(
            _is_negated_isinstance_call(node, "int")
            for node in ast.walk(statement.test)
        )
    if not bool_guard or not integer_guard:
        raise _CandidateInvalid


def _is_isinstance_call(node: ast.AST, expected_type: str) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "isinstance"
        and not node.keywords
        and len(node.args) == 2
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "value"
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == expected_type
    )


def _is_negated_isinstance_call(node: ast.AST, expected_type: str) -> bool:
    return (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.Not)
        and _is_isinstance_call(node.operand, expected_type)
    )


def _raises_type_error(statement: ast.stmt) -> bool:
    if (
        not isinstance(statement, ast.If)
        or statement.orelse
        or len(statement.body) != 1
    ):
        return False
    raised = statement.body[0]
    return (
        isinstance(raised, ast.Raise)
        and isinstance(raised.exc, ast.Call)
        and isinstance(raised.exc.func, ast.Name)
        and raised.exc.func.id == "TypeError"
    )


def _child_environment() -> dict[str, str]:
    if sys.platform != "win32":
        return {}
    windows_root = str(Path(Path(sys.executable).anchor) / "Windows")
    return {"SYSTEMROOT": windows_root, "WINDIR": windows_root}


def _validated_temp_root(temp_root: object) -> Path:
    if (
        not isinstance(temp_root, Path)
        or not temp_root.is_dir()
        or temp_root.is_symlink()
    ):
        raise ValueError("invalid_temp_root")
    try:
        resolved = temp_root.resolve(strict=True)
        system_temp = Path(tempfile.gettempdir()).resolve(strict=True)
    except OSError as error:
        raise ValueError("invalid_temp_root") from error
    if (
        system_temp not in resolved.parents
        or resolved == _SOURCE_TREE_ROOT
        or _SOURCE_TREE_ROOT in resolved.parents
    ):
        raise ValueError("invalid_temp_root")
    return resolved


def _run_oracle(target: Path, workspace: Path) -> tuple[bytes, bool, bool]:
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-S", "-c", _ORACLE_SCRIPT, str(target)],
            cwd=workspace,
            env=_child_environment(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise _OracleFailed from error
    if completed.returncode != 0 or len(completed.stdout) > 1_024:
        raise _OracleFailed(completed.stdout)
    try:
        document = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _OracleFailed(completed.stdout) from error
    if not isinstance(document, dict) or set(document) != {
        "hidden_passed",
        "public_passed",
        "status",
    }:
        raise _OracleFailed(completed.stdout)
    public_passed = document["public_passed"]
    hidden_passed = document["hidden_passed"]
    expected_status = (
        "passed" if public_passed is True and hidden_passed is True else "rejected"
    )
    if (
        type(public_passed) is not bool
        or type(hidden_passed) is not bool
        or document["status"] != expected_status
    ):
        raise _OracleFailed(completed.stdout)
    return completed.stdout, public_passed, hidden_passed


def verify_candidate_patch(
    *,
    fixture: SyntheticRepairFixtureV1,
    candidate: CandidateArtifactV1,
    temp_root: Path,
) -> SyntheticVerificationResultV1:
    if (
        type(fixture) is not SyntheticRepairFixtureV1
        or fixture != SyntheticRepairFixtureV1.default()
    ):
        raise ValueError("invalid_fixture")
    approved_temp_root = _validated_temp_root(temp_root)

    source_hash = _sha256(fixture.source_bytes)
    patched_hash: str | None = None
    oracle_hash: str | None = None
    public_count = 0
    hidden_count = 0
    child_count = 0
    status = "rejected"
    reason_code = "candidate_invalid"
    workspace = Path(tempfile.mkdtemp(prefix="g2_a0_verify_", dir=approved_temp_root))

    try:
        target = workspace / fixture.target_relative_path
        target.write_bytes(fixture.source_bytes)
        approved_candidate = _validate_candidate(candidate)
        patched = _apply_unified_diff(
            fixture.source_bytes,
            approved_candidate.unified_diff,
        )
        _validate_repaired_source(patched)
        target.write_bytes(patched)
        patched_hash = _sha256(patched)
        child_count = 1
        oracle_output, public_passed, hidden_passed = _run_oracle(target, workspace)
        oracle_hash = _sha256(oracle_output)
        public_count = fixture.public_case_count if public_passed else 0
        hidden_count = fixture.hidden_case_count if hidden_passed else 0
        if public_passed and hidden_passed:
            status = "passed"
            reason_code = "verified"
        else:
            reason_code = "oracle_failed"
    except _CandidateInvalid:
        reason_code = "candidate_invalid"
    except _OracleFailed as error:
        reason_code = "oracle_failed"
        if error.stdout:
            oracle_hash = _sha256(error.stdout)
    except OSError:
        reason_code = "verifier_failed"
    finally:
        try:
            shutil.rmtree(workspace)
        except OSError:
            pass

    cleanup_count = int(not workspace.exists())
    if cleanup_count != 1:
        status = "rejected"
        reason_code = "cleanup_failed"
    return SyntheticVerificationResultV1(
        status=status,
        reason_code=reason_code,
        source_sha256=source_hash,
        patched_sha256=patched_hash,
        oracle_output_sha256=oracle_hash,
        public_case_count=public_count,
        hidden_case_count=hidden_count,
        source_write_count=0,
        network_call_count=0,
        child_process_count=child_count,
        fixture_cleanup_count=cleanup_count,
    )
