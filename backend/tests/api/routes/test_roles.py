import uuid

from fastapi.testclient import TestClient

from app.core.config import settings
from tests.utils.utils import random_lower_string

API = settings.API_V1_STR


# ---------------------------------------------------------------------------
# List roles
# ---------------------------------------------------------------------------


def test_read_roles_returns_default_system_roles(as_manager: TestClient):
    response = as_manager.get(f"{API}/roles/")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 4
    role_names = {r["name"] for r in data["data"]}
    assert {"manager", "support", "engineer", "warehouse"} <= role_names
    # All default roles are system roles
    for role in data["data"]:
        if role["name"] in {"manager", "support", "engineer", "warehouse"}:
            assert role["is_system"] is True


# ---------------------------------------------------------------------------
# Read single role with permissions
# ---------------------------------------------------------------------------


def test_read_role_by_id(as_manager: TestClient):
    # Get the manager role first
    list_resp = as_manager.get(f"{API}/roles/")
    manager_role = next(
        r for r in list_resp.json()["data"] if r["name"] == "manager"
    )

    response = as_manager.get(f"{API}/roles/{manager_role['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "manager"
    assert data["is_system"] is True
    assert "permissions" in data
    assert len(data["permissions"]) > 0


def test_read_role_not_found(as_manager: TestClient):
    fake_id = uuid.uuid4()
    response = as_manager.get(f"{API}/roles/{fake_id}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Read permissions
# ---------------------------------------------------------------------------


def test_read_permissions(as_manager: TestClient):
    response = as_manager.get(f"{API}/roles/permissions")
    assert response.status_code == 200
    data = response.json()
    # At least 28 seeded permissions
    assert data["count"] >= 28
    # Spot-check a few known permissions
    perm_keys = {(p["resource"], p["action"]) for p in data["data"]}
    assert ("customer", "view") in perm_keys
    assert ("service_request", "create") in perm_keys
    assert ("user", "delete") in perm_keys


# ---------------------------------------------------------------------------
# Create / Update / Delete custom role
# ---------------------------------------------------------------------------


def test_create_custom_role(as_manager: TestClient):
    name = f"custom_{random_lower_string()[:8]}"
    payload = {"name": name, "description": "A test role"}
    response = as_manager.post(f"{API}/roles/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name
    assert data["is_system"] is False


def test_create_duplicate_role_conflict(as_manager: TestClient):
    payload = {"name": "manager", "description": "Duplicate"}
    response = as_manager.post(f"{API}/roles/", json=payload)
    assert response.status_code == 409


def test_update_custom_role(as_manager: TestClient):
    # Create a role to update
    create_resp = as_manager.post(
        f"{API}/roles/", json={"name": f"upd_{random_lower_string()[:8]}"}
    )
    role_id = create_resp.json()["id"]

    response = as_manager.patch(
        f"{API}/roles/{role_id}",
        json={"description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"


def test_set_role_permissions(as_manager: TestClient):
    # Create a fresh role
    create_resp = as_manager.post(
        f"{API}/roles/", json={"name": f"perm_{random_lower_string()[:8]}"}
    )
    role_id = create_resp.json()["id"]

    # Get some permission IDs
    perms_resp = as_manager.get(f"{API}/roles/permissions")
    all_perms = perms_resp.json()["data"]
    # Pick the first 3 permissions
    perm_ids = [p["id"] for p in all_perms[:3]]

    response = as_manager.put(
        f"{API}/roles/{role_id}/permissions",
        json={"permission_ids": perm_ids},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["permissions"]) == 3


def test_delete_custom_role(as_manager: TestClient):
    create_resp = as_manager.post(
        f"{API}/roles/", json={"name": f"del_{random_lower_string()[:8]}"}
    )
    role_id = create_resp.json()["id"]

    response = as_manager.delete(f"{API}/roles/{role_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_resp = as_manager.get(f"{API}/roles/{role_id}")
    assert get_resp.status_code == 404


def test_delete_system_role_forbidden(as_manager: TestClient):
    list_resp = as_manager.get(f"{API}/roles/")
    system_role = next(
        r for r in list_resp.json()["data"] if r["is_system"] is True
    )

    response = as_manager.delete(f"{API}/roles/{system_role['id']}")
    assert response.status_code == 400
    assert "Cannot delete system role" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Permission checks — engineer cannot manage roles (no user.create/edit/delete)
# ---------------------------------------------------------------------------


def test_engineer_cannot_create_role(as_engineer: TestClient):
    payload = {"name": "should_fail"}
    response = as_engineer.post(f"{API}/roles/", json=payload)
    assert response.status_code == 403


def test_engineer_cannot_delete_role(as_engineer: TestClient):
    # Try to delete a role — engineer lacks user.delete permission
    fake_id = uuid.uuid4()
    response = as_engineer.delete(f"{API}/roles/{fake_id}")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Unauthenticated access
# ---------------------------------------------------------------------------


def test_unauthenticated_cannot_list_roles(unauthenticated_client: TestClient):
    response = unauthenticated_client.get(f"{API}/roles/")
    # OAuth2PasswordBearer returns 401 when no token is provided
    assert response.status_code == 401
