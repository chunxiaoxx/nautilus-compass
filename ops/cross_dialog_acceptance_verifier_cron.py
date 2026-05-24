#!/usr/bin/env python3
"""cross_dialog_acceptance_verifier_cron.py · v0.1 · L3 of cross-dialog ACK protocol.

Run every 6h via cron. Scan outbound handoffs with `acceptance:` criteria
in frontmatter. For each handoff where L1 ack file says `ack_status: done`,
verify that the actual work was shipped by checking:
  - git_commit: grep target repo's git log for matching pattern
  - metric: run shell query · compare expected vs actual

Marks handoff frontmatter:
  acceptance_verified: true · <ISO8601>   (all criteria pass)
  acceptance_failed: <criterion-summary>  (any criterion failed)

If acceptance_failed · the L2 bounty's escrow should NOT be released
(human / evaluator decides next step).

Use:
  cross_dialog_acceptance_verifier_cron.py [--memory-dir PATH] [--dry-run]

Cron install (suggested):
  0 */6 * * * /usr/bin/python3 /home/ubuntu/nautilus-compass/ops/cross_dialog_acceptance_verifier_cron.py >> /home/ubuntu/.cache/compass/ack-verify.log 2>&1

Per SPEC: memory/spec_cross_dialog_ack_protocol_v01.md §3.3
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required · pip install pyyaml")
    sys.exit(2)

PROJECTS_DIR = Path.home() / ".claude" / "projects"
DEFAULT_REPO_BASE = Path.home()   # repo names resolved as ~/repo_name


def load_frontmatter(file_path):
    """Parse YAML frontmatter between --- markers · returns dict or None.

    Silent fail on YAML errors · memory dirs contain many cycle dumps with
    malformed frontmatter (e.g. unquoted colons in description).
    """
    try:
        content = Path(file_path).read_text(encoding='utf-8', errors='replace')
    except Exception:
        return None
    m = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None  # silent · noise reduction for 20k+ files


def check_git_commit(criterion):
    """Returns (passed: bool, detail: str)."""
    repo_name = criterion.get('repo')
    pattern = criterion.get('pattern')
    expected_count = int(criterion.get('expected_count', 1))
    if not repo_name or not pattern:
        return False, "missing repo or pattern"
    repo_path = DEFAULT_REPO_BASE / repo_name
    if not (repo_path / '.git').exists():
        return False, f"repo not found at {repo_path}"
    try:
        result = subprocess.run(
            ['git', '-C', str(repo_path), 'log', '--all', '--oneline',
             '--grep', pattern, '-i', '--regexp-ignore-case'],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return False, f"git log err: {result.stderr.strip()[:100]}"
        matched = [l for l in result.stdout.strip().split('\n') if l.strip()]
        count = len(matched)
        if count >= expected_count:
            sample = matched[0][:80] if matched else ""
            return True, f"{count} commits match (>= {expected_count}) · e.g. {sample}"
        return False, f"only {count} commits match (need {expected_count})"
    except Exception as e:
        return False, f"git exception: {e}"


def check_metric(criterion):
    """Returns (passed: bool, detail: str)."""
    query = criterion.get('query')
    expected = criterion.get('expected')
    if not query or not expected:
        return False, "missing query or expected"
    try:
        result = subprocess.run(
            ['bash', '-c', query],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return False, f"query fail: {result.stderr.strip()[:100]}"
        actual = result.stdout.strip()
        # parse expected like "< 200" or "= 5" or "1024"
        m = re.match(r'^([<>=]=?)\s*([\d.]+)$', expected)
        if m:
            op, target_str = m.groups()
            target = float(target_str)
            try:
                actual_n = float(actual)
            except ValueError:
                return False, f"non-numeric actual: {actual!r}"
            ops = {'<': actual_n < target, '>': actual_n > target,
                   '<=': actual_n <= target, '>=': actual_n >= target,
                   '=': actual_n == target, '==': actual_n == target}
            if ops.get(op, False):
                return True, f"{actual_n} {op} {target} · query={query}"
            return False, f"{actual_n} not {op} {target} · query={query}"
        # plain string equality
        if actual == str(expected):
            return True, f"actual={actual!r} matches expected"
        return False, f"actual={actual!r} != expected={expected!r}"
    except Exception as e:
        return False, f"metric exception: {e}"


def verify_acceptance(handoff_path, dry_run=False):
    """Returns (verdict: 'verified'|'failed'|'skipped', detail: str)."""
    fm = load_frontmatter(handoff_path) or {}
    # idempotency: skip if already marked verified
    if fm.get('acceptance_verified'):
        return 'skipped', 'already verified'
    # acceptance can be at top-level or under metadata
    acceptance = fm.get('acceptance') or fm.get('metadata', {}).get('acceptance')
    if not acceptance:
        return 'skipped', 'no acceptance criteria'
    # check L1 ack file says done
    ack_file = handoff_path.parent / f"ack_{handoff_path.stem}.md"
    if not ack_file.exists():
        return 'skipped', 'no L1 ack file yet'
    ack_fm = load_frontmatter(ack_file) or {}
    ack_status = (ack_fm.get('metadata', {}).get('ack_status')
                  or ack_fm.get('ack_status'))
    if ack_status != 'done':
        return 'skipped', f'ack_status={ack_status} (waiting for done)'

    # run each criterion
    results = []
    for crit in acceptance:
        ctype = crit.get('type')
        if ctype == 'git_commit':
            passed, detail = check_git_commit(crit)
        elif ctype == 'metric':
            passed, detail = check_metric(crit)
        else:
            passed, detail = False, f"unknown type: {ctype}"
        results.append((ctype, passed, detail))

    all_passed = all(r[1] for r in results)
    summary = "; ".join(f"{t}={'OK' if p else 'FAIL'}({d})" for t, p, d in results)
    verdict = 'verified' if all_passed else 'failed'

    if not dry_run:
        mark_acceptance_status(handoff_path, verdict, summary)
    return verdict, summary


def mark_acceptance_status(handoff_path, verdict, summary):
    """Append acceptance_verified/_failed to frontmatter (best-effort regex)."""
    try:
        content = Path(handoff_path).read_text(encoding='utf-8', errors='replace')
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        field_name = 'acceptance_verified' if verdict == 'verified' else 'acceptance_failed'
        # remove old marker if present
        content = re.sub(rf'^\s*{field_name}:.*$\n', '', content, flags=re.MULTILINE)
        # insert before closing --- of frontmatter
        new_marker = f"  {field_name}: \"{ts} · {summary[:200]}\"\n"
        content = re.sub(r'(\n---\n)', f'{new_marker}\\1', content, count=1)
        Path(handoff_path).write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"  mark fail: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--memory-dir', type=str, default=None,
                    help='specific memory dir to scan')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--days', type=int, default=30,
                    help='only scan files modified within N days (default 30)')
    args = ap.parse_args()

    if args.memory_dir:
        dirs = [Path(args.memory_dir)]
    else:
        dirs = [d / 'memory' for d in PROJECTS_DIR.iterdir() if d.is_dir()]

    # use find -mtime to avoid 20k+ session glob explosion (memory dirs have
    # cycle-NNNNN-auto outputs · same pattern as L1 sweep script)
    cutoff = datetime.datetime.now().timestamp() - args.days * 86400

    totals = {'verified': 0, 'failed': 0, 'skipped': 0}
    for memory_dir in dirs:
        if not memory_dir.exists():
            continue
        for f in memory_dir.glob('session_*.md'):
            if f.name.startswith('ack_'):
                continue
            try:
                if f.stat().st_mtime < cutoff:
                    continue
            except Exception:
                continue
            verdict, summary = verify_acceptance(f, args.dry_run)
            totals[verdict] += 1
            if verdict != 'skipped':
                tag = "[DRY-RUN]" if args.dry_run else ""
                print(f"{verdict.upper()} {tag}: {f.name}")
                print(f"  {summary}")

    print(f"\nsummary: {totals['verified']} verified | {totals['failed']} failed | {totals['skipped']} skipped (scope: last {args.days}d)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
