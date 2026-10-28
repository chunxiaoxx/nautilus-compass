# Compute API Integration Guide

## Quick Start

### 1. Authentication

All requests require `X-API-Key` header:

```bash
curl -H "X-API-Key: YOUR_API_KEY" https://api.example.com/api/v1/balance
```

### 2. Check Balance

```bash
GET /api/v1/balance
```

Response:
```json
{
  "balance": 48500.0,
  "total_deposited": 50000.0,
  "total_spent": 1500.0,
  "discount_rate": 0.3
}
```

### 3. View Prices

```bash
GET /api/v1/prices
```

Response:
```json
{
  "prices": {
    "curve_fitting": 150.0,
    "jc_constitutive": 450.0,
    "thmc_coupling": 750.0,
    "ode_simulation": 240.0,
    "pde_simulation": 300.0,
    "ml_training": 360.0,
    "general_computation": 60.0,
    "data_visualization": 90.0,
    "physics_simulation": 300.0,
    "monte_carlo": 150.0,
    "statistical_analysis": 150.0
  },
  "discount_rate": 0.3,
  "currency": "RMB"
}
```

### 4. Submit a Task

```bash
POST /api/v1/tasks
Content-Type: application/json

{
  "type": "jc_constitutive",
  "title": "J-C constitutive model fitting",
  "description": "Fit Johnson-Cook model to experimental stress-strain data",
  "input_data": "strain_rate,temperature,stress\n0.001,293,450\n0.01,293,520\n...",
  "external_ref": "your-internal-id-001"
}
```

Response:
```json
{
  "task_id": "acad_a1b2c3d4e5f6g7h8",
  "external_ref": "your-internal-id-001",
  "status": "pending",
  "estimated_cost": 450.0
}
```

### 5. Check Task Status

```bash
GET /api/v1/tasks/{task_id}
```

Statuses: `pending` → `processing` → `completed` / `failed`

When completed:
```json
{
  "task_id": "acad_a1b2c3d4e5f6g7h8",
  "external_ref": "your-internal-id-001",
  "type": "jc_constitutive",
  "status": "completed",
  "result": {
    "code": "import numpy as np\n...",
    "output": "A=792.3 MPa, B=510.2 MPa, C=0.014, n=0.26, m=1.03\nR²=0.956",
    "plots": ["data:image/png;base64,..."],
    "execution_time": 21.5
  }
}
```

When failed (auto-refunded):
```json
{
  "task_id": "acad_a1b2c3d4e5f6g7h8",
  "status": "failed",
  "error": "Error description"
}
```

### 6. Batch Submit (up to 50 tasks)

```bash
POST /api/v1/tasks/batch
Content-Type: application/json

{
  "tasks": [
    {"type": "curve_fitting", "title": "Fit 1", "description": "..."},
    {"type": "curve_fitting", "title": "Fit 2", "description": "..."},
    {"type": "jc_constitutive", "title": "JC 1", "description": "..."}
  ]
}
```

Response:
```json
{
  "submitted": 3,
  "total_cost": 1050.0,
  "tasks": [
    {"task_id": "acad_xxx1", "type": "curve_fitting", "cost": 150.0},
    {"task_id": "acad_xxx2", "type": "curve_fitting", "cost": 150.0},
    {"task_id": "acad_xxx3", "type": "jc_constitutive", "cost": 750.0}
  ]
}
```

### 7. List Tasks

```bash
GET /api/v1/tasks?status=completed&limit=10&offset=0
```

### 8. Usage Statistics

```bash
GET /api/v1/stats
```

Response:
```json
{
  "total_tasks": 42,
  "completed": 38,
  "failed": 2,
  "pending": 2,
  "success_rate": 90.5,
  "total_spent": 15000.0,
  "balance": 35000.0
}
```

---

## Webhook Callbacks

When a task completes or fails, we send a POST to your registered webhook URL:

```json
{
  "event": "task.completed",
  "task_id": "acad_xxx",
  "external_ref": "your-internal-id-001",
  "type": "jc_constitutive",
  "status": "completed",
  "timestamp": "2026-03-24T10:30:00",
  "result": {
    "code": "...",
    "output": "...",
    "plots": [...],
    "execution_time": 21.5
  }
}
```

Your endpoint should return 2xx within 10 seconds. We retry up to 3 times.

---

## Python SDK

```python
from partner_sdk import ComputeClient

client = ComputeClient(api_key="nk_xxx", base_url="https://api.example.com")

# Submit
task = client.submit("jc_constitutive", "JC Fitting", "Fit JC model", input_data="...")

# Wait for result (polls every 5s, max 5 min)
result = client.wait_for_result(task["task_id"])

# Check balance
print(client.get_balance())
```

---

## Error Codes

| HTTP | Code | Description |
|------|------|-------------|
| 401 | - | Invalid API key |
| 402 | INSUFFICIENT_BALANCE | Not enough balance |
| 400 | - | Bad request (invalid type, params, etc.) |
| 404 | - | Task not found |

---

## Task Types

| Type | Description | Price (30% rate) |
|------|-------------|-----------------|
| general_computation | General numerical computation | 60 |
| curve_fitting | Curve fitting / regression | 150 |
| ode_simulation | ODE system simulation | 240 |
| pde_simulation | PDE numerical solution | 300 |
| monte_carlo | Monte Carlo simulation | 150 |
| statistical_analysis | Statistical analysis | 150 |
| ml_training | Machine learning training | 360 |
| data_visualization | Data visualization | 90 |
| physics_simulation | Physics simulation | 300 |
| jc_constitutive | Johnson-Cook constitutive model | 450 |
| thmc_coupling | THMC multi-physics coupling | 750 |

---

## SLA

- Task queue: < 30s
- Execution: depends on complexity (typical 10-120s)
- Availability: 99.5% uptime
- Failed tasks: auto-refunded
