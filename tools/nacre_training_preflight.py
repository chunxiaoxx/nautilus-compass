#!/usr/bin/env python3
"""Check whether the local MLX-LoRA training gate is ready.

The command is read-only apart from writing the optional JSON receipt. It does
not start training. The current 9B service and training environment are
separate processes, so a passing preflight still requires a deliberate train
command and an independent evaluation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "nacre" / "mlx_lora_stage_a.yaml"
DEFAULT_DATA = ROOT / "runtime" / "nacre" / "mlx_data"
DEFAULT_PYTHON = Path("/Users/chunxiao.wang/infra/mlx-venv/bin/python")


def _read_simple_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def _mlx_available(python_path: Path) -> bool:
    if not python_path.exists():
        return False
    result = subprocess.run(
        [str(python_path), "-c", "import mlx_lm"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.returncode == 0


def preflight(
    config_path: Path,
    data_path: Path,
    min_train: int = 32,
    min_valid: int = 8,
    python_path: Path = DEFAULT_PYTHON,
) -> dict:
    blockers: list[str] = []
    config = _read_simple_yaml(config_path) if config_path.exists() else {}
    model_path = Path(config.get("model", ""))
    if not config_path.exists():
        blockers.append("config_missing")
    if not model_path.exists():
        blockers.append("base_model_missing")
    counts = {}
    manifest_path = data_path / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        counts = manifest.get("counts") or {}
    else:
        blockers.append("mlx_data_manifest_missing")
    for filename in ("train.jsonl", "valid.jsonl", "test.jsonl"):
        if not (data_path / filename).exists():
            blockers.append(f"{filename}_missing")
    if int(counts.get("train", 0)) < min_train:
        blockers.append(f"train_count_below_{min_train}")
    if int(counts.get("validation", 0)) < min_valid:
        blockers.append(f"validation_count_below_{min_valid}")
    if int(counts.get("test", 0)) < min_valid:
        blockers.append(f"test_count_below_{min_valid}")
    mlx_lm_available = _mlx_available(python_path)
    if not mlx_lm_available:
        blockers.append("mlx_lm_unavailable_in_current_python")
    return {
        "schema": "nacre-training-preflight-v0",
        "config": str(config_path),
        "model": str(model_path),
        "data": str(data_path),
        "python": str(python_path),
        "counts": counts,
        "mlx_lm_available": mlx_lm_available,
        "ready": not blockers,
        "blockers": blockers,
        "training_started": False,
        "reason": "gold_set_and_frozen_validation_required" if blockers else "ready_for_deliberate_dry_run",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--min-train", type=int, default=32)
    parser.add_argument("--min-valid", type=int, default=8)
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = preflight(args.config, args.data, args.min_train, args.min_valid, args.python)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
