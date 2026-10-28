"""
Bootstrap feedback loop - the platform improves itself.

Runs periodically to:
1. Analyze recent task results (success/failure rates per type)
2. Extract failure patterns (common errors, timeout issues)
3. Optimize templates based on real execution data
4. Track improvement metrics over time
"""
import json
import logging
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import case, func, literal
from sqlalchemy.orm import Session

from models.database import AcademicTask
from services.academic_templates import ACADEMIC_TEMPLATES, AcademicTemplate

logger = logging.getLogger(__name__)

# Persistent storage for cycle reports
_REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "bootstrap_loop"
)

# Known error patterns and their categories
_ERROR_PATTERNS: Dict[str, str] = {
    r"read-only file system": "filesystem_readonly",
    r"ModuleNotFoundError": "missing_module",
    r"SyntaxError": "code_syntax",
    r"TimeoutError|timed?\s*out": "timeout",
    r"substring not found": "code_extraction",
    r"MemoryError": "memory_exceeded",
    r"PermissionError": "permission_denied",
    r"FileNotFoundError": "file_not_found",
    r"ZeroDivisionError": "division_by_zero",
    r"ValueError": "value_error",
}


class TaskAnalysis(BaseModel):
    """Aggregated analysis for a single task type."""
    task_type: str
    total: int
    completed: int
    failed: int
    success_rate: float
    avg_execution_time: float
    common_errors: List[str]
    avg_code_lines: float


class FailurePattern(BaseModel):
    """A detected failure pattern across tasks."""
    category: str
    count: int
    affected_task_types: List[str]
    sample_errors: List[str]


class ImprovementAction(BaseModel):
    """A concrete improvement to apply to a template."""
    task_type: str
    issue: str
    action: str  # "reduce_lines", "add_guard", "simplify_prompt", "add_example"
    detail: str
    applied: bool
    timestamp: str


class BootstrapLoop:
    """Feedback loop that analyzes task outcomes and suggests template improvements."""

    def __init__(self, db: Session) -> None:
        self._db = db
        os.makedirs(_REPORTS_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Analyze
    # ------------------------------------------------------------------

    def analyze_recent_tasks(self, days: int = 7) -> List[TaskAnalysis]:
        """Analyze task results from the last N days, grouped by task_type."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = (
            self._db.query(
                AcademicTask.task_type,
                func.count(AcademicTask.id).label("total"),
                func.sum(case(
                    (AcademicTask.status == "completed", literal(1)),
                    else_=literal(0),
                )).label("completed"),
                func.sum(case(
                    (AcademicTask.status == "failed", literal(1)),
                    else_=literal(0),
                )).label("failed"),
                func.avg(AcademicTask.execution_time).label("avg_exec"),
            )
            .filter(AcademicTask.created_at >= cutoff)
            .group_by(AcademicTask.task_type)
            .all()
        )

        analyses: List[TaskAnalysis] = []
        for row in rows:
            total = row.total or 0
            completed = int(row.completed or 0)
            failed = int(row.failed or 0)
            errors = self._collect_errors(row.task_type, cutoff)
            avg_lines = self._avg_code_lines(row.task_type, cutoff)
            analyses.append(TaskAnalysis(
                task_type=row.task_type,
                total=total,
                completed=completed,
                failed=failed,
                success_rate=completed / total if total > 0 else 0.0,
                avg_execution_time=float(row.avg_exec or 0.0),
                common_errors=errors[:5],
                avg_code_lines=avg_lines,
            ))

        # Sort by failure rate descending (worst first)
        analyses.sort(key=lambda a: a.success_rate)
        return analyses

    def _collect_errors(self, task_type: str, cutoff: datetime) -> List[str]:
        """Return most common error strings for a task type since cutoff."""
        error_rows = (
            self._db.query(AcademicTask.result_error)
            .filter(
                AcademicTask.task_type == task_type,
                AcademicTask.status == "failed",
                AcademicTask.created_at >= cutoff,
                AcademicTask.result_error.isnot(None),
            )
            .all()
        )
        counter: Counter[str] = Counter()
        for (err,) in error_rows:
            category = _categorize_error(err)
            counter[category] += 1
        return [cat for cat, _ in counter.most_common(5)]

    def _avg_code_lines(self, task_type: str, cutoff: datetime) -> float:
        """Return average number of lines in result_code for a task type."""
        code_rows = (
            self._db.query(AcademicTask.result_code)
            .filter(
                AcademicTask.task_type == task_type,
                AcademicTask.created_at >= cutoff,
                AcademicTask.result_code.isnot(None),
            )
            .all()
        )
        if not code_rows:
            return 0.0
        total_lines = sum(len((c or "").splitlines()) for (c,) in code_rows)
        return total_lines / len(code_rows)

    # ------------------------------------------------------------------
    # 2. Pattern detection
    # ------------------------------------------------------------------

    def identify_failure_patterns(
        self, analyses: List[TaskAnalysis]
    ) -> List[FailurePattern]:
        """Extract common failure patterns across task types."""
        category_map: Dict[str, Dict] = {}
        for analysis in analyses:
            for err_cat in analysis.common_errors:
                if err_cat not in category_map:
                    category_map[err_cat] = {
                        "count": 0,
                        "task_types": set(),
                        "samples": [],
                    }
                category_map[err_cat]["count"] += analysis.failed
                category_map[err_cat]["task_types"].add(analysis.task_type)

        # Fetch sample error messages per category
        self._attach_sample_errors(category_map)

        patterns = [
            FailurePattern(
                category=cat,
                count=info["count"],
                affected_task_types=sorted(info["task_types"]),
                sample_errors=info["samples"][:3],
            )
            for cat, info in category_map.items()
            if info["count"] > 0
        ]
        patterns.sort(key=lambda p: p.count, reverse=True)
        return patterns

    def _attach_sample_errors(self, category_map: Dict[str, Dict]) -> None:
        """Fetch a few raw error strings per category for context."""
        error_rows = (
            self._db.query(AcademicTask.result_error)
            .filter(
                AcademicTask.status == "failed",
                AcademicTask.result_error.isnot(None),
            )
            .limit(200)
            .all()
        )
        for (err,) in error_rows:
            cat = _categorize_error(err)
            if cat in category_map and len(category_map[cat]["samples"]) < 3:
                truncated = (err[:200] + "...") if len(err) > 200 else err
                category_map[cat]["samples"].append(truncated)

    # ------------------------------------------------------------------
    # 3. Suggest improvements
    # ------------------------------------------------------------------

    def suggest_improvements(
        self, analyses: List[TaskAnalysis], patterns: List[FailurePattern]
    ) -> List[ImprovementAction]:
        """Generate improvement actions based on analysis and patterns."""
        actions: List[ImprovementAction] = []
        now = datetime.utcnow().isoformat()

        for analysis in analyses:
            if analysis.success_rate >= 0.9:
                continue  # Good enough, skip
            actions.extend(self._actions_for_task(analysis, patterns, now))

        return actions

    def _actions_for_task(
        self,
        analysis: TaskAnalysis,
        patterns: List[FailurePattern],
        now: str,
    ) -> List[ImprovementAction]:
        """Generate actions for a single underperforming task type."""
        tt = analysis.task_type
        template = ACADEMIC_TEMPLATES.get(tt)
        if template is None:
            return []

        actions: List[ImprovementAction] = []

        # Rule: excessive code lines
        max_lines = _extract_max_lines(template.system_prompt)
        if max_lines and analysis.avg_code_lines > max_lines * 1.2:
            actions.append(ImprovementAction(
                task_type=tt,
                issue=f"avg code lines ({analysis.avg_code_lines:.0f}) exceeds MAX {max_lines}",
                action="reduce_lines",
                detail=f"Reduce MAX_LINES from {max_lines} to {max(40, max_lines - 10)}",
                applied=False,
                timestamp=now,
            ))

        # Rule: pattern-based actions
        relevant = [p for p in patterns if tt in p.affected_task_types]
        for pattern in relevant:
            action = _pattern_to_action(tt, pattern, now)
            if action is not None:
                actions.append(action)

        return actions

    # ------------------------------------------------------------------
    # 4. Apply
    # ------------------------------------------------------------------

    def apply_improvement(self, action: ImprovementAction) -> bool:
        """
        Apply a safe improvement action to the in-memory template registry.

        Supported actions: add_guard, reduce_lines, add_example.
        Templates are immutable, so we replace the registry entry with a new
        instance that incorporates the change.
        """
        template = ACADEMIC_TEMPLATES.get(action.task_type)
        if template is None:
            logger.warning("apply_improvement: unknown task_type %s", action.task_type)
            action.applied = False
            return False

        try:
            if action.action == "add_guard":
                # 去重闸(2026-10-10 · compass #10897 ④-1):同 detail 已在 prompt 中则跳过——
                # 根治"每 2h 向同一条活 prompt 追加同一句占位符"的自伤循环(981 轮实证)。
                if action.detail and action.detail in template.system_prompt:
                    action.applied = False
                    logger.info(
                        "bootstrap_loop add_guard dedup-skip on %s: %s",
                        action.task_type, action.detail[:80],
                    )
                    return False
                guard_text = f"\n{action.detail}"
                new_prompt = template.system_prompt + guard_text
                new_template = AcademicTemplate(
                    task_type=template.task_type,
                    display_name=template.display_name,
                    system_prompt=new_prompt,
                    description_suffix=template.description_suffix,
                    output_files=template.output_files,
                    validation_checks=template.validation_checks,
                )
                ACADEMIC_TEMPLATES[action.task_type] = new_template
                action.applied = True
                logger.info(
                    "bootstrap_loop applied add_guard to %s: %s",
                    action.task_type, action.detail[:80],
                )

            elif action.action == "reduce_lines":
                current_max = _extract_max_lines(template.system_prompt)
                if current_max is None:
                    action.applied = False
                    return False
                new_max = max(40, current_max - 10)
                new_prompt = re.sub(
                    r"MAX\s+" + str(current_max) + r"\s+lines",
                    f"MAX {new_max} lines",
                    template.system_prompt,
                    flags=re.IGNORECASE,
                )
                new_suffix = re.sub(
                    r"MAX\s+" + str(current_max) + r"\s+lines",
                    f"MAX {new_max} lines",
                    template.description_suffix,
                    flags=re.IGNORECASE,
                )
                new_template = AcademicTemplate(
                    task_type=template.task_type,
                    display_name=template.display_name,
                    system_prompt=new_prompt,
                    description_suffix=new_suffix,
                    output_files=template.output_files,
                    validation_checks=template.validation_checks,
                )
                ACADEMIC_TEMPLATES[action.task_type] = new_template
                action.applied = True
                logger.info(
                    "bootstrap_loop applied reduce_lines to %s: %d -> %d",
                    action.task_type, current_max, new_max,
                )

            elif action.action == "add_example":
                example_text = f"\nExample: {action.detail}"
                new_suffix = template.description_suffix + example_text
                new_template = AcademicTemplate(
                    task_type=template.task_type,
                    display_name=template.display_name,
                    system_prompt=template.system_prompt,
                    description_suffix=new_suffix,
                    output_files=template.output_files,
                    validation_checks=template.validation_checks,
                )
                ACADEMIC_TEMPLATES[action.task_type] = new_template
                action.applied = True
                logger.info(
                    "bootstrap_loop applied add_example to %s: %s",
                    action.task_type, action.detail[:80],
                )

            else:
                logger.info(
                    "bootstrap_loop skipped unsupported action %s for %s",
                    action.action, action.task_type,
                )
                action.applied = False

        except Exception as exc:
            logger.error(
                "bootstrap_loop apply_improvement failed for %s/%s: %s",
                action.task_type, action.action, exc,
            )
            action.applied = False
            return False

        return action.applied

    # ------------------------------------------------------------------
    # 5. Run cycle
    # ------------------------------------------------------------------

    def run_cycle(self, days: int = 7) -> Dict:
        """Run one complete bootstrap feedback cycle."""
        analysis = self.analyze_recent_tasks(days=days)
        patterns = self.identify_failure_patterns(analysis)
        actions = self.suggest_improvements(analysis, patterns)

        for action in actions:
            self.apply_improvement(action)

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "days_analyzed": days,
            "tasks_analyzed": sum(a.total for a in analysis),
            "patterns_found": len(patterns),
            "improvements_suggested": len(actions),
            "improvements_applied": sum(1 for a in actions if a.applied),
            "analysis": [a.model_dump() for a in analysis],
            "patterns": [p.model_dump() for p in patterns],
            "actions": [a.model_dump() for a in actions],
        }

        self._persist_report(report)
        logger.info(
            "bootstrap_loop cycle complete: tasks=%d patterns=%d actions=%d",
            report["tasks_analyzed"],
            report["patterns_found"],
            report["improvements_suggested"],
        )
        return report

    # ------------------------------------------------------------------
    # 6. Metrics
    # ------------------------------------------------------------------

    def get_metrics(self) -> Dict:
        """Return success-rate trends from stored cycle reports."""
        reports = self._load_reports()
        if not reports:
            return {"cycles": 0, "trend": []}

        trend = []
        for r in reports[-20:]:
            total = r.get("tasks_analyzed", 0)
            completed = sum(
                a.get("completed", 0) for a in r.get("analysis", [])
            )
            trend.append({
                "timestamp": r.get("timestamp"),
                "tasks": total,
                "success_rate": completed / total if total > 0 else 0.0,
                "patterns": r.get("patterns_found", 0),
                "actions": r.get("improvements_suggested", 0),
            })

        return {"cycles": len(reports), "trend": trend}

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _persist_report(self, report: Dict) -> None:
        """Append report to the JSON log file."""
        path = os.path.join(_REPORTS_DIR, "cycle_reports.json")
        existing: List[Dict] = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing = []
        existing.append(report)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, default=str)

    def _load_reports(self) -> List[Dict]:
        """Load all past cycle reports."""
        path = os.path.join(_REPORTS_DIR, "cycle_reports.json")
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


# Maps failure-pattern categories to (action, detail) tuples
_PATTERN_ACTION_MAP: Dict[str, tuple] = {
    "timeout": ("add_guard", "Add timeout guard instruction to system prompt"),
    "code_syntax": ("simplify_prompt", "Add 'No complex syntax' guard to prompt"),
    "missing_module": ("add_example", "Add allowed-libraries list to prompt"),
}


def _pattern_to_action(
    task_type: str, pattern: FailurePattern, timestamp: str
) -> Optional[ImprovementAction]:
    """Convert a failure pattern into an improvement action, if applicable."""
    entry = _PATTERN_ACTION_MAP.get(pattern.category)
    if entry is None:
        return None
    action_name, detail = entry
    return ImprovementAction(
        task_type=task_type,
        issue=f"{pattern.category} failures ({pattern.count})",
        action=action_name,
        detail=detail,
        applied=False,
        timestamp=timestamp,
    )


def _categorize_error(error_text: str) -> str:
    """Map a raw error string to a known category."""
    for pattern, category in _ERROR_PATTERNS.items():
        if re.search(pattern, error_text, re.IGNORECASE):
            return category
    return "unknown"


def _extract_max_lines(prompt: str) -> Optional[int]:
    """Extract the MAX N lines number from a system prompt string."""
    match = re.search(r"MAX\s+(\d+)\s+lines", prompt, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None
