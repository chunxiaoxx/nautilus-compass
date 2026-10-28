"""
Bootstrap CLI - Command-line interface for the NautilusBootstrapAgent.

Usage:
  python -m bootstrap.bootstrap_cli --analyze             # Scan for issues
  python -m bootstrap.bootstrap_cli --improve             # Generate & validate fixes
  python -m bootstrap.bootstrap_cli --optimize-prompts    # Optimize executor prompts
  python -m bootstrap.bootstrap_cli --report              # Full report to JSON file

Run from: cd phase3/agent-engine && python -m bootstrap.bootstrap_cli <command>
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bootstrap.nautilus_bootstrap_agent import (
    NautilusBootstrapAgent,
    _find_python_files,
)

logger = logging.getLogger(__name__)

# Output directory for reports
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def _get_project_root() -> str:
    """Resolve the Nautilus project root."""
    # bootstrap_cli.py lives in phase3/agent-engine/bootstrap/
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )


def _get_agent(use_llm: bool = True) -> NautilusBootstrapAgent:
    """Create a BootstrapAgent, optionally with a real LLM client."""
    root = _get_project_root()
    if use_llm:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
        from llm.client import get_llm_client
        llm = get_llm_client()
    else:
        llm = None  # Analysis-only mode doesn't need LLM
    return NautilusBootstrapAgent(llm_client=llm, project_root=root)


def _ensure_reports_dir():
    """Create the reports directory if it doesn't exist."""
    os.makedirs(REPORTS_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

async def cmd_analyze(args):
    """Scan the codebase and print issues."""
    agent = _get_agent(use_llm=False)
    issues = await agent.analyze_codebase()

    # Summary counts
    by_severity = {}
    by_category = {}
    for issue in issues:
        by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
        by_category[issue.category] = by_category.get(issue.category, 0) + 1

    print(f"\n{'='*60}")
    print(f"Nautilus Bootstrap Agent - Codebase Analysis")
    print(f"{'='*60}")
    print(f"Python files scanned: {len(_find_python_files(agent.project_root))}")
    print(f"Total issues found: {len(issues)}")
    print()

    print("By severity:")
    for sev in ("critical", "high", "medium", "low"):
        count = by_severity.get(sev, 0)
        if count > 0:
            print(f"  {sev.upper():10s}: {count}")

    print("\nBy category:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat:20s}: {count}")

    # Print top issues
    limit = args.limit if hasattr(args, "limit") else 20
    print(f"\nTop {min(limit, len(issues))} issues:")
    print(f"{'-'*60}")
    for issue in issues[:limit]:
        print(f"  [{issue.severity.upper():8s}] {issue.file}:{issue.line}")
        print(f"            {issue.description}")
        if issue.context:
            print(f"            > {issue.context[:80]}")
        print()

    # Save to file if requested
    if args.output:
        _ensure_reports_dir()
        out_path = os.path.join(REPORTS_DIR, args.output)
        with open(out_path, "w") as f:
            json.dump([i.to_dict() for i in issues], f, indent=2)
        print(f"Full results saved to {out_path}")


async def cmd_improve(args):
    """Generate and validate improvements."""
    agent = _get_agent(use_llm=True)
    report = await agent.run_improvement_cycle()

    print(f"\n{'='*60}")
    print(f"Nautilus Bootstrap Agent - Improvement Cycle")
    print(f"{'='*60}")
    print(f"Issues found:           {report.issues_found}")
    print(f"Improvements proposed:  {report.improvements_proposed}")
    print(f"Improvements validated: {report.improvements_validated}")
    print()

    for imp in report.improvements:
        status = "VALID" if imp.get("validated") else "INVALID"
        print(f"  [{status}] {imp['file']} ({imp['category']})")
        print(f"    {imp['description']}")
        if imp.get("validation_error"):
            print(f"    Error: {imp['validation_error']}")
        print()

    if report.improvements_validated > 0:
        print("Validated improvements (ready for review):")
        print(f"{'-'*60}")
        for imp in report.improvements:
            if not imp.get("validated"):
                continue
            print(f"\nFile: {imp['file']}")
            print(f"Description: {imp['description']}")
            print(f"Confidence: {imp.get('confidence', 0):.0%}")
            print(f"\n--- OLD ---\n{imp['old_code']}")
            print(f"\n--- NEW ---\n{imp['new_code']}")
            print(f"{'~'*40}")

    # Save report
    _ensure_reports_dir()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(REPORTS_DIR, f"improvement_{ts}.json")
    with open(out_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"\nReport saved to {out_path}")


async def cmd_optimize_prompts(args):
    """Optimize executor prompts using task result data."""
    agent = _get_agent(use_llm=True)
    result = await agent.optimize_prompts()

    print(f"\n{'='*60}")
    print(f"Nautilus Bootstrap Agent - Prompt Optimization")
    print(f"{'='*60}")

    if not result.get("optimized"):
        print(f"No optimization performed: {result.get('reason', 'unknown')}")
        return

    print(f"Analyzed results: {result.get('analyzed_results', 0)}")
    print(f"Reasoning: {result.get('reasoning', 'N/A')}")

    patterns = result.get("patterns", [])
    if patterns:
        print(f"\nPatterns identified:")
        for p in patterns:
            print(f"  - {p}")

    recommendations = result.get("recommendations", [])
    if recommendations:
        print(f"\nRecommendations ({len(recommendations)}):")
        for rec in recommendations:
            print(f"  Target: {rec.get('target', 'N/A')}")
            print(f"  Issue:  {rec.get('current_issue', 'N/A')}")
            print(f"  Change: {rec.get('suggested_change', 'N/A')}")
            print(f"  Impact: {rec.get('expected_impact', 'N/A')}")
            print()

    # Save
    _ensure_reports_dir()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(REPORTS_DIR, f"prompt_opt_{ts}.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Report saved to {out_path}")


async def cmd_report(args):
    """Generate a comprehensive analysis report."""
    agent = _get_agent(use_llm=False)
    report = await agent.generate_report()

    # Aggregate stats
    by_sev = {}
    by_cat = {}
    by_file = {}
    for issue in report.issues:
        sev = issue.get("severity", "unknown")
        cat = issue.get("category", "unknown")
        fil = issue.get("file", "unknown")
        by_sev[sev] = by_sev.get(sev, 0) + 1
        by_cat[cat] = by_cat.get(cat, 0) + 1
        by_file[fil] = by_file.get(fil, 0) + 1

    print(f"\n{'='*60}")
    print(f"Nautilus Bootstrap Agent - Full Report")
    print(f"{'='*60}")
    print(f"Total issues: {report.issues_found}")
    print()

    print("Severity breakdown:")
    for sev in ("critical", "high", "medium", "low"):
        count = by_sev.get(sev, 0)
        bar = "#" * min(count, 40)
        print(f"  {sev.upper():10s}: {count:4d}  {bar}")

    print("\nCategory breakdown:")
    for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {cat:20s}: {count}")

    # Top files with most issues
    top_files = sorted(by_file.items(), key=lambda x: -x[1])[:10]
    if top_files:
        print(f"\nTop files by issue count:")
        for fil, count in top_files:
            print(f"  {count:3d}  {fil}")

    # Save full report
    _ensure_reports_dir()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(REPORTS_DIR, f"report_{ts}.json")
    full_report = {
        "timestamp": report.timestamp,
        "total_issues": report.issues_found,
        "by_severity": by_sev,
        "by_category": by_cat,
        "top_files": dict(top_files),
        "issues": report.issues,
    }
    with open(out_path, "w") as f:
        json.dump(full_report, f, indent=2)
    print(f"\nFull report saved to {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Nautilus Bootstrap Agent - Self-improvement CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m bootstrap.bootstrap_cli --analyze
  python -m bootstrap.bootstrap_cli --analyze --limit 50 --output issues.json
  python -m bootstrap.bootstrap_cli --improve
  python -m bootstrap.bootstrap_cli --optimize-prompts
  python -m bootstrap.bootstrap_cli --report
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--analyze", action="store_true",
                       help="Scan codebase for issues (no changes)")
    group.add_argument("--improve", action="store_true",
                       help="Generate and validate improvements")
    group.add_argument("--optimize-prompts", action="store_true",
                       help="Optimize executor prompts from task data")
    group.add_argument("--report", action="store_true",
                       help="Generate a full analysis report")

    parser.add_argument("--limit", type=int, default=20,
                        help="Max issues to display (default: 20)")
    parser.add_argument("--output", type=str, default="",
                        help="Save results to file (in reports/ dir)")
    parser.add_argument("--verbose", action="store_true", default=True,
                        help="Verbose output")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if args.analyze:
        asyncio.run(cmd_analyze(args))
    elif args.improve:
        asyncio.run(cmd_improve(args))
    elif args.optimize_prompts:
        asyncio.run(cmd_optimize_prompts(args))
    elif args.report:
        asyncio.run(cmd_report(args))


if __name__ == "__main__":
    main()
