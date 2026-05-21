#!/usr/bin/env python3
"""v1.7.1 · S_GBrain module 5 · CLI · compass-mcp skill {init,promote,list,evaluate,schedule}.

License: MIT.
Reference: paper/SPEC_GBRAIN_SKILLPACK_REWRITE.md section 4.4 row 5.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skills_pkg.skill_registry import (
    list_by_status, promote, rebuild_registry, load_registry,
)
from skills_pkg.skill_evaluator import evaluate
from skills_pkg.skill_cron_emitter import emit_for_skill


def cmd_init(args, skills_root: Path) -> int:
    target = skills_root / "prototypes" / args.name
    if target.exists():
        print(f"already exists: {target}", file=sys.stderr)
        return 1
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text(
        f"---\nname: {args.name}\nstatus: prototype\nhandler_path: handler.py\n"
        f"cron_schedule: null\ntrigger_events: []\nreview_count: 0\nlast_eval_at: null\n"
        f"last_eval_pass: null\ncodified_at: null\n---\n# {args.name}\n",
        encoding="utf-8",
    )
    (target / "handler.py").write_text(
        f"\"\"\"Skill handler for {args.name}.\"\"\"\n"
        f"def execute(event_payload, context):\n"
        f"    return {{'success': True, 'output': None, 'llm_calls_used': 0, 'walltime_ms': 0}}\n",
        encoding="utf-8",
    )
    tests = target / "tests"
    tests.mkdir()
    (tests / "test_smoke.py").write_text(
        f"import sys\nsys.path.insert(0, '..')\nimport handler\nif __name__ == '__main__':\n"
        f"    r = handler.execute({{}}, {{}})\n    assert r.get('success')\n    print('OK')\n",
        encoding="utf-8",
    )
    print(f"created skill scaffold: {target}")
    return 0


def cmd_list(args, skills_root: Path) -> int:
    status = args.status or "codified"
    skills = list_by_status(skills_root, status)
    print(f"{len(skills)} skills in status={status}")
    for s in skills:
        print(f"  - {s}")
    return 0


def cmd_promote(args, skills_root: Path) -> int:
    result = promote(skills_root, args.name, from_status=args.from_status)
    print(result)
    return 0 if result.get("ok") else 1


def cmd_evaluate(args, skills_root: Path) -> int:
    skill_dir = skills_root / "codified" / args.name
    if not skill_dir.exists():
        skill_dir = skills_root / "prototypes" / args.name
    if not skill_dir.exists():
        print(f"skill not found: {args.name}", file=sys.stderr)
        return 1
    result = evaluate(skill_dir, skills_root=skills_root)
    print(f"skill={result['skill_name']} pass={result.get('pass')} "
          f"walltime_ms={result.get('walltime_ms')}")
    if not result.get("pass"):
        print(result.get("stderr", "")[-500:])
        return 1
    return 0


def cmd_schedule(args, skills_root: Path) -> int:
    skill_dir = skills_root / "codified" / args.name
    if not skill_dir.exists():
        print(f"skill not in codified: {args.name}", file=sys.stderr)
        return 1
    result = emit_for_skill(skill_dir)
    print(result)
    return 0 if result.get("ok") else 1


def main():
    ap = argparse.ArgumentParser(prog="compass-mcp skill")
    ap.add_argument("--skills-root", default=None,
                    help="skills/ root (defaults to <repo>/skills)")
    sub = ap.add_subparsers(dest="subcmd", required=True)

    init = sub.add_parser("init", help="scaffold new skill in prototypes/")
    init.add_argument("name")

    lst = sub.add_parser("list", help="list skills by status")
    lst.add_argument("--status", default="codified",
                     choices=["concept", "prototype", "codified", "retired"])

    pm = sub.add_parser("promote", help="promote skill to next stage")
    pm.add_argument("name")
    pm.add_argument("--from", dest="from_status", required=True,
                    choices=["concept", "prototype", "codified"])

    ev = sub.add_parser("evaluate", help="run skill smoke test")
    ev.add_argument("name")

    sc = sub.add_parser("schedule", help="emit crontab wrapper for skill")
    sc.add_argument("name")

    args = ap.parse_args()

    if args.skills_root:
        skills_root = Path(args.skills_root)
    else:
        skills_root = Path(__file__).resolve().parent.parent / "skills"

    dispatch = {
        "init": cmd_init, "list": cmd_list, "promote": cmd_promote,
        "evaluate": cmd_evaluate, "schedule": cmd_schedule,
    }
    return dispatch[args.subcmd](args, skills_root)


if __name__ == "__main__":
    sys.exit(main())
