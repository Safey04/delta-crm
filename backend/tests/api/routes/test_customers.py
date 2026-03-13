import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings

API = settings.API_V1_STR


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def test_create_customer(as_support: TestClient):
    payload = {
        "name": "Acme Corp",
        "company_name": "Acme Corporation",
        "phone": "+201234567890",
        "email": "info@acme.example.com",
        "segment": "enterprise",
    }
    response = as_support.post(f"{API}/customers/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["segment"] == "enterprise"
    assert "id" in data


def test_read_customers(as_support: TestClient, db: Session):
    from tests.utils.customer import create_random_customer

    create_random_customer(db)
    response = as_support.get(f"{API}/customers/")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert len(data["data"]) >= 1


def test_read_customer_by_id(as_support: TestClient, db: Session):
    from tests.utils.customer import create_random_customer

    customer = create_random_customer(db)
    response = as_support.get(f"{API}/customers/{customer.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(customer.id)


def test_read_customer_not_found(as_support: TestClient):
    response = as_support.get(f"{API}/customers/{uuid.uuid4()}")
    assert response.status_code == 404


def test_update_customer(as_support: TestClient, db: Session):
    from tests.utils.customer import create_random_customer

    customer = create_random_customer(db)
    response = as_support.patch(
        f"{API}/customers/{customer.id}",
        json={"name": "Updated Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_delete_customer(as_manager: TestClient, db: Session):
    from tests.utils.customer import create_random_customer

    customer = create_random_customer(db)
    response = as_manager.delete(f"{API}/customers/{customer.id}")
    assert response.status_code == 200

    # Verify deleted
    get_resp = as_manager.get(f"{API}/customers/{customer.id}")
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Search & Filter
# ---------------------------------------------------------------------------


def test_customer_search(as_support: TestClient, db: Session):
    from tests.utils.customer import create_random_customer

    customer = create_random_customer(db, name="UniqueSearchName123")
    response = as_support.get(
        f"{API}/customers/", params={"search": "UniqueSearchName123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    names = [c["name"] for c in data["data"]]
    assert "UniqueSearchName123" in names


def test_customer_filter_segment(as_support: TestClient, db: Session):
    from tests.utils.customer import create_random_customer

    create_random_customer(db, segment="walk_in")
    response = as_support.get(
        f"{API}/customers/", params={"segment": "walk_in"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    for c in data["data"]:
        assert c["segment"] == "walk_in"


# ---------------------------------------------------------------------------
# Permission checks
# ---------------------------------------------------------------------------


def test_engineer_cannot_create_customer(as_engineer: TestClient):
    payload = {"name": "Should Fail", "segment": "smb"}
    response = as_engineer.post(f"{API}/customers/", json=payload)
    assert response.status_code == 403


def test_engineer_cannot_delete_customer(as_engineer: TestClient):
    response = as_engineer.delete(f"{API}/customers/{uuid.uuid4()}")
    assert response.status_code == 403
