"""Stable fail-closed launcher for the active Compass runtime slot."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

from release_manifest import ReleaseManifest, ReleaseManifestError
from runtime_release import RuntimeReleaseError, load_pointer, verify_slot


RESOLVED_SCHEMA_VERSION = "compass.runtime.resolved.v1"
MCP_MODULE = "nautilus_compass.mcp_server"

Executor = Callable[[Sequence[str]], int]


class RuntimeLauncherError(ValueError):
    """Launcher error that exposes only a controlled reason code."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


@dataclass(frozen=True)
class ResolvedCommand:
    schema_version: str
    release_id: str
    manifest_sha256: str
    default_policy: str
    executable: Path
    arguments: Tuple[str, ...]

    def to_mapping(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "release_id": self.release_id,
            "manifest_sha256": self.manifest_sha256,
            "default_policy": self.default_policy,
            "executable": str(self.executable),
            "arguments": list(self.arguments),
        }


def resolve_active_command(runtime_root: Path) -> ResolvedCommand:
    root = Path(runtime_root)
    try:
        pointer = load_pointer(root)
        if pointer is None:
            raise RuntimeLauncherError("no_active_release")
        binding = verify_slot(root, pointer.active_slot, pointer.release_id)
        if binding.manifest_sha256 != pointer.manifest_sha256:
            raise RuntimeLauncherError("active_pointer_mismatch")
        manifest = ReleaseManifest.from_json_bytes(
            (binding.path / "release-manifest.json").read_bytes()
        )
    except RuntimeLauncherError:
        raise
    except RuntimeReleaseError as exc:
        raise RuntimeLauncherError(exc.reason_code) from exc
    except ReleaseManifestError as exc:
        raise RuntimeLauncherError("slot_manifest_invalid") from exc
    except OSError as exc:
        raise RuntimeLauncherError("slot_manifest_invalid") from exc

    arguments = (str(binding.python_executable), "-m", MCP_MODULE)
    return ResolvedCommand(
        schema_version=RESOLVED_SCHEMA_VERSION,
        release_id=binding.release_id,
        manifest_sha256=binding.manifest_sha256,
        default_policy=manifest.default_policy,
        executable=binding.python_executable,
        arguments=arguments,
    )


def execute_resolved(
    resolved: ResolvedCommand,
    executor: Optional[Executor] = None,
) -> int:
    arguments = list(resolved.arguments)
    if executor is not None:
        return int(executor(arguments))
    if os.name == "nt":
        return subprocess.call(arguments, shell=False)
    os.execv(arguments[0], arguments)
    return 127


def _runtime_root(explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit)
    configured = os.environ.get("COMPASS_RUNTIME_ROOT", "").strip()
    if configured:
        return Path(configured)
    return Path.home() / ".nautilus-compass" / "runtime"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compass-runtime",
        description="Launch the manifest-bound active Compass MCP runtime",
    )
    parser.add_argument("--runtime-root")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    if args.json and not args.dry_run:
        sys.stderr.write("compass_runtime_error:json_requires_dry_run\n")
        return 2
    try:
        resolved = resolve_active_command(_runtime_root(args.runtime_root))
    except RuntimeLauncherError as exc:
        sys.stderr.write("compass_runtime_error:{}\n".format(exc.reason_code))
        return 2
    if args.dry_run:
        if args.json:
            sys.stdout.write(
                json.dumps(
                    resolved.to_mapping(),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
        else:
            sys.stdout.write("compass_runtime_ok:{}\n".format(resolved.release_id))
        return 0
    return execute_resolved(resolved)


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "MCP_MODULE",
    "RESOLVED_SCHEMA_VERSION",
    "ResolvedCommand",
    "RuntimeLauncherError",
    "execute_resolved",
    "main",
    "resolve_active_command",
]
