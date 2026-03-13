from fastapi.testclient import TestClient

from app.core.config import settings


def test_list_runs_empty(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/harvest/runs/",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "count" in data
    assert "data" in data


def test_compare_runs_requires_2_ids(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    import uuid
    r = client.post(
        f"{settings.API_V1_STR}/harvest/runs/compare",
        headers=superuser_token_headers,
        json={"run_ids": [str(uuid.uuid4())]},
    )
    assert r.status_code == 400
