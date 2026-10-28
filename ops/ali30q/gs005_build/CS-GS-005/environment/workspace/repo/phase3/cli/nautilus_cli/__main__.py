"""
Nautilus CLI v0 · entry point.

Usage:
  nautilus init
  nautilus audit <spec_file> [options]
  nautilus status <audit_id> [--watch]
  nautilus cert <audit_id> [--verify] [--json] [--public]
  nautilus code <task> [options]       # local code generation via Nautilus Engine
  nautilus engine <task> [options]     # alias for `code` (matches DMAS plan naming)
  nautilus demo
  nautilus --version

Auth: env NAUTILUS_API_KEY=nau_xxx OR `nautilus init` to save in ~/.nautilus/config.json

Examples:
  nautilus audit my_spec.md --budget 100 --deadline 24
  nautilus status audit_abc123 --watch
  nautilus cert audit_abc123 --verify
  nautilus engine "add user auth to backend/main.py" --runtime-check --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import urllib.request
    import urllib.error
except ImportError:
    print("ERROR: urllib required (Python 3.6+)", file=sys.stderr)
    sys.exit(1)

from . import __version__

API_BASE = os.getenv("NAUTILUS_API_BASE", "https://www.nautilus.social")
CONFIG_DIR = Path.home() / ".nautilus"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:
        pass


def _get_api_key() -> Optional[str]:
    env_key = os.getenv("NAUTILUS_API_KEY")
    if env_key:
        return env_key
    cfg = _load_config()
    return cfg.get("api_key")


def _http(method: str, path: str, body: Optional[dict] = None, auth: bool = True) -> dict:
    url = f"{API_BASE}{path}"
    data = None
    headers = {"Content-Type": "application/json", "User-Agent": f"nautilus-cli/{__version__}"}
    if auth:
        key = _get_api_key()
        if not key:
            print("ERROR: NAUTILUS_API_KEY not set · run `nautilus init` or set env", file=sys.stderr)
            sys.exit(2)
        headers["Authorization"] = f"Bearer {key}"
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            err_body = {"error": {"message": str(e)}}
        print(f"HTTP {e.code}: {err_body.get('detail', err_body)}", file=sys.stderr)
        sys.exit(3)
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(4)


def cmd_init(args: argparse.Namespace) -> int:
    """Interactive setup of API key + base URL."""
    print(f"Nautilus CLI v{__version__} · setup")
    print(f"Default API base: {API_BASE}")
    print(f"Config location: {CONFIG_FILE}")
    print()
    api_key = input("Enter your API key (starts with nau_ · from https://www.nautilus.social/audit): ").strip()
    if not api_key.startswith("nau_"):
        print("ERROR: API key must start with nau_", file=sys.stderr)
        return 1
    cfg = _load_config()
    cfg["api_key"] = api_key
    cfg["api_base"] = API_BASE
    _save_config(cfg)
    print(f"✅ Saved to {CONFIG_FILE} (mode 0600)")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """Dispatch a new audit · POST /api/v1/audit/dispatch."""
    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        print(f"ERROR: spec file not found: {spec_path}", file=sys.stderr)
        return 1

    task_spec = spec_path.read_text(encoding="utf-8").strip()
    if len(task_spec) < 20:
        print(f"ERROR: spec too short ({len(task_spec)} chars · min 20)", file=sys.stderr)
        return 1
    if len(task_spec) > 10000:
        print(f"ERROR: spec too long ({len(task_spec)} chars · max 10000)", file=sys.stderr)
        return 1

    title = args.title or f"CLI audit · {spec_path.name}"
    body = {
        "task_spec": task_spec,
        "budget_nau": args.budget,
        "deadline_hours": args.deadline,
        "title": title[:200],
        "task_type": args.task_type,
    }

    print(f"🚀 Dispatching audit · budget={args.budget} NAU · deadline={args.deadline}h")
    print(f"   spec: {spec_path.name} ({len(task_spec)} chars)")

    result = _http("POST", "/api/v1/audit/dispatch", body)
    data = result.get("data", {})
    audit_id = data.get("audit_id")
    if not audit_id:
        print(f"ERROR: no audit_id returned: {result}", file=sys.stderr)
        return 5

    print()
    print(f"✅ Audit dispatched · ID: {audit_id}")
    print(f"   Status URL: {API_BASE}{data.get('status_url', '')}")
    print(f"   Cert URL  : {API_BASE}{data.get('certificate_url', '')}")
    print(f"   Estimated : {data.get('estimated_completion', 'n/a')}")
    print(f"   Escrow    : {'locked' if data.get('escrow_locked') else 'NOT locked'}")
    if data.get('escrow_error'):
        print(f"   ⚠ Escrow error: {data['escrow_error']}")

    if args.watch:
        print()
        print("👀 Watching status (Ctrl+C to stop) · polling every 15s...")
        return cmd_status_watch(audit_id)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Get current audit status · GET /api/v1/audit/{id}."""
    audit_id = args.audit_id
    if args.watch:
        return cmd_status_watch(audit_id)
    result = _http("GET", f"/api/v1/audit/{audit_id}")
    data = result.get("data", {})
    print(f"audit_id    : {data.get('audit_id')}")
    print(f"title       : {data.get('title')}")
    print(f"status      : {data.get('status')} (phase: {data.get('phase')})")
    print(f"claimer     : {data.get('claimer')}")
    print(f"reward_nau  : {data.get('reward_nau')}")
    print(f"fidelity    : {data.get('fidelity_score')}")
    print(f"quality     : {data.get('quality_score')}")
    print(f"verdict     : {data.get('customer_verdict') or '(none)'}")
    print(f"cert URL    : {data.get('certificate_url') or '(not finalized)'}")
    out = data.get("output")
    if out:
        print(f"output      : {len(out)} chars · first 200: {out[:200]}...")
    return 0


def cmd_status_watch(audit_id: str) -> int:
    """Poll status until terminal state · max 60 polls × 15s = 15 min."""
    terminal = {"completed", "settled", "rejected", "failed"}
    last_status = None
    for i in range(60):
        result = _http("GET", f"/api/v1/audit/{audit_id}")
        data = result.get("data", {})
        s = data.get("status")
        claimer = data.get("claimer") or "(unclaimed)"
        if s != last_status:
            print(f"  [{i+1:02d}] {time.strftime('%H:%M:%S')} status={s} · claimer={claimer}")
            last_status = s
        if s in terminal:
            print()
            print(f"✅ Audit reached terminal state: {s}")
            print(f"   Cert URL: {API_BASE}{data.get('certificate_url') or ''}")
            if s in ("completed", "settled"):
                print(f"   Public:   {API_BASE}/cert/{audit_id}")
            return 0
        time.sleep(15)
    print(f"⚠ Watch timeout after 15 min · current status={last_status} · run `nautilus status {audit_id}` to re-check")
    return 6


def cmd_cert(args: argparse.Namespace) -> int:
    """Get the JSON-LD signed audit certificate · GET /api/v1/audit/{id}/certificate."""
    audit_id = args.audit_id
    use_public = args.public

    if use_public:
        # Public endpoint · no auth required
        endpoint = f"/api/v1/public/cert/{audit_id}"
        result = _http("GET", endpoint, auth=False)
    else:
        endpoint = f"/api/v1/audit/{audit_id}/certificate"
        result = _http("GET", endpoint)

    cert = result.get("data", {})

    if args.json:
        print(json.dumps(cert, indent=2, ensure_ascii=False))
        return 0

    # Human-readable summary
    print(f"📜 Audit Certificate · {cert.get('audit_id')}")
    print(f"   Type   : {cert.get('@type')} · v{cert.get('certificate_version') or cert.get('version')}")
    print(f"   Issued : {cert.get('issued_at')}")
    print(f"   Signing: {cert.get('signing_algorithm')}")
    task = cert.get("task", {})
    if task:
        print(f"   Title  : {task.get('title')}")
        print(f"   Spec   : {task.get('spec_chars')} chars · sha256={(task.get('spec_hash') or '')[:32]}...")
    out = cert.get("output", {})
    if out:
        if isinstance(out, dict):
            print(f"   Output : {out.get('chars')} chars · sha256={(out.get('hash') or '')[:32]}...")
            if out.get('content_excerpt'):
                print(f"   Preview: {out['content_excerpt'][:300]}...")
    scores = cert.get("scores", {})
    if scores:
        print(f"   Scores : fidelity={scores.get('fidelity_score')} · quality={scores.get('quality_score')}")
    parties = cert.get("parties", {})
    if parties:
        print(f"   Parties: customer={parties.get('customer')} · agent={parties.get('agent')}")
    verdict = cert.get("customer_verdict", {})
    if verdict and verdict.get("verdict"):
        print(f"   Verdict: {verdict.get('verdict')} · rating={verdict.get('rating')}")
    sig = cert.get("signature")
    if isinstance(sig, dict):
        sig_val = sig.get("value")
    else:
        sig_val = sig
    print(f"   Sig    : {(sig_val or '')[:64]}...")
    print(f"   Public : {API_BASE}/cert/{audit_id}")

    if args.verify and not use_public:
        # Re-verify signature via public endpoint
        verify_body = {
            "payload": {k: v for k, v in cert.items() if k != "signature"},
            "claimed_signature": sig_val,
        }
        verify_result = _http("POST", f"/api/v1/public/cert/{audit_id}/verify", verify_body, auth=False)
        vd = verify_result.get("data", {})
        if vd.get("valid"):
            print("   🔐 Signature VERIFIED ✅")
        else:
            print(f"   🔐 Signature INVALID ❌ · note: {vd.get('note')}")
    return 0


def cmd_code(args: argparse.Namespace) -> int:
    """Generate code via Nautilus Engine · check → audit → optional commit."""
    # Engine lives in phase3/backend/engine · sibling of phase3/cli
    engine_pkg_dir = Path(__file__).resolve().parent.parent.parent / "backend"
    if str(engine_pkg_dir) not in sys.path:
        sys.path.insert(0, str(engine_pkg_dir))

    try:
        from engine.nautilus_engine import NautilusEngine
        from engine.repo_map import RepoMap
        from engine.ship import ship
    except ImportError as e:
        print(f"ERROR: cannot import engine modules from {engine_pkg_dir}: {e}", file=sys.stderr)
        return 7

    base = Path(args.base_dir).resolve()
    if not base.exists():
        print(f"ERROR: base-dir does not exist: {base}", file=sys.stderr)
        return 8

    repo_map = None
    if not args.no_repo_map:
        print(f"[scan] indexing {base} for context map ...")
        repo_map = RepoMap(str(base))
        repo_map.scan()
        print(f"       {len(repo_map._files)} files indexed")

    engine = NautilusEngine(
        repo_map=repo_map,
        repo_context_budget=args.budget_tokens,
        base_dir=str(base),
        dry_run=True,  # ship() owns staging · always dry at engine level
    )

    api_key = None if args.no_audit else _get_api_key()
    commit_msg = args.commit_msg if args.apply and args.commit_msg else None

    print(f"[gen]  task={args.task[:80]}")
    result = ship(
        engine=engine,
        task=args.task,
        base_dir=str(base),
        apply=args.apply,
        fidelity_threshold=args.fidelity_threshold,
        dispatch_audit=not args.no_audit,
        api_key=api_key,
        git_commit_msg=commit_msg,
        run_runtime_check=args.runtime_check,
        run_runtime_args_check=args.runtime_args_check,
        runtime_timeout=args.runtime_timeout,
        max_retries=args.max_retries,
        request_a2a_review=args.a2a_review,
        a2a_timeout=args.a2a_timeout,
        cycle_id=args.cycle_id,
    )

    print()
    print(f"[plan] {len(result.files_planned)} files:")
    for f in result.files_planned:
        print(f"       - {f['path']} ({f['size']} chars · {f['lang']})")

    cks = result.check_result.get("checks", [])
    print(f"[chk]  passed={result.check_result.get('passed')} · {len(cks)} run")
    for c in cks:
        flag = "PASS" if c["passed"] else "FAIL"
        skip = " [skip]" if c.get("skipped") else ""
        msg = (c.get("message") or "")[:70]
        print(f"       [{flag}] {c['name']}{skip} · {c.get('duration_ms', 0)}ms · {msg}")

    if hasattr(result, "attempts") and len(result.attempts) > 1:
        print(f"[retry] {len(result.attempts)} attempts total (max_retries={args.max_retries})")
        for att in result.attempts:
            p = att["check_result"].get("passed")
            print(f"        attempt {att['attempt_number']}: passed={p} · files={len(att['files_planned'])} · raw={att['raw_response_chars']} chars")

    if result.audit:
        if result.audit.get("skipped"):
            print(f"[audit] skipped · {result.audit.get('reason')}")
        elif result.audit.get("error"):
            print(f"[audit] ERROR · {result.audit['error']}")
        else:
            fid = result.audit.get("fidelity_score")
            print(f"[audit] dispatched · id={result.audit.get('audit_id')} · fidelity={fid}")

    if getattr(result, "a2a_review", None):
        ar = result.a2a_review
        if ar.get("error"):
            print(f"[a2a]   ERROR · {ar['error']}")
        else:
            tl = len(ar.get("timeouts", []) or [])
            print(f"[a2a]   approve={ar.get('approve_count', 0)} · reject={ar.get('reject_count', 0)} · abstain={ar.get('abstain_count', 0)} · timeouts={tl}")

    if result.applied:
        commit_note = f" · commit={result.git_commit[:10]}" if result.git_commit else " · no commit"
        print(f"[done] APPLIED{commit_note}")
        return 0
    elif args.apply:
        print(f"[done] NOT applied · errors: {result.errors}")
        return 9
    else:
        print(f"[done] dry-run · pass --apply (and optionally --commit-msg) to write+commit")
        return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Run the canned-replay walkthrough · no auth · no network."""
    from .demo import run_demo
    return run_demo()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="nautilus",
        description="Nautilus CLI · multi-agent audit with stake-backed cert · github.com/chunxiaoxx/nautilus-core",
    )
    parser.add_argument("--version", action="version", version=f"nautilus-cli {__version__}")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Configure API key + base URL")
    p_init.set_defaults(func=cmd_init)

    p_audit = sub.add_parser("audit", help="Dispatch a new audit from a spec file")
    p_audit.add_argument("spec_file", help="Path to spec file (markdown / plain text · 20-10000 chars)")
    p_audit.add_argument("--budget", type=int, default=100, help="Budget in NAU (default 100 · range 10-100000)")
    p_audit.add_argument("--deadline", type=int, default=24, help="Deadline in hours (default 24 · range 1-720)")
    p_audit.add_argument("--title", default=None, help="Optional title (default: filename)")
    p_audit.add_argument("--task-type", default="general", help="Task type (default: general · platform_meta for council route)")
    p_audit.add_argument("--watch", action="store_true", help="Watch status until completion (max 15 min)")
    p_audit.set_defaults(func=cmd_audit)

    p_code = sub.add_parser(
        "code",
        aliases=["engine"],
        help="Generate code via Nautilus Engine (check → audit → optional commit) · `nautilus engine <task>` is an equivalent alias",
    )
    p_code.add_argument("task", help="Task description (natural language · what to build)")
    p_code.add_argument("--base-dir", default=".", help="Project root for context + writes (default cwd)")
    p_code.add_argument("--apply", action="store_true", help="Actually write files (default: dry-run preview)")
    p_code.add_argument("--commit-msg", default=None, help="Git commit message (only with --apply)")
    p_code.add_argument("--no-audit", action="store_true", help="Skip /api/v1/audit/dispatch POST")
    p_code.add_argument("--no-repo-map", action="store_true", help="Skip repository symbol map context")
    p_code.add_argument("--budget-tokens", type=int, default=1000, help="Token budget for repo map context (default 1000)")
    p_code.add_argument("--fidelity-threshold", type=float, default=0.7, help="Min fidelity to allow apply (default 0.7 · ignored when --no-audit)")
    p_code.add_argument("--runtime-check", action="store_true", help="Add subprocess runtime smoke without args (catches import + top-level errors)")
    p_code.add_argument("--runtime-args-check", action="store_true", help="Add subprocess runtime smoke with auto-detected sample args (catches main()-only bugs · cycle 7)")
    p_code.add_argument("--runtime-timeout", type=int, default=10, help="Runtime check timeout in seconds (default 10)")
    p_code.add_argument("--max-retries", type=int, default=0, help="Self-healing retry · re-prompt LLM with error context on check failure (default 0 · cycle 8)")
    p_code.add_argument("--a2a-review", action="store_true", help="Request V5/V7/Kairos council review via platform_agent_messages (needs DATABASE_URL · v5agent cycle 8 a2a wiring)")
    p_code.add_argument("--a2a-timeout", type=int, default=30, help="A2A review poll timeout in seconds (default 30)")
    p_code.add_argument(
        "--cycle-id", default=None,
        help="Cycle ID for outcome telemetry (default: auto YYYYMMDD_sha8(task))",
    )
    p_code.set_defaults(func=cmd_code)

    p_status = sub.add_parser("status", help="Get current audit status")
    p_status.add_argument("audit_id", help="Audit ID returned from `nautilus audit`")
    p_status.add_argument("--watch", action="store_true", help="Poll until terminal state (max 15 min)")
    p_status.set_defaults(func=cmd_status)

    p_cert = sub.add_parser("cert", help="Get the signed audit certificate")
    p_cert.add_argument("audit_id", help="Audit ID")
    p_cert.add_argument("--verify", action="store_true", help="Re-verify HMAC signature via public endpoint")
    p_cert.add_argument("--json", action="store_true", help="Output raw JSON (default: human-readable summary)")
    p_cert.add_argument("--public", action="store_true", help="Use public endpoint (no auth needed)")
    p_cert.set_defaults(func=cmd_cert)

    p_demo = sub.add_parser("demo", help="Canned-replay walkthrough of cycle 5 + 9 dogfood (no API key)")
    p_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
