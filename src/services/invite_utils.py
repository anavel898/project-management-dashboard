from datetime import datetime, timedelta, timezone
import os
from fastapi import HTTPException
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from starlette import status

from src.services.project_manager_tables import Users


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")


def decode_join_token(token: str, db: Session):
    join_exception = HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                   detail="Invalid join token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise join_exception
    username: str = payload.get("sub")
    expires: datetime = payload.get("exp")
    project_id: int = payload.get("project")
    if username is None:
        raise join_exception
    elif datetime.fromtimestamp(expires, tz=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Join token expired")
    # check if username from sub claim exists in db
    user = db.get(Users, username)
    if user is None:
        raise join_exception
    return username, project_id


def check_email_validity(email: str,
                         db: Session):
    user = db.execute(select(Users.username).where(Users.email == email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No users are registered with provided email address")
    # ovo je potencijalno mesto za error, nisam sigurna dal samo [0] ili [0][0]
    username = user.all()[0][0]
    return username


def create_join_token(to_encode: dict):
    my_claims = to_encode.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=3)
    my_claims.update({"exp": expire})
    encoded_token = jwt.encode(my_claims, SECRET_KEY, algorithm="HS256")
    return encoded_token