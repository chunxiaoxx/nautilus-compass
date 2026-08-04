"""Atomic dual-slot runtime state for immutable Compass wheel releases."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import venv
import zipfile
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Dict, Optional, Tuple

from release_manifest import ReleaseManifest, ReleaseManifestError


POINTER_SCHEMA_VERSION = "compass.runtime.pointer.v1"
RECEIPT_SCHEMA_VERSION = "compass.runtime.receipt.v1"
SLOT_SCHEMA_VERSION = "compass.runtime.slot.v1"

_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_RELEASE_ID_PATTERN = re.compile(
    r"compass-[A-Za-z0-9][A-Za-z0-9._+-]*-[0-9a-f]{12}-[0-9a-f]{12}"
)
_UTC_RFC3339_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z"
)
_POINTER_KEYS = frozenset(
    {"schema_version", "active_slot", "release_id", "manifest_sha256", "generation"}
)
_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "operation",
        "release_id",
        "manifest_sha256",
        "previous_release_id",
        "generation",
        "status",
        "reason_code",
        "created_at",
    }
)
_SLOT_KEYS = frozenset(
    {
        "schema_version",
        "release_id",
        "manifest_sha256",
        "wheel_sha256",
        "wheel_filename",
        "python_executable",
        "status",
    }
)
_OPERATIONS = frozenset({"stage", "activate", "rollback", "blocked"})
_STATUSES = frozenset({"verified", "active", "rolled_back", "blocked"})
_PROCESS_LOCKS: Dict[str, threading.Lock] = {}
_PROCESS_LOCKS_GUARD = threading.Lock()

Installer = Callable[[Path, Path], Path]


class RuntimeReleaseError(ValueError):
    """Fail-closed runtime transition error with a stable reason code."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


def _canonical_bytes(mapping: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(mapping, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        + b"\n"
    )


def _load_json_mapping(path: Path, reason_code: str) -> Mapping[str, Any]:
    try:
        raw = path.read_bytes()
        mapping = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeReleaseError(reason_code) from exc
    if not isinstance(mapping, Mapping):
        raise RuntimeReleaseError(reason_code)
    return mapping


def _validate_hash(value: Any, reason_code: str) -> str:
    if not isinstance(value, str) or _HASH_PATTERN.fullmatch(value) is None:
        raise RuntimeReleaseError(reason_code)
    return value


def _validate_release_id(value: Any, reason_code: str) -> str:
    if not isinstance(value, str) or _RELEASE_ID_PATTERN.fullmatch(value) is None:
        raise RuntimeReleaseError(reason_code)
    return value


def _validate_timestamp(value: Any) -> str:
    if not isinstance(value, str) or _UTC_RFC3339_PATTERN.fullmatch(value) is None:
        raise RuntimeReleaseError("invalid_timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RuntimeReleaseError("invalid_timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise RuntimeReleaseError("invalid_timestamp")
    return value


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise RuntimeReleaseError("artifact_unreadable") from exc
    return "sha256:" + digest.hexdigest()


def _atomic_write(path: Path, encoded: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + os.urandom(8).hex())
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _safe_remove_tree(path: Path, parent: Path) -> None:
    resolved_path = path.resolve()
    resolved_parent = parent.resolve()
    try:
        resolved_path.relative_to(resolved_parent)
    except ValueError as exc:
        raise RuntimeReleaseError("unsafe_cleanup_path") from exc
    if resolved_path != resolved_parent and resolved_path.exists():
        shutil.rmtree(resolved_path)


def _process_lock(path: Path) -> threading.Lock:
    key = os.path.normcase(os.path.abspath(str(path)))
    with _PROCESS_LOCKS_GUARD:
        return _PROCESS_LOCKS.setdefault(key, threading.Lock())


@contextmanager
def _transition_lock(runtime_root: Path, timeout_seconds: float = 10.0):
    root = Path(runtime_root)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".transition.lock"
    local_lock = _process_lock(lock_path)
    if not local_lock.acquire(timeout=timeout_seconds):
        raise RuntimeReleaseError("transition_lock_timeout")
    handle = None
    locked = False
    try:
        handle = lock_path.open("a+b")
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise RuntimeReleaseError("transition_lock_timeout") from exc
                time.sleep(0.01)
        yield
    finally:
        if handle is not None and locked:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        if handle is not None:
            handle.close()
        local_lock.release()


@dataclass(frozen=True)
class RuntimePointer:
    schema_version: str
    active_slot: str
    release_id: str
    manifest_sha256: str
    generation: int

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "RuntimePointer":
        if not isinstance(mapping, Mapping) or set(mapping) != _POINTER_KEYS:
            raise RuntimeReleaseError("invalid_pointer_keys")
        if mapping["schema_version"] != POINTER_SCHEMA_VERSION:
            raise RuntimeReleaseError("invalid_pointer")
        slot = mapping["active_slot"]
        generation = mapping["generation"]
        if slot not in ("a", "b"):
            raise RuntimeReleaseError("invalid_pointer")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
            raise RuntimeReleaseError("invalid_pointer")
        return cls(
            schema_version=POINTER_SCHEMA_VERSION,
            active_slot=slot,
            release_id=_validate_release_id(mapping["release_id"], "invalid_pointer"),
            manifest_sha256=_validate_hash(
                mapping["manifest_sha256"], "invalid_pointer"
            ),
            generation=generation,
        )

    def to_mapping(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "active_slot": self.active_slot,
            "release_id": self.release_id,
            "manifest_sha256": self.manifest_sha256,
            "generation": self.generation,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_mapping())


@dataclass(frozen=True)
class RuntimeReceipt:
    schema_version: str
    operation: str
    release_id: str
    manifest_sha256: str
    previous_release_id: Optional[str]
    generation: int
    status: str
    reason_code: str
    created_at: str

    def __post_init__(self) -> None:
        if self.schema_version != RECEIPT_SCHEMA_VERSION:
            raise RuntimeReleaseError("invalid_receipt")
        if self.operation not in _OPERATIONS or self.status not in _STATUSES:
            raise RuntimeReleaseError("invalid_receipt")
        _validate_release_id(self.release_id, "invalid_receipt")
        _validate_hash(self.manifest_sha256, "invalid_receipt")
        if self.previous_release_id is not None:
            _validate_release_id(self.previous_release_id, "invalid_receipt")
        if isinstance(self.generation, bool) or self.generation < 0:
            raise RuntimeReleaseError("invalid_receipt")
        if not isinstance(self.reason_code, str) or not re.fullmatch(
            r"[a-z][a-z0-9_]{0,63}", self.reason_code
        ):
            raise RuntimeReleaseError("invalid_receipt")
        _validate_timestamp(self.created_at)

    def to_mapping(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "release_id": self.release_id,
            "manifest_sha256": self.manifest_sha256,
            "previous_release_id": self.previous_release_id,
            "generation": self.generation,
            "status": self.status,
            "reason_code": self.reason_code,
            "created_at": self.created_at,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_mapping())


@dataclass(frozen=True)
class SlotRecord:
    schema_version: str
    release_id: str
    manifest_sha256: str
    wheel_sha256: str
    wheel_filename: str
    python_executable: str
    status: str

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "SlotRecord":
        if not isinstance(mapping, Mapping) or set(mapping) != _SLOT_KEYS:
            raise RuntimeReleaseError("invalid_slot_record_keys")
        string_values = tuple(mapping[key] for key in _SLOT_KEYS if key != "schema_version")
        if any(not isinstance(value, str) for value in string_values):
            raise RuntimeReleaseError("invalid_slot_record")
        if mapping["schema_version"] != SLOT_SCHEMA_VERSION or mapping["status"] != "verified":
            raise RuntimeReleaseError("invalid_slot_record")
        _validate_release_id(mapping["release_id"], "invalid_slot_record")
        _validate_hash(mapping["manifest_sha256"], "invalid_slot_record")
        _validate_hash(mapping["wheel_sha256"], "invalid_slot_record")
        wheel_name = mapping["wheel_filename"]
        if "/" in wheel_name or "\\" in wheel_name or not wheel_name.endswith(".whl"):
            raise RuntimeReleaseError("invalid_slot_record")
        relative = PurePosixPath(mapping["python_executable"])
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise RuntimeReleaseError("invalid_slot_record")
        return cls(
            schema_version=SLOT_SCHEMA_VERSION,
            release_id=mapping["release_id"],
            manifest_sha256=mapping["manifest_sha256"],
            wheel_sha256=mapping["wheel_sha256"],
            wheel_filename=wheel_name,
            python_executable=mapping["python_executable"],
            status="verified",
        )

    def to_mapping(self) -> Dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "release_id": self.release_id,
            "manifest_sha256": self.manifest_sha256,
            "wheel_sha256": self.wheel_sha256,
            "wheel_filename": self.wheel_filename,
            "python_executable": self.python_executable,
            "status": self.status,
        }


@dataclass(frozen=True)
class SlotBinding:
    slot: str
    release_id: str
    manifest_sha256: str
    path: Path
    python_executable: Path
    wheel_path: Path


@dataclass(frozen=True)
class StagedRelease:
    slot: str
    release_id: str
    manifest_sha256: str
    path: Path
    idempotent: bool = False

    def as_idempotent(self) -> "StagedRelease":
        return replace(self, idempotent=True)


def load_pointer(runtime_root: Path, name: str = "current.json") -> Optional[RuntimePointer]:
    path = Path(runtime_root) / name
    if not path.exists():
        return None
    return RuntimePointer.from_mapping(_load_json_mapping(path, "invalid_pointer"))


def _write_receipt(runtime_root: Path, receipt: RuntimeReceipt) -> Path:
    encoded = receipt.canonical_bytes()
    digest = hashlib.sha256(encoded).hexdigest()[:12]
    compact_time = re.sub(r"[^0-9]", "", receipt.created_at)[:14]
    filename = "{:08d}-{}-{}-{}.json".format(
        receipt.generation, compact_time, receipt.operation, digest
    )
    path = Path(runtime_root) / "receipts" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        if path.read_bytes() != encoded:
            raise RuntimeReleaseError("receipt_conflict")
    return path


def _slot_path(runtime_root: Path, slot: str, release_id: str) -> Path:
    if slot not in ("a", "b"):
        raise RuntimeReleaseError("invalid_slot")
    _validate_release_id(release_id, "invalid_release_id")
    return Path(runtime_root) / "slots" / slot / release_id


def _load_candidate(manifest_path: Path, wheel_path: Path) -> Tuple[ReleaseManifest, bytes, str]:
    try:
        manifest_bytes = Path(manifest_path).read_bytes()
        manifest = ReleaseManifest.from_json_bytes(manifest_bytes)
    except (OSError, ReleaseManifestError) as exc:
        raise RuntimeReleaseError("manifest_invalid") from exc
    if manifest_bytes != manifest.canonical_bytes():
        raise RuntimeReleaseError("manifest_not_canonical")
    wheel = Path(wheel_path)
    if wheel.name != manifest.wheel_filename:
        raise RuntimeReleaseError("wheel_filename_mismatch")
    wheel_hash = _sha256_file(wheel)
    if wheel_hash != manifest.wheel_sha256:
        raise RuntimeReleaseError("wheel_hash_mismatch")
    return manifest, manifest_bytes, _sha256_bytes(manifest_bytes)


def _default_installer(stage_dir: Path, wheel_path: Path) -> Path:
    venv_path = stage_dir / "venv"
    try:
        venv.EnvBuilder(with_pip=True, clear=False).create(venv_path)
        if os.name == "nt":
            python = venv_path / "Scripts" / "python.exe"
        else:
            python = venv_path / "bin" / "python"
        completed = subprocess.run(
            [str(python), "-m", "pip", "install", "--no-deps", str(wheel_path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeReleaseError("installer_failed") from exc
    if completed.returncode != 0:
        raise RuntimeReleaseError("installer_failed")
    return python


def _site_packages_for_python(python_executable: Path) -> Path:
    venv_root = python_executable.parent.parent
    windows_path = venv_root / "Lib" / "site-packages"
    if windows_path.is_dir():
        return windows_path
    candidates = tuple(sorted((venv_root / "lib").glob("python*/site-packages")))
    if len(candidates) != 1 or not candidates[0].is_dir():
        raise RuntimeReleaseError("slot_install_missing")
    return candidates[0]


def _verify_installed_wheel(wheel_path: Path, python_executable: Path) -> None:
    site_packages = _site_packages_for_python(python_executable)
    verified_runtime_member = False
    try:
        with zipfile.ZipFile(wheel_path) as archive:
            for member in archive.infolist():
                normalized = PurePosixPath(member.filename.replace("\\", "/"))
                if normalized.is_absolute() or ".." in normalized.parts:
                    raise RuntimeReleaseError("slot_install_mismatch")
                if member.is_dir() or member.filename.endswith(".dist-info/RECORD"):
                    continue
                if ".data" in normalized.parts:
                    raise RuntimeReleaseError("slot_install_layout_unsupported")
                installed_path = site_packages.joinpath(*normalized.parts)
                try:
                    installed_bytes = installed_path.read_bytes()
                    wheel_bytes = archive.read(member)
                except (KeyError, OSError) as exc:
                    raise RuntimeReleaseError("slot_install_mismatch") from exc
                if installed_bytes != wheel_bytes:
                    raise RuntimeReleaseError("slot_install_mismatch")
                if normalized.parts and normalized.parts[0] == "nautilus_compass":
                    verified_runtime_member = True
    except zipfile.BadZipFile as exc:
        raise RuntimeReleaseError("slot_wheel_invalid") from exc
    if not verified_runtime_member:
        raise RuntimeReleaseError("slot_install_mismatch")


def _stage_record(
    stage_dir: Path,
    manifest: ReleaseManifest,
    manifest_hash: str,
    python_executable: Path,
) -> SlotRecord:
    try:
        relative_python = python_executable.resolve().relative_to(stage_dir.resolve())
    except (OSError, ValueError) as exc:
        raise RuntimeReleaseError("installer_invalid_output") from exc
    if not python_executable.is_file():
        raise RuntimeReleaseError("installer_invalid_output")
    return SlotRecord(
        schema_version=SLOT_SCHEMA_VERSION,
        release_id=manifest.release_id,
        manifest_sha256=manifest_hash,
        wheel_sha256=manifest.wheel_sha256,
        wheel_filename=manifest.wheel_filename,
        python_executable=relative_python.as_posix(),
        status="verified",
    )


def verify_slot(runtime_root: Path, slot: str, release_id: str) -> SlotBinding:
    path = _slot_path(runtime_root, slot, release_id)
    record = SlotRecord.from_mapping(
        _load_json_mapping(path / "slot.json", "invalid_slot_record")
    )
    if record.release_id != release_id:
        raise RuntimeReleaseError("slot_release_mismatch")
    try:
        manifest_bytes = (path / "release-manifest.json").read_bytes()
        manifest = ReleaseManifest.from_json_bytes(manifest_bytes)
    except (OSError, ReleaseManifestError) as exc:
        raise RuntimeReleaseError("slot_manifest_invalid") from exc
    if manifest_bytes != manifest.canonical_bytes():
        raise RuntimeReleaseError("slot_manifest_mismatch")
    if _sha256_bytes(manifest_bytes) != record.manifest_sha256:
        raise RuntimeReleaseError("slot_manifest_mismatch")
    if manifest.release_id != record.release_id:
        raise RuntimeReleaseError("slot_manifest_mismatch")
    wheel_path = path / record.wheel_filename
    if _sha256_file(wheel_path) != record.wheel_sha256:
        raise RuntimeReleaseError("slot_wheel_mismatch")
    python_executable = path / Path(record.python_executable)
    if not python_executable.is_file():
        raise RuntimeReleaseError("slot_python_missing")
    _verify_installed_wheel(wheel_path, python_executable)
    return SlotBinding(
        slot=slot,
        release_id=release_id,
        manifest_sha256=record.manifest_sha256,
        path=path,
        python_executable=python_executable,
        wheel_path=wheel_path,
    )


def _blocked_receipt(
    runtime_root: Path,
    manifest: ReleaseManifest,
    manifest_hash: str,
    current: Optional[RuntimePointer],
    created_at: str,
    reason_code: str,
) -> None:
    _write_receipt(
        runtime_root,
        RuntimeReceipt(
            schema_version=RECEIPT_SCHEMA_VERSION,
            operation="blocked",
            release_id=manifest.release_id,
            manifest_sha256=manifest_hash,
            previous_release_id=current.release_id if current else None,
            generation=current.generation if current else 0,
            status="blocked",
            reason_code=reason_code,
            created_at=created_at,
        ),
    )


def stage_release(
    runtime_root: Path,
    manifest_path: Path,
    wheel_path: Path,
    installer: Optional[Installer] = None,
    created_at: Optional[str] = None,
) -> StagedRelease:
    root = Path(runtime_root)
    timestamp = _validate_timestamp(created_at or _now())
    manifest, manifest_bytes, manifest_hash = _load_candidate(manifest_path, wheel_path)
    current = load_pointer(root)
    slot = "b" if current and current.active_slot == "a" else "a"
    final_path = _slot_path(root, slot, manifest.release_id)
    if final_path.exists():
        try:
            binding = verify_slot(root, slot, manifest.release_id)
        except RuntimeReleaseError as exc:
            raise RuntimeReleaseError("slot_conflict") from exc
        return StagedRelease(
            binding.slot,
            binding.release_id,
            binding.manifest_sha256,
            binding.path,
            True,
        )

    slot_parent = final_path.parent
    slot_parent.mkdir(parents=True, exist_ok=True)
    stage_path = Path(tempfile.mkdtemp(prefix=".stage-", dir=str(slot_parent)))
    install = installer or _default_installer
    try:
        staged_wheel = stage_path / manifest.wheel_filename
        shutil.copyfile(wheel_path, staged_wheel)
        if _sha256_file(staged_wheel) != manifest.wheel_sha256:
            raise RuntimeReleaseError("wheel_copy_mismatch")
        (stage_path / "release-manifest.json").write_bytes(manifest_bytes)
        try:
            python_executable = Path(install(stage_path, staged_wheel))
        except Exception as exc:
            _blocked_receipt(
                root, manifest, manifest_hash, current, timestamp, "installer_failed"
            )
            raise RuntimeReleaseError("installer_failed") from exc
        record = _stage_record(
            stage_path, manifest, manifest_hash, python_executable
        )
        (stage_path / "slot.json").write_bytes(_canonical_bytes(record.to_mapping()))
        os.replace(stage_path, final_path)
    finally:
        if stage_path.exists():
            _safe_remove_tree(stage_path, slot_parent)

    binding = verify_slot(root, slot, manifest.release_id)
    _write_receipt(
        root,
        RuntimeReceipt(
            schema_version=RECEIPT_SCHEMA_VERSION,
            operation="stage",
            release_id=manifest.release_id,
            manifest_sha256=manifest_hash,
            previous_release_id=current.release_id if current else None,
            generation=current.generation if current else 0,
            status="verified",
            reason_code="staged",
            created_at=timestamp,
        ),
    )
    return StagedRelease(
        binding.slot,
        binding.release_id,
        binding.manifest_sha256,
        binding.path,
        False,
    )


def _find_staged(runtime_root: Path, release_id: str) -> SlotBinding:
    matches = []
    for slot in ("a", "b"):
        if _slot_path(runtime_root, slot, release_id).exists():
            matches.append(verify_slot(runtime_root, slot, release_id))
    if len(matches) != 1:
        raise RuntimeReleaseError("staged_release_not_unique")
    return matches[0]


def _write_pointer(runtime_root: Path, pointer: RuntimePointer, name: str) -> None:
    _atomic_write(Path(runtime_root) / name, pointer.canonical_bytes())


def activate_release(
    runtime_root: Path,
    release_id: str,
    created_at: Optional[str] = None,
) -> RuntimePointer:
    root = Path(runtime_root)
    timestamp = _validate_timestamp(created_at or _now())
    with _transition_lock(root):
        return _activate_release_locked(root, release_id, timestamp)


def _activate_release_locked(
    root: Path,
    release_id: str,
    timestamp: str,
) -> RuntimePointer:
    current = load_pointer(root)
    if current and current.release_id == release_id:
        binding = verify_slot(root, current.active_slot, release_id)
        if binding.manifest_sha256 != current.manifest_sha256:
            raise RuntimeReleaseError("active_pointer_mismatch")
        return current
    binding = _find_staged(root, release_id)
    if current and binding.slot == current.active_slot:
        raise RuntimeReleaseError("candidate_in_active_slot")
    if current:
        _write_pointer(root, current, "previous.json")
    pointer = RuntimePointer(
        schema_version=POINTER_SCHEMA_VERSION,
        active_slot=binding.slot,
        release_id=binding.release_id,
        manifest_sha256=binding.manifest_sha256,
        generation=current.generation + 1 if current else 1,
    )
    _write_pointer(root, pointer, "current.json")
    _write_receipt(
        root,
        RuntimeReceipt(
            schema_version=RECEIPT_SCHEMA_VERSION,
            operation="activate",
            release_id=pointer.release_id,
            manifest_sha256=pointer.manifest_sha256,
            previous_release_id=current.release_id if current else None,
            generation=pointer.generation,
            status="active",
            reason_code="activated",
            created_at=timestamp,
        ),
    )
    return pointer


def rollback_release(
    runtime_root: Path,
    created_at: Optional[str] = None,
) -> RuntimePointer:
    root = Path(runtime_root)
    timestamp = _validate_timestamp(created_at or _now())
    with _transition_lock(root):
        return _rollback_release_locked(root, timestamp)


def _rollback_release_locked(root: Path, timestamp: str) -> RuntimePointer:
    current = load_pointer(root)
    previous = load_pointer(root, "previous.json")
    if current is None or previous is None:
        raise RuntimeReleaseError("rollback_unavailable")
    binding = verify_slot(root, previous.active_slot, previous.release_id)
    if binding.manifest_sha256 != previous.manifest_sha256:
        raise RuntimeReleaseError("rollback_pointer_mismatch")
    rolled_back = RuntimePointer(
        schema_version=POINTER_SCHEMA_VERSION,
        active_slot=previous.active_slot,
        release_id=previous.release_id,
        manifest_sha256=previous.manifest_sha256,
        generation=current.generation + 1,
    )
    _write_pointer(root, current, "previous.json")
    _write_pointer(root, rolled_back, "current.json")
    _write_receipt(
        root,
        RuntimeReceipt(
            schema_version=RECEIPT_SCHEMA_VERSION,
            operation="rollback",
            release_id=rolled_back.release_id,
            manifest_sha256=rolled_back.manifest_sha256,
            previous_release_id=current.release_id,
            generation=rolled_back.generation,
            status="rolled_back",
            reason_code="rolled_back",
            created_at=timestamp,
        ),
    )
    return rolled_back


__all__ = [
    "POINTER_SCHEMA_VERSION",
    "RECEIPT_SCHEMA_VERSION",
    "SLOT_SCHEMA_VERSION",
    "RuntimePointer",
    "RuntimeReceipt",
    "RuntimeReleaseError",
    "SlotBinding",
    "StagedRelease",
    "activate_release",
    "load_pointer",
    "rollback_release",
    "stage_release",
    "verify_slot",
    "_transition_lock",
]
