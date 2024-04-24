from fastapi import APIRouter, HTTPException, Depends, Request
from starlette import status

from sqlalchemy.orm import Session
from src.project_handler_factory import createHandler
from src.routers.project.schemas import NewProject, UpdateProject, Project, InviteProject, ProjectPermission, CoreProjectData
from src.dependecies import get_db
from src.services.auth_utils import check_privilege

project_router = APIRouter()

@project_router.get("/projects", response_model=list[CoreProjectData])
async def get_all_projects(request: Request,
                           db: Session = Depends(get_db),
                           project_handler: object = Depends(createHandler)):
    owned = request.state.owned
    participating = request.state.participating
    accessible = owned + participating
    return project_handler.get_all(db, accessible)


@project_router.post("/projects")
async def make_new_project(request: Request,
                           new_project: NewProject,
                           db: Session = Depends(get_db),
                           project_handler: object = Depends(createHandler)):
    user_calling = request.state.username
    return project_handler.create(name=new_project.name,
                                  created_by=user_calling,
                                  description=new_project.description,
                                  db=db)
    

@project_router.get("/project/{project_id}/info", response_model=Project)
async def get_project_details(request: Request,
                              project_id: int,
                              db: Session = Depends(get_db),
                              project_handler: object = Depends(createHandler)):
    # check if project exists
    project_handler.check_project_exists(project_id, db)
    # extract user permissions injected by middleware
    owned = request.state.owned
    participating = request.state.participating
    # check appropriate privileges for this operation
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    return project_handler.get(project_id=project_id, db=db)
    

@project_router.put("/project/{project_id}/info", response_model=Project)
async def update_project_details(request: Request,
                                 project_id: int,
                                 new_info: UpdateProject,
                                 db: Session = Depends(get_db),
                                 project_handler: object = Depends(createHandler)):
    # check if any fields were set to be updated
    if new_info.model_fields_set == set():
        raise HTTPException(
            status_code=400,
            detail="No project properties were specified in the request body"
        )
    # check if project exists
    project_handler.check_project_exists(project_id, db)
    owned = request.state.owned
    participating = request.state.participating
    # check appropriate privileges
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    # if all checks pass call appropriate handler method
    user_calling = request.state.username
    for_update = new_info.model_dump(exclude_unset=True)
    for_update.update({"updated_by":  user_calling})
    return project_handler.update_info(project_id, for_update, db)


@project_router.delete("/project/{project_id}")
async def delete_project(request: Request,
                         project_id: int,
                         db: Session = Depends(get_db),
                         project_handler: object = Depends(createHandler)):
    project_handler.check_project_exists(project_id, db)
    owned = request.state.owned
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    owner_status_required=True)        
    project_handler.delete(project_id, db)
    return status.HTTP_204_NO_CONTENT
    

@project_router.post("/project/{project_id}/invite", response_model=ProjectPermission)
async def add_collaborator(request: Request,
                           project_id: int,
                           new_participant: InviteProject,
                           db: Session = Depends(get_db),
                           project_handler: object = Depends(createHandler)):
    # check if project exists
    project_handler.check_project_exists(project_id, db)
    owned = request.state.owned
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    owner_status_required=True)  
    return project_handler.grant_access(project_id, new_participant.name, db)
    