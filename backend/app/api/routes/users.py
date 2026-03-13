import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models.user import User
from app.domain.user import (
    UserCreate,
    UserPublic,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.repository import user as user_repo

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UsersPublic)
def read_users(
    session: SessionDep,
    _: User = Depends(require_permission("user", "view")),
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
    _: User = Depends(require_permission("user", "create")),
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
    _: User = Depends(require_permission("user", "view")),
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
    _: User = Depends(require_permission("user", "edit")),
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
    _: User = Depends(require_permission("user", "edit")),
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
    _: User = Depends(require_permission("user", "edit")),
):
    user = user_repo.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_repo.activate_user(session=session, db_user=user)
    return UserPublic.model_validate(user)
