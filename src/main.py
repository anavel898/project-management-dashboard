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
from datetime import datetime

app = FastAPI()
app.include_router(projects.project_router)
app.include_router(auth.auth_router)

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def is_excluded(path: str):
    paths_excluded_from_authorization = ["/", "/auth", "/login", "/openapi.json", "/docs"]
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
    else:
        try:
            # extract token from header
            token = request.headers["Authorization"][7:]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            username: str = payload.get("sub")
            expires: datetime = payload.get("exp")
            if username is None:
                raise credentials_exception
            elif datetime.fromtimestamp(expires) < datetime.now():
                raise credentials_exception
            db = get_session()
            # if username specified in sub doesn't exist, raise error
            if get_user(db, username) is None:
                raise credentials_exception
            # get owner and participant privileges for authenticated user
            owned, participating = DbProjectHandler().get_project_privileges(db=db, username=username)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="No Authorization header")
        except JWTError:
            raise credentials_exception
        # add extracted info into request header
        headers = dict(request.scope['headers'])
        headers[b'username'] = bytes(username, "utf-8")
        headers[b'owned'] = bytes(owned, "utf-8")
        headers[b'participating'] = bytes(participating, "utf-8")
        request.scope['headers'] = [(k, v) for k, v in headers.items()]
        response = await call_next(request)
        return response

@app.get("/")
async def root():
    return {"message": "hello from root!"}

