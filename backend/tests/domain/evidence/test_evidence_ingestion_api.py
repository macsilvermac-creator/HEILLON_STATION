"""HTTP-level ingestion coverage."""

from __future__ import annotations

import io


def test_ingestion_flow(api_client, auth_headers):
    mission_id = "mission_http_case"
    response = api_client.post(
        "/api/v1/ingestion",
        headers=auth_headers,
        files=[("file", ("sample.txt", io.BytesIO(b"case-file"), "text/plain"))],
        data={"mission_id": mission_id},
    )

    assert response.status_code == 200

    envelope = response.json()
    hdr = envelope["hdr"]
    checksum = hdr["execution"]["input_hash"]

    verification = api_client.get(f"/api/v1/verify/{hdr['hdr_id']}")
    body = verification.json()

    assert body["valid"]
    assert body["hdr_id"] == hdr["hdr_id"]
    assert envelope["hdr"]["hdr_type"] == "ingestion"
    assert len(checksum) == 64


def test_ingestion_synthesizes_mission_id(api_client, auth_headers):
    """When callers omit mission_id the service fabricates deterministic custody lanes."""

    response = api_client.post(
        "/api/v1/ingestion",
        headers=auth_headers,
        files=[("file", ("orphan.bin", io.BytesIO(b"no-mission-yet"), "application/octet-stream"))],
    )
    assert response.status_code == 200
    body = response.json()
    hdr = body["hdr"]
    assert hdr["mission_id"].startswith("mission_")


def test_ingestion_chains_optional_previous_hdr(api_client, auth_headers):
    seed = api_client.post(
        "/api/v1/ingestion",
        headers=auth_headers,
        files=[("file", ("first.bin", io.BytesIO(b"alpha-chain"), "application/octet-stream"))],
        data={"mission_id": "mission-chain-ingest"},
    )
    assert seed.status_code == 200
    first_hdr = seed.json()["hdr"]

    follow = api_client.post(
        "/api/v1/ingestion",
        headers=auth_headers,
        files=[("file", ("second.bin", io.BytesIO(b"beta-chain"), "application/octet-stream"))],
        data={"mission_id": "mission-chain-ingest", "previous_hdr": first_hdr["hdr_id"]},
    )
    assert follow.status_code == 200
    chained = follow.json()["hdr"]
    assert chained["previous_hdr"] == first_hdr["hdr_id"]


def test_ingestion_minimal_payload(api_client, auth_headers):
    """Single-byte artefacts still traverse deterministic ingestion custody."""

    response = api_client.post(
        "/api/v1/ingestion",
        headers=auth_headers,
        files=[("file", ("minimal.bin", io.BytesIO(b"f"), "application/octet-stream"))],
        data={"mission_id": "mission-minimal-ingest"},
    )
    assert response.status_code == 200
