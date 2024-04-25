from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from src.services.project_manager_tables import Users
from src.routers.auth.schemas import CreatedUser, User
from jose import jwt
from starlette import status
from dotenv import load_dotenv
import os


load_dotenv()
SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db, username: str, given_password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(given_password, user.password):
        return False
    return user

def get_user(db: Session, username: str):
    user = db.get(Users, username)
    db.close()
    return user

def write_new_user(db: Session, user: User):
    if db.get(Users, user.username) is not None:
        raise HTTPException(status_code=400,
                            detail=f"Username '{user.username}' is already taken")
    hashed_passw = get_password_hash(user.password)
    passw_byte_version = bytes(hashed_passw, encoding="utf-8")
    new_user = Users(username=user.username,
                     name=user.full_name,
                     email=user.email,
                     password=passw_byte_version)
    db.add(new_user)
    db.commit()
    created_user = db.get(Users, user.username)
    return CreatedUser(username=created_user.username,
                       full_name=created_user.name,
                       email=created_user.email)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def check_privilege(project_id: int,
                    owned_projects: list[int],
                    participating_projects: list[int] = [],
                    owner_status_required: bool = False):
    if owner_status_required:
        if project_id not in owned_projects:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Only project owners can perform this action.")
    else:
        if project_id not in owned_projects and project_id not in participating_projects:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You don't have access to this project.")