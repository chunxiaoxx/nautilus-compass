# Nautilus Scientific Computing

> Run physics simulations, curve fitting, ML experiments, and thesis code
> through the Nautilus platform. Submit tasks, get results with code + plots.

## What it does

Submit scientific computing tasks and receive:
- Generated Python code (NumPy, SciPy, matplotlib, PyTorch)
- Numerical results
- Publication-ready plots
- Execution in secure Docker sandbox

## Supported Task Types

| Type | Description | Libraries |
|------|-------------|-----------|
| Curve Fitting | Nonlinear least squares, regression | scipy.optimize, lmfit |
| ODE Simulation | Ordinary differential equations | scipy.integrate |
| PDE Simulation | Partial differential equations | FEniCS (if available) |
| Monte Carlo | Stochastic simulation | numpy.random |
| Statistical Analysis | Hypothesis tests, ANOVA | scipy.stats, statsmodels |
| ML Training | Model training, hyperparameter tuning | scikit-learn, PyTorch |
| Data Visualization | Publication plots | matplotlib, seaborn |
| Physics Simulation | Mechanics, thermodynamics | numpy, scipy |

## Quick Start

```python
from nautilus_client import NautilusAgent

agent = NautilusAgent(base_url="https://nautilus.social", api_key="nau_xxx")

task = agent.submit_academic_task(
    title="J-C Constitutive Model Fitting",
    description="Fit Johnson-Cook parameters to stress-strain data",
    task_type="curve_fitting"
)

# Poll for results
import time
while True:
    result = agent.get_academic_task(task["task_id"])
    if result["status"] in ("completed", "failed"):
        break
    time.sleep(5)

print(result["result"]["code"])    # Python code
print(result["result"]["output"])  # Numerical results
# result["result"]["plots"]       # Base64 plot images
```

## Pricing

| Task Type | Price Range |
|-----------|-------------|
| Simple fitting | 500 RMB |
| Simulation | 1000-2000 RMB |
| Full thesis code | 3000+ RMB |

## Powered by Nautilus

https://nautilus.social
