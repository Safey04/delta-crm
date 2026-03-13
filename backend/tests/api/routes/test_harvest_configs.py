from fastapi.testclient import TestClient

from app.core.config import settings


def test_create_and_list_config(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    # Create
    r = client.post(
        f"{settings.API_V1_STR}/harvest/configs/",
        headers=superuser_token_headers,
        json={
            "name": "Summer Standard",
            "settings": {"daily_capacity": 30000, "min_weight": 1.8},
            "is_public": False,
        },
    )
    assert r.status_code == 200
    config = r.json()
    assert config["name"] == "Summer Standard"
    config_id = config["id"]

    # List
    r = client.get(
        f"{settings.API_V1_STR}/harvest/configs/",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1

    # Get by ID
    r = client.get(
        f"{settings.API_V1_STR}/harvest/configs/{config_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Summer Standard"

    # Update
    r = client.put(
        f"{settings.API_V1_STR}/harvest/configs/{config_id}",
        headers=superuser_token_headers,
        json={"name": "Winter Standard"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Winter Standard"

    # Delete
    r = client.delete(
        f"{settings.API_V1_STR}/harvest/configs/{config_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200


def test_create_config_requires_auth(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/harvest/configs/",
        json={"name": "Test", "settings": {}},
    )
    assert r.status_code in (401, 403)
