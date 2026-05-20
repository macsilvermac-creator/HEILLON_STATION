"""Lightweight routing smoke checks independent of dossier payloads."""

from __future__ import annotations


def test_health_returns_ok(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_openapi_includes_easy_prefixes(api_client):
    spec = api_client.get("/openapi.json").json()
    paths = spec.get("paths", {})
    assert any(p.startswith("/api/v1/mission") for p in paths)
    assert any(p.startswith("/api/v1/auth") for p in paths)
    assert any(p.startswith("/api/v1/compliance") for p in paths)


def test_swagger_docs_ui_responds(api_client):
    resp = api_client.get("/docs")
    assert resp.status_code == 200
