"""Public verification endpoints."""

from __future__ import annotations

import io
import json
import sqlite3


def _ingest(
    api_client,
    auth_headers,
    *,
    mission_id: str,
    payload: bytes,
    previous_hdr: str | None = None,
) -> dict:
    data = {"mission_id": mission_id}
    if previous_hdr is not None:
        data["previous_hdr"] = previous_hdr

    response = api_client.post(
        "/api/v1/ingestion",
        headers=auth_headers,
        files=[("file", ("chunk.bin", io.BytesIO(payload), "application/octet-stream"))],
        data=data,
    )

    assert response.status_code == 200
    return response.json()["hdr"]


def test_verify_single_hdr_positive(api_client, auth_headers):
    hdr = _ingest(api_client, auth_headers, mission_id="mission_single", payload=b"a")

    verdict = api_client.get(f"/api/v1/verify/{hdr['hdr_id']}")

    body = verdict.json()
    assert body["valid"]
    assert body["hdr_id"] == hdr["hdr_id"]


def test_verify_chain_positive(api_client, auth_headers):
    mission_id = "mission_chain_ok"
    first = _ingest(api_client, auth_headers, mission_id=mission_id, payload=b"alpha")
    second = _ingest(
        api_client,
        auth_headers,
        mission_id=mission_id,
        payload=b"beta",
        previous_hdr=first["hdr_id"],
    )

    response = api_client.get(f"/api/v1/verify/chain/{mission_id}")

    verdict = response.json()
    assert verdict["valid"]
    assert verdict["chained_hdr_count"] == 2
    assert second["previous_hdr"] == first["hdr_id"]


def test_verify_chain_negative_branch(api_client, auth_headers):
    mission_id = "mission_branch"
    genesis = _ingest(api_client, auth_headers, mission_id=mission_id, payload=b"one")

    fork_a = _ingest(api_client, auth_headers, mission_id=mission_id, payload=b"fork-a", previous_hdr=genesis["hdr_id"])
    fork_b = _ingest(api_client, auth_headers, mission_id=mission_id, payload=b"fork-b", previous_hdr=genesis["hdr_id"])

    verdict = api_client.get(f"/api/v1/verify/chain/{mission_id}")

    body = verdict.json()
    assert not body["valid"]
    assert fork_a["previous_hdr"] == fork_b["previous_hdr"] == genesis["hdr_id"]


def test_missing_hdr_returns_404(api_client):
    unknown = "0" * 64
    response = api_client.get(f"/api/v1/verify/{unknown}")
    assert response.status_code == 404


def test_missing_chain_returns_404(api_client):
    response = api_client.get("/api/v1/verify/chain/ghost_mission")
    assert response.status_code == 404


def test_detects_database_tampering(api_client, auth_headers):
    hdr = _ingest(api_client, auth_headers, mission_id="tampering", payload=b"tampered-payload")

    db_path = api_client.app.state.sqlite_path
    conn = sqlite3.connect(db_path, check_same_thread=False)
    row = conn.execute("SELECT payload FROM hdrs WHERE hdr_id = ?", (hdr["hdr_id"],)).fetchone()
    assert row is not None

    corrupted = json.loads(row[0])
    corrupted["mission_id"] = "bogus"
    conn.execute(
        "UPDATE hdrs SET payload = ? WHERE hdr_id = ?",
        (json.dumps(corrupted), hdr["hdr_id"]),
    )
    conn.commit()
    conn.close()

    verdict = api_client.get(f"/api/v1/verify/{hdr['hdr_id']}")
    body = verdict.json()
    assert not body["valid"]
