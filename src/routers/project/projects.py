from fastapi import APIRouter, HTTPException, Depends, Request
from starlette import status

from sqlalchemy.orm import Session
from src.project_handler_factory import createHandler
from src.routers.project.schemas import NewProject, UpdateProject, Project
from src.dependecies import get_db

project_router = APIRouter()

@project_router.get("/projects", response_model=list[Project])
async def get_all_projects(request: Request,
                           db: Session = Depends(get_db),
                           project_handler: object = Depends(createHandler)):
    owned = request.headers["owned"]
    participating = request.headers["participating"]
    accessible = []
    for li in [owned, participating]:
        if len(li.rstrip()) != 0:
            accessible = accessible + li.split(" ")
    try:
        return project_handler.get_all(db, accessible)
    except HTTPException as ex:
        raise ex


@project_router.post("/projects")
async def make_new_project(request: Request,
                           new_project: NewProject,
                           db: Session = Depends(get_db),
                           project_handler: object = Depends(createHandler)):
    user_calling = request.headers["username"]
    try:
        return project_handler.create(
            name=new_project.name,
            created_by=user_calling,
            description=new_project.description,
            db=db
        )
    except HTTPException as ex:
        raise ex

@project_router.get("/project/{project_id}/info", response_model=Project)
async def get_project_details(request: Request,
                              project_id: int,
                              db: Session = Depends(get_db),
                              project_handler: object = Depends(createHandler)):
    owned = request.headers["owned"]
    print(owned.split(" "))
    participating = request.headers["participating"]
    print(participating.split(" "))
    # check appropriate privileges
    if str(project_id) not in owned.split(" ") and str(project_id) not in participating.split(" "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have access to this project.")
    try:
        return project_handler.get(project_id, db)
    except HTTPException as ex:
        raise ex


@project_router.put("/project/{project_id}/info", response_model=Project)
async def update_project_details(request: Request,
                                 project_id: int,
                                 new_info: UpdateProject,
                                 db: Session = Depends(get_db),
                                 project_handler: object = Depends(createHandler)):
    if new_info.model_fields_set == set():
        raise HTTPException(
            status_code=400,
            detail="No project properties were specified in the request body"
        )
    owned = request.headers["owned"]
    participating = request.headers["participating"]
    # check appropriate privileges
    if str(project_id) not in owned.split(" ") and str(project_id) not in participating.split(" "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have access to this project.")
    user_calling = request.headers["username"]
    for_update = new_info.model_dump(exclude_unset=True)
    for_update.update({"updated_by":  user_calling})
    try:
        return project_handler.update_info(project_id, for_update, db)
    except HTTPException as ex:
        raise ex


@project_router.delete("/project/{project_id}")
async def delete_project(request: Request,
                         project_id: int,
                         db: Session = Depends(get_db),
                         project_handler: object = Depends(createHandler)):
    owned = request.headers["owned"]
    if str(project_id) not in owned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete it"
        )        
    try:
        project_handler.delete(project_id, db)
        return status.HTTP_204_NO_CONTENT
    except HTTPException as ex:
        raise ex
    

@project_router.post("/project/{project_id}/invite")
async def add_collaborator(request: Request,
                           project_id: int,
                           user: str,
                           db: Session = Depends(get_db),
                           project_handler: object = Depends(createHandler)):
    owned = request.headers["owned"]
    if str(project_id) not in owned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can invite participants"
        )
    try:
        project_handler.grant_access(project_id, user, db)
    except HTTPException as ex:
        raise ex