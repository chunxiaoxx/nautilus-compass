#!/usr/bin/env python3
"""cross_dialog_ack_upgrade_cron.py · v0.1 · L2 of cross-dialog ACK protocol.

Run every 1h via cron. Scan memory dirs for outbound handoffs that have:
  - ack_required: true
  - ack_deadline: <past ISO8601>
  - no corresponding ack_<basename>.md file in the same dir
  - no ack_bounty_id assigned yet (or set to null)

For each match: INSERT INTO platform_bounties · update handoff frontmatter
ack_bounty_id to record idempotency.

Per SPEC: memory/spec_cross_dialog_ack_protocol_v01.md §3.2

Use:
  cross_dialog_ack_upgrade_cron.py [--memory-dir PATH] [--dry-run]
                                    [--reward N] [--deadline-hours H]

Cron install (suggested):
  0 * * * * /usr/bin/python3 /home/ubuntu/nautilus-compass/ops/cross_dialog_ack_upgrade_cron.py >> /home/ubuntu/.cache/compass/ack-upgrade.log 2>&1
"""
import argparse
import datetime
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"
DEFAULT_REWARD = int(os.environ.get("COMPASS_ACK_BOUNTY_DEFAULT_REWARD", "100"))
DEADLINE_HOURS = int(os.environ.get("COMPASS_ACK_BOUNTY_DEADLINE_HOURS", "24"))
PG_DATABASE = os.environ.get("COMPASS_ACK_PG_DB", "nautilus_v5")


def parse_iso8601(s):
    if not s:
        return None
    s = s.strip().strip('"').strip("'")
    if not s or s.lower() == 'null':
        return None
    try:
        return datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
    except Exception:
        return None


def extract_frontmatter_field(file_path, field):
    """Best-effort: extract a top-level frontmatter field value within --- blocks."""
    try:
        content = Path(file_path).read_text(encoding='utf-8', errors='replace')
    except Exception:
        return None
    in_frontmatter = False
    pattern = re.compile(rf'^\s*{re.escape(field)}:\s*(.+?)\s*$')
    for line in content.split('\n'):
        if line.strip() == '---':
            if in_frontmatter:
                break  # end of frontmatter
            in_frontmatter = True
            continue
        if not in_frontmatter:
            continue
        m = pattern.match(line)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return None


def find_expired_handoffs(memory_dir):
    """Return list of (Path, deadline) needing bounty upgrade."""
    now = datetime.datetime.now(datetime.timezone.utc)
    results = []
    if not memory_dir.exists():
        return results
    # use mtime -90 to cover full ack_deadline window (24h default but env-tunable)
    # but glob is fine for typical small memory dirs · auto-cycle dirs need find -mtime
    for f in memory_dir.glob('session_*.md'):
        ack_required = extract_frontmatter_field(f, 'ack_required')
        if ack_required != 'true':
            continue
        ack_bounty_id = extract_frontmatter_field(f, 'ack_bounty_id')
        if ack_bounty_id and ack_bounty_id.lower() not in ('null', 'none', ''):
            continue
        deadline_str = extract_frontmatter_field(f, 'ack_deadline')
        deadline = parse_iso8601(deadline_str)
        if not deadline:
            continue
        if now <= deadline:
            continue
        ack_file = memory_dir / f"ack_{f.stem}.md"
        if ack_file.exists():
            continue
        results.append((f, deadline))
    return results


def create_bounty(handoff_path, deadline, deadline_hours, reward, dry_run=False):
    """INSERT INTO platform_bounties · return bounty_id or None on failure."""
    bounty_id = 'b-ack-' + hashlib.md5(str(handoff_path).encode()).hexdigest()[:10]
    handoff_basename = Path(handoff_path).name
    title = f"ACK: {handoff_basename}"
    description = (
        f"cross-dialog handoff requires ack · expired since {deadline.isoformat()}\n"
        f"see file: {handoff_path}\n"
        f"submit ack with result=path/to/ack_file.md"
    )
    new_deadline = (datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(hours=deadline_hours)).isoformat()
    # f-string SQL with manual single-quote escape · psql -v doesn't expand
    # in -tAc mode. All inputs come from our own code/config · trusted.
    def q(s):
        return "'" + str(s).replace("'", "''") + "'"

    sql = f"""
INSERT INTO platform_bounties (
    bounty_id, title, description, reward_nau, deadline,
    posted_by, status, task_type, phase
) VALUES (
    {q(bounty_id)}, {q(title)}, {q(description)}, {reward},
    {q(new_deadline)}, 'compass-dev-ack-upgrader', 'open',
    'cross_dialog_ack', 'request'
) ON CONFLICT (bounty_id) DO NOTHING
RETURNING bounty_id;
"""
    if dry_run:
        return bounty_id
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', PG_DATABASE, '-tAc', sql],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            print(f"  SQL error: {result.stderr.strip()}")
            return None
        returned = result.stdout.strip()
        return returned if returned else bounty_id  # ON CONFLICT case
    except Exception as e:
        print(f"  bounty create exception: {e}")
        return None


def mark_handoff_bounty_id(handoff_path, bounty_id, dry_run=False):
    """Update handoff frontmatter ack_bounty_id field. Returns True if modified."""
    if dry_run:
        return True
    try:
        content = Path(handoff_path).read_text(encoding='utf-8', errors='replace')
        new_content, n = re.subn(
            r'^(\s*ack_bounty_id:\s*)(null|none|""|\'\')\s*$',
            rf'\1{bounty_id}',
            content,
            flags=re.MULTILINE,
        )
        if n == 0:
            return False
        Path(handoff_path).write_text(new_content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"  mark fail: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--memory-dir', type=str, default=None,
                    help='specific memory dir to scan (default: all ~/.claude/projects/*/memory/)')
    ap.add_argument('--dry-run', action='store_true', help='no DB writes · no file mutations')
    ap.add_argument('--reward', type=int, default=DEFAULT_REWARD)
    ap.add_argument('--deadline-hours', type=int, default=DEADLINE_HOURS)
    args = ap.parse_args()

    if args.memory_dir:
        dirs = [Path(args.memory_dir)]
    else:
        dirs = [d / 'memory' for d in PROJECTS_DIR.iterdir() if d.is_dir()]

    total_expired = 0
    total_created = 0
    total_skipped = 0
    for memory_dir in dirs:
        expired = find_expired_handoffs(memory_dir)
        for f, deadline in expired:
            total_expired += 1
            print(f"EXPIRED: {f}")
            print(f"  deadline: {deadline.isoformat()}")
            bounty_id = create_bounty(f, deadline, args.deadline_hours, args.reward, args.dry_run)
            if not bounty_id:
                total_skipped += 1
                continue
            tag = "[DRY-RUN]" if args.dry_run else ""
            if mark_handoff_bounty_id(f, bounty_id, args.dry_run):
                print(f"  {tag}bounty: {bounty_id} · handoff marked")
                total_created += 1
            else:
                print(f"  {tag}bounty: {bounty_id} · handoff mark FAIL (no ack_bounty_id field?)")
                total_skipped += 1

    print(f"\nsummary: {total_expired} expired | {total_created} created | {total_skipped} skipped")
    print(f"scope: {len(dirs)} dirs · reward={args.reward} NAU · deadline_hours={args.deadline_hours}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
