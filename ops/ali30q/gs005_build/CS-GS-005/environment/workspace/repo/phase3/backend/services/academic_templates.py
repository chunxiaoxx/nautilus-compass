"""
Pre-built templates for common academic tasks.

Each template provides a specialized system prompt and description suffix
that dramatically improve LLM code generation quality for that task type.
These templates reduce user input and ensure consistent, professional output.
"""
from typing import Dict, Any, Optional


class AcademicTemplate:
    """Immutable template for an academic task type."""

    __slots__ = (
        "task_type",
        "display_name",
        "system_prompt",
        "description_suffix",
        "output_files",
        "validation_checks",
    )

    def __init__(
        self,
        task_type: str,
        display_name: str,
        system_prompt: str,
        description_suffix: str,
        output_files: tuple[str, ...] = (),
        validation_checks: tuple[str, ...] = (),
    ) -> None:
        object.__setattr__(self, "task_type", task_type)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "system_prompt", system_prompt)
        object.__setattr__(self, "description_suffix", description_suffix)
        object.__setattr__(self, "output_files", output_files)
        object.__setattr__(self, "validation_checks", validation_checks)

    def __setattr__(self, *_: Any) -> None:
        raise AttributeError("AcademicTemplate instances are immutable")


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

_CURVE_FITTING = AcademicTemplate(
    task_type="curve_fitting",
    display_name="Curve Fitting / Regression",
    system_prompt=(
        "Write a CONCISE Python script (MAX 80 lines) for curve fitting. "
        "Use scipy.optimize.curve_fit. "
        "Steps: import libs, define/load data, define model function, "
        "fit with initial guesses and bounds, calculate R-squared and RMSE, "
        "print parameters with uncertainties, save one plot to "
        "/workspace/output/fit_result.png. "
        "Keep code SHORT. No classes. Use matplotlib.use('Agg')."
    ),
    description_suffix=(
        "\n\nIMPORTANT: MAX 80 lines. Simple and direct.\n"
        "- Print each fitted parameter with uncertainty\n"
        "- Print R-squared and RMSE\n"
        "- Save one plot with data + fit curve to /workspace/output/fit_result.png"
    ),
    output_files=("fit_result.png",),
    validation_checks=("R-squared", "RMSE", "parameter", "fit"),
)

_ODE_SIMULATION = AcademicTemplate(
    task_type="ode_simulation",
    display_name="ODE Numerical Simulation",
    system_prompt=(
        "Write a CONCISE Python script (MAX 60 lines) for solving ODEs. "
        "Use scipy.integrate.solve_ivp. "
        "Define the ODE system, set initial conditions and time span, "
        "solve, print key values (max, min, steady state), "
        "plot solution and save to /workspace/output/ode_result.png. "
        "Keep code SHORT. No classes. Use matplotlib.use('Agg')."
    ),
    description_suffix=(
        "\n\nIMPORTANT: MAX 60 lines. Simple and direct. "
        "Use solve_ivp. Save one plot."
    ),
    output_files=("ode_result.png",),
    validation_checks=("solve_ivp", "t_span"),
)

_MONTE_CARLO = AcademicTemplate(
    task_type="monte_carlo",
    display_name="Monte Carlo Simulation",
    system_prompt=(
        "Write a CONCISE Python script (MAX 70 lines) for Monte Carlo simulation. "
        "Use numpy.random with np.random.seed(42) for reproducibility. "
        "Run simulation, compute mean/std/95% CI, print statistics, "
        "plot histogram and save to /workspace/output/monte_carlo.png. "
        "Keep code SHORT. No classes. Use matplotlib.use('Agg')."
    ),
    description_suffix=(
        "\n\nIMPORTANT: MAX 70 lines. Simple and direct.\n"
        "- Set np.random.seed(42)\n"
        "- Print mean, std, 95% confidence interval\n"
        "- Save one plot to /workspace/output/monte_carlo.png"
    ),
    output_files=("monte_carlo.png",),
    validation_checks=("mean", "std", "confidence", "seed"),
)

_STATISTICAL_ANALYSIS = AcademicTemplate(
    task_type="statistical_analysis",
    display_name="Statistical Analysis",
    system_prompt=(
        "Write a CONCISE Python script (MAX 70 lines) for statistical analysis. "
        "Use scipy.stats. State hypotheses, run test, report test statistic and "
        "p-value, state conclusion, save one plot to "
        "/workspace/output/stats_result.png. "
        "Keep code SHORT. No classes. Use matplotlib.use('Agg')."
    ),
    description_suffix=(
        "\n\nIMPORTANT: MAX 70 lines. Simple and direct.\n"
        "- Print H0 and H1\n"
        "- Print test statistic, p-value, effect size\n"
        "- Print conclusion (reject/fail to reject)\n"
        "- Save one plot to /workspace/output/stats_result.png"
    ),
    output_files=("stats_result.png",),
    validation_checks=("p-value", "statistic", "hypothesis", "reject"),
)

_PHYSICS_SIMULATION = AcademicTemplate(
    task_type="physics_simulation",
    display_name="Physics Simulation",
    system_prompt=(
        "Write a CONCISE Python script (MAX 80 lines) for a physics simulation. "
        "Use numpy and scipy. Use SI units. "
        "Define constants, run simulation, print key results with units, "
        "save one plot to /workspace/output/physics_result.png. "
        "Keep code SHORT and SIMPLE. No classes. Use matplotlib.use('Agg')."
    ),
    description_suffix=(
        "\n\nIMPORTANT: MAX 80 lines. Simple and direct. "
        "Print results with units. Save one plot."
    ),
    output_files=("physics_result.png",),
    validation_checks=("units", "result"),
)

_ML_TRAINING = AcademicTemplate(
    task_type="ml_training",
    display_name="Machine Learning Training",
    system_prompt=(
        "Write a CONCISE Python script (MAX 80 lines) for ML training. "
        "Use scikit-learn. Split data 80/20 with random_state=42, "
        "train model, print metrics (accuracy/F1 or MSE/R2), "
        "save one plot to /workspace/output/ml_result.png. "
        "Keep code SHORT. No classes. Use matplotlib.use('Agg')."
    ),
    description_suffix=(
        "\n\nIMPORTANT: MAX 80 lines. Simple and direct.\n"
        "- Use random_state=42 for reproducibility\n"
        "- Print accuracy/F1 (classification) or MSE/R2 (regression)\n"
        "- Save one plot to /workspace/output/ml_result.png"
    ),
    output_files=("ml_result.png",),
    validation_checks=("accuracy", "score", "train", "test"),
)

_JC_CONSTITUTIVE = AcademicTemplate(
    task_type="jc_constitutive",
    display_name="Johnson-Cook Constitutive Model Fitting",
    system_prompt=(
        "Write a Python script (STRICTLY MAX 40 lines) for Johnson-Cook model fitting.\n"
        "FOLLOW THIS EXACT STRUCTURE - do not deviate:\n"
        "```\n"
        "import numpy as np\n"
        "from scipy.optimize import curve_fit\n"
        "eps = np.linspace(0.01, 0.5, 50)\n"
        "# True params: A=200, B=800, n=0.5\n"
        "sigma_data = (200 + 800*eps**0.5) * (1 + np.random.normal(0, 5, 50)/ 100)\n"
        "def jc(eps, A, B, n):\n"
        "    return A + B * eps**n\n"
        "popt, pcov = curve_fit(jc, eps, sigma_data, p0=[200,500,0.5], bounds=([0,0,0.01],[2000,5000,2.0]))\n"
        "perr = np.sqrt(np.diag(pcov))\n"
        "ss_res = np.sum((sigma_data - jc(eps, *popt))**2)\n"
        "ss_tot = np.sum((sigma_data - np.mean(sigma_data))**2)\n"
        "r2 = 1 - ss_res/ss_tot\n"
        "print(f'A = {popt[0]:.2f} +/- {perr[0]:.2f}')\n"
        "print(f'B = {popt[1]:.2f} +/- {perr[1]:.2f}')\n"
        "print(f'n = {popt[2]:.4f} +/- {perr[2]:.4f}')\n"
        "print(f'R-squared = {r2:.6f}')\n"
        "```\n"
        "DO NOT use matplotlib. DO NOT use classes. DO NOT read files.\n"
        "DO NOT use os.makedirs or create directories. DO NOT import os.\n"
        "DO NOT write files. DO NOT use open(). No strain rate fitting.\n"
        "Print parameters only. No plots. STDOUT ONLY."
    ),
    description_suffix=(
        "\n\nCRITICAL CONSTRAINTS (violating ANY = automatic failure):\n"
        "- STRICTLY MAX 40 lines. Count your lines.\n"
        "- Do NOT import matplotlib or os or any plotting library.\n"
        "- Do NOT use os.makedirs or create directories.\n"
        "- Do NOT save files or plots. No open(), no savefig.\n"
        "- Generate synthetic data INLINE with numpy.\n"
        "- Fit quasi-static J-C: sigma = A + B*eps^n using curve_fit.\n"
        "- Print A, B, n with uncertainties and R-squared to stdout. That is ALL."
    ),
    output_files=(),
    validation_checks=("A =", "B =", "n =", "R-squared"),
)

_THMC_COUPLING = AcademicTemplate(
    task_type="thmc_coupling",
    display_name="THMC Coupled Simulation",
    system_prompt=(
        "Write a Python script (STRICTLY MAX 50 lines) for a simplified THMC simulation.\n"
        "FOLLOW THIS EXACT STRUCTURE:\n"
        "```\n"
        "import numpy as np\n"
        "N = 20  # grid size\n"
        "dt, dx = 0.01, 0.05\n"
        "alpha = 1e-6  # thermal diffusivity\n"
        "D = 1e-7  # chemical diffusivity\n"
        "T = np.ones((N, N)) * 300.0  # temperature field (K)\n"
        "C = np.zeros((N, N))  # concentration\n"
        "T[N//2-2:N//2+2, N//2-2:N//2+2] = 500.0  # heat source\n"
        "C[0, :] = 1.0  # chemical boundary\n"
        "for step in range(200):\n"
        "    Tn = T.copy()\n"
        "    Cn = C.copy()\n"
        "    T[1:-1,1:-1] = Tn[1:-1,1:-1] + alpha*dt/dx**2 * (Tn[2:,1:-1]+Tn[:-2,1:-1]+Tn[1:-1,2:]+Tn[1:-1,:-2]-4*Tn[1:-1,1:-1])\n"
        "    C[1:-1,1:-1] = Cn[1:-1,1:-1] + D*dt/dx**2 * (Cn[2:,1:-1]+Cn[:-2,1:-1]+Cn[1:-1,2:]+Cn[1:-1,:-2]-4*Cn[1:-1,1:-1])\n"
        "    stress = 200e9 * 12e-6 * (T - 300)  # thermal stress = E * alpha_th * dT\n"
        "    pressure = 1e6 * C  # simplified pressure from concentration\n"
        "print(f'Temperature: min={T.min():.1f} max={T.max():.1f} K')\n"
        "print(f'Concentration: min={C.min():.4f} max={C.max():.4f}')\n"
        "print(f'Stress: min={stress.min():.1f} max={stress.max():.1f} Pa')\n"
        "print(f'Pressure: min={pressure.min():.1f} max={pressure.max():.1f} Pa')\n"
        "print('Convergence: OK')\n"
        "```\n"
        "DO NOT use matplotlib. DO NOT use classes. DO NOT read files.\n"
        "Pure numpy only. Print field min/max values. No plots."
    ),
    description_suffix=(
        "\n\nCRITICAL: MAX 50 lines. NO matplotlib. NO plots. NO file I/O.\n"
        "2D finite difference: heat equation + diffusion + thermal stress + pressure.\n"
        "Print min/max of temperature, concentration, stress, pressure. That is ALL."
    ),
    output_files=(),
    validation_checks=("temperature", "pressure", "Convergence"),
)

_GENERAL_COMPUTATION = AcademicTemplate(
    task_type="general_computation",
    display_name="General Scientific Computation",
    system_prompt=(
        "Write a CONCISE Python script (MAX 80 lines) for scientific computation. "
        "Use numpy, scipy, matplotlib as needed. "
        "Print results clearly to stdout with units where applicable. "
        "If plotting, save to /workspace/output/result.png. "
        "Keep code SHORT and SIMPLE. No classes. Use matplotlib.use('Agg') "
        "before importing pyplot."
    ),
    description_suffix=(
        "\n\nIMPORTANT: MAX 80 lines. Simple and direct. "
        "Print numerical results. Save plot if applicable."
    ),
    output_files=("result.png",),
    validation_checks=("result", "="),
)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ACADEMIC_TEMPLATES: Dict[str, AcademicTemplate] = {
    t.task_type: t
    for t in (
        _CURVE_FITTING,
        _ODE_SIMULATION,
        _MONTE_CARLO,
        _STATISTICAL_ANALYSIS,
        _PHYSICS_SIMULATION,
        _ML_TRAINING,
        _JC_CONSTITUTIVE,
        _THMC_COUPLING,
        _GENERAL_COMPUTATION,
    )
}


def get_template(task_type: str) -> Optional[AcademicTemplate]:
    """Return the template for *task_type*, or None if not found."""
    return ACADEMIC_TEMPLATES.get(task_type)


def list_templates() -> list[dict[str, str]]:
    """Return a lightweight list of available templates for the API."""
    return [
        {"task_type": t.task_type, "display_name": t.display_name}
        for t in ACADEMIC_TEMPLATES.values()
    ]
