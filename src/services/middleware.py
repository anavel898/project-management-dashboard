from datetime import datetime
from typing import Annotated
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette import status
from src.dependecies import get_session
from src.services.auth_utils import get_user
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        expires: datetime = payload.get("exp")
        if username is None:
            raise credentials_exception
        elif expires < datetime.now():
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db = get_session()
    user = get_user(db=db, username=username)
    if user is None:
        raise credentials_exception
    return user.username

credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

# @app.middleware("http")
# async def add_user_privilieges_to_header(request, call_next, token: Annotated[str, Depends(oauth2_scheme)]):
#     # headers = dict(request.scope['headers'])
#     # headers[b'my_var'] = b'my custom header'
#     # headers[b'owned_projects'] = b"1 2 3 555554 5"
#     # request.scope['headers'] = [(k, v) for k, v in headers.items()]
#     payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#     username: str = payload.get("sub")
#     expires: datetime = payload.get("exp")
#     try:
#         if username is None:
#             raise credentials_exception
#         elif expires < datetime.now():
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     response = await call_next(request)
#     return response



# @app.get("/{some_str}")
# async def root(some_str: str, some_query: str, request: Request):
#     my_var = request.headers["my_var"]
#     owned = request.headers["owned_projects"]
#     owned_list = owned.split()
#     int_list = [int(x) for x in owned_list]
    
#     return {"some_str": some_str, "some_quer": some_query,
#             "my_var": my_var, "owned_projects": int_list}
    

