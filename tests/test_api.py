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
