"""Lightweight throughput checks for EASY mission ingestion."""

from __future__ import annotations


def test_mission_throughput_burst(api_client):
    """Smoke exercise ensuring sustained planning remains stable under modest cadence."""

    for index in range(25):
        response = api_client.post(
            "/api/v1/mission/plan",
            json={
                "description": f"Synthetic EASY throughput dossier iteration {index:03d}",
                "authorized_agents": ["classification-agent"],
            },
        )
        assert response.status_code == 200, response.text

    listing = api_client.get("/api/v1/mission/", params={"skip": 0, "limit": 200})
    assert listing.status_code == 200
