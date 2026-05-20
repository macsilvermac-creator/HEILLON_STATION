"""Mission diary retrieval coverage."""

from __future__ import annotations


def test_diary_endpoint(api_client, seeded_missions_diary):  # noqa: ARG001
    """Aggregate missions with pagination safeguards."""

    response = api_client.get("/api/v1/mission/diary")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "missions" in data
    assert data["total"] >= 1


def test_diary_filter_by_status(api_client, seeded_missions_diary):  # noqa: ARG001
    """Status filters constrain diary responses."""

    response = api_client.get("/api/v1/mission/diary", params={"status": "completed"})
    assert response.status_code == 200
    payload = response.json()
    for mission in payload["missions"]:
        assert mission["status"] == "completed"


def test_diary_stats(api_client, seeded_missions_diary):  # noqa: ARG001
    """STATS endpoint summarizes aggregate workload."""

    stats = api_client.get("/api/v1/mission/diary/stats")
    assert stats.status_code == 200
    blob = stats.json()
    assert "total_missions" in blob
    assert "completed" in blob
    assert "total_hdrs_generated" in blob


def test_diary_text_search_matches_description(api_client, seeded_missions_diary):  # noqa: ARG001
    probe = api_client.get("/api/v1/mission/diary", params={"search": "OCR"})
    assert probe.status_code == 200
    payload = probe.json()
    assert payload["total"] >= 1
