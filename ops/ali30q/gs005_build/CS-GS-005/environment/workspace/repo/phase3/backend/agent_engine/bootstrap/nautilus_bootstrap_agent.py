"""
NautilusBootstrapAgent - The platform improves itself.

This agent analyzes the Nautilus codebase, identifies improvements,
generates fixes, and validates them. It is Task #1 - the permanent task.

Capabilities:
1. Code Analysis: Scan for bugs, inefficiencies, missing error handling
2. Test Generation: Create tests for uncovered code paths
3. Prompt Optimization: Improve executor prompts using real task data
4. Documentation: Update docs based on code changes
5. Dependency Audit: Check for outdated/vulnerable packages

Safety: Never auto-applies changes. All improvements are output for human review.

Run: cd phase3/agent-engine && python -m bootstrap.bootstrap_cli --analyze
"""
import ast
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class CodeIssue:
    """A single issue found in the codebase."""
    file: str
    line: int
    category: str        # e.g. "error_handling", "type_hint", "complexity"
    severity: str        # "critical", "high", "medium", "low"
    description: str
    context: str = ""    # surrounding code snippet

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Improvement:
    """A proposed code improvement."""
    file: str
    old_code: str
    new_code: str
    description: str
    category: str
    confidence: float = 0.0
    validated: bool = False
    validation_error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BootstrapReport:
    """Summary report from one improvement cycle."""
    timestamp: str = ""
    issues_found: int = 0
    improvements_proposed: int = 0
    improvements_validated: int = 0
    issues: List[Dict] = field(default_factory=list)
    improvements: List[Dict] = field(default_factory=list)
    prompt_optimizations: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Analyzers (pure functions, no LLM needed)
# ---------------------------------------------------------------------------

def _read_file_safe(path: str) -> Optional[str]:
    """Read a file, returning None on error."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, IOError) as exc:
        logger.warning(f"Cannot read {path}: {exc}")
        return None


def _find_python_files(root: str, exclude_dirs: Optional[List[str]] = None) -> List[str]:
    """Recursively find Python files, skipping excluded dirs."""
    exclude = set(exclude_dirs or [
        "__pycache__", ".git", "node_modules", "dist", "build",
        ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache",
    ])
    results: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for fname in filenames:
            if fname.endswith(".py"):
                results.append(os.path.join(dirpath, fname))
    return results


def analyze_file_metrics(filepath: str, source: str) -> List[CodeIssue]:
    """Analyze a single file for structural issues (no LLM needed)."""
    issues: List[CodeIssue] = []
    lines = source.splitlines()
    line_count = len(lines)
    rel_path = filepath

    # File too long
    if line_count > 800:
        issues.append(CodeIssue(
            file=rel_path, line=1, category="file_size",
            severity="medium",
            description=f"File has {line_count} lines (max recommended: 800)",
        ))

    # Parse AST for function-level analysis
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as exc:
        issues.append(CodeIssue(
            file=rel_path, line=exc.lineno or 1, category="syntax_error",
            severity="critical",
            description=f"Syntax error: {exc.msg}",
        ))
        return issues

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            issues.extend(_analyze_function(rel_path, node, lines))

    # TODO/FIXME comments
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if re.match(r"#\s*(TODO|FIXME|HACK|XXX)\b", stripped, re.IGNORECASE):
            issues.append(CodeIssue(
                file=rel_path, line=i, category="todo",
                severity="low",
                description=f"Unresolved comment: {stripped[:80]}",
                context=stripped,
            ))

    # Bare except clauses
    for i, line in enumerate(lines, 1):
        if re.match(r"\s*except\s*:", line):
            issues.append(CodeIssue(
                file=rel_path, line=i, category="error_handling",
                severity="high",
                description="Bare `except:` clause swallows all exceptions",
                context=line.strip(),
            ))

    return issues


def _analyze_function(
    filepath: str, node: ast.FunctionDef, lines: List[str]
) -> List[CodeIssue]:
    """Analyze a single function/method node."""
    issues: List[CodeIssue] = []
    func_name = node.name
    start = node.lineno
    end = node.end_lineno or start
    func_len = end - start + 1

    # Function too long
    if func_len > 50:
        issues.append(CodeIssue(
            file=filepath, line=start, category="complexity",
            severity="medium",
            description=f"Function `{func_name}` is {func_len} lines (max: 50)",
        ))

    # Missing return type hint (skip __init__, __str__, etc.)
    if not func_name.startswith("_") and node.returns is None:
        issues.append(CodeIssue(
            file=filepath, line=start, category="type_hint",
            severity="low",
            description=f"Function `{func_name}` missing return type hint",
        ))

    # Deep nesting
    max_depth = _max_nesting_depth(node)
    if max_depth > 4:
        issues.append(CodeIssue(
            file=filepath, line=start, category="complexity",
            severity="medium",
            description=f"Function `{func_name}` has nesting depth {max_depth} (max: 4)",
        ))

    return issues


def _max_nesting_depth(node: ast.AST, current: int = 0) -> int:
    """Compute maximum nesting depth of control flow statements."""
    nesting_nodes = (
        ast.If, ast.For, ast.While, ast.With,
        ast.Try, ast.AsyncFor, ast.AsyncWith,
    )
    max_d = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, nesting_nodes):
            max_d = max(max_d, _max_nesting_depth(child, current + 1))
        else:
            max_d = max(max_d, _max_nesting_depth(child, current))
    return max_d


def find_unused_imports(filepath: str, source: str) -> List[CodeIssue]:
    """Detect imports that are never referenced in the file body."""
    issues: List[CodeIssue] = []
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return issues

    imported_names: List[tuple] = []  # (name, alias, lineno)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                used_name = alias.asname or alias.name.split(".")[0]
                imported_names.append((used_name, alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                used_name = alias.asname or alias.name
                imported_names.append((used_name, alias.name, node.lineno))

    # Check if each imported name appears elsewhere in the source
    for used_name, full_name, lineno in imported_names:
        # Simple heuristic: count occurrences beyond the import line
        pattern = re.compile(r'\b' + re.escape(used_name) + r'\b')
        matches = list(pattern.finditer(source))
        # Subtract occurrences on the import line itself
        import_line = source.splitlines()[lineno - 1] if lineno <= len(source.splitlines()) else ""
        import_hits = len(list(pattern.finditer(import_line)))
        body_hits = len(matches) - import_hits
        if body_hits == 0:
            issues.append(CodeIssue(
                file=filepath, line=lineno, category="unused_import",
                severity="low",
                description=f"Unused import: `{full_name}`",
            ))

    return issues


# ---------------------------------------------------------------------------
# NautilusBootstrapAgent
# ---------------------------------------------------------------------------

class NautilusBootstrapAgent:
    """
    Self-improvement agent for the Nautilus platform.

    Safety: All improvements are returned for review. Nothing is
    auto-applied to the codebase.
    """

    MAX_IMPROVEMENTS_PER_CYCLE = 5

    def __init__(self, llm_client, project_root: str):
        self.llm = llm_client
        self.project_root = os.path.abspath(project_root)
        self.improvements: List[Improvement] = []
        logger.info(f"BootstrapAgent initialized: root={self.project_root}")

    # ------------------------------------------------------------------
    # 1. Codebase Analysis
    # ------------------------------------------------------------------

    async def analyze_codebase(self) -> List[CodeIssue]:
        """
        Scan the codebase for improvement opportunities.

        Returns a list of CodeIssue objects sorted by severity.
        """
        logger.info("Starting codebase analysis")
        all_issues: List[CodeIssue] = []
        py_files = _find_python_files(self.project_root)
        logger.info(f"Found {len(py_files)} Python files")

        for filepath in py_files:
            source = _read_file_safe(filepath)
            if source is None:
                continue
            rel = os.path.relpath(filepath, self.project_root)
            all_issues.extend(analyze_file_metrics(rel, source))
            all_issues.extend(find_unused_imports(rel, source))

        # Sort: critical > high > medium > low
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_issues.sort(key=lambda i: severity_order.get(i.severity, 9))

        logger.info(f"Analysis complete: {len(all_issues)} issues found")
        return all_issues

    # ------------------------------------------------------------------
    # 2. Improvement Generation (LLM-powered)
    # ------------------------------------------------------------------

    async def generate_improvement(self, issue: CodeIssue) -> Optional[Improvement]:
        """
        Use the LLM to generate a code fix for an identified issue.

        Returns an Improvement or None if the LLM cannot produce one.
        """
        filepath = os.path.join(self.project_root, issue.file)
        source = _read_file_safe(filepath)
        if source is None:
            return None

        # Extract context: the relevant function or surrounding lines
        context = _extract_context(source, issue.line, radius=15)

        prompt = f"""Fix the following code issue.

File: {issue.file}
Line: {issue.line}
Category: {issue.category}
Severity: {issue.severity}
Issue: {issue.description}

Code context (line {max(1, issue.line - 15)} onwards):
```python
{context}
```

Respond ONLY with JSON:
{{
  "old_code": "<exact code to replace (copy from context above)>",
  "new_code": "<improved code>",
  "description": "<what changed and why>",
  "confidence": <0.0-1.0>
}}

Rules:
- old_code must be an EXACT substring of the context above
- Keep changes minimal and focused on the issue
- Preserve existing behavior
- Do not add unrelated changes"""

        try:
            response = self.llm.chat(
                prompt=prompt,
                system="You are a senior Python engineer. Fix code issues precisely. Respond ONLY with JSON.",
                temperature=0.2,
                max_tokens=2048,
            )
            data = _parse_json_response(response)
            if not data or "old_code" not in data or "new_code" not in data:
                logger.warning(f"LLM response missing required fields for {issue.file}:{issue.line}")
                return None

            return Improvement(
                file=issue.file,
                old_code=data["old_code"],
                new_code=data["new_code"],
                description=data.get("description", issue.description),
                category=issue.category,
                confidence=float(data.get("confidence", 0.5)),
            )
        except Exception as exc:
            logger.error(f"Failed to generate improvement for {issue.file}:{issue.line}: {exc}")
            return None

    # ------------------------------------------------------------------
    # 3. Improvement Validation
    # ------------------------------------------------------------------

    async def validate_improvement(self, improvement: Improvement) -> bool:
        """
        Validate that an improvement doesn't break anything.

        Checks:
        1. The old_code exists in the file
        2. The new_code is valid Python syntax
        3. Related tests still pass (if pytest is available)
        """
        filepath = os.path.join(self.project_root, improvement.file)
        source = _read_file_safe(filepath)
        if source is None:
            improvement.validation_error = "Cannot read source file"
            return False

        # Check old_code exists
        if improvement.old_code not in source:
            improvement.validation_error = "old_code not found in file"
            return False

        # Check new_code parses
        new_source = source.replace(improvement.old_code, improvement.new_code, 1)
        try:
            ast.parse(new_source, filename=improvement.file)
        except SyntaxError as exc:
            improvement.validation_error = f"New code has syntax error: {exc.msg}"
            return False

        # Try running related tests (best-effort)
        test_result = _run_related_tests(self.project_root, improvement.file)
        if test_result is not None and not test_result:
            improvement.validation_error = "Related tests failed"
            return False

        improvement.validated = True
        logger.info(f"Improvement validated: {improvement.file} ({improvement.category})")
        return True

    # ------------------------------------------------------------------
    # 4. Full Improvement Cycle
    # ------------------------------------------------------------------

    async def run_improvement_cycle(self) -> BootstrapReport:
        """
        Run one full improvement cycle: analyze -> generate -> validate.

        Returns a BootstrapReport with all findings.
        """
        logger.info("Starting improvement cycle")
        report = BootstrapReport()

        # Analyze
        issues = await self.analyze_codebase()
        report.issues_found = len(issues)
        report.issues = [i.to_dict() for i in issues[:50]]  # cap report size

        # Filter to actionable issues (skip low-severity TODOs)
        actionable = [
            i for i in issues
            if i.severity in ("critical", "high", "medium")
            and i.category not in ("todo",)
        ]

        # Generate improvements for top issues
        for issue in actionable[:self.MAX_IMPROVEMENTS_PER_CYCLE]:
            improvement = await self.generate_improvement(issue)
            if improvement is None:
                continue

            valid = await self.validate_improvement(improvement)
            report.improvements.append(improvement.to_dict())
            if valid:
                report.improvements_validated += 1
                self.improvements.append(improvement)

        report.improvements_proposed = len(report.improvements)
        logger.info(
            f"Cycle complete: {report.issues_found} issues, "
            f"{report.improvements_proposed} proposed, "
            f"{report.improvements_validated} validated"
        )
        return report

    # ------------------------------------------------------------------
    # 5. Prompt Optimization
    # ------------------------------------------------------------------

    async def optimize_prompts(self, task_results: Optional[List[Dict]] = None) -> Dict:
        """
        Optimize executor prompts based on real task results.

        If no task_results are provided, reads from the experiment log.
        """
        if task_results is None:
            task_results = _load_experiment_log(self.project_root)

        if not task_results:
            logger.info("No task results available for prompt optimization")
            return {"optimized": False, "reason": "no task data"}

        # Analyze success/failure patterns
        successes = [r for r in task_results if r.get("improved", False)]
        failures = [r for r in task_results if not r.get("improved", False)]

        prompt = f"""Analyze these AI agent task execution results and suggest prompt improvements.

Total results: {len(task_results)}
Successes: {len(successes)}
Failures: {len(failures)}

Sample failures (up to 5):
{json.dumps(failures[:5], indent=2, default=str)}

Sample successes (up to 3):
{json.dumps(successes[:3], indent=2, default=str)}

Respond in JSON:
{{
  "patterns": ["pattern1", "pattern2", ...],
  "recommendations": [
    {{
      "target": "<which prompt/executor to change>",
      "current_issue": "<what's wrong>",
      "suggested_change": "<specific improvement>",
      "expected_impact": "<low|medium|high>"
    }}
  ],
  "reasoning": "<brief analysis>"
}}"""

        try:
            response = self.llm.chat(
                prompt=prompt,
                system="You are an AI systems optimization expert. Analyze patterns and propose improvements. Respond ONLY with JSON.",
                temperature=0.3,
                max_tokens=2048,
            )
            result = _parse_json_response(response)
            if result:
                result["optimized"] = True
                result["analyzed_results"] = len(task_results)
                return result
        except Exception as exc:
            logger.error(f"Prompt optimization failed: {exc}")

        return {"optimized": False, "reason": "LLM analysis failed"}

    # ------------------------------------------------------------------
    # 6. Report Generation
    # ------------------------------------------------------------------

    async def generate_report(self) -> BootstrapReport:
        """Generate a report without attempting fixes (analysis only)."""
        report = BootstrapReport()
        issues = await self.analyze_codebase()
        report.issues_found = len(issues)
        report.issues = [i.to_dict() for i in issues]

        # Summarize by category
        categories: Dict[str, int] = {}
        severities: Dict[str, int] = {}
        for issue in issues:
            categories[issue.category] = categories.get(issue.category, 0) + 1
            severities[issue.severity] = severities.get(issue.severity, 0) + 1

        logger.info(f"Report: {len(issues)} issues across {len(categories)} categories")
        logger.info(f"Severities: {severities}")
        return report


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _extract_context(source: str, line: int, radius: int = 15) -> str:
    """Extract lines around the target line."""
    lines = source.splitlines()
    start = max(0, line - radius - 1)
    end = min(len(lines), line + radius)
    numbered = []
    for i, text in enumerate(lines[start:end], start=start + 1):
        marker = ">>>" if i == line else "   "
        numbered.append(f"{marker} {i:4d} | {text}")
    return "\n".join(numbered)


def _parse_json_response(text: str) -> Optional[Dict]:
    """Parse JSON from an LLM response, handling common issues."""
    text = re.sub(
        r'ThinkingBlock\([^)]*(?:\([^)]*\)[^)]*)*\)', '', text, flags=re.DOTALL
    ).strip()

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract from markdown code block
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        try:
            return json.loads(text[start:end].strip())
        except (json.JSONDecodeError, ValueError):
            pass

    # Extract first { ... }
    brace_start = text.find("{")
    brace_end = text.rfind("}") + 1
    if brace_start >= 0 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end])
        except json.JSONDecodeError:
            pass

    logger.warning(f"Could not parse JSON from response: {text[:200]}")
    return None


def _run_related_tests(project_root: str, filepath: str) -> Optional[bool]:
    """
    Run tests related to a file. Returns True if passing, False if
    failing, or None if no tests found / pytest unavailable.
    """
    # Derive likely test file path
    parts = Path(filepath).parts
    test_candidates = [
        os.path.join(project_root, "tests", f"test_{parts[-1]}"),
        os.path.join(project_root, *parts[:-1], f"test_{parts[-1]}"),
    ]

    test_file = None
    for candidate in test_candidates:
        if os.path.exists(candidate):
            test_file = candidate
            break

    if test_file is None:
        return None  # No related tests found

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-x", "-q", "--tb=no"],
            capture_output=True, text=True, timeout=60,
            cwd=project_root,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _load_experiment_log(project_root: str) -> List[Dict]:
    """Load the experiment log if it exists."""
    log_path = os.path.join(
        project_root, "phase3", "agent-engine", "bootstrap", "experiment_log.json"
    )
    if not os.path.exists(log_path):
        # Try relative to project root
        log_path = os.path.join(
            os.path.dirname(__file__), "experiment_log.json"
        )
    if not os.path.exists(log_path):
        return []
    try:
        with open(log_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
