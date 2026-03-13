import uuid

from sqlmodel import Session, func, select

from app.core.supabase import get_supabase_admin_client
from app.domain.user import UserCreate, UserUpdate
from app.domain.utils import get_datetime_utc
from app.models.user import User


def create_user(*, session: Session, user_in: UserCreate) -> User:
    """Create a Supabase auth user and a local user record."""
    supabase = get_supabase_admin_client()

    # Create Supabase auth user
    auth_response = supabase.auth.admin.create_user({
        "email": user_in.email,
        "password": user_in.password,
        "email_confirm": True,  # Auto-confirm since manager is creating
    })

    supabase_user = auth_response.user
    if not supabase_user:
        raise ValueError("Failed to create Supabase auth user")

    # Create local user record
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        phone=user_in.phone,
        role_id=user_in.role_id,
        supabase_auth_id=uuid.UUID(supabase_user.id),
        is_active=True,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    db_user.sqlmodel_update(user_data)
    db_user.updated_at = get_datetime_utc()
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def get_user_by_supabase_id(*, session: Session, supabase_auth_id: uuid.UUID) -> User | None:
    return session.exec(
        select(User).where(User.supabase_auth_id == supabase_auth_id)
    ).first()


def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def get_users(*, session: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return list(session.exec(select(User).offset(skip).limit(limit)).all())


def get_users_count(*, session: Session) -> int:
    return session.exec(select(func.count()).select_from(User)).one()


def deactivate_user(*, session: Session, db_user: User) -> User:
    db_user.is_active = False
    db_user.updated_at = get_datetime_utc()
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    # Also disable in Supabase
    supabase = get_supabase_admin_client()
    supabase.auth.admin.update_user_by_id(
        str(db_user.supabase_auth_id),
        {"ban_duration": "876600h"},  # ~100 years = effectively disabled
    )
    return db_user


def activate_user(*, session: Session, db_user: User) -> User:
    db_user.is_active = True
    db_user.updated_at = get_datetime_utc()
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    # Also re-enable in Supabase
    supabase = get_supabase_admin_client()
    supabase.auth.admin.update_user_by_id(
        str(db_user.supabase_auth_id),
        {"ban_duration": "none"},
    )
    return db_user
