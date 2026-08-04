from __future__ import annotations

import zipfile
from pathlib import Path


def write_test_wheel(path: Path, payload: bytes = b"fixture") -> None:
    version = path.name.split("-")[1]
    dist_info = f"nautilus_compass-{version}.dist-info"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("nautilus_compass/__init__.py", b"PAYLOAD = " + repr(payload).encode())
        archive.writestr(
            f"{dist_info}/METADATA",
            f"Metadata-Version: 2.1\nName: nautilus-compass\nVersion: {version}\n",
        )
        archive.writestr(
            f"{dist_info}/WHEEL",
            "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
        archive.writestr(f"{dist_info}/RECORD", "")


def extract_test_wheel(stage_dir: Path, wheel_path: Path) -> Path:
    executable = stage_dir / "venv" / "Scripts" / "python.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"fake-python")
    site_packages = stage_dir / "venv" / "Lib" / "site-packages"
    site_packages.mkdir(parents=True)
    with zipfile.ZipFile(wheel_path) as archive:
        archive.extractall(site_packages)
    return executable
