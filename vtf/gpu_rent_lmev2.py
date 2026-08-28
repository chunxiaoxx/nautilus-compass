"""智星云 plan+rent 单进程连做(quote TTL 坑规避)· LME-V2 GPU。"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/c/Users/chunx/.workbuddy/ai-galaxy-compute/src")

from ai_galaxy_compute.broker import (  # noqa: E402
    ComputeBroker,
    RentalCriteria,
)
from ai_galaxy_compute.client import AIGalaxyClient  # noqa: E402
from ai_galaxy_compute.ledger import ApprovalAuthority, ApprovalLedger  # noqa: E402
from ai_galaxy_compute.broker import SafetyPolicy  # noqa: E402

_creds = json.loads(
    Path(
        os.environ.get(
            "AI_GALAXY_CREDENTIALS_FILE",
            str(Path.home() / ".config/ai-galaxy-compute/credentials.json"),
        )
    ).read_text()
)
client = AIGalaxyClient(_creds["access_key"], _creds["secret_key"])
broker = ComputeBroker(
    client,
    policy=SafetyPolicy(
        max_total_price=130.0,
        max_duration_hours=12,
        max_hourly_price=4.0,
        max_gpu_count=1,
        max_disk_gb=100,
        max_bandwidth_mbps=32,
        quote_ttl_seconds=120,
    ),
    ledger=ApprovalLedger(),
    authority=ApprovalAuthority(),
)

criteria = RentalCriteria(
    gpu_type="GeForce RTX 4090PLUS",
    gpu_count=1,
    image="ubuntu22_cuda12.4",
    duration_hours=12,
    min_cpu=16,
    min_memory=48,
    disk_gb=100,
    bandwidth_mbps=32,
    pay_type_first="money",
    due_mode=1,
)
plan = broker.prepare_rental(criteria)
print("PLAN:", json.dumps(plan.to_dict(), ensure_ascii=False)[:400])
result = broker.execute_rental(plan, plan.approval_token)
print("RENT_OK")
print(json.dumps(result, ensure_ascii=False, default=str)[:600])
