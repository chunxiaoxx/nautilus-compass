import sys
from pathlib import Path

from engine.nautilus_engine import NautilusEngine
from engine.ship import ship


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m engine <task>", file=sys.stderr)
        return 1

    task = sys.argv[1]
    base_dir = str(Path.cwd())

    engine = NautilusEngine(base_dir=base_dir, dry_run=True)
    try:
        result = ship(engine, task, base_dir, apply=False, dispatch_audit=False)
    except Exception as e:
        print(f"Error: ship() failed: {e}", file=sys.stderr)
        return 1

    print(f"Files planned: {result.files_planned}")
    print(f"Check passed: {result.check_result['passed']}")

    return 0 if result.check_result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())