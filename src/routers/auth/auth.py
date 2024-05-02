from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from sqlalchemy.orm import Session
from src.dependecies import get_db
from src.routers.auth.schemas import CreatedUser, Token, User
from src.services.auth_utils import authenticate_user, write_new_user, create_access_token
from src.logs.logger import get_logger


auth_router = APIRouter()
logger = get_logger(__name__)

@auth_router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.error(f"Log in for {form_data.username} with password {form_data.password} failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info(f"JWT generated for '{user.username}'")
    return Token(access_token=access_token, token_type="bearer")

@auth_router.post("/auth", response_model=CreatedUser)
async def create_new_user(db: Annotated[Session, Depends(get_db)],
                          new_user: User = Depends(User.as_form),):        
    created_user = write_new_user(db, new_user)
    logger.info(f"Created user with username {created_user.username}")
    return created_user
