import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings

API = settings.API_V1_STR


# ---------------------------------------------------------------------------
# Fixtures (module-level helpers)
# ---------------------------------------------------------------------------


def _make_customer_and_equipment(db: Session):
    from tests.utils.customer import create_random_customer
    from tests.utils.equipment import create_random_equipment

    customer = create_random_customer(db)
    equipment = create_random_equipment(db, customer_id=customer.id)
    return customer, equipment


# ---------------------------------------------------------------------------
# Customer-scoped equipment
# ---------------------------------------------------------------------------


def test_create_equipment(as_support: TestClient, db: Session):
    from tests.utils.customer import create_random_customer

    customer = create_random_customer(db)
    payload = {
        "model": "Canon IR-4525",
        "serial_number": "SN-ABC123",
        "manufacturer": "Canon",
        "customer_id": str(customer.id),
    }
    response = as_support.post(
        f"{API}/customers/{customer.id}/equipment", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "Canon IR-4525"
    assert data["customer_id"] == str(customer.id)


def test_create_equipment_customer_mismatch(as_support: TestClient, db: Session):
    from tests.utils.customer import create_random_customer

    customer = create_random_customer(db)
    other_id = uuid.uuid4()
    payload = {
        "model": "HP LaserJet",
        "serial_number": "SN-XYZ",
        "customer_id": str(other_id),
    }
    response = as_support.post(
        f"{API}/customers/{customer.id}/equipment", json=payload
    )
    assert response.status_code == 400


def test_read_customer_equipment(as_support: TestClient, db: Session):
    customer, equipment = _make_customer_and_equipment(db)
    response = as_support.get(f"{API}/customers/{customer.id}/equipment")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    ids = [e["id"] for e in data["data"]]
    assert str(equipment.id) in ids


# ---------------------------------------------------------------------------
# Global equipment
# ---------------------------------------------------------------------------


def test_read_all_equipment(as_support: TestClient, db: Session):
    _make_customer_and_equipment(db)
    response = as_support.get(f"{API}/equipment")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1


def test_read_equipment_by_id(as_support: TestClient, db: Session):
    _, equipment = _make_customer_and_equipment(db)
    response = as_support.get(f"{API}/equipment/{equipment.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(equipment.id)
    # Global view includes customer_name
    assert "customer_name" in data


def test_read_equipment_not_found(as_support: TestClient):
    response = as_support.get(f"{API}/equipment/{uuid.uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Update / Delete
# ---------------------------------------------------------------------------


def test_update_equipment(as_support: TestClient, db: Session):
    _, equipment = _make_customer_and_equipment(db)
    response = as_support.patch(
        f"{API}/equipment/{equipment.id}",
        json={"model": "HP LaserJet Pro MFP"},
    )
    assert response.status_code == 200
    assert response.json()["model"] == "HP LaserJet Pro MFP"


def test_delete_equipment(as_manager: TestClient, db: Session):
    _, equipment = _make_customer_and_equipment(db)
    response = as_manager.delete(f"{API}/equipment/{equipment.id}")
    assert response.status_code == 200

    get_resp = as_manager.get(f"{API}/equipment/{equipment.id}")
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Permission checks
# ---------------------------------------------------------------------------


def test_engineer_cannot_create_equipment(as_engineer: TestClient, db: Session):
    from tests.utils.customer import create_random_customer

    customer = create_random_customer(db)
    payload = {
        "model": "Fail",
        "serial_number": "SN-FAIL",
        "customer_id": str(customer.id),
    }
    response = as_engineer.post(
        f"{API}/customers/{customer.id}/equipment", json=payload
    )
    assert response.status_code == 403
