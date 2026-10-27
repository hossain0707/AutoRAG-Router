import os
from fastapi.testclient import TestClient
from autorag.api import app


def test_api_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTORAG_DB", str(tmp_path / "api.db"))
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        response = client.post("/v1/documents", json={"documents": [
            {"id": "test", "text": "Encryption protects customer data.", "tenant_id": "t"}]})
        assert response.status_code == 200
        q = client.post("/v1/query", json={"query": "How does encryption protect data?", "tenant_id": "t"})
        assert q.status_code == 200
        assert q.json()["hits"][0]["document_id"] == "test"
        assert client.get("/").status_code == 200


def test_api_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTORAG_DB", str(tmp_path / "auth.db"))
    monkeypatch.setenv("AUTORAG_API_KEY", "a-private-test-key")
    with TestClient(app) as client:
        assert client.get("/v1/strategies").status_code == 401
        assert client.get("/v1/strategies", headers={"x-api-key":"a-private-test-key"}).status_code == 200
        assert client.get("/healthz").status_code == 200
