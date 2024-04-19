from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from src.services.project_manager_tables import Users
from src.routers.auth.schemas import User
from jose import jwt


SECRET_KEY = "c502c12a9cc0af07578e81da09fdf31e1b2730134a613f81730ce525dda57492"
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
    hashed_passw = get_password_hash(user.password)
    passw_byte_version = bytes(hashed_passw, encoding="utf-8")
    new_user = Users(username=user.username,
                     name=user.full_name,
                     email=user.email,
                     password=passw_byte_version)
    db.add(new_user)
    db.commit()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt
    