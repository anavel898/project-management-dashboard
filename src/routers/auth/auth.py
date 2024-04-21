from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from sqlalchemy.orm import Session
from src.dependecies import get_db
from src.routers.auth.schemas import Token, User
from src.services.auth_utils import authenticate_user, write_new_user, create_access_token


auth_router = APIRouter()

@auth_router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@auth_router.post("/auth")
async def create_new_user(db: Annotated[Session, Depends(get_db)],
                          new_user: User = Depends(User.as_form),):
    try:
        write_new_user(db, new_user)
        return status.HTTP_201_CREATED
    except HTTPException as ex:
        raise ex
