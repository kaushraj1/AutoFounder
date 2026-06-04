"""API integration tests (via TestClient)."""

import uuid

from fastapi.testclient import TestClient


def test_submit_idea_then_fetch_run(client: TestClient) -> None:
    response = client.post(
        "/v1/ideas", json={"text": "A SaaS to auto-generate compliance docs for startups."}
    )
    assert response.status_code == 201
    run_id = response.json()["id"]

    fetched = client.get(f"/v1/runs/{run_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == run_id


def test_unknown_run_returns_404(client: TestClient) -> None:
    response = client.get(f"/v1/runs/{uuid.uuid4()}")
    assert response.status_code == 404


def test_short_idea_is_rejected(client: TestClient) -> None:
    response = client.post("/v1/ideas", json={"text": "tooshort"})
    assert response.status_code == 422
