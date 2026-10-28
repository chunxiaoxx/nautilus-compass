from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.fde_phase3_s0 import router


def test_s0_public_surface_exposes_identity_first_human_gate_but_no_workbench():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    response = client.get("/api/platform/fde/phase3/s0/version")
    assert response.status_code == 200
    assert response.json() == {
        "version": "platform-t1-s0-admission-v3",
        "constitution_version": "t1-constitution-v1.0-20260730",
        "mode": "invitation_only_identity_first",
        "invitation_delivery": "direct_im_bound_to_open_id",
        "human_admission_gate": True,
        "workbench_exposed": False,
    }
    assert client.get("/api/platform/fde/phase3/workbench").status_code == 404
