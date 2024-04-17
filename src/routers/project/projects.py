from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from starlette import status

from sqlalchemy.orm import Session
from src.project_handler_factory import createHandler
from src.routers.project.schemas import NewProject, UpdatableData, Project
from src.services.database import SessionLocal, engine
from src.services.project_manager_tables import Base
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from src.services.auth_utils import SECRET_KEY, ALGORITHM, get_user

project_router = APIRouter()
project_handler = createHandler()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db=SessionLocal()
    user = get_user(db=db, username=username)
    if user is None:
        raise credentials_exception
    return user.username


@project_router.get("/projects", response_model=dict[int, Project])
async def get_all_projects(db: Session = Depends(get_db), user_calling: str = Depends(get_current_user)):
    try:
        print("DA LI JE IDENTIFIKOVAO USER-A?")
        print(user_calling)
        return project_handler.get_all(db)
    except HTTPException as ex:
        raise ex


@project_router.post("/projects")
async def make_new_project(new_project: NewProject,
                           db: Session = Depends(get_db),
                           user_calling: str = Depends(get_current_user)):
    try:
        print("DA LI JE IDENTIFIKOVAO USER-A?")
        print(user_calling)
        project_handler.create(
            name=new_project.name,
            created_by=user_calling,
            description=new_project.description,
            db=db
        )
        return status.HTTP_201_CREATED
    except HTTPException as ex:
        raise ex

@project_router.get("/project/{project_id}/info", response_model=Project)
async def get_project_details(project_id: int,
                              db: Session = Depends(get_db),
                              user_calling: str = Depends(get_current_user)):
    try:
        return project_handler.get(project_id, db)
    except HTTPException as ex:
        raise ex


@project_router.put("/project/{project_id}/info", response_model=Project)
async def update_project_details(project_id: int,
                                 new_info: UpdatableData,
                                 db: Session = Depends(get_db),
                                 user_calling: str = Depends(get_current_user)):
    if new_info.model_fields_set == set():
        raise HTTPException(
            status_code=400,
            detail="No project properties were specified in the request body"
        )
    for_update = new_info.model_dump(exclude_unset=True)
    for_update.update({"updated_by":  user_calling})
    try:
        return project_handler.update_info(project_id, for_update, db)
    except HTTPException as ex:
        raise ex


@project_router.delete("/project/{project_id}")
async def delete_project(project_id: int,
                         db: Session = Depends(get_db),
                         user_calling: str = Depends(get_current_user)):
    try:
        project_handler.delete(project_id, db)
        return status.HTTP_204_NO_CONTENT
    except HTTPException as ex:
        raise ex
    

@project_router.post("/project/{project_id}/invite")
async def add_collaborator(project_id: int,
                           user: str,
                           db: Session = Depends(get_db),
                           user_calling: str = Depends(get_current_user)):
    try:
        project_handler.grant_access(project_id, user, db)
    except HTTPException as ex:
        raise ex