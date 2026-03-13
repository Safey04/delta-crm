import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.user import User

API = settings.API_V1_STR


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def test_create_service_request(
    as_support: TestClient, db: Session, support_user: User
):
    from tests.utils.customer import create_random_customer

    customer = create_random_customer(db)
    payload = {
        "description": "Toner replacement needed",
        "priority": "high",
        "source": "email",
        "customer_id": str(customer.id),
    }
    response = as_support.post(f"{API}/service-requests/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Toner replacement needed"
    assert data["status"] == "new"
    assert data["customer_id"] == str(customer.id)
    assert data["created_by"] == str(support_user.id)


def test_create_service_request_customer_not_found(as_support: TestClient):
    payload = {
        "description": "Should fail",
        "customer_id": str(uuid.uuid4()),
    }
    response = as_support.post(f"{API}/service-requests/", json=payload)
    assert response.status_code == 404


def test_read_service_requests(
    as_support: TestClient, db: Session, support_user: User
):
    from tests.utils.customer import create_random_customer
    from tests.utils.service_request import create_random_service_request

    customer = create_random_customer(db)
    create_random_service_request(db, customer.id, support_user.id)

    response = as_support.get(f"{API}/service-requests/")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1


def test_read_service_request_by_id(
    as_support: TestClient, db: Session, support_user: User
):
    from tests.utils.customer import create_random_customer
    from tests.utils.service_request import create_random_service_request

    customer = create_random_customer(db)
    sr = create_random_service_request(db, customer.id, support_user.id)

    response = as_support.get(f"{API}/service-requests/{sr.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(sr.id)


def test_update_service_request(
    as_support: TestClient, db: Session, support_user: User
):
    from tests.utils.customer import create_random_customer
    from tests.utils.service_request import create_random_service_request

    customer = create_random_customer(db)
    sr = create_random_service_request(db, customer.id, support_user.id)

    response = as_support.patch(
        f"{API}/service-requests/{sr.id}",
        json={"diagnosis": "Paper feed roller worn out"},
    )
    assert response.status_code == 200
    assert response.json()["diagnosis"] == "Paper feed roller worn out"


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


def test_valid_status_transition(
    as_support: TestClient, db: Session, support_user: User
):
    from tests.utils.customer import create_random_customer
    from tests.utils.service_request import create_random_service_request

    customer = create_random_customer(db)
    sr = create_random_service_request(db, customer.id, support_user.id)

    # new → assigned → in_progress → completed
    for new_status in ["assigned", "in_progress", "completed"]:
        resp = as_support.post(
            f"{API}/service-requests/{sr.id}/status",
            json={"status": new_status},
        )
        assert resp.status_code == 200, (
            f"Transition to '{new_status}' failed: {resp.json()}"
        )
        assert resp.json()["status"] == new_status


def test_invalid_status_transition(
    as_support: TestClient, db: Session, support_user: User
):
    from tests.utils.customer import create_random_customer
    from tests.utils.service_request import create_random_service_request

    customer = create_random_customer(db)
    sr = create_random_service_request(db, customer.id, support_user.id)

    # new → completed is NOT allowed (must go through assigned first)
    response = as_support.post(
        f"{API}/service-requests/{sr.id}/status",
        json={"status": "completed"},
    )
    assert response.status_code == 400
    assert "Cannot transition" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Assign engineer
# ---------------------------------------------------------------------------


def test_assign_engineer(
    as_support: TestClient, db: Session, support_user: User, engineer_user: User
):
    from tests.utils.customer import create_random_customer
    from tests.utils.service_request import create_random_service_request

    customer = create_random_customer(db)
    sr = create_random_service_request(db, customer.id, support_user.id)

    response = as_support.post(
        f"{API}/service-requests/{sr.id}/assign",
        params={"engineer_id": str(engineer_user.id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assigned_engineer_id"] == str(engineer_user.id)
    assert data["status"] == "assigned"


def test_assign_nonexistent_engineer(
    as_support: TestClient, db: Session, support_user: User
):
    from tests.utils.customer import create_random_customer
    from tests.utils.service_request import create_random_service_request

    customer = create_random_customer(db)
    sr = create_random_service_request(db, customer.id, support_user.id)

    response = as_support.post(
        f"{API}/service-requests/{sr.id}/assign",
        params={"engineer_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------


def test_filter_by_status(
    as_support: TestClient, db: Session, support_user: User
):
    from tests.utils.customer import create_random_customer
    from tests.utils.service_request import create_random_service_request

    customer = create_random_customer(db)
    create_random_service_request(db, customer.id, support_user.id)

    response = as_support.get(
        f"{API}/service-requests/", params={"status": "new"}
    )
    assert response.status_code == 200
    for sr in response.json()["data"]:
        assert sr["status"] == "new"


# ---------------------------------------------------------------------------
# Permission checks
# ---------------------------------------------------------------------------


def test_warehouse_cannot_create_service_request(as_warehouse: TestClient):
    payload = {
        "description": "Should fail",
        "customer_id": str(uuid.uuid4()),
    }
    response = as_warehouse.post(f"{API}/service-requests/", json=payload)
    assert response.status_code == 403
