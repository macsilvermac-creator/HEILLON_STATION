"""End-to-end regressions bridging missions, custody, and forensic exports."""

from __future__ import annotations


def test_full_mission_to_forensic_package(api_client):
    """Golden path validating planning → custody → dossier minting."""

    plan_resp = api_client.post(
        "/api/v1/mission/plan",
        json={
            "description": "Analyze financial documents for risk and prioritize by relevance",
            "authorized_agents": ["analysis-agent", "prioritization-agent"],
        },
    )
    assert plan_resp.status_code == 200
    mission_id = plan_resp.json()["mission_id"]
    assert plan_resp.json()["normative_result"]["allowed"] is True

    approve_resp = api_client.post(f"/api/v1/mission/{mission_id}/approve")
    assert approve_resp.status_code == 200

    exec_resp = api_client.post(f"/api/v1/mission/{mission_id}/execute")
    assert exec_resp.status_code == 200
    assert exec_resp.json()["total_hdrs"] == 2

    verify_resp = api_client.get(f"/api/v1/verify/chain/{mission_id}")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["valid"] is True

    pkg_resp = api_client.post(
        f"/api/v1/forensic/package/{mission_id}",
        params={"generated_by": "perito_test"},
    )
    assert pkg_resp.status_code == 200
    package_id = pkg_resp.json()["package_id"]

    pdf_resp = api_client.get(f"/api/v1/forensic/package/{package_id}/download/pdf")
    assert pdf_resp.status_code == 200

    json_resp = api_client.get(f"/api/v1/forensic/package/{package_id}/download/json")
    assert json_resp.status_code == 200

    manifest_resp = api_client.get(
        f"/api/v1/forensic/package/{package_id}/download/manifest"
    )
    assert manifest_resp.status_code == 200
