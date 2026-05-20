"""Mission EASY HTTP contract tests."""

from __future__ import annotations


def test_plan_endpoint(api_client):
    response = api_client.post(
        "/api/v1/mission/plan",
        json={
            "description": "Analyze documents for risk",
            "authorized_agents": ["analysis-agent"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["normative_result"]["allowed"] is True


def test_approve_endpoint(api_client):
    plan_resp = api_client.post(
        "/api/v1/mission/plan",
        json={
            "description": "Analyze documents",
            "authorized_agents": ["analysis-agent"],
        },
    )
    mission_id = plan_resp.json()["mission_id"]

    approve_resp = api_client.post(f"/api/v1/mission/{mission_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"


def test_reject_endpoint(api_client):
    plan_resp = api_client.post(
        "/api/v1/mission/plan",
        json={
            "description": "Risk review",
            "authorized_agents": ["analysis-agent"],
        },
    )
    mission_id = plan_resp.json()["mission_id"]

    reject_resp = api_client.post(f"/api/v1/mission/{mission_id}/reject")
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"


def test_execute_endpoint(api_client):
    plan_resp = api_client.post(
        "/api/v1/mission/plan",
        json={
            "description": "OCR and analyze documents",
            "authorized_agents": ["ocr-agent", "analysis-agent"],
        },
    )
    mission_id = plan_resp.json()["mission_id"]
    api_client.post(f"/api/v1/mission/{mission_id}/approve")

    exec_resp = api_client.post(f"/api/v1/mission/{mission_id}/execute")
    assert exec_resp.status_code == 200
    data = exec_resp.json()

    assert data["status"] == "completed"
    assert data["total_hdrs"] == 2
    assert data["chain_root"] is not None
    assert data["chain_tail"] is not None


def test_blocked_mission_not_executed(api_client):
    response = api_client.post(
        "/api/v1/mission/plan",
        json={
            "description": "Access privileged attorney-client documents",
            "authorized_agents": ["analysis-agent"],
        },
    )
    data = response.json()
    assert data["normative_result"]["allowed"] is False
    assert data["status"] == "pending"

    forbid = api_client.post(f"/api/v1/mission/{data['mission_id']}/approve")
    assert forbid.status_code == 403


def test_public_normative_rules(api_client):
    response = api_client.get("/api/v1/normative/rules")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 10
    assert body[0]["rule_id"]
