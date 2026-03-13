from sqlmodel import Session

from app.domain.user import UserCreate
from app.models import User
from app.repository import user as user_repo
from tests.utils.utils import random_email, random_lower_string


def create_random_user(db: Session) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = user_repo.create_user(session=db, user_create=user_in)
    return user
