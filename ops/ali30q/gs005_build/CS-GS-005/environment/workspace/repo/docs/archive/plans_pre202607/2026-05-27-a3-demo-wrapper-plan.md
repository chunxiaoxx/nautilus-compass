# A3 Demo Wrapper Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship a 1-command zero-deps canned-replay demo that lets an external HN/dev.to visitor verify "engine actually self-modifies" in 60s without any API keys or setup.

**Architecture:** Static `CYCLES` metadata dict in `phase3/cli/nautilus_cli/demo.py` describes cycle 5 + cycle 9 dogfood ships. Demo enriches with live `git show` evidence for each commit. Three invocation paths: `python demo.py` (root shim), `python phase3/cli/nautilus_cli/__main__.py demo`, `nautilus demo` (post pip install). Cast recorded on cloud-server (Windows has no native asciinema) and committed for HN/dev.to embed.

**Tech Stack:** Python 3.8+ stdlib only (argparse · subprocess · pathlib · sys) · pytest for tests · asciinema (cloud-server side · not a runtime dep).

---

## Pre-flight

Confirm working state.

Run: `cd /c/Users/chunx/Projects/nautilus-core && git status -b -s | head -3`
Expected: `## master...origin/master` clean (no ahead/behind · A1 already pushed · A3 design commit `020b1b946` already landed).

Run: `git log -1 --oneline`
Expected: `020b1b946 docs: brainstorming · A3 demo wrapper design (cycle 5 + 9 canned replay + asciinema)`

---

### Task 1: Write 3 failing tests for demo module

**Files:**
- Create: `phase3/cli/tests/test_demo.py`

**Step 1: Write the failing tests**

Use Write tool to create `phase3/cli/tests/test_demo.py` with this exact content:

```python
"""Tests for nautilus_cli.demo · canned replay walkthrough."""
from __future__ import annotations
import sys
from pathlib import Path

# Make nautilus_cli importable when tests run from anywhere
CLI_ROOT = Path(__file__).resolve().parent.parent
if str(CLI_ROOT) not in sys.path:
    sys.path.insert(0, str(CLI_ROOT))


def test_demo_prints_both_cycles(capsys):
    from nautilus_cli.demo import run_demo
    code = run_demo()
    assert code == 0
    out = capsys.readouterr().out
    assert "CYCLE 5" in out
    assert "CYCLE 9" in out


def test_demo_includes_commit_hashes(capsys):
    from nautilus_cli.demo import run_demo
    run_demo()
    out = capsys.readouterr().out
    assert "572547e7d" in out
    assert "9248e84c5" in out


def test_demo_exits_zero():
    from nautilus_cli.demo import run_demo
    assert run_demo() == 0
```

**Step 2: Run tests · expect ImportError**

Run: `cd /c/Users/chunx/Projects/nautilus-core/phase3/cli && python -m pytest tests/test_demo.py -v 2>&1 | tail -15`
Expected: 3 tests collected · 3 FAILED · error includes `ModuleNotFoundError: No module named 'nautilus_cli.demo'`.

**Step 3: Do NOT commit yet.** Tests + impl will commit together in Task 6.

---

### Task 2: Implement demo.py module

**Files:**
- Create: `phase3/cli/nautilus_cli/demo.py`

**Step 1: Write demo.py**

Use Write tool to create `phase3/cli/nautilus_cli/demo.py` with this exact content:

```python
"""Nautilus Soul · canned-replay demo · zero-deps walkthrough of cycle 5 + cycle 9 dogfood ships.

Designed for HN / dev.to visitors who arrive without API keys and want to verify
"engine self-modifies" in 60 seconds. Pulls commit metadata via `git show` so the
evidence chain is live, not faked.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

# phase3/cli/nautilus_cli/demo.py → repo root is parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]
GITHUB_REPO = "chunxiaoxx/nautilus-core"

CYCLES = [
    {
        "n": 5,
        "title": "engine __main__ runner",
        "commit": "572547e7d",
        "file_rel": "phase3/backend/engine/__main__.py",
        "loc": 29,
        "task": (
            "engine needs a standalone CLI runner so users can invoke "
            "`python -m engine <task>` without importing engine programmatically"
        ),
        "checks_summary": "6 checks run · all PASS · single attempt",
        "live_invocation": "python -m engine 'hello world'",
    },
    {
        "n": 9,
        "title": "text_utils.truncate",
        "commit": "9248e84c5",
        "file_rel": "phase3/backend/engine/text_utils.py",
        "loc": 18,
        "task": (
            "engine needs a text_utils.truncate(text, max_len, ellipsis='...') "
            "helper for clean LLM output trimming"
        ),
        "checks_summary": (
            "attempt 1: FAIL · line_count guard (LLM shrank existing file 0.42 < 0.85 threshold)\n"
            "              attempt 2 after LLM re-prompt with error context: PASS · 8 checks all green"
        ),
        "live_invocation": (
            "python -c \"from engine.text_utils import truncate; "
            "print(truncate('long string here', 10))\""
        ),
    },
]


def _git_show_oneline(commit: str) -> str:
    """Returns 'hash YYYY-MM-DD subject' or fallback string if git unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "log", "-1",
             "--format=%h %ad %s", "--date=short", commit],
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return f"{commit} (commit not found locally · clone from github.com to see)"


def _file_exists(rel_path: str) -> bool:
    return (REPO_ROOT / rel_path).is_file()


def _render_cycle(c: dict) -> None:
    title_line = f"─ CYCLE {c['n']} · {c['title']} "
    print(title_line + "─" * max(0, 72 - len(title_line)))
    print()
    print(f"[1/6] Task    {c['task']}")
    print(f"[2/6] Gen     LLM generated {c['file_rel']} ({c['loc']} LOC)")
    print(f"[3/6] Check   {c['checks_summary']}")
    print(f"[4/6] Ship    {_git_show_oneline(c['commit'])}")
    print(f"[5/6] Verify  https://github.com/{GITHUB_REPO}/commit/{c['commit']}")
    exists_note = "exists in this checkout" if _file_exists(c["file_rel"]) else "MISSING · git status?"
    print(f"[6/6] Live    $ {c['live_invocation']}  # {exists_note}")
    print()


def run_demo() -> int:
    """Print the cycle 5 + cycle 9 walkthrough. Exits 0 always (informational)."""
    print()
    print("=" * 72)
    print("  Nautilus Soul · canned-replay demo · cycle 5 + cycle 9 dogfood")
    print("  Zero deps · no LLM call · no API key · no network · ~60s")
    print("=" * 72)
    print()
    print("Premise: the engine generated, checked, and committed its own code.")
    print("Below are two real cycles. Verify each commit on GitHub yourself.")
    print()

    for c in CYCLES:
        _render_cycle(c)

    print("─" * 72)
    print(f"Both commits verifiable on GitHub: github.com/{GITHUB_REPO}")
    for c in CYCLES:
        print(f"  · {c['commit']}  ({c['title']})")
    print()
    print("Try a live cycle yourself:")
    print('  $ nautilus code "your task description" --apply --commit-msg "your msg"')
    print()
    return 0


if __name__ == "__main__":
    sys.exit(run_demo())
```

**Step 2: Run tests · expect all 3 PASS**

Run: `cd /c/Users/chunx/Projects/nautilus-core/phase3/cli && python -m pytest tests/test_demo.py -v 2>&1 | tail -15`
Expected: 3 passed.

If `test_demo_includes_commit_hashes` fails because `_git_show_oneline` returned the full 40-char hash (`%H`) instead of short, that's fine — assertion uses short hash substring which is also in full hash. If `%h` returns shorter than 9 chars (possible on certain repos), update assertion to use first 7 chars. Verify hash in actual output before troubleshooting.

**Step 3: Smoke run the module directly**

Run: `cd /c/Users/chunx/Projects/nautilus-core && python phase3/cli/nautilus_cli/demo.py 2>&1 | head -40`
Expected: prints banner · CYCLE 5 block · CYCLE 9 block · both with real commit dates pulled from `git log`.

---

### Task 3: Wire `demo` subcommand into __main__.py

**Files:**
- Modify: `phase3/cli/nautilus_cli/__main__.py` (add cmd_demo function + p_demo subparser)

**Step 1: Add cmd_demo function**

Use Edit tool on `phase3/cli/nautilus_cli/__main__.py`. Find the `def cmd_code(args` function (currently line 277-ish · is the last cmd_* function). After its closing return and before `def main(argv=None):`, insert:

old_string (use the closing of cmd_code to anchor uniquely — pick the last few lines of cmd_code that include the closing return and blank line before main):

```python
        print(f"[done] dry-run · pass --apply (and optionally --commit-msg) to write+commit")
        return 0


def main(argv=None) -> int:
```

new_string:

```python
        print(f"[done] dry-run · pass --apply (and optionally --commit-msg) to write+commit")
        return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Run the canned-replay walkthrough · no auth · no network."""
    from .demo import run_demo
    return run_demo()


def main(argv=None) -> int:
```

**Step 2: Add p_demo subparser registration**

Use Edit tool on the same file. Find the existing `p_cert = sub.add_parser(...)` block (the last sub-parser registration before `args = parser.parse_args(argv)`). After `p_cert.set_defaults(func=cmd_cert)`, insert the demo subparser:

old_string:

```python
    p_cert.set_defaults(func=cmd_cert)

    args = parser.parse_args(argv)
```

new_string:

```python
    p_cert.set_defaults(func=cmd_cert)

    p_demo = sub.add_parser("demo", help="Canned-replay walkthrough of cycle 5 + 9 dogfood (no API key)")
    p_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args(argv)
```

**Step 3: Smoke check the subcommand**

Run: `cd /c/Users/chunx/Projects/nautilus-core && python phase3/cli/nautilus_cli/__main__.py demo 2>&1 | head -10`
Expected: same banner as Task 2 Step 3 (banner + Cycle 5 header start).

Run: `cd /c/Users/chunx/Projects/nautilus-core && python phase3/cli/nautilus_cli/__main__.py --help 2>&1 | grep demo`
Expected: line includes `demo` and the help text "Canned-replay walkthrough...".

---

### Task 4: Add root `demo.py` shim

**Files:**
- Create: `demo.py` (at repo root)

**Step 1: Write the shim**

Use Write tool to create `/c/Users/chunx/Projects/nautilus-core/demo.py` with this content:

```python
"""Convenience shim · run Nautilus Soul demo from fresh clone without pip install.

Usage from repo root:
    python demo.py

Equivalent to (after pip install -e phase3/cli/):
    nautilus demo
"""
import sys
from pathlib import Path

# Make phase3/cli importable so `nautilus_cli.demo` resolves
sys.path.insert(0, str(Path(__file__).resolve().parent / "phase3" / "cli"))

from nautilus_cli.demo import run_demo

if __name__ == "__main__":
    sys.exit(run_demo())
```

**Step 2: Smoke check root shim**

Run: `cd /c/Users/chunx/Projects/nautilus-core && python demo.py 2>&1 | head -10`
Expected: identical output to Task 3 Step 3 (same banner).

Run: `cd /c/Users/chunx/Projects/nautilus-core && python demo.py | wc -l`
Expected: between 20 and 50 lines of output (varies with cycle text wrap).

---

### Task 5: Full test sweep · no regressions

**Step 1: Run all phase3/cli tests**

Run: `cd /c/Users/chunx/Projects/nautilus-core/phase3/cli && python -m pytest -q 2>&1 | tail -5`
Expected: 5 passed (2 from `test_main_cycle_id.py` baseline + 3 from `test_demo.py`).

**Step 2: Confirm engine tests still pass (paranoia)**

Run: `cd /c/Users/chunx/Projects/nautilus-core/phase3/backend/engine && python -m pytest -q --tb=no 2>&1 | tail -3`
Expected: 196 passed · 6 skipped (PG when DATABASE_URL unset).

Engine tests have nothing to do with demo · this is paranoia. If anything fails here, it is unrelated to A3.

---

### Task 6: Commit code + tests

**Files:** stage 4 modified/new files.

**Step 1: Stage**

Run:
```
cd /c/Users/chunx/Projects/nautilus-core && git add \
  phase3/cli/nautilus_cli/demo.py \
  phase3/cli/nautilus_cli/__main__.py \
  phase3/cli/tests/test_demo.py \
  demo.py
```

**Step 2: Inspect staged diff**

Run: `git status --short`
Expected (order may differ):
```
A  demo.py
A  phase3/cli/nautilus_cli/demo.py
M  phase3/cli/nautilus_cli/__main__.py
A  phase3/cli/tests/test_demo.py
```

Run: `git diff --cached --stat`
Expected: 4 files changed · roughly 130 insertions · 0 deletions (only Modify of __main__.py adds 2 small blocks).

**Step 3: Commit**

Run:
```
cd /c/Users/chunx/Projects/nautilus-core && git commit -m "feat(cli): A3 · nautilus-soul demo · canned replay cycle 5 + 9 dogfood

Adds zero-dependency 1-command demo so external visitors (HN / dev.to) can
verify engine self-modification claim in ~60s without API keys, DB, or network.
Pulls live git evidence for each cycle so the trust anchor stays verifiable.

Invocation paths (all equivalent):
  python demo.py                        # root shim · fresh clone
  python phase3/cli/nautilus_cli/__main__.py demo
  nautilus demo                         # post pip install -e phase3/cli/

Tests: 3 new (CLI 2 → 5) · engine 196 unchanged.

Closes Path A W1 item A3."
```

**Step 4: Verify commit landed**

Run: `git log -1 --stat`
Expected: 4 files · ~130 lines added · commit message as above.

Run: `git status -b -s | head -1`
Expected: `## master...origin/master [ahead 1]` (this commit is local · not yet pushed).

---

### Task 7: Record asciinema cast on cloud-server

> **Why cloud-server:** Windows lacks native asciinema. The demo code is platform-agnostic so output is identical on Linux.

**Step 1: SSH into cloud-server**

Note: this step requires user (not Claude) if a fresh SSH session needs key prompt. Try:

Run: `ssh -o BatchMode=yes cloud "echo ok && which asciinema || echo no-asciinema"`
Expected (case A · asciinema present): `ok` + path. Proceed to Step 3.
Expected (case B · no asciinema): `ok` + `no-asciinema`. Proceed to Step 2.
Expected (case C · BatchMode fails): error · request user help running interactive `ssh cloud` first.

If case C, stop and ask user to confirm SSH agent is loaded for cloud-server.

**Step 2: Install asciinema on cloud-server (if not present)**

Run: `ssh cloud "pip install --user asciinema 2>&1 | tail -3 && asciinema --version"`
Expected: `asciinema 2.x` line at end.

**Step 3: Pull latest master on cloud-server**

Run: `ssh cloud "cd ~/nautilus-mvp && git fetch origin master && git reset --hard origin/master 2>&1 | tail -3 && git log -1 --oneline"`
Expected: commit hash of the Task 6 commit (after that is pushed · see note below).

**⚠ Dependency note:** Task 7 Step 3 requires the Task 6 commit to be on origin/master. If not yet pushed, push first using the same ad-hoc URL pattern from earlier in this session OR ask the user to push manually. The cast recording uses the cloud-server's checkout · which only sees pushed commits.

**Step 4: Pre-flight on cloud-server · confirm demo runs there**

Run: `ssh cloud "cd ~/nautilus-mvp && python3 demo.py 2>&1 | head -10"`
Expected: same banner as Windows · proves cross-platform.

**Step 5: Record the cast**

Run:
```
ssh cloud "cd ~/nautilus-mvp && mkdir -p assets && asciinema rec assets/demo.cast --title 'Nautilus Soul · cycle 5 + 9 dogfood' --command 'python3 demo.py' --overwrite"
```

This is non-interactive · `--command` runs the demo as the cast subject · exits when demo exits · writes cast file.

Expected: prints `~ Recording started · ~ Recording finished · asciicast saved to assets/demo.cast`.

**Step 6: SCP the cast back to Windows**

Run: `scp cloud:~/nautilus-mvp/assets/demo.cast /c/Users/chunx/Projects/nautilus-core/assets/demo.cast`
Expected: file copied · size ~10-100 KB.

If `assets/` doesn't exist locally, first: `mkdir -p /c/Users/chunx/Projects/nautilus-core/assets`.

**Step 7: (Optional) upload to asciinema.org for public URL**

Run: `ssh cloud "cd ~/nautilus-mvp && asciinema upload assets/demo.cast 2>&1 | tail -3"`
Expected: returns `https://asciinema.org/a/<id>` URL · note this URL for A2 README rewrite.

This requires asciinema.org account or anonymous upload (anonymous casts auto-deleted after 7 days · use real account for permanent). If anonymous is fine for A3 v0, do it · note URL · revisit in A2.

If upload fails or user wants to skip, that's OK · `assets/demo.cast` in repo is still usable (consumers can `asciinema play assets/demo.cast` locally).

---

### Task 8: Commit cast file

**Step 1: Stage cast**

Run: `cd /c/Users/chunx/Projects/nautilus-core && git add assets/demo.cast`

**Step 2: Confirm only cast staged**

Run: `git status --short`
Expected: `A  assets/demo.cast` and nothing else.

**Step 3: Commit**

Build the commit message based on whether upload happened.

If asciinema URL exists:

```
cd /c/Users/chunx/Projects/nautilus-core && git commit -m "chore(demo): A3 · asciinema cast for nautilus-soul demo (60s walkthrough)

Recording of \`python demo.py\` from cloud-server (Linux). Cross-platform
output identical to Windows local run. Public asciinema.org URL:
https://asciinema.org/a/<ID>

Consumers can replay locally:
  asciinema play assets/demo.cast

A2 README hero rewrite will embed the asciinema.org link."
```

(Replace `<ID>` with the actual ID from Task 7 Step 7.)

If no upload:

```
cd /c/Users/chunx/Projects/nautilus-core && git commit -m "chore(demo): A3 · asciinema cast for nautilus-soul demo (60s walkthrough)

Recording of \`python demo.py\` from cloud-server. Consumers can replay:
  asciinema play assets/demo.cast

asciinema.org upload deferred · cast is self-contained JSON."
```

**Step 4: Verify**

Run: `git log -1 --stat`
Expected: 1 file (`assets/demo.cast`) · large insertions count (JSON · 100-1000 lines).

Run: `git status -b -s | head -1`
Expected: `## master...origin/master [ahead N]` where N is 1 or 2 depending on whether Task 6 was pushed already.

---

### Task 9: Push to origin (deferred unless user explicitly wants it)

Pushing is owned by the user this session (token in chat history). Two states possible:

- If only Task 6 committed (no cast yet): user can push to make commit visible on GitHub before Task 7.
- If Task 6 + Task 8 both committed: user can push once at end.

**Recommend asking the user** which they prefer rather than auto-pushing. If user gives go-ahead, push via:

Run: `cd /c/Users/chunx/Projects/nautilus-core && env -u GITHUB_TOKEN git push origin master`
Expected: `master -> master` success.

This step is optional in the plan · do not block A3 completion on it.

---

## Out of Scope (Do Not Touch)

- `--live` flag (live LLM call) · defer to W2 if user demand surfaces
- GIF generation from cast · defer to A4 dev.to article
- README inline ASCII block · defer to A2 README hero rewrite
- README hero rewrite itself · A2 separate task
- Colored / boxed terminal UX · defer to demo v2 (ROI too low vs distribution)
- PyPI publish · A7 W2
- Recording on Windows · use cloud-server (Linux)
- `engine_cycle_outcomes` table integration · canned dict is enough for v0
- `alembic/versions/` · user hard constraint
- Path B (Gap 3-5) · deferred to W4

---

## Risk + Rollback

- Risk: negligible. Demo is read-only (git log + filesystem checks · no mutations). Recording on cloud-server touches only `~/nautilus-mvp/assets/`.
- Rollback: `git revert <task6-commit> <task8-commit>` · 2 reverts (one for code · one for cast). Or single revert if commits combined.

---

## Done Criteria

1. `python demo.py` from fresh clone prints both cycles + verifiable commits + exits 0.
2. `nautilus demo` (post `pip install -e phase3/cli/`) does the same.
3. `assets/demo.cast` exists in repo · optional asciinema.org public URL in commit body.
4. 3 new tests in `phase3/cli/tests/test_demo.py` all pass.
5. Test count: CLI 2 → 5 · engine 196 unchanged.
6. 1 or 2 commits on master · ~115 LOC code + cast file.
7. Smoke `python demo.py | head -20` from Windows local works identically to cloud-server run.
