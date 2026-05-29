"""Forensic package HTTP surface checks."""

from __future__ import annotations


def test_generate_package_endpoint(api_client, completed_mission):
    """POST /forensic/package/{mission_id} materializes dossiers."""

    response = api_client.post(
        f"/api/v1/forensic/package/{completed_mission.mission_id}",
        params={"generated_by": "perito_test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["manifest"] is not None


def test_download_json_chain(api_client, completed_mission):
    """JSON lineage downloads remain byte-identical to repository exports."""

    gen_resp = api_client.post(
        f"/api/v1/forensic/package/{completed_mission.mission_id}",
        params={"generated_by": "perito_test"},
    )
    package_id = gen_resp.json()["package_id"]

    dl_resp = api_client.get(f"/api/v1/forensic/package/{package_id}/download/json")
    assert dl_resp.status_code == 200
    body = dl_resp.text
    assert "mission_lineage" in body


def test_forensic_package_get_roundtrip(api_client, completed_mission):
    gen_resp = api_client.post(
        f"/api/v1/forensic/package/{completed_mission.mission_id}",
        params={"generated_by": "perito_probe"},
    )
    package_id = gen_resp.json()["package_id"]
    detail_resp = api_client.get(f"/api/v1/forensic/package/{package_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["package_id"] == package_id
