from __future__ import annotations

import dataclasses
import socket
import subprocess
from pathlib import Path
from typing import Callable

import g2_a0_synthetic_verifier as verifier_module
import pytest
from g2_a0_deepseek_client import CandidateArtifactV1
from g2_a0_synthetic_fixture import SyntheticRepairFixtureV1
from g2_a0_synthetic_verifier import (
    SyntheticVerificationResultV1,
    verify_candidate_patch,
)

VALID_PATCH = """--- a/synthetic_target.py
+++ b/synthetic_target.py
@@ -1,2 +1,4 @@
 def clamp_score(value):
-    return max(0, value)
+    if isinstance(value, bool) or not isinstance(value, int):
+        raise TypeError("value must be an integer")
+    return max(0, min(100, value))
"""

HIDDEN_FAILURE_PATCH = """--- a/synthetic_target.py
+++ b/synthetic_target.py
@@ -1,2 +1,6 @@
 def clamp_score(value):
-    return max(0, value)
+    if isinstance(value, bool) or not isinstance(value, int):
+        raise TypeError("value must be an integer")
+    if value == 100:
+        return 0
+    return max(0, min(100, value))
"""

FLOAT_ACCEPTING_PATCH = """--- a/synthetic_target.py
+++ b/synthetic_target.py
@@ -1,2 +1,4 @@
 def clamp_score(value):
-    return max(0, value)
+    if isinstance(value, bool):
+        raise TypeError("value must be an integer")
+    return max(0, min(100, value))
"""


def candidate(
    unified_diff: str = VALID_PATCH, **overrides: object
) -> CandidateArtifactV1:
    values: dict[str, object] = {
        "artifact_version": "g2-a0-candidate-v1",
        "claimed_test_scope": ("public_behavior",),
        "language": "python",
        "summary_code": "bounded_repair",
        "unified_diff": unified_diff,
    }
    values.update(overrides)
    return CandidateArtifactV1(**values)


def single_line_patch(replacement: str) -> str:
    return f"""--- a/synthetic_target.py
+++ b/synthetic_target.py
@@ -1,2 +1,2 @@
 def clamp_score(value):
-    return max(0, value)
+    {replacement}
"""


def assert_cleaned(temp_root: Path) -> None:
    assert list(temp_root.iterdir()) == []


def test_fixed_fixture_is_immutable_bounded_and_contains_disjoint_oracles() -> None:
    fixture = SyntheticRepairFixtureV1.default()

    assert dataclasses.fields(fixture)
    assert fixture.fixture_version == "g2-a0-synthetic-repair-v1"
    assert fixture.target_relative_path == "synthetic_target.py"
    assert fixture.public_example == "clamp_score(120) == 100"
    assert "integer" in fixture.public_prompt
    assert "0 through 100" in fixture.public_prompt
    assert fixture.source_bytes == (
        b"def clamp_score(value):\n    return max(0, value)\n"
    )
    assert fixture.public_case_count == 3
    assert fixture.hidden_case_count == 10
    with pytest.raises(dataclasses.FrozenInstanceError):
        fixture.target_relative_path = "other.py"


def test_valid_patch_runs_fixed_hidden_oracle_without_network_or_source_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    real_run = subprocess.run

    def guarded_run(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        calls.append((args, kwargs))
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        assert not any(
            "KEY" in key.upper() or "PROXY" in key.upper() for key in environment
        )
        assert kwargs.get("shell", False) is False
        return real_run(*args, **kwargs)

    def deny_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("network is prohibited")

    monkeypatch.setattr(verifier_module.subprocess, "run", guarded_run)
    monkeypatch.setattr(socket, "socket", deny_socket)
    protected_source = Path(__file__)
    before = protected_source.read_bytes()

    result = verify_candidate_patch(
        fixture=SyntheticRepairFixtureV1.default(),
        candidate=candidate(),
        temp_root=tmp_path,
    )

    assert result.status == "passed"
    assert result.reason_code == "verified"
    assert result.public_case_count == 3
    assert result.hidden_case_count == 10
    assert result.source_write_count == 0
    assert result.network_call_count == 0
    assert result.fixture_cleanup_count == 1
    assert result.source_sha256 != result.patched_sha256
    assert len(result.source_sha256) == 64
    assert len(result.patched_sha256) == 64
    assert result.oracle_output_sha256 is not None
    assert len(result.oracle_output_sha256) == 64
    assert result.child_process_count == 1
    assert len(calls) == 1
    assert protected_source.read_bytes() == before
    assert_cleaned(tmp_path)


def test_result_contains_only_fixed_statuses_hashes_and_counts(tmp_path: Path) -> None:
    result = verify_candidate_patch(
        fixture=SyntheticRepairFixtureV1.default(),
        candidate=candidate(),
        temp_root=tmp_path,
    )

    assert isinstance(result, SyntheticVerificationResultV1)
    assert {field.name for field in dataclasses.fields(result)} == {
        "child_process_count",
        "fixture_cleanup_count",
        "hidden_case_count",
        "network_call_count",
        "oracle_output_sha256",
        "patched_sha256",
        "public_case_count",
        "reason_code",
        "source_sha256",
        "source_write_count",
        "status",
    }
    serialized = dataclasses.asdict(result)
    assert not {
        "path",
        "prompt",
        "reasoning",
        "response",
        "unified_diff",
    }.intersection(serialized)
    assert_cleaned(tmp_path)


@pytest.mark.parametrize(
    ("case", "unified_diff"),
    (
        ("markdown", f"```diff\n{VALID_PATCH}```\n"),
        ("prose", f"Apply this repair:\n{VALID_PATCH}"),
        (
            "absolute",
            VALID_PATCH.replace("a/synthetic_target.py", "C:/synthetic_target.py"),
        ),
        (
            "unc",
            VALID_PATCH.replace("a/synthetic_target.py", "//server/share/target.py"),
        ),
        (
            "device",
            VALID_PATCH.replace("a/synthetic_target.py", r"\\?\C:\target.py"),
        ),
        (
            "traversal",
            VALID_PATCH.replace("a/synthetic_target.py", "a/../target.py"),
        ),
        ("nul", f"{VALID_PATCH}\x00"),
        (
            "multiple_files",
            f"{VALID_PATCH}{VALID_PATCH.replace('synthetic_target', 'other')}",
        ),
        ("delete", VALID_PATCH.replace("+++ b/synthetic_target.py", "+++ /dev/null")),
        ("create", VALID_PATCH.replace("--- a/synthetic_target.py", "--- /dev/null")),
        ("binary", f"GIT binary patch\n{VALID_PATCH}"),
        ("mode", f"old mode 100644\nnew mode 100755\n{VALID_PATCH}"),
        ("rename", f"rename from a.py\nrename to b.py\n{VALID_PATCH}"),
        ("oversized", f"{VALID_PATCH}{'#' * 65_536}"),
        (
            "huge_hunk_count",
            VALID_PATCH.replace("@@ -1,2 +1,4 @@", f"@@ -1,{'9' * 5_000} +1,4 @@"),
        ),
        (
            "huge_hunk_start",
            VALID_PATCH.replace("@@ -1,2 +1,4 @@", f"@@ -{'9' * 5_000},2 +1,4 @@"),
        ),
        ("malformed_hunk", VALID_PATCH.replace("@@ -1,2 +1,4 @@", "@@ -1,99 +1,4 @@")),
        ("command", single_line_patch('return __import__("os").system("echo x")')),
        ("url", single_line_patch('return "https://prohibited.invalid"')),
        ("environment", single_line_patch('return __import__("os").environ')),
        ("subprocess", single_line_patch('return __import__("subprocess").run([])')),
        ("network", single_line_patch('return __import__("socket").socket()')),
        ("source_write", single_line_patch('return open("outside", "w")')),
        ("recursive", single_line_patch("return clamp_score(value)")),
    ),
    ids=lambda value: (
        value
        if isinstance(value, str) and "\n" not in value and len(value) < 32
        else "patch"
    ),
)
def test_untrusted_patch_shapes_fail_closed_and_cleanup(
    case: str,
    unified_diff: str,
    tmp_path: Path,
) -> None:
    result = verify_candidate_patch(
        fixture=SyntheticRepairFixtureV1.default(),
        candidate=candidate(unified_diff),
        temp_root=tmp_path,
    )

    assert result.status == "rejected", case
    assert result.reason_code == "candidate_invalid", case
    assert result.source_write_count == 0
    assert result.network_call_count == 0
    assert result.fixture_cleanup_count == 1
    assert result.child_process_count == 0
    assert_cleaned(tmp_path)


@pytest.mark.parametrize(
    "overrides",
    (
        {"artifact_version": "other"},
        {"claimed_test_scope": ()},
        {"claimed_test_scope": ("public_behavior", "hidden_behavior")},
        {"language": "javascript"},
        {"summary_code": "other"},
    ),
)
def test_candidate_contract_widening_fails_before_child_process(
    overrides: dict[str, object],
    tmp_path: Path,
) -> None:
    result = verify_candidate_patch(
        fixture=SyntheticRepairFixtureV1.default(),
        candidate=candidate(**overrides),
        temp_root=tmp_path,
    )

    assert result.status == "rejected"
    assert result.reason_code == "candidate_invalid"
    assert result.child_process_count == 0
    assert result.fixture_cleanup_count == 1
    assert_cleaned(tmp_path)


def test_plausible_public_patch_that_fails_hidden_boundary_is_rejected(
    tmp_path: Path,
) -> None:
    result = verify_candidate_patch(
        fixture=SyntheticRepairFixtureV1.default(),
        candidate=candidate(HIDDEN_FAILURE_PATCH),
        temp_root=tmp_path,
    )

    assert result.status == "rejected"
    assert result.reason_code == "oracle_failed"
    assert result.public_case_count == 3
    assert result.hidden_case_count == 0
    assert result.child_process_count == 1
    assert result.fixture_cleanup_count == 1
    assert_cleaned(tmp_path)


def test_float_accepting_patch_is_rejected_before_execution(tmp_path: Path) -> None:
    result = verify_candidate_patch(
        fixture=SyntheticRepairFixtureV1.default(),
        candidate=candidate(FLOAT_ACCEPTING_PATCH),
        temp_root=tmp_path,
    )

    assert result.status == "rejected"
    assert result.reason_code == "candidate_invalid"
    assert result.child_process_count == 0
    assert result.fixture_cleanup_count == 1
    assert_cleaned(tmp_path)


def test_timeout_is_fixed_redacted_and_cleanup_is_mandatory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd="prohibited-raw-command", timeout=2)

    monkeypatch.setattr(verifier_module.subprocess, "run", timeout)

    result = verify_candidate_patch(
        fixture=SyntheticRepairFixtureV1.default(),
        candidate=candidate(),
        temp_root=tmp_path,
    )

    assert result.status == "rejected"
    assert result.reason_code == "oracle_failed"
    assert result.child_process_count == 1
    assert result.fixture_cleanup_count == 1
    assert "prohibited" not in repr(result)
    assert_cleaned(tmp_path)


def test_temp_root_must_be_an_existing_real_directory(tmp_path: Path) -> None:
    bad_roots = (tmp_path / "missing", tmp_path / "file")
    bad_roots[1].write_text("not-a-directory", encoding="utf-8")

    for bad_root in bad_roots:
        with pytest.raises(ValueError, match="invalid_temp_root"):
            verify_candidate_patch(
                fixture=SyntheticRepairFixtureV1.default(),
                candidate=candidate(),
                temp_root=bad_root,
            )


def test_source_tree_cannot_be_selected_as_temp_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def deny_workspace_creation(*args: object, **kwargs: object) -> str:
        raise AssertionError("workspace creation must not be reached")

    monkeypatch.setattr(verifier_module.tempfile, "mkdtemp", deny_workspace_creation)
    monkeypatch.setattr(
        verifier_module.tempfile,
        "tempdir",
        str(Path(__file__).resolve().parents[4]),
    )

    with pytest.raises(ValueError, match="invalid_temp_root"):
        verify_candidate_patch(
            fixture=SyntheticRepairFixtureV1.default(),
            candidate=candidate(),
            temp_root=Path(__file__).parent,
        )


def test_oracle_invocation_is_fixed_and_not_candidate_selected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[tuple[object, ...]] = []
    real_run: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run

    def inspect_run(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        command = args[0]
        assert isinstance(command, list)
        observed.append(tuple(command[:5]))
        assert command[1:4] == ["-I", "-S", "-c"]
        assert kwargs["timeout"] == 2
        assert kwargs["check"] is False
        return real_run(*args, **kwargs)

    monkeypatch.setattr(verifier_module.subprocess, "run", inspect_run)

    result = verify_candidate_patch(
        fixture=SyntheticRepairFixtureV1.default(),
        candidate=candidate(),
        temp_root=tmp_path,
    )

    assert result.status == "passed"
    assert len(observed) == 1
    assert_cleaned(tmp_path)
