"""Reference-data endpoint tests.

GET /v1/meta/enums is the frontend's single source of truth for enum values,
signal dimensions, and reason codes — generated from the source so UI labels
can never drift from the backend.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.models.domain import SIGNAL_DIMENSION, Signal


def test_meta_enums_match_the_source(offline_app: Any) -> None:
    with TestClient(offline_app) as client:
        response = client.get("/v1/meta/enums")

    assert response.status_code == 200
    body = response.json()

    assert body["policyVersion"] == "v2"
    assert body["enums"]["signal"] == [s.value for s in Signal]
    assert body["enums"]["mandateStatus"] == ["active", "revoked", "expired", "challenge_only"]
    assert body["signalDimension"] == {
        s.value: SIGNAL_DIMENSION[s].value for s in Signal
    }
    assert "new_beneficiary_material_value" in body["reasonCodes"]["step_up"]
    assert "sim_swap_recent_high_value" in body["reasonCodes"]["deny"]
