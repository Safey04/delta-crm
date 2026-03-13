# Delta CRM Phase 1 — Foundation (MVP) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the foundation of Delta CRM: Supabase Auth, configurable RBAC, customer management (with contacts and equipment), and service request lifecycle — all following DDD layered architecture.

**Architecture:** Replace the template's built-in JWT + password auth with Supabase Auth. Backend validates Supabase JWTs and maintains a local `users` table linked by `supabase_auth_id`. All new entities follow the existing 5-layer pattern: domain (schemas) → models (ORM) → repository (data access) → services (business logic) → api/routes (HTTP). Frontend uses Supabase JS SDK for login, sends JWT on all API calls.

**Tech Stack:** FastAPI + SQLModel + PostgreSQL (Supabase) + Supabase Auth + Supabase Storage + React 19 + TanStack Router/Query + shadcn/ui + Tailwind CSS

**Design Document:** `docs/2026-03-13-delta-crm-design.md`

---

## Task 1: Add Supabase Dependencies & Config

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py`
- Modify: `.env`
- Create: `backend/app/core/supabase.py`

**Step 1: Add supabase-py and PyJWT dependencies**

In `backend/pyproject.toml`, add to `[project.dependencies]`:
```toml
"supabase>=2.13.0",
```

**Step 2: Install dependencies**

Run: `cd backend && uv sync`
Expected: Dependencies installed successfully

**Step 3: Add Supabase config to Settings**

In `backend/app/core/config.py`, add fields to the `Settings` class:
```python
SUPABASE_URL: str
SUPABASE_ANON_KEY: str
SUPABASE_SERVICE_ROLE_KEY: str  # For admin operations (creating users)
SUPABASE_JWT_SECRET: str  # For validating JWTs
```

**Step 4: Add env vars to .env**

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

**Step 5: Create Supabase client utility**

Create `backend/app/core/supabase.py`:
```python
from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings


@lru_cache
def get_supabase_client() -> Client:
    """Supabase client with anon key (for general operations)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@lru_cache
def get_supabase_admin_client() -> Client:
    """Supabase client with service role key (for admin operations like creating auth users)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
```

**Step 6: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/app/core/config.py backend/app/core/supabase.py .env
git commit -m "feat: add Supabase dependencies and configuration"
```

---

## Task 2: RBAC Models — Role, Permission, RolePermission

**Files:**
- Create: `backend/app/models/role.py`
- Create: `backend/app/domain/role.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write the domain schemas**

Create `backend/app/domain/role.py`:
```python
import uuid

from sqlmodel import SQLModel


# --- Role ---

class RoleBase(SQLModel):
    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(SQLModel):
    name: str | None = None
    description: str | None = None


class RolePublic(RoleBase):
    id: uuid.UUID
    is_system: bool


class RolesPublic(SQLModel):
    data: list[RolePublic]
    count: int


# --- Permission ---

class PermissionBase(SQLModel):
    resource: str  # e.g. "customer", "service_request", "inventory"
    action: str  # e.g. "view", "create", "edit", "delete", "approve", "export"
    description: str | None = None


class PermissionPublic(PermissionBase):
    id: uuid.UUID


class PermissionsPublic(SQLModel):
    data: list[PermissionPublic]
    count: int


# --- RolePermission ---

class RolePermissionSet(SQLModel):
    """Used to set permissions for a role — list of permission IDs."""
    permission_ids: list[uuid.UUID]


class RoleWithPermissions(RolePublic):
    permissions: list[PermissionPublic]
```

**Step 2: Write the ORM models**

Create `backend/app/models/role.py`:
```python
import uuid

from sqlmodel import Field, Relationship, SQLModel

from app.domain.role import PermissionBase, RoleBase


class RolePermission(SQLModel, table=True):
    role_id: uuid.UUID = Field(foreign_key="role.id", primary_key=True, ondelete="CASCADE")
    permission_id: uuid.UUID = Field(foreign_key="permission.id", primary_key=True, ondelete="CASCADE")


class Role(RoleBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    is_system: bool = Field(default=False)
    permissions: list["Permission"] = Relationship(
        back_populates="roles",
        link_model=RolePermission,
    )
    users: list["User"] = Relationship(back_populates="role")


class Permission(PermissionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    roles: list[Role] = Relationship(
        back_populates="permissions",
        link_model=RolePermission,
    )
```

**Step 3: Register models in __init__.py**

In `backend/app/models/__init__.py`, add:
```python
from app.models.role import Permission, Role, RolePermission  # noqa: F401
```

**Step 4: Commit**

```bash
git add backend/app/models/role.py backend/app/domain/role.py backend/app/models/__init__.py
git commit -m "feat: add Role, Permission, RolePermission models and domain schemas"
```

---

## Task 3: Update User Model for Supabase Auth + RBAC

**Files:**
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/domain/user.py`

**Step 1: Update User ORM model**

Replace `backend/app/models/user.py` with:
```python
import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from app.domain.user import UserBase
from app.domain.utils import get_datetime_utc


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    supabase_auth_id: uuid.UUID = Field(unique=True, index=True)
    hashed_password: str = Field(default="")  # Keep for backward compat during migration, unused with Supabase
    role_id: uuid.UUID | None = Field(default=None, foreign_key="role.id", ondelete="SET NULL")
    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    updated_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    role: "Role | None" = Relationship(back_populates="users")
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
```

**Step 2: Update User domain schemas**

Replace `backend/app/domain/user.py` with:
```python
import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from app.domain.role import RolePublic


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    full_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)


class UserCreate(SQLModel):
    """Manager creates a user — Supabase Auth account + local record."""
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None
    password: str = Field(min_length=8, max_length=128)
    role_id: uuid.UUID


class UserUpdate(SQLModel):
    email: EmailStr | None = None
    full_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    role_id: uuid.UUID | None = None


class UserUpdateMe(SQLModel):
    full_name: str | None = None
    phone: str | None = None


class UserPublic(UserBase):
    id: uuid.UUID
    role_id: uuid.UUID | None
    role: RolePublic | None = None
    created_at: datetime | None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
```

**Step 3: Commit**

```bash
git add backend/app/models/user.py backend/app/domain/user.py
git commit -m "feat: update User model for Supabase Auth and RBAC"
```

---

## Task 4: Supabase Auth — Replace JWT Validation in deps.py

**Files:**
- Modify: `backend/app/api/deps.py`
- Modify: `backend/app/core/security.py`

**Step 1: Update security.py — add Supabase JWT validation**

Keep existing functions but add:
```python
import jwt

from app.core.config import settings


def decode_supabase_token(token: str) -> dict:
    """Decode and validate a Supabase JWT. Returns payload or raises."""
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")
```

**Step 2: Update deps.py — validate Supabase JWT and look up local user**

Replace `get_current_user` in `backend/app/api/deps.py`:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from typing import Annotated

from app.core.db import engine
from app.core.security import decode_supabase_token
from app.models.user import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = decode_supabase_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    supabase_user_id = payload.get("sub")
    if not supabase_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token payload",
        )

    user = session.exec(
        select(User).where(User.supabase_auth_id == supabase_user_id)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(resource: str, action: str):
    """Dependency factory: checks if current user's role has the given permission."""
    def check(current_user: CurrentUser, session: SessionDep) -> User:
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned",
            )
        # Check if any of the role's permissions match
        from app.models.role import Permission, RolePermission
        has_perm = session.exec(
            select(RolePermission)
            .join(Permission)
            .where(
                RolePermission.role_id == current_user.role_id,
                Permission.resource == resource,
                Permission.action == action,
            )
        ).first()

        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource}.{action}",
            )
        return current_user
    return check
```

**Step 3: Remove get_current_active_superuser**

This dependency is no longer needed — permission checks replace it. Remove the function from `deps.py` but keep it commented or remove references gradually.

**Step 4: Commit**

```bash
git add backend/app/api/deps.py backend/app/core/security.py
git commit -m "feat: replace JWT auth with Supabase token validation and permission system"
```

---

## Task 5: RBAC Repository & Seed Data

**Files:**
- Create: `backend/app/repository/role.py`
- Modify: `backend/app/core/db.py`

**Step 1: Create role repository**

Create `backend/app/repository/role.py`:
```python
import uuid

from sqlmodel import Session, select

from app.domain.role import RoleCreate, RoleUpdate
from app.models.role import Permission, Role, RolePermission


def create_role(*, session: Session, role_in: RoleCreate, is_system: bool = False) -> Role:
    db_role = Role.model_validate(role_in, update={"is_system": is_system})
    session.add(db_role)
    session.commit()
    session.refresh(db_role)
    return db_role


def get_role_by_name(*, session: Session, name: str) -> Role | None:
    return session.exec(select(Role).where(Role.name == name)).first()


def get_role_by_id(*, session: Session, role_id: uuid.UUID) -> Role | None:
    return session.get(Role, role_id)


def get_roles(*, session: Session, skip: int = 0, limit: int = 100) -> list[Role]:
    return list(session.exec(select(Role).offset(skip).limit(limit)).all())


def get_roles_count(*, session: Session) -> int:
    from sqlmodel import func
    return session.exec(select(func.count()).select_from(Role)).one()


def update_role(*, session: Session, db_role: Role, role_in: RoleUpdate) -> Role:
    role_data = role_in.model_dump(exclude_unset=True)
    db_role.sqlmodel_update(role_data)
    session.add(db_role)
    session.commit()
    session.refresh(db_role)
    return db_role


def delete_role(*, session: Session, db_role: Role) -> None:
    session.delete(db_role)
    session.commit()


# --- Permissions ---

def get_or_create_permission(
    *, session: Session, resource: str, action: str, description: str | None = None
) -> Permission:
    perm = session.exec(
        select(Permission).where(
            Permission.resource == resource,
            Permission.action == action,
        )
    ).first()
    if perm:
        return perm
    perm = Permission(resource=resource, action=action, description=description)
    session.add(perm)
    session.commit()
    session.refresh(perm)
    return perm


def get_permissions(*, session: Session) -> list[Permission]:
    return list(session.exec(select(Permission)).all())


def set_role_permissions(
    *, session: Session, role_id: uuid.UUID, permission_ids: list[uuid.UUID]
) -> None:
    # Remove existing
    existing = session.exec(
        select(RolePermission).where(RolePermission.role_id == role_id)
    ).all()
    for rp in existing:
        session.delete(rp)

    # Add new
    for perm_id in permission_ids:
        session.add(RolePermission(role_id=role_id, permission_id=perm_id))

    session.commit()


def get_role_permissions(*, session: Session, role_id: uuid.UUID) -> list[Permission]:
    return list(
        session.exec(
            select(Permission)
            .join(RolePermission)
            .where(RolePermission.role_id == role_id)
        ).all()
    )
```

**Step 2: Update init_db to seed default roles and permissions**

Modify `backend/app/core/db.py` — replace the existing `init_db` function:
```python
from app.models.role import Permission, Role, RolePermission  # noqa: F401
from app.repository import role as role_repo
from app.repository import user as user_repo

# Define all permissions
PERMISSIONS = [
    ("customer", "view"), ("customer", "create"), ("customer", "edit"), ("customer", "delete"),
    ("service_request", "view"), ("service_request", "create"), ("service_request", "edit"),
    ("service_request", "delete"), ("service_request", "approve"),
    ("quotation", "view"), ("quotation", "create"), ("quotation", "edit"),
    ("quotation", "delete"), ("quotation", "approve"),
    ("inventory", "view"), ("inventory", "create"), ("inventory", "edit"),
    ("inventory", "delete"), ("inventory", "request"),
    ("invoice", "view"), ("invoice", "create"), ("invoice", "edit"), ("invoice", "delete"),
    ("report", "view"), ("report", "financial"), ("report", "operational"), ("report", "inventory"),
    ("user", "view"), ("user", "create"), ("user", "edit"), ("user", "delete"),
]

# Default role → permission mappings
DEFAULT_ROLES = {
    "manager": [
        "customer.*", "service_request.*", "quotation.*", "inventory.*",
        "invoice.*", "report.*", "user.*",
    ],
    "support": [
        "customer.view", "customer.create", "customer.edit",
        "service_request.view", "service_request.create", "service_request.edit",
        "quotation.view", "quotation.create", "quotation.edit",
        "inventory.view",
        "invoice.view",
        "report.view", "report.operational",
    ],
    "engineer": [
        "customer.view",
        "service_request.view", "service_request.edit",
        "inventory.view", "inventory.request",
    ],
    "warehouse": [
        "customer.view",
        "service_request.view",
        "inventory.view", "inventory.create", "inventory.edit", "inventory.delete",
        "report.view", "report.inventory",
    ],
}


def _match_permission(perm_pattern: str, resource: str, action: str) -> bool:
    """Check if a permission pattern (e.g. 'customer.*') matches a resource.action."""
    pat_resource, pat_action = perm_pattern.split(".")
    if pat_resource != resource:
        return False
    return pat_action == "*" or pat_action == action


def seed_roles_and_permissions(session: Session) -> None:
    """Create default permissions and roles if they don't exist."""
    # Create all permissions
    perm_map: dict[tuple[str, str], Permission] = {}
    for resource, action in PERMISSIONS:
        perm = role_repo.get_or_create_permission(
            session=session, resource=resource, action=action,
            description=f"{action} {resource}",
        )
        perm_map[(resource, action)] = perm

    # Create default roles with permissions
    for role_name, patterns in DEFAULT_ROLES.items():
        existing = role_repo.get_role_by_name(session=session, name=role_name)
        if existing:
            continue

        from app.domain.role import RoleCreate
        role = role_repo.create_role(
            session=session,
            role_in=RoleCreate(name=role_name, description=f"Default {role_name} role"),
            is_system=True,
        )

        # Resolve patterns to permission IDs
        perm_ids = []
        for pattern in patterns:
            for (resource, action), perm in perm_map.items():
                if _match_permission(pattern, resource, action):
                    perm_ids.append(perm.id)

        role_repo.set_role_permissions(
            session=session, role_id=role.id, permission_ids=perm_ids,
        )


def init_db(session: Session) -> None:
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

    # Seed roles and permissions
    seed_roles_and_permissions(session)

    # Create first superuser (manager role) if doesn't exist
    user = user_repo.get_user_by_email(session=session, email=settings.FIRST_SUPERUSER)
    if not user:
        manager_role = role_repo.get_role_by_name(session=session, name="manager")
        if manager_role:
            from app.core.supabase import get_supabase_admin_client
            # Note: First superuser Supabase account should be created manually
            # or via Supabase dashboard. This just creates the local record.
            import logging
            logging.getLogger(__name__).warning(
                "First superuser local record must be created after Supabase auth user exists. "
                "Create the Supabase auth user first, then the app will sync on first login."
            )
```

**Step 3: Commit**

```bash
git add backend/app/repository/role.py backend/app/core/db.py
git commit -m "feat: add RBAC repository with seed data for default roles and permissions"
```

---

## Task 6: User Repository — Supabase Integration

**Files:**
- Modify: `backend/app/repository/user.py`

**Step 1: Rewrite user repository for Supabase**

Replace `backend/app/repository/user.py`:
```python
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
```

**Step 2: Commit**

```bash
git add backend/app/repository/user.py
git commit -m "feat: rewrite user repository for Supabase Auth integration"
```

---

## Task 7: User & Role API Routes

**Files:**
- Modify: `backend/app/api/routes/users.py`
- Create: `backend/app/api/routes/roles.py`
- Modify: `backend/app/api/main.py`

**Step 1: Rewrite user routes**

Replace `backend/app/api/routes/users.py` with routes that use permission checks:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.user import UserCreate, UserPublic, UserUpdate, UserUpdateMe, UsersPublic
from app.repository import user as user_repo

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UsersPublic)
def read_users(
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("user", "view")),
    skip: int = 0,
    limit: int = 100,
):
    users = user_repo.get_users(session=session, skip=skip, limit=limit)
    count = user_repo.get_users_count(session=session)
    return UsersPublic(data=[UserPublic.model_validate(u) for u in users], count=count)


@router.post("/", response_model=UserPublic)
def create_user(
    session: SessionDep,
    user_in: UserCreate,
    _: CurrentUser = Depends(require_permission("user", "create")),
):
    existing = user_repo.get_user_by_email(session=session, email=user_in.email)
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    user = user_repo.create_user(session=session, user_in=user_in)
    return UserPublic.model_validate(user)


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser):
    return UserPublic.model_validate(current_user)


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    session: SessionDep,
    user_in: UserUpdateMe,
    current_user: CurrentUser,
):
    user = user_repo.update_user(session=session, db_user=current_user, user_in=user_in)
    return UserPublic.model_validate(user)


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("user", "view")),
):
    user = user_repo.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic.model_validate(user)


@router.patch("/{user_id}", response_model=UserPublic)
def update_user(
    user_id: uuid.UUID,
    session: SessionDep,
    user_in: UserUpdate,
    _: CurrentUser = Depends(require_permission("user", "edit")),
):
    user = user_repo.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_repo.update_user(session=session, db_user=user, user_in=user_in)
    return UserPublic.model_validate(user)


@router.post("/{user_id}/deactivate", response_model=UserPublic)
def deactivate_user(
    user_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("user", "edit")),
):
    user = user_repo.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_repo.deactivate_user(session=session, db_user=user)
    return UserPublic.model_validate(user)


@router.post("/{user_id}/activate", response_model=UserPublic)
def activate_user(
    user_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("user", "edit")),
):
    user = user_repo.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_repo.activate_user(session=session, db_user=user)
    return UserPublic.model_validate(user)
```

**Step 2: Create role routes**

Create `backend/app/api/routes/roles.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.role import (
    PermissionsPublic,
    RoleCreate,
    RolePermissionSet,
    RolePublic,
    RoleUpdate,
    RoleWithPermissions,
    RolesPublic,
)
from app.repository import role as role_repo

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=RolesPublic)
def read_roles(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    roles = role_repo.get_roles(session=session, skip=skip, limit=limit)
    count = role_repo.get_roles_count(session=session)
    return RolesPublic(data=[RolePublic.model_validate(r) for r in roles], count=count)


@router.post("/", response_model=RolePublic)
def create_role(
    session: SessionDep,
    role_in: RoleCreate,
    _: CurrentUser = Depends(require_permission("user", "create")),
):
    existing = role_repo.get_role_by_name(session=session, name=role_in.name)
    if existing:
        raise HTTPException(status_code=409, detail="Role with this name already exists")
    role = role_repo.create_role(session=session, role_in=role_in)
    return RolePublic.model_validate(role)


@router.get("/permissions", response_model=PermissionsPublic)
def read_permissions(
    session: SessionDep,
    current_user: CurrentUser,
):
    perms = role_repo.get_permissions(session=session)
    return PermissionsPublic(
        data=[p for p in perms],
        count=len(perms),
    )


@router.get("/{role_id}", response_model=RoleWithPermissions)
def read_role(
    role_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
):
    role = role_repo.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    permissions = role_repo.get_role_permissions(session=session, role_id=role_id)
    return RoleWithPermissions(
        **RolePublic.model_validate(role).model_dump(),
        permissions=permissions,
    )


@router.patch("/{role_id}", response_model=RolePublic)
def update_role(
    role_id: uuid.UUID,
    session: SessionDep,
    role_in: RoleUpdate,
    _: CurrentUser = Depends(require_permission("user", "edit")),
):
    role = role_repo.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role = role_repo.update_role(session=session, db_role=role, role_in=role_in)
    return RolePublic.model_validate(role)


@router.put("/{role_id}/permissions", response_model=RoleWithPermissions)
def set_role_permissions(
    role_id: uuid.UUID,
    session: SessionDep,
    perm_set: RolePermissionSet,
    _: CurrentUser = Depends(require_permission("user", "edit")),
):
    role = role_repo.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role_repo.set_role_permissions(
        session=session, role_id=role_id, permission_ids=perm_set.permission_ids,
    )
    permissions = role_repo.get_role_permissions(session=session, role_id=role_id)
    return RoleWithPermissions(
        **RolePublic.model_validate(role).model_dump(),
        permissions=permissions,
    )


@router.delete("/{role_id}")
def delete_role(
    role_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("user", "delete")),
):
    role = role_repo.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    role_repo.delete_role(session=session, db_role=role)
    return {"message": "Role deleted"}
```

**Step 3: Register new routes**

In `backend/app/api/main.py`, add:
```python
from app.api.routes import roles
api_router.include_router(roles.router)
```

**Step 4: Commit**

```bash
git add backend/app/api/routes/users.py backend/app/api/routes/roles.py backend/app/api/main.py
git commit -m "feat: add user and role management API routes with permission checks"
```

---

## Task 8: Customer Model — Domain, ORM, Repository, Routes

**Files:**
- Create: `backend/app/domain/customer.py`
- Create: `backend/app/models/customer.py`
- Create: `backend/app/repository/customer.py`
- Create: `backend/app/api/routes/customers.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/api/main.py`

**Step 1: Write domain schemas**

Create `backend/app/domain/customer.py`:
```python
import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class CustomerBase(SQLModel):
    name: str = Field(max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    address: str | None = None
    tax_id: str | None = Field(default=None, max_length=50)
    segment: str = Field(default="walk_in")  # enterprise, smb, walk_in
    notes: str | None = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(SQLModel):
    name: str | None = None
    company_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    tax_id: str | None = None
    segment: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class CustomerPublic(CustomerBase):
    id: uuid.UUID
    created_at: datetime | None
    updated_at: datetime | None


class CustomersPublic(SQLModel):
    data: list[CustomerPublic]
    count: int
```

**Step 2: Write ORM model**

Create `backend/app/models/customer.py`:
```python
import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from app.domain.customer import CustomerBase
from app.domain.utils import get_datetime_utc


class Customer(CustomerBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    updated_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    contacts: list["Contact"] = Relationship(back_populates="customer", cascade_delete=True)
    equipment: list["Equipment"] = Relationship(back_populates="customer", cascade_delete=True)
    service_requests: list["ServiceRequest"] = Relationship(back_populates="customer")
```

**Step 3: Register model**

In `backend/app/models/__init__.py`:
```python
from app.models.customer import Customer  # noqa: F401
```

**Step 4: Write repository**

Create `backend/app/repository/customer.py`:
```python
import uuid

from sqlmodel import Session, func, select

from app.domain.customer import CustomerCreate, CustomerUpdate
from app.domain.utils import get_datetime_utc
from app.models.customer import Customer


def create_customer(*, session: Session, customer_in: CustomerCreate) -> Customer:
    db_customer = Customer.model_validate(customer_in)
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer


def get_customer_by_id(*, session: Session, customer_id: uuid.UUID) -> Customer | None:
    return session.get(Customer, customer_id)


def get_customers(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    segment: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> list[Customer]:
    query = select(Customer)
    if segment:
        query = query.where(Customer.segment == segment)
    if is_active is not None:
        query = query.where(Customer.is_active == is_active)
    if search:
        query = query.where(
            Customer.name.ilike(f"%{search}%")  # type: ignore
            | Customer.company_name.ilike(f"%{search}%")  # type: ignore
            | Customer.phone.ilike(f"%{search}%")  # type: ignore
            | Customer.email.ilike(f"%{search}%")  # type: ignore
        )
    return list(session.exec(query.offset(skip).limit(limit)).all())


def get_customers_count(
    *,
    session: Session,
    segment: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> int:
    query = select(func.count()).select_from(Customer)
    if segment:
        query = query.where(Customer.segment == segment)
    if is_active is not None:
        query = query.where(Customer.is_active == is_active)
    if search:
        query = query.where(
            Customer.name.ilike(f"%{search}%")  # type: ignore
            | Customer.company_name.ilike(f"%{search}%")  # type: ignore
        )
    return session.exec(query).one()


def update_customer(*, session: Session, db_customer: Customer, customer_in: CustomerUpdate) -> Customer:
    customer_data = customer_in.model_dump(exclude_unset=True)
    db_customer.sqlmodel_update(customer_data)
    db_customer.updated_at = get_datetime_utc()
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer


def delete_customer(*, session: Session, db_customer: Customer) -> None:
    session.delete(db_customer)
    session.commit()
```

**Step 5: Write API routes**

Create `backend/app/api/routes/customers.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.customer import CustomerCreate, CustomerPublic, CustomerUpdate, CustomersPublic
from app.repository import customer as customer_repo

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=CustomersPublic)
def read_customers(
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
    skip: int = 0,
    limit: int = 100,
    segment: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
):
    customers = customer_repo.get_customers(
        session=session, skip=skip, limit=limit,
        segment=segment, is_active=is_active, search=search,
    )
    count = customer_repo.get_customers_count(
        session=session, segment=segment, is_active=is_active, search=search,
    )
    return CustomersPublic(data=[CustomerPublic.model_validate(c) for c in customers], count=count)


@router.post("/", response_model=CustomerPublic)
def create_customer(
    session: SessionDep,
    customer_in: CustomerCreate,
    _: CurrentUser = Depends(require_permission("customer", "create")),
):
    customer = customer_repo.create_customer(session=session, customer_in=customer_in)
    return CustomerPublic.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerPublic)
def read_customer(
    customer_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
):
    customer = customer_repo.get_customer_by_id(session=session, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerPublic.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerPublic)
def update_customer(
    customer_id: uuid.UUID,
    session: SessionDep,
    customer_in: CustomerUpdate,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    customer = customer_repo.get_customer_by_id(session=session, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer = customer_repo.update_customer(session=session, db_customer=customer, customer_in=customer_in)
    return CustomerPublic.model_validate(customer)


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "delete")),
):
    customer = customer_repo.get_customer_by_id(session=session, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer_repo.delete_customer(session=session, db_customer=customer)
    return {"message": "Customer deleted"}
```

**Step 6: Register routes**

In `backend/app/api/main.py`:
```python
from app.api.routes import customers
api_router.include_router(customers.router)
```

**Step 7: Commit**

```bash
git add backend/app/domain/customer.py backend/app/models/customer.py backend/app/repository/customer.py backend/app/api/routes/customers.py backend/app/models/__init__.py backend/app/api/main.py
git commit -m "feat: add Customer model with full CRUD API"
```

---

## Task 9: Contact Model — Domain, ORM, Repository, Routes

**Files:**
- Create: `backend/app/domain/contact.py`
- Create: `backend/app/models/contact.py`
- Create: `backend/app/repository/contact.py`
- Create: `backend/app/api/routes/contacts.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/api/main.py`

**Step 1: Write domain schemas**

Create `backend/app/domain/contact.py`:
```python
import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class ContactBase(SQLModel):
    name: str = Field(max_length=255)
    title: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    is_primary: bool = False


class ContactCreate(ContactBase):
    customer_id: uuid.UUID


class ContactUpdate(SQLModel):
    name: str | None = None
    title: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    is_primary: bool | None = None


class ContactPublic(ContactBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime | None


class ContactsPublic(SQLModel):
    data: list[ContactPublic]
    count: int
```

**Step 2: Write ORM model**

Create `backend/app/models/contact.py`:
```python
import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from app.domain.contact import ContactBase
from app.domain.utils import get_datetime_utc


class Contact(ContactBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_id: uuid.UUID = Field(foreign_key="customer.id", ondelete="CASCADE")
    created_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    customer: "Customer" = Relationship(back_populates="contacts")
```

**Step 3: Register model**

In `backend/app/models/__init__.py`:
```python
from app.models.contact import Contact  # noqa: F401
```

**Step 4: Write repository**

Create `backend/app/repository/contact.py`:
```python
import uuid

from sqlmodel import Session, func, select

from app.domain.contact import ContactCreate, ContactUpdate
from app.models.contact import Contact


def create_contact(*, session: Session, contact_in: ContactCreate) -> Contact:
    db_contact = Contact.model_validate(contact_in)
    session.add(db_contact)
    session.commit()
    session.refresh(db_contact)
    return db_contact


def get_contact_by_id(*, session: Session, contact_id: uuid.UUID) -> Contact | None:
    return session.get(Contact, contact_id)


def get_contacts_by_customer(
    *, session: Session, customer_id: uuid.UUID
) -> list[Contact]:
    return list(
        session.exec(
            select(Contact).where(Contact.customer_id == customer_id)
        ).all()
    )


def get_contacts_count_by_customer(*, session: Session, customer_id: uuid.UUID) -> int:
    return session.exec(
        select(func.count()).select_from(Contact).where(Contact.customer_id == customer_id)
    ).one()


def update_contact(*, session: Session, db_contact: Contact, contact_in: ContactUpdate) -> Contact:
    contact_data = contact_in.model_dump(exclude_unset=True)
    db_contact.sqlmodel_update(contact_data)
    session.add(db_contact)
    session.commit()
    session.refresh(db_contact)
    return db_contact


def delete_contact(*, session: Session, db_contact: Contact) -> None:
    session.delete(db_contact)
    session.commit()
```

**Step 5: Write routes (nested under customers)**

Create `backend/app/api/routes/contacts.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.contact import ContactCreate, ContactPublic, ContactUpdate, ContactsPublic
from app.repository import contact as contact_repo
from app.repository import customer as customer_repo

router = APIRouter(prefix="/customers/{customer_id}/contacts", tags=["contacts"])


@router.get("/", response_model=ContactsPublic)
def read_contacts(
    customer_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
):
    customer = customer_repo.get_customer_by_id(session=session, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    contacts = contact_repo.get_contacts_by_customer(session=session, customer_id=customer_id)
    count = contact_repo.get_contacts_count_by_customer(session=session, customer_id=customer_id)
    return ContactsPublic(data=[ContactPublic.model_validate(c) for c in contacts], count=count)


@router.post("/", response_model=ContactPublic)
def create_contact(
    customer_id: uuid.UUID,
    session: SessionDep,
    contact_in: ContactCreate,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    if contact_in.customer_id != customer_id:
        raise HTTPException(status_code=400, detail="Customer ID mismatch")
    customer = customer_repo.get_customer_by_id(session=session, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    contact = contact_repo.create_contact(session=session, contact_in=contact_in)
    return ContactPublic.model_validate(contact)


@router.patch("/{contact_id}", response_model=ContactPublic)
def update_contact(
    customer_id: uuid.UUID,
    contact_id: uuid.UUID,
    session: SessionDep,
    contact_in: ContactUpdate,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    contact = contact_repo.get_contact_by_id(session=session, contact_id=contact_id)
    if not contact or contact.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact = contact_repo.update_contact(session=session, db_contact=contact, contact_in=contact_in)
    return ContactPublic.model_validate(contact)


@router.delete("/{contact_id}")
def delete_contact(
    customer_id: uuid.UUID,
    contact_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    contact = contact_repo.get_contact_by_id(session=session, contact_id=contact_id)
    if not contact or contact.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact_repo.delete_contact(session=session, db_contact=contact)
    return {"message": "Contact deleted"}
```

**Step 6: Register routes**

In `backend/app/api/main.py`:
```python
from app.api.routes import contacts
api_router.include_router(contacts.router)
```

**Step 7: Commit**

```bash
git add backend/app/domain/contact.py backend/app/models/contact.py backend/app/repository/contact.py backend/app/api/routes/contacts.py backend/app/models/__init__.py backend/app/api/main.py
git commit -m "feat: add Contact model with CRUD API nested under customers"
```

---

## Task 10: Equipment Model — Domain, ORM, Repository, Routes

**Files:**
- Create: `backend/app/domain/equipment.py`
- Create: `backend/app/models/equipment.py`
- Create: `backend/app/repository/equipment.py`
- Create: `backend/app/api/routes/equipment.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/api/main.py`

**Step 1: Write domain schemas**

Create `backend/app/domain/equipment.py`:
```python
import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class EquipmentBase(SQLModel):
    model: str = Field(max_length=255)
    serial_number: str = Field(max_length=255)
    manufacturer: str | None = Field(default=None, max_length=255)
    install_date: date | None = None
    warranty_expiry: date | None = None
    notes: str | None = None
    is_active: bool = True


class EquipmentCreate(EquipmentBase):
    customer_id: uuid.UUID


class EquipmentUpdate(SQLModel):
    model: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    install_date: date | None = None
    warranty_expiry: date | None = None
    notes: str | None = None
    is_active: bool | None = None


class EquipmentPublic(EquipmentBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime | None


class EquipmentListPublic(SQLModel):
    data: list[EquipmentPublic]
    count: int


class EquipmentWithCustomer(EquipmentPublic):
    """For global equipment list — includes customer name."""
    customer_name: str | None = None
```

**Step 2: Write ORM model**

Create `backend/app/models/equipment.py`:
```python
import uuid
from datetime import date, datetime

from sqlmodel import Field, Relationship, SQLModel

from app.domain.equipment import EquipmentBase
from app.domain.utils import get_datetime_utc


class Equipment(EquipmentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_id: uuid.UUID = Field(foreign_key="customer.id", ondelete="CASCADE")
    created_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    customer: "Customer" = Relationship(back_populates="equipment")
    service_requests: list["ServiceRequest"] = Relationship(back_populates="equipment")
```

**Step 3: Register model**

In `backend/app/models/__init__.py`:
```python
from app.models.equipment import Equipment  # noqa: F401
```

**Step 4: Write repository**

Create `backend/app/repository/equipment.py`:
```python
import uuid

from sqlmodel import Session, func, select

from app.domain.equipment import EquipmentCreate, EquipmentUpdate
from app.models.equipment import Equipment


def create_equipment(*, session: Session, equipment_in: EquipmentCreate) -> Equipment:
    db_equipment = Equipment.model_validate(equipment_in)
    session.add(db_equipment)
    session.commit()
    session.refresh(db_equipment)
    return db_equipment


def get_equipment_by_id(*, session: Session, equipment_id: uuid.UUID) -> Equipment | None:
    return session.get(Equipment, equipment_id)


def get_equipment_by_customer(
    *, session: Session, customer_id: uuid.UUID
) -> list[Equipment]:
    return list(
        session.exec(
            select(Equipment).where(Equipment.customer_id == customer_id)
        ).all()
    )


def get_equipment_count_by_customer(*, session: Session, customer_id: uuid.UUID) -> int:
    return session.exec(
        select(func.count()).select_from(Equipment).where(Equipment.customer_id == customer_id)
    ).one()


def get_all_equipment(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> list[Equipment]:
    query = select(Equipment)
    if search:
        query = query.where(
            Equipment.serial_number.ilike(f"%{search}%")  # type: ignore
            | Equipment.model.ilike(f"%{search}%")  # type: ignore
            | Equipment.manufacturer.ilike(f"%{search}%")  # type: ignore
        )
    return list(session.exec(query.offset(skip).limit(limit)).all())


def get_all_equipment_count(*, session: Session, search: str | None = None) -> int:
    query = select(func.count()).select_from(Equipment)
    if search:
        query = query.where(
            Equipment.serial_number.ilike(f"%{search}%")  # type: ignore
            | Equipment.model.ilike(f"%{search}%")  # type: ignore
        )
    return session.exec(query).one()


def update_equipment(*, session: Session, db_equipment: Equipment, equipment_in: EquipmentUpdate) -> Equipment:
    equipment_data = equipment_in.model_dump(exclude_unset=True)
    db_equipment.sqlmodel_update(equipment_data)
    session.add(db_equipment)
    session.commit()
    session.refresh(db_equipment)
    return db_equipment


def delete_equipment(*, session: Session, db_equipment: Equipment) -> None:
    session.delete(db_equipment)
    session.commit()
```

**Step 5: Write routes (both global and customer-scoped)**

Create `backend/app/api/routes/equipment.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.equipment import (
    EquipmentCreate,
    EquipmentListPublic,
    EquipmentPublic,
    EquipmentUpdate,
    EquipmentWithCustomer,
)
from app.repository import customer as customer_repo
from app.repository import equipment as equipment_repo

router = APIRouter(tags=["equipment"])


# --- Global equipment routes ---

@router.get("/equipment", response_model=EquipmentListPublic)
def read_all_equipment(
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
):
    items = equipment_repo.get_all_equipment(session=session, skip=skip, limit=limit, search=search)
    count = equipment_repo.get_all_equipment_count(session=session, search=search)
    data = []
    for e in items:
        pub = EquipmentWithCustomer.model_validate(e)
        pub.customer_name = e.customer.name if e.customer else None
        data.append(pub)
    return EquipmentListPublic(data=data, count=count)


@router.get("/equipment/{equipment_id}", response_model=EquipmentWithCustomer)
def read_equipment(
    equipment_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
):
    eq = equipment_repo.get_equipment_by_id(session=session, equipment_id=equipment_id)
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    pub = EquipmentWithCustomer.model_validate(eq)
    pub.customer_name = eq.customer.name if eq.customer else None
    return pub


# --- Customer-scoped equipment routes ---

@router.get("/customers/{customer_id}/equipment", response_model=EquipmentListPublic)
def read_customer_equipment(
    customer_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
):
    customer = customer_repo.get_customer_by_id(session=session, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    items = equipment_repo.get_equipment_by_customer(session=session, customer_id=customer_id)
    count = equipment_repo.get_equipment_count_by_customer(session=session, customer_id=customer_id)
    return EquipmentListPublic(data=[EquipmentPublic.model_validate(e) for e in items], count=count)


@router.post("/customers/{customer_id}/equipment", response_model=EquipmentPublic)
def create_equipment(
    customer_id: uuid.UUID,
    session: SessionDep,
    equipment_in: EquipmentCreate,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    if equipment_in.customer_id != customer_id:
        raise HTTPException(status_code=400, detail="Customer ID mismatch")
    customer = customer_repo.get_customer_by_id(session=session, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    eq = equipment_repo.create_equipment(session=session, equipment_in=equipment_in)
    return EquipmentPublic.model_validate(eq)


@router.patch("/equipment/{equipment_id}", response_model=EquipmentPublic)
def update_equipment(
    equipment_id: uuid.UUID,
    session: SessionDep,
    equipment_in: EquipmentUpdate,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    eq = equipment_repo.get_equipment_by_id(session=session, equipment_id=equipment_id)
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    eq = equipment_repo.update_equipment(session=session, db_equipment=eq, equipment_in=equipment_in)
    return EquipmentPublic.model_validate(eq)


@router.delete("/equipment/{equipment_id}")
def delete_equipment(
    equipment_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "delete")),
):
    eq = equipment_repo.get_equipment_by_id(session=session, equipment_id=equipment_id)
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    equipment_repo.delete_equipment(session=session, db_equipment=eq)
    return {"message": "Equipment deleted"}
```

**Step 6: Register routes**

In `backend/app/api/main.py`:
```python
from app.api.routes import equipment
api_router.include_router(equipment.router)
```

**Step 7: Commit**

```bash
git add backend/app/domain/equipment.py backend/app/models/equipment.py backend/app/repository/equipment.py backend/app/api/routes/equipment.py backend/app/models/__init__.py backend/app/api/main.py
git commit -m "feat: add Equipment model with global and customer-scoped CRUD API"
```

---

## Task 11: Service Request Model — Domain, ORM, Repository, Routes

**Files:**
- Create: `backend/app/domain/service_request.py`
- Create: `backend/app/models/service_request.py`
- Create: `backend/app/repository/service_request.py`
- Create: `backend/app/api/routes/service_requests.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/api/main.py`

**Step 1: Write domain schemas**

Create `backend/app/domain/service_request.py`:
```python
import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class ServiceRequestBase(SQLModel):
    description: str
    priority: str = Field(default="medium")  # low, medium, high, critical
    source: str = Field(default="phone")  # phone, email, walk_in


class ServiceRequestCreate(ServiceRequestBase):
    customer_id: uuid.UUID
    equipment_id: uuid.UUID | None = None


class ServiceRequestUpdate(SQLModel):
    description: str | None = None
    priority: str | None = None
    diagnosis: str | None = None
    resolution_notes: str | None = None
    assigned_engineer_id: uuid.UUID | None = None
    status: str | None = None


class ServiceRequestPublic(ServiceRequestBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    equipment_id: uuid.UUID | None
    assigned_engineer_id: uuid.UUID | None
    status: str
    diagnosis: str | None
    resolution_notes: str | None
    sla_response_due: datetime | None
    sla_resolution_due: datetime | None
    sla_response_breached: bool
    sla_resolution_breached: bool
    created_by: uuid.UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class ServiceRequestsPublic(SQLModel):
    data: list[ServiceRequestPublic]
    count: int


class ServiceRequestStatusUpdate(SQLModel):
    """Dedicated schema for status transitions."""
    status: str
    notes: str | None = None
```

**Step 2: Write ORM model**

Create `backend/app/models/service_request.py`:
```python
import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from app.domain.service_request import ServiceRequestBase
from app.domain.utils import get_datetime_utc


class ServiceRequest(ServiceRequestBase, table=True):
    __tablename__ = "service_request"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_id: uuid.UUID = Field(foreign_key="customer.id", ondelete="CASCADE")
    equipment_id: uuid.UUID | None = Field(default=None, foreign_key="equipment.id", ondelete="SET NULL")
    assigned_engineer_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    created_by: uuid.UUID | None = Field(default=None, foreign_key="user.id", ondelete="SET NULL")

    status: str = Field(default="new")
    diagnosis: str | None = None
    resolution_notes: str | None = None

    # SLA fields
    sla_response_due: datetime | None = None
    sla_resolution_due: datetime | None = None
    sla_response_breached: bool = Field(default=False)
    sla_resolution_breached: bool = Field(default=False)
    sla_paused_at: datetime | None = None
    sla_total_paused_seconds: int = Field(default=0)

    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    updated_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    customer: "Customer" = Relationship(back_populates="service_requests")
    equipment: "Equipment | None" = Relationship(back_populates="service_requests")
    service_visits: list["ServiceVisit"] = Relationship(back_populates="service_request", cascade_delete=True)
```

**Step 3: Register model**

In `backend/app/models/__init__.py`:
```python
from app.models.service_request import ServiceRequest  # noqa: F401
```

**Step 4: Write repository**

Create `backend/app/repository/service_request.py`:
```python
import uuid

from sqlmodel import Session, func, select

from app.domain.service_request import ServiceRequestCreate, ServiceRequestUpdate
from app.domain.utils import get_datetime_utc
from app.models.service_request import ServiceRequest

# Valid status transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "new": ["quoted", "assigned", "closed"],
    "quoted": ["approved", "closed"],
    "approved": ["assigned", "closed"],
    "assigned": ["in_progress", "closed"],
    "in_progress": ["completed", "assigned"],  # can reassign
    "completed": ["invoiced", "closed"],
    "invoiced": ["closed"],
    "closed": [],  # terminal state
}


def create_service_request(
    *, session: Session, request_in: ServiceRequestCreate, created_by: uuid.UUID
) -> ServiceRequest:
    db_request = ServiceRequest.model_validate(
        request_in, update={"created_by": created_by}
    )
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request


def get_service_request_by_id(
    *, session: Session, request_id: uuid.UUID
) -> ServiceRequest | None:
    return session.get(ServiceRequest, request_id)


def get_service_requests(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    priority: str | None = None,
    customer_id: uuid.UUID | None = None,
    assigned_engineer_id: uuid.UUID | None = None,
) -> list[ServiceRequest]:
    query = select(ServiceRequest)
    if status:
        query = query.where(ServiceRequest.status == status)
    if priority:
        query = query.where(ServiceRequest.priority == priority)
    if customer_id:
        query = query.where(ServiceRequest.customer_id == customer_id)
    if assigned_engineer_id:
        query = query.where(ServiceRequest.assigned_engineer_id == assigned_engineer_id)
    return list(
        session.exec(query.order_by(ServiceRequest.created_at.desc()).offset(skip).limit(limit)).all()  # type: ignore
    )


def get_service_requests_count(
    *,
    session: Session,
    status: str | None = None,
    priority: str | None = None,
    customer_id: uuid.UUID | None = None,
    assigned_engineer_id: uuid.UUID | None = None,
) -> int:
    query = select(func.count()).select_from(ServiceRequest)
    if status:
        query = query.where(ServiceRequest.status == status)
    if priority:
        query = query.where(ServiceRequest.priority == priority)
    if customer_id:
        query = query.where(ServiceRequest.customer_id == customer_id)
    if assigned_engineer_id:
        query = query.where(ServiceRequest.assigned_engineer_id == assigned_engineer_id)
    return session.exec(query).one()


def update_service_request(
    *, session: Session, db_request: ServiceRequest, request_in: ServiceRequestUpdate
) -> ServiceRequest:
    request_data = request_in.model_dump(exclude_unset=True)
    db_request.sqlmodel_update(request_data)
    db_request.updated_at = get_datetime_utc()
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request


def transition_status(
    *, session: Session, db_request: ServiceRequest, new_status: str
) -> ServiceRequest:
    """Validate and apply a status transition."""
    allowed = VALID_TRANSITIONS.get(db_request.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from '{db_request.status}' to '{new_status}'. "
            f"Allowed: {allowed}"
        )
    db_request.status = new_status
    db_request.updated_at = get_datetime_utc()
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request
```

**Step 5: Write routes**

Create `backend/app/api/routes/service_requests.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.service_request import (
    ServiceRequestCreate,
    ServiceRequestPublic,
    ServiceRequestStatusUpdate,
    ServiceRequestUpdate,
    ServiceRequestsPublic,
)
from app.repository import customer as customer_repo
from app.repository import service_request as sr_repo

router = APIRouter(prefix="/service-requests", tags=["service-requests"])


@router.get("/", response_model=ServiceRequestsPublic)
def read_service_requests(
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("service_request", "view")),
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    priority: str | None = None,
    customer_id: uuid.UUID | None = None,
    assigned_engineer_id: uuid.UUID | None = None,
):
    items = sr_repo.get_service_requests(
        session=session, skip=skip, limit=limit,
        status=status, priority=priority,
        customer_id=customer_id, assigned_engineer_id=assigned_engineer_id,
    )
    count = sr_repo.get_service_requests_count(
        session=session, status=status, priority=priority,
        customer_id=customer_id, assigned_engineer_id=assigned_engineer_id,
    )
    return ServiceRequestsPublic(
        data=[ServiceRequestPublic.model_validate(r) for r in items],
        count=count,
    )


@router.post("/", response_model=ServiceRequestPublic)
def create_service_request(
    session: SessionDep,
    request_in: ServiceRequestCreate,
    current_user: CurrentUser,
    _: CurrentUser = Depends(require_permission("service_request", "create")),
):
    customer = customer_repo.get_customer_by_id(session=session, customer_id=request_in.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    sr = sr_repo.create_service_request(
        session=session, request_in=request_in, created_by=current_user.id,
    )
    return ServiceRequestPublic.model_validate(sr)


@router.get("/{request_id}", response_model=ServiceRequestPublic)
def read_service_request(
    request_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("service_request", "view")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")
    return ServiceRequestPublic.model_validate(sr)


@router.patch("/{request_id}", response_model=ServiceRequestPublic)
def update_service_request(
    request_id: uuid.UUID,
    session: SessionDep,
    request_in: ServiceRequestUpdate,
    _: CurrentUser = Depends(require_permission("service_request", "edit")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")
    sr = sr_repo.update_service_request(session=session, db_request=sr, request_in=request_in)
    return ServiceRequestPublic.model_validate(sr)


@router.post("/{request_id}/status", response_model=ServiceRequestPublic)
def update_service_request_status(
    request_id: uuid.UUID,
    session: SessionDep,
    status_update: ServiceRequestStatusUpdate,
    _: CurrentUser = Depends(require_permission("service_request", "edit")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")
    try:
        sr = sr_repo.transition_status(
            session=session, db_request=sr, new_status=status_update.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ServiceRequestPublic.model_validate(sr)


@router.post("/{request_id}/assign", response_model=ServiceRequestPublic)
def assign_engineer(
    request_id: uuid.UUID,
    session: SessionDep,
    engineer_id: uuid.UUID,
    _: CurrentUser = Depends(require_permission("service_request", "edit")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")

    from app.repository import user as user_repo
    engineer = user_repo.get_user_by_id(session=session, user_id=engineer_id)
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer not found")

    from app.domain.service_request import ServiceRequestUpdate as SRUpdate
    sr = sr_repo.update_service_request(
        session=session,
        db_request=sr,
        request_in=SRUpdate(assigned_engineer_id=engineer_id, status="assigned"),
    )
    return ServiceRequestPublic.model_validate(sr)
```

**Step 6: Register routes**

In `backend/app/api/main.py`:
```python
from app.api.routes import service_requests
api_router.include_router(service_requests.router)
```

**Step 7: Commit**

```bash
git add backend/app/domain/service_request.py backend/app/models/service_request.py backend/app/repository/service_request.py backend/app/api/routes/service_requests.py backend/app/models/__init__.py backend/app/api/main.py
git commit -m "feat: add ServiceRequest model with status transitions and CRUD API"
```

---

## Task 12: Service Visit Model

**Files:**
- Create: `backend/app/domain/service_visit.py`
- Create: `backend/app/models/service_visit.py`
- Create: `backend/app/repository/service_visit.py`
- Create: `backend/app/api/routes/service_visits.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/api/main.py`

**Step 1: Write domain schemas**

Create `backend/app/domain/service_visit.py`:
```python
import uuid
from datetime import date, datetime, time

from sqlmodel import SQLModel


class ServiceVisitBase(SQLModel):
    visit_date: date
    arrival_time: time | None = None
    departure_time: time | None = None
    notes: str | None = None


class ServiceVisitCreate(ServiceVisitBase):
    service_request_id: uuid.UUID


class ServiceVisitUpdate(SQLModel):
    visit_date: date | None = None
    arrival_time: time | None = None
    departure_time: time | None = None
    notes: str | None = None


class ServiceVisitPublic(ServiceVisitBase):
    id: uuid.UUID
    service_request_id: uuid.UUID
    engineer_id: uuid.UUID
    created_at: datetime | None


class ServiceVisitsPublic(SQLModel):
    data: list[ServiceVisitPublic]
    count: int
```

**Step 2: Write ORM model**

Create `backend/app/models/service_visit.py`:
```python
import uuid
from datetime import date, datetime, time

from sqlmodel import Field, Relationship, SQLModel

from app.domain.service_visit import ServiceVisitBase
from app.domain.utils import get_datetime_utc


class ServiceVisit(ServiceVisitBase, table=True):
    __tablename__ = "service_visit"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    service_request_id: uuid.UUID = Field(foreign_key="service_request.id", ondelete="CASCADE")
    engineer_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    created_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    service_request: "ServiceRequest" = Relationship(back_populates="service_visits")
```

**Step 3: Register model**

In `backend/app/models/__init__.py`:
```python
from app.models.service_visit import ServiceVisit  # noqa: F401
```

**Step 4: Write repository**

Create `backend/app/repository/service_visit.py`:
```python
import uuid

from sqlmodel import Session, func, select

from app.domain.service_visit import ServiceVisitCreate, ServiceVisitUpdate
from app.models.service_visit import ServiceVisit


def create_service_visit(
    *, session: Session, visit_in: ServiceVisitCreate, engineer_id: uuid.UUID
) -> ServiceVisit:
    db_visit = ServiceVisit.model_validate(
        visit_in, update={"engineer_id": engineer_id}
    )
    session.add(db_visit)
    session.commit()
    session.refresh(db_visit)
    return db_visit


def get_service_visit_by_id(*, session: Session, visit_id: uuid.UUID) -> ServiceVisit | None:
    return session.get(ServiceVisit, visit_id)


def get_visits_by_service_request(
    *, session: Session, service_request_id: uuid.UUID
) -> list[ServiceVisit]:
    return list(
        session.exec(
            select(ServiceVisit)
            .where(ServiceVisit.service_request_id == service_request_id)
            .order_by(ServiceVisit.visit_date.desc())  # type: ignore
        ).all()
    )


def get_visits_count_by_service_request(
    *, session: Session, service_request_id: uuid.UUID
) -> int:
    return session.exec(
        select(func.count())
        .select_from(ServiceVisit)
        .where(ServiceVisit.service_request_id == service_request_id)
    ).one()


def update_service_visit(
    *, session: Session, db_visit: ServiceVisit, visit_in: ServiceVisitUpdate
) -> ServiceVisit:
    visit_data = visit_in.model_dump(exclude_unset=True)
    db_visit.sqlmodel_update(visit_data)
    session.add(db_visit)
    session.commit()
    session.refresh(db_visit)
    return db_visit
```

**Step 5: Write routes (nested under service requests)**

Create `backend/app/api/routes/service_visits.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.service_visit import (
    ServiceVisitCreate,
    ServiceVisitPublic,
    ServiceVisitUpdate,
    ServiceVisitsPublic,
)
from app.repository import service_request as sr_repo
from app.repository import service_visit as visit_repo

router = APIRouter(
    prefix="/service-requests/{request_id}/visits",
    tags=["service-visits"],
)


@router.get("/", response_model=ServiceVisitsPublic)
def read_visits(
    request_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("service_request", "view")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")
    visits = visit_repo.get_visits_by_service_request(
        session=session, service_request_id=request_id,
    )
    count = visit_repo.get_visits_count_by_service_request(
        session=session, service_request_id=request_id,
    )
    return ServiceVisitsPublic(
        data=[ServiceVisitPublic.model_validate(v) for v in visits],
        count=count,
    )


@router.post("/", response_model=ServiceVisitPublic)
def create_visit(
    request_id: uuid.UUID,
    session: SessionDep,
    visit_in: ServiceVisitCreate,
    current_user: CurrentUser,
    _: CurrentUser = Depends(require_permission("service_request", "edit")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")
    if visit_in.service_request_id != request_id:
        raise HTTPException(status_code=400, detail="Service request ID mismatch")

    visit = visit_repo.create_service_visit(
        session=session, visit_in=visit_in, engineer_id=current_user.id,
    )
    return ServiceVisitPublic.model_validate(visit)


@router.patch("/{visit_id}", response_model=ServiceVisitPublic)
def update_visit(
    request_id: uuid.UUID,
    visit_id: uuid.UUID,
    session: SessionDep,
    visit_in: ServiceVisitUpdate,
    _: CurrentUser = Depends(require_permission("service_request", "edit")),
):
    visit = visit_repo.get_service_visit_by_id(session=session, visit_id=visit_id)
    if not visit or visit.service_request_id != request_id:
        raise HTTPException(status_code=404, detail="Service visit not found")
    visit = visit_repo.update_service_visit(
        session=session, db_visit=visit, visit_in=visit_in,
    )
    return ServiceVisitPublic.model_validate(visit)
```

**Step 6: Register routes**

In `backend/app/api/main.py`:
```python
from app.api.routes import service_visits
api_router.include_router(service_visits.router)
```

**Step 7: Commit**

```bash
git add backend/app/domain/service_visit.py backend/app/models/service_visit.py backend/app/repository/service_visit.py backend/app/api/routes/service_visits.py backend/app/models/__init__.py backend/app/api/main.py
git commit -m "feat: add ServiceVisit model with CRUD API nested under service requests"
```

---

## Task 13: SLA Config Model & Service

**Files:**
- Create: `backend/app/domain/sla_config.py`
- Create: `backend/app/models/sla_config.py`
- Create: `backend/app/repository/sla_config.py`
- Create: `backend/app/services/sla.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write SLA domain schemas**

Create `backend/app/domain/sla_config.py`:
```python
import uuid

from sqlmodel import Field, SQLModel


class SLAConfigBase(SQLModel):
    segment: str = Field(unique=True)  # enterprise, smb, walk_in
    response_hours: int
    resolution_hours: int


class SLAConfigCreate(SLAConfigBase):
    pass


class SLAConfigUpdate(SQLModel):
    response_hours: int | None = None
    resolution_hours: int | None = None


class SLAConfigPublic(SLAConfigBase):
    id: uuid.UUID
```

**Step 2: Write ORM model**

Create `backend/app/models/sla_config.py`:
```python
import uuid

from sqlmodel import Field, SQLModel

from app.domain.sla_config import SLAConfigBase


class SLAConfig(SLAConfigBase, table=True):
    __tablename__ = "sla_config"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
```

**Step 3: Register model**

In `backend/app/models/__init__.py`:
```python
from app.models.sla_config import SLAConfig  # noqa: F401
```

**Step 4: Write repository**

Create `backend/app/repository/sla_config.py`:
```python
from sqlmodel import Session, select

from app.domain.sla_config import SLAConfigCreate, SLAConfigUpdate
from app.models.sla_config import SLAConfig


def get_sla_config_by_segment(*, session: Session, segment: str) -> SLAConfig | None:
    return session.exec(
        select(SLAConfig).where(SLAConfig.segment == segment)
    ).first()


def get_all_sla_configs(*, session: Session) -> list[SLAConfig]:
    return list(session.exec(select(SLAConfig)).all())


def upsert_sla_config(*, session: Session, config_in: SLAConfigCreate) -> SLAConfig:
    existing = get_sla_config_by_segment(session=session, segment=config_in.segment)
    if existing:
        existing.response_hours = config_in.response_hours
        existing.resolution_hours = config_in.resolution_hours
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    db_config = SLAConfig.model_validate(config_in)
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config
```

**Step 5: Write SLA service**

Create `backend/app/services/sla.py`:
```python
from datetime import timedelta

from sqlmodel import Session

from app.domain.utils import get_datetime_utc
from app.models.service_request import ServiceRequest
from app.repository import sla_config as sla_repo

# Default SLA hours if no config found
DEFAULT_SLA = {
    "enterprise": {"response": 2, "resolution": 24},
    "smb": {"response": 4, "resolution": 48},
    "walk_in": {"response": 8, "resolution": 72},
}


def apply_sla_deadlines(
    *, session: Session, service_request: ServiceRequest, customer_segment: str
) -> ServiceRequest:
    """Set SLA deadlines on a service request based on customer segment."""
    config = sla_repo.get_sla_config_by_segment(session=session, segment=customer_segment)

    if config:
        response_hours = config.response_hours
        resolution_hours = config.resolution_hours
    else:
        defaults = DEFAULT_SLA.get(customer_segment, DEFAULT_SLA["walk_in"])
        response_hours = defaults["response"]
        resolution_hours = defaults["resolution"]

    now = get_datetime_utc()
    service_request.sla_response_due = now + timedelta(hours=response_hours)
    service_request.sla_resolution_due = now + timedelta(hours=resolution_hours)

    session.add(service_request)
    session.commit()
    session.refresh(service_request)
    return service_request
```

**Step 6: Seed default SLA configs in db.py**

Add to `init_db` in `backend/app/core/db.py`:
```python
from app.domain.sla_config import SLAConfigCreate
from app.repository import sla_config as sla_repo

# Seed default SLA configs
for segment, hours in DEFAULT_SLA.items():
    sla_repo.upsert_sla_config(
        session=session,
        config_in=SLAConfigCreate(
            segment=segment,
            response_hours=hours["response"],
            resolution_hours=hours["resolution"],
        ),
    )
```

Where DEFAULT_SLA is imported from `app.services.sla`.

**Step 7: Commit**

```bash
git add backend/app/domain/sla_config.py backend/app/models/sla_config.py backend/app/repository/sla_config.py backend/app/services/sla.py backend/app/models/__init__.py backend/app/core/db.py
git commit -m "feat: add SLAConfig model and SLA service with default configurations"
```

---

## Task 14: Backend Tests — RBAC & Auth

**Files:**
- Create: `backend/tests/api/routes/test_roles.py`
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/utils/utils.py`

**Step 1: Update test fixtures for Supabase Auth**

The test setup needs to work with Supabase Auth. Update `backend/tests/conftest.py` to:
- Mock or bypass Supabase JWT validation for tests
- Create test users with mock supabase_auth_ids
- Create test fixtures for each role (manager, support, engineer, warehouse)

```python
# In conftest.py, add fixtures:

@pytest.fixture(scope="module")
def manager_user(db: Session) -> User:
    """Create a test user with manager role."""
    from app.repository.role import get_role_by_name
    role = get_role_by_name(session=db, name="manager")
    user = User(
        email=f"manager-{random_lower_string()}@test.com",
        full_name="Test Manager",
        supabase_auth_id=uuid.uuid4(),
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Similar fixtures for support, engineer, warehouse roles

@pytest.fixture(scope="module")
def manager_token_headers(manager_user: User) -> dict[str, str]:
    """Create a mock JWT for the manager user."""
    # Override the deps.get_current_user to return manager_user directly
    # Or create a real Supabase test token
    ...
```

**Note:** The exact test auth setup depends on whether you use a Supabase test project or mock the auth layer. The recommended approach for testing is to override `get_current_user` dependency with a test dependency that returns a specific user.

**Step 2: Write role API tests**

Create `backend/tests/api/routes/test_roles.py` with tests for:
- List roles (should return 4 default roles)
- Create custom role
- Set permissions on role
- Delete custom role
- Cannot delete system role
- Unauthorized users cannot manage roles

**Step 3: Run tests**

```bash
cd backend && pytest tests/api/routes/test_roles.py -v
```

**Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test: add RBAC and role API tests"
```

---

## Task 15: Backend Tests — Customer, Equipment, Service Request

**Files:**
- Create: `backend/tests/api/routes/test_customers.py`
- Create: `backend/tests/api/routes/test_equipment.py`
- Create: `backend/tests/api/routes/test_service_requests.py`
- Create: `backend/tests/utils/customer.py`
- Create: `backend/tests/utils/equipment.py`

**Step 1: Write test utilities**

Create helpers for creating test customers, equipment, and service requests.

**Step 2: Write customer tests**

Test CRUD operations, search, filtering, permission checks.

**Step 3: Write equipment tests**

Test CRUD, global listing, customer-scoped listing, search by serial number.

**Step 4: Write service request tests**

Test creation, status transitions (valid and invalid), assignment, filtering.

**Step 5: Run all tests**

```bash
cd backend && pytest tests/ -v --tb=short
```

**Step 6: Commit**

```bash
git add backend/tests/
git commit -m "test: add Customer, Equipment, and ServiceRequest API tests"
```

---

## Task 16: Frontend — Supabase Auth Setup

**Files:**
- Modify: `frontend/package.json` (add @supabase/supabase-js)
- Create: `frontend/src/lib/supabase.ts`
- Modify: `frontend/src/hooks/useAuth.ts`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/routes/login.tsx`

**Step 1: Install Supabase JS SDK**

```bash
cd frontend && bun add @supabase/supabase-js
```

**Step 2: Create Supabase client**

Create `frontend/src/lib/supabase.ts`:
```typescript
import { createClient } from "@supabase/supabase-js"

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

**Step 3: Update useAuth hook**

Replace `frontend/src/hooks/useAuth.ts` to use Supabase Auth:
- `login()` → calls `supabase.auth.signInWithPassword()`
- `logout()` → calls `supabase.auth.signOut()`
- Token management → get session from Supabase, pass JWT to API

**Step 4: Update main.tsx**

Replace the localStorage token management with Supabase session:
```typescript
import { supabase } from "@/lib/supabase"

OpenAPI.TOKEN = async () => {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token || ""
}
```

**Step 5: Update login page**

Modify `frontend/src/routes/login.tsx` to use Supabase Auth instead of the old login endpoint.

**Step 6: Add env vars**

Add to `frontend/.env`:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

**Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: replace frontend auth with Supabase Auth"
```

---

## Task 17: Frontend — Customer List Page

**Files:**
- Create: `frontend/src/routes/_layout/customers.tsx`
- Create: `frontend/src/components/Customers/columns.tsx`
- Create: `frontend/src/components/Customers/AddCustomer.tsx`
- Regenerate: `frontend/src/client/` (after backend OpenAPI spec is available)

**Step 1: Generate updated API client**

```bash
cd frontend && bun run generate-client
```

**Step 2: Create customers route**

Create `frontend/src/routes/_layout/customers.tsx` following the pattern from `items.tsx`:
- TanStack Query to fetch customers
- DataTable with columns (name, company, phone, email, segment, status)
- Add Customer dialog
- Search input
- Segment filter

**Step 3: Create table columns**

Create `frontend/src/components/Customers/columns.tsx` following the pattern from `Items/columns.tsx`.

**Step 4: Create Add Customer dialog**

Create `frontend/src/components/Customers/AddCustomer.tsx` following the pattern from `Items/AddItem.tsx`:
- Form with: name, company_name, phone, email, address, tax_id, segment (select), notes
- Zod validation
- React Hook Form
- Mutation with query invalidation

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: add Customer list page with search and add dialog"
```

---

## Task 18: Frontend — Customer Detail Page

**Files:**
- Create: `frontend/src/routes/_layout/customers.$customerId.tsx`
- Create: `frontend/src/components/Customers/EditCustomer.tsx`
- Create: `frontend/src/components/Customers/CustomerContacts.tsx`
- Create: `frontend/src/components/Customers/CustomerEquipment.tsx`

**Step 1: Create customer detail route with tabs**

`frontend/src/routes/_layout/customers.$customerId.tsx`:
- Tabs: Profile | Contacts | Equipment | Service History | Financials (last two can be placeholder)
- Profile tab: editable customer details
- Contacts tab: list + add/edit/delete
- Equipment tab: list + add/edit

**Step 2: Create edit customer component**

Following pattern from `Items/EditItem.tsx`.

**Step 3: Create contacts component**

Table of contacts with inline add/edit/delete. Each contact shows name, title, phone, email, primary flag.

**Step 4: Create equipment component**

Table of equipment with add form. Each equipment shows model, serial, manufacturer, install date, warranty, status.

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: add Customer detail page with contacts and equipment tabs"
```

---

## Task 19: Frontend — Equipment Global Page

**Files:**
- Create: `frontend/src/routes/_layout/equipment.tsx`
- Create: `frontend/src/components/Equipment/columns.tsx`

**Step 1: Create equipment route**

`frontend/src/routes/_layout/equipment.tsx`:
- Global equipment list with search by serial number, model, customer
- Links to customer profile
- DataTable with columns: serial, model, manufacturer, customer, warranty status

**Step 2: Commit**

```bash
git add frontend/src/
git commit -m "feat: add global Equipment list page with search"
```

---

## Task 20: Frontend — Service Request List Page

**Files:**
- Create: `frontend/src/routes/_layout/service-requests.tsx`
- Create: `frontend/src/components/ServiceRequests/columns.tsx`
- Create: `frontend/src/components/ServiceRequests/AddServiceRequest.tsx`

**Step 1: Create service requests route**

`frontend/src/routes/_layout/service-requests.tsx`:
- List with filters: status, priority, assigned engineer, customer
- DataTable with columns: ID, customer, equipment, priority, status, assigned to, created date
- Status badges with colors
- Add Service Request dialog

**Step 2: Create Add Service Request dialog**

Multi-step form:
1. Select customer (searchable dropdown)
2. Select equipment (filtered by selected customer)
3. Enter description, priority, source

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: add Service Request list page with filters and create dialog"
```

---

## Task 21: Frontend — Service Request Detail Page

**Files:**
- Create: `frontend/src/routes/_layout/service-requests.$requestId.tsx`
- Create: `frontend/src/components/ServiceRequests/StatusTimeline.tsx`
- Create: `frontend/src/components/ServiceRequests/ServiceVisits.tsx`
- Create: `frontend/src/components/ServiceRequests/AssignEngineer.tsx`

**Step 1: Create service request detail route with tabs**

Tabs: Timeline | Visits | Parts (placeholder for Phase 3) | Quotation (placeholder for Phase 2)

**Step 2: Create status timeline component**

Shows current status with progress bar through the lifecycle. Buttons for valid next transitions.

**Step 3: Create service visits component**

List of visits with add form. Each visit shows date, times, engineer, notes.

**Step 4: Create assign engineer component**

Dropdown to select engineer, triggers assignment API.

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: add Service Request detail page with timeline and visits"
```

---

## Task 22: Frontend — Role-Specific Dashboard

**Files:**
- Modify: `frontend/src/routes/_layout/index.tsx`
- Create: `frontend/src/components/Dashboard/ManagerDashboard.tsx`
- Create: `frontend/src/components/Dashboard/SupportDashboard.tsx`
- Create: `frontend/src/components/Dashboard/EngineerDashboard.tsx`
- Create: `frontend/src/components/Dashboard/WarehouseDashboard.tsx`

**Step 1: Create dashboard components**

Each dashboard shows role-relevant KPI cards:

**Manager:** Total customers, open tickets, SLA breaches, unassigned tickets
**Support:** My open tickets, pending quotations (placeholder), today's new tickets
**Engineer:** My assigned tickets, in-progress tickets
**Warehouse:** Low stock alerts (placeholder), pending parts requests (placeholder)

For Phase 1, use simple count cards. Charts come in Phase 4.

**Step 2: Update index route**

Modify `frontend/src/routes/_layout/index.tsx` to render the correct dashboard based on current user's role.

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: add role-specific dashboard views"
```

---

## Task 23: Frontend — Sidebar Navigation + Permission-Based Visibility

**Files:**
- Modify: `frontend/src/components/Sidebar/Main.tsx`
- Create: `frontend/src/hooks/usePermissions.ts`

**Step 1: Create usePermissions hook**

```typescript
// Fetches current user's role permissions and provides a hasPermission() check
export function usePermissions() {
  const { user } = useAuth()
  const { data: role } = useQuery({
    queryKey: ["role", user?.role_id],
    queryFn: () => RolesService.readRole({ roleId: user!.role_id! }),
    enabled: !!user?.role_id,
  })

  const hasPermission = (resource: string, action: string) => {
    return role?.permissions?.some(p => p.resource === resource && p.action === action) ?? false
  }

  return { hasPermission, role, roleName: role?.name }
}
```

**Step 2: Update sidebar navigation**

Add new navigation items (conditionally visible based on permissions):
- Dashboard (always)
- Customers (customer.view)
- Equipment (customer.view)
- Service Requests (service_request.view)
- Admin > Users (user.view)
- Admin > Roles (user.view)

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: add permission-based sidebar navigation"
```

---

## Task 24: Frontend — Admin User Management

**Files:**
- Modify: `frontend/src/routes/_layout/admin.tsx`
- Create: `frontend/src/components/Admin/AddUser.tsx` (rewrite for new user model)
- Modify: `frontend/src/components/Admin/columns.tsx`

**Step 1: Update admin page**

Rewrite to use the new user API with role assignment:
- User list with role column
- Add User dialog: email, full name, phone, password, role (dropdown)
- Edit user: change role, activate/deactivate
- No delete — only deactivate

**Step 2: Commit**

```bash
git add frontend/src/
git commit -m "feat: update admin user management for RBAC"
```

---

## Task 25: Frontend — Admin Role Management

**Files:**
- Create: `frontend/src/routes/_layout/admin.roles.tsx`
- Create: `frontend/src/components/Admin/RolePermissionMatrix.tsx`

**Step 1: Create roles admin page**

Table of roles with expand to show permission matrix (checkboxes per resource×action).
- Edit permissions for any role
- Create custom roles
- Cannot delete system roles

**Step 2: Create permission matrix component**

Grid of checkboxes: rows = resources, columns = actions. Toggle individual permissions.

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: add role and permission management admin page"
```

---

## Task 26: Remove Legacy Auth Code

**Files:**
- Modify: `backend/app/api/routes/login.py` (simplify — remove password-based login, keep health check)
- Remove or simplify: `backend/app/services/auth.py`
- Clean up: `backend/app/core/security.py` (remove unused password functions if no longer needed)
- Remove: `frontend/src/routes/signup.tsx` (managers create users, no self-signup)

**Step 1: Simplify login routes**

Remove the `/login/access-token` endpoint (Supabase handles login). Keep utility routes.

**Step 2: Clean up unused auth code**

Remove `authenticate()` function and password-related code that's now handled by Supabase.

**Step 3: Remove signup page**

Delete `frontend/src/routes/signup.tsx` — user creation is manager-only via admin panel.

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove legacy auth code replaced by Supabase Auth"
```

---

## Task 27: Final Integration Test

**Step 1: Run full backend test suite**

```bash
cd backend && pytest tests/ -v --tb=short
```

**Step 2: Run frontend type check and lint**

```bash
cd frontend && tsc -p tsconfig.build.json && biome check --write --unsafe ./
```

**Step 3: Regenerate API client**

```bash
cd frontend && bun run generate-client
```

**Step 4: Build frontend**

```bash
cd frontend && bun run build
```

**Step 5: Fix any issues found**

**Step 6: Final commit**

```bash
git add -A
git commit -m "chore: Phase 1 integration fixes and final cleanup"
```

---

## Summary

| Task | Component | Type |
|------|-----------|------|
| 1 | Supabase dependencies & config | Backend infra |
| 2 | Role, Permission, RolePermission models | Backend models |
| 3 | User model update for Supabase + RBAC | Backend models |
| 4 | Supabase JWT validation in deps.py | Backend auth |
| 5 | RBAC repository & seed data | Backend repository |
| 6 | User repository — Supabase integration | Backend repository |
| 7 | User & Role API routes | Backend API |
| 8 | Customer model (full stack) | Backend CRUD |
| 9 | Contact model (full stack) | Backend CRUD |
| 10 | Equipment model (full stack) | Backend CRUD |
| 11 | ServiceRequest model (full stack) | Backend CRUD |
| 12 | ServiceVisit model (full stack) | Backend CRUD |
| 13 | SLAConfig model & service | Backend service |
| 14 | Backend tests — RBAC & Auth | Tests |
| 15 | Backend tests — Customer, Equipment, SR | Tests |
| 16 | Frontend — Supabase Auth setup | Frontend auth |
| 17 | Frontend — Customer list page | Frontend UI |
| 18 | Frontend — Customer detail page | Frontend UI |
| 19 | Frontend — Equipment global page | Frontend UI |
| 20 | Frontend — Service Request list | Frontend UI |
| 21 | Frontend — Service Request detail | Frontend UI |
| 22 | Frontend — Role-specific dashboards | Frontend UI |
| 23 | Frontend — Permission-based navigation | Frontend UI |
| 24 | Frontend — Admin user management | Frontend UI |
| 25 | Frontend — Admin role management | Frontend UI |
| 26 | Remove legacy auth code | Cleanup |
| 27 | Final integration test | QA |
