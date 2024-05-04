from datetime import datetime, timedelta, timezone
import os
from fastapi import HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from starlette import status
from src.logs.logger import get_logger
from src.services.project_manager_tables import Users


load_dotenv()
SECRET_KEY = os.getenv("JOIN_SECRET_KEY")
logger = get_logger(__name__)

def decode_join_token(token: str, db: Session):
    join_exception = HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                   detail="Invalid join token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        logger.error(f"Join token could not be decoded")
        raise join_exception
    username: str = payload.get("sub")
    expires: datetime = payload.get("exp")
    project_id: int = payload.get("project")
    if username is None:
        logger.error(f"Join token does not contain user in payload")
        raise join_exception
    elif datetime.fromtimestamp(expires, tz=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Join token expired")
    # check if username from sub claim exists in db
    user = db.get(Users, username)
    if user is None:
        logger.error(f"Join token with non existent user in payload")
        raise join_exception
    return username, project_id


def get_user_from_email(email: str,
                         db: Session):
    user = db.query(Users.username).filter(Users.email == email)
    if user.all() == []:
        logger.error(f"Join attempted for non-existent user with email {email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No users are registered with provided email address")
    username = user.all()[0][0]
    return username


def create_join_token(to_encode: dict):
    my_claims = to_encode.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=3)
    my_claims.update({"exp": expire})
    encoded_token = jwt.encode(my_claims, SECRET_KEY, algorithm="HS256")
    return encoded_token
