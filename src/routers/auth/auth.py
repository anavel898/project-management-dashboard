from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from sqlalchemy.orm import Session
from src.project_handler_factory import createHandler
from src.services.database import SessionLocal, engine
from src.services.project_manager_tables import Base
from src.routers.auth.schemas import Token, User
from src.services.auth_utils import authenticate_user, write_new_user, create_access_token


auth_router = APIRouter()
project_handler = createHandler()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    # will call function to write stuff into the database
    try:
        write_new_user(db, new_user)
        return status.HTTP_201_CREATED
    except:
        raise HTTPException(status_code=500)
