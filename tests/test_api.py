"""tests/test_api.py - Unit test stub for api module.

Owner: M4 (Network & API Lead)
"""



def test_api_module_import():
    """Verify api package and FastAPI app import cleanly."""
    import api
    from api.main import app
    from api.models import TelemetryPayload

    assert api is not None
    assert app is not None
    assert TelemetryPayload is not None


def test_telemetry_schema_validation():
    """Verify that the required FedMed telemetry JSON schema parses and validates perfectly."""
    from api.models import TelemetryPayload

    raw_payload = {
        "round": 4,
        "phase": "aggregating",
        "global": {"loss": 0.31, "dice": 0.78},
        "nodes": [
            {"id": 1, "status": "active", "dice": 0.76, "upload_ms": 812, "bytes": 5242880}
        ],
        "privacy": {"epsilon": 5.0, "delta": 1e-5, "epsilon_spent": 2.3},
        "encrypted": True,
    }

    # Validate against Pydantic model
    parsed = TelemetryPayload.model_validate(raw_payload)
    assert parsed.round == 4
    assert parsed.phase == "aggregating"
    assert parsed.global_metrics.loss == 0.31
    assert parsed.global_metrics.dice == 0.78
    assert len(parsed.nodes) == 1
    assert parsed.nodes[0].id == 1
    assert parsed.nodes[0].dice == 0.76
    assert parsed.privacy.epsilon_spent == 2.3
    assert parsed.encrypted is True

    # Re-serialization with by_alias=True should produce exact key "global"
    dumped = parsed.model_dump(by_alias=True)
    assert "global" in dumped
    assert dumped["global"]["dice"] == 0.78


def test_api_routes_registered():
    """Verify expected REST routes are registered on the FastAPI app."""
    from api.main import app

    route_paths = [route.path for route in app.routes]
    assert "/" in route_paths
    assert "/scans" in route_paths
    assert "/scans/{scan_id}/slice/{axis}/{index}" in route_paths
    assert "/scans/{scan_id}/mask/{index}" in route_paths
    assert "/ws/telemetry" in route_paths


def test_mri_slice_and_mask_png_generation():
    """Verify that MRI slice and tumor mask endpoints return valid PNG byte streams."""
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)

    # 1. Test raw slice endpoint across axial, sagittal, and coronal planes
    for axis in ["axial", "sagittal", "coronal"]:
        resp = client.get(f"/scans/BraTS2021_00001/slice/{axis}/32?modality=FLAIR")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert resp.content.startswith(b"\x89PNG\r\n\x1a\n")

    # 2. Test multi-region tumor mask overlay endpoint
    mask_resp = client.get("/scans/BraTS2021_00001/mask/axial/32?wt=true&tc=true&et=true")
    assert mask_resp.status_code == 200
    assert mask_resp.headers["content-type"] == "image/png"
    assert mask_resp.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_interactive_control_endpoints():
    """Verify demo control panel endpoints: node dropout, reconnect, encryption toggle, and step."""
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)

    # 1. Trigger node dropout
    drop_resp = client.post("/api/control/dropout/2")
    assert drop_resp.status_code == 200
    data = drop_resp.json()
    assert data["success"] is True
    assert data["action"] == "dropout"

    # 2. Trigger node reconnect
    rec_resp = client.post("/api/control/reconnect/2")
    assert rec_resp.status_code == 200
    assert rec_resp.json()["success"] is True

    # 3. Toggle encryption scheme
    enc_resp = client.post("/api/control/toggle-encryption")
    assert enc_resp.status_code == 200
    assert enc_resp.json()["success"] is True

    # 4. Step communication round
    step_resp = client.post("/api/control/step-round")
    assert step_resp.status_code == 200
    assert step_resp.json()["success"] is True

    # 5. Check privacy audit endpoint
    audit_resp = client.get("/api/privacy/audit")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert "is_compliant" in audit_data
    assert "spent_epsilon" in audit_data

