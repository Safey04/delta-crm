from fastapi.testclient import TestClient

from app.core.config import settings


def test_list_plans_empty(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/harvest/plans/",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "count" in data
    assert "data" in data


def test_list_plans_requires_auth(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/harvest/plans/")
    assert r.status_code in (401, 403)


def test_get_plan_not_found(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    import uuid
    r = client.get(
        f"{settings.API_V1_STR}/harvest/plans/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404
