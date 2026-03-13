import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.api.deps import SessionDep, get_current_user
from app.core.db import engine, init_db
from app.main import app
from app.models import (
    Contact,
    Customer,
    Equipment,
    Item,
    ServiceRequest,
    ServiceVisit,
    User,
)
from app.repository import role as role_repo
from tests.utils.utils import random_lower_string


# ---------------------------------------------------------------------------
# Database fixture — session-scoped, seeds roles/permissions/SLA on first use
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        # Cleanup test data (order respects FK constraints)
        session.execute(delete(ServiceVisit))
        session.execute(delete(ServiceRequest))
        session.execute(delete(Contact))
        session.execute(delete(Equipment))
        session.execute(delete(Customer))
        session.execute(delete(Item))
        session.execute(delete(User))
        session.commit()


@pytest.fixture(autouse=True)
def _clean_session(db: Session) -> Generator[None, None, None]:
    """Roll back pending transactions to prevent cross-test contamination."""
    try:
        db.rollback()
    except Exception:
        pass
    yield


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Test users — one per role, session-scoped (created once for the whole run)
# ---------------------------------------------------------------------------


def _create_test_user(db: Session, role_name: str, label: str) -> User:
    role = role_repo.get_role_by_name(session=db, name=role_name)
    if not role:
        raise RuntimeError(f"Role '{role_name}' not found — was init_db called?")
    user = User(
        email=f"test-{label}-{random_lower_string()[:8]}@test.com",
        full_name=f"Test {label.title()}",
        supabase_auth_id=uuid.uuid4(),
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="session")
def manager_user(db: Session) -> User:
    return _create_test_user(db, "manager", "manager")


@pytest.fixture(scope="session")
def support_user(db: Session) -> User:
    return _create_test_user(db, "support", "support")


@pytest.fixture(scope="session")
def engineer_user(db: Session) -> User:
    return _create_test_user(db, "engineer", "engineer")


@pytest.fixture(scope="session")
def warehouse_user(db: Session) -> User:
    return _create_test_user(db, "warehouse", "warehouse")


# ---------------------------------------------------------------------------
# Auth-override fixtures — bypass Supabase JWT, set current user per role
# ---------------------------------------------------------------------------
# The override fetches the user from the *request's own session* so that
# SQLModel relationship access (e.g. user.role) works without detached errors.


def _make_current_user_override(user_id: uuid.UUID):
    def override(session: SessionDep) -> User:
        user = session.get(User, user_id)
        if not user:
            raise RuntimeError(f"Test user {user_id} not found in DB")
        return user

    return override


@pytest.fixture
def as_manager(
    client: TestClient, manager_user: User
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user] = _make_current_user_override(
        manager_user.id
    )
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def as_support(
    client: TestClient, support_user: User
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user] = _make_current_user_override(
        support_user.id
    )
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def as_engineer(
    client: TestClient, engineer_user: User
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user] = _make_current_user_override(
        engineer_user.id
    )
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def as_warehouse(
    client: TestClient, warehouse_user: User
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user] = _make_current_user_override(
        warehouse_user.id
    )
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def unauthenticated_client(
    client: TestClient,
) -> Generator[TestClient, None, None]:
    """Client with no auth override — requests should get 401."""
    app.dependency_overrides.pop(get_current_user, None)
    yield client


# ---------------------------------------------------------------------------
# Legacy compatibility stubs — tests using these fixtures are skipped until
# they are rewritten to use the role-based auth override fixtures above.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def superuser_token_headers() -> dict[str, str]:
    pytest.skip("Legacy auth removed — rewrite test to use as_manager fixture")


@pytest.fixture(scope="module")
def normal_user_token_headers() -> dict[str, str]:
    pytest.skip("Legacy auth removed — rewrite test to use role-based fixture")
