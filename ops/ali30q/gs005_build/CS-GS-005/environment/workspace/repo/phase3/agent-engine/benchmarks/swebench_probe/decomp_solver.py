"""arm-3 decomposed SWE-bench solver: localize -> edit -> test with isolated context.

The Paradigm-B context-isolation arm. Each stage is a FRESH agent context seeded
only with the prior stage's curated handoff (its submission string), never the prior
stage's full transcript. All stages share ONE container env (so file edits persist
across stages) and ONE token budget (matched to arm 1). The generic bash tool is the
same in every stage — the ONLY thing that differs from arm 1 (mono) is that context
is partitioned and reset per stage instead of one ever-growing window.

`solve_decomp` is the pure orchestration (inject `run_stage`, unit-testable).
`make_stage_runner` builds the production `run_stage` over mini-swe-agent's
DefaultAgent (imported lazily so this module loads without mini-swe-agent installed).
"""
from typing import Callable, Dict, List

from budget import BudgetExceeded

STAGES = ("localize", "edit", "test")


def solve_decomp(
    task: str,
    *,
    run_stage: Callable[[str, str, Dict[str, str]], dict],
    stages=STAGES,
) -> dict:
    """Run the decomposed stages in order; return the final stage's result dict.

    `run_stage(stage, task, handoffs) -> {"submission": str, "exit_status": str}`
    is injected. Isolation invariant: a stage receives ONLY (stage, task, handoffs),
    and `handoffs` holds only prior stages' submission STRINGS keyed `<stage>_handoff`
    — never a transcript / message list. A stage that raises BudgetExceeded ends the
    run, preserving whatever patch the shared container already holds.
    """
    handoffs: Dict[str, str] = {}
    last = {"submission": "", "exit_status": "no_stages"}
    for stage in stages:
        try:
            result = run_stage(stage, task, dict(handoffs))
        except BudgetExceeded:
            return {**last, "exit_status": "budget_exceeded"}
        last = result
        handoffs[f"{stage}_handoff"] = result.get("submission", "")
    return last


# --- Stage prompts (generic bash tool in every stage; only the focus differs) ---
# Each stage's instance template is rendered with {task} + prior {*_handoff} vars.
# Localize/edit end with a plain textual handoff; only `test` submits the git patch
# (via the same COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT mechanism as arm 1).

_FINISH_HANDOFF = (
    "To END this stage, write your concise structured handoff to /tmp/handoff.txt, "
    "then run this EXACT command as a SEPARATE final command:\n"
    "`echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat /tmp/handoff.txt`\n"
    "(The first output line must be that marker; the rest is your handoff. You "
    "cannot continue after this command.)"
)

STAGE_TEMPLATES: Dict[str, str] = {
    "localize": (
        "<pr_description>\n{{task}}\n</pr_description>\n\n"
        "# Stage 1 of 3 — LOCALIZE (do NOT edit any file)\n"
        "Explore /testbed with bash (grep, find, sed, cat) and identify the exact "
        "source file(s) and function/line region that must change to fix the issue. "
        "Do NOT modify any file in this stage.\n"
        "Your handoff MUST name the file path(s) and the specific location/function.\n"
        + _FINISH_HANDOFF
    ),
    "edit": (
        "<pr_description>\n{{task}}\n</pr_description>\n\n"
        "# Stage 2 of 3 — EDIT\n"
        "A previous localization step found:\n<localization>\n{{localize_handoff}}\n"
        "</localization>\n"
        "Edit ONLY the relevant non-test source file(s) in /testbed to fix the issue, "
        "general and consistent with the codebase. Do not modify tests/config.\n"
        "Your handoff MUST state which files+lines you changed and why.\n"
        + _FINISH_HANDOFF
    ),
    "test": (
        "<pr_description>\n{{task}}\n</pr_description>\n\n"
        "# Stage 3 of 3 — TEST & SUBMIT\n"
        "A previous edit step reported:\n<edit_report>\n{{edit_handoff}}\n"
        "</edit_report>\n"
        "Reproduce the issue and run the relevant tests to verify the fix already "
        "applied in /testbed. If something is still broken, make the minimal "
        "additional source edit needed. When the fix is verified, END by submitting "
        "the git patch of ONLY the source files changed (NOT tests/repro/helper "
        "files). Run as SEPARATE final commands:\n"
        "1. `git -C /testbed diff -- <changed source files> > /tmp/patch.txt`\n"
        "2. `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat /tmp/patch.txt`\n"
        "(First output line must be the marker; the rest is your patch.)"
    ),
}

# Reused system prompt (same generic shell assistant as arm 1).
STAGE_SYSTEM = (
    "You are a helpful assistant that can interact with a computer shell to solve "
    "programming tasks. You work in stages; follow the stage instructions exactly."
)


def make_stage_runner(
    budgeted_model,
    env,
    *,
    agent_factory=None,
    step_limit: int = 120,
) -> Callable[[str, str, Dict[str, str]], dict]:
    """Build the production `run_stage` over mini-swe-agent's DefaultAgent.

    All stages share `budgeted_model` (one token cap across the whole instance) and
    `env` (one container — file edits persist). Each call builds a FRESH agent whose
    `run()` resets `self.messages`, so a stage never inherits a prior stage's
    transcript; the only cross-stage signal is the handoff string in the template.
    """

    def run_stage(stage: str, task: str, handoffs: Dict[str, str]) -> dict:
        # Lazy import so this module loads without mini-swe-agent (e.g. in unit tests).
        from minisweagent.agents.default import DefaultAgent

        factory = agent_factory or DefaultAgent
        agent = factory(
            budgeted_model,
            env,
            system_template=STAGE_SYSTEM,
            instance_template=STAGE_TEMPLATES[stage],
            step_limit=step_limit,
            cost_limit=0.0,  # budget enforced by BudgetedModel, not cost
        )
        info = agent.run(task=task, **handoffs)
        return {
            "submission": info.get("submission", ""),
            "exit_status": info.get("exit_status", ""),
        }

    return run_stage


def collect_patch(stage_results: List[dict]) -> str:
    """The arm-3 patch = the final (test) stage's submission (the git diff)."""
    return stage_results[-1].get("submission", "") if stage_results else ""
