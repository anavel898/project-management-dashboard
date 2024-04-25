from fastapi import FastAPI, HTTPException
from starlette import status
from jose import JWTError, jwt
from src.dependecies import get_session
from src.services.auth_utils import get_user
from src.services.db_project_handler import DbProjectHandler
from .routers.project import projects
from .routers.auth import auth
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from .routers.documents import documents
from .routers.join import join

app = FastAPI()
app.include_router(projects.project_router)
app.include_router(auth.auth_router)
app.include_router(documents.documents_router)
app.include_router(join.join_router)


load_dotenv()
SECRET_KEY = os.getenv("AUTH_SECRET_KEY")

def is_excluded(path: str):
    paths_excluded_from_authorization = ["/", "/auth", "/login", "/openapi.json", "/docs", "/join"]
    if path not in paths_excluded_from_authorization:
        return False
    else:
        return True

@app.middleware("http")
async def add_user_privilieges_to_header(request, call_next):
    # HTTPException to return if jwt is invalid or expired
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if is_excluded(request.url.path):
        return await call_next(request)
    try:
        # extract token from header
        token = request.headers["Authorization"][7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        expires: datetime = payload.get("exp")
        if username is None:
            raise credentials_exception
        elif datetime.fromtimestamp(expires, tz=timezone.utc) < datetime.now(timezone.utc):
            raise credentials_exception
        db = get_session()
        # if username specified in sub doesn't exist, raise error
        if get_user(db, username) is None:
            raise credentials_exception
        # get owner and participant privileges for authenticated user
        owned, participating = DbProjectHandler.get_project_privileges(db=db, username=username)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No Authorization header")
    except JWTError:
        raise credentials_exception
    # add extracted info into request
    request.state.username = username
    request.state.owned = owned
    request.state.participating = participating
    # proxy the request and return response
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    return {"message": "hello from root!"}

