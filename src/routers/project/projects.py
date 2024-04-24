from fastapi import APIRouter, HTTPException, Depends, Request, Response, UploadFile
from starlette import status

from sqlalchemy.orm import Session
from src.project_handler_factory import createHandler
from src.routers.project.schemas import NewProject, UpdateProject, Project, InviteProject, ProjectDocument, ProjectLogo, CoreProjectData, ProjectPermission
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
    try:
        project_handler.check_project_exists(project_id, db)
    except HTTPException as ex:
        raise ex
    owned = request.headers["owned"]
    if str(project_id) not in owned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can invite participants"
        )
    try:
        project_handler.grant_access(project_id, new_participant.name, db)
    except HTTPException as ex:
        raise ex
    

@project_router.post("/project/{project_id}/documents", response_model=list[ProjectDocument])
async def upload_document(request: Request,
                          project_id: int,
                          upload_files: list[UploadFile],
                          db: Session = Depends(get_db),
                          project_handler: object = Depends(createHandler)):
    # check project exists
    try:
        project_handler.check_project_exists(project_id, db)
    except HTTPException as ex:
        raise ex
    # check privileges
    owned = request.headers["owned"]
    participating = request.headers["participating"]
    if str(project_id) not in owned.split(" ") and str(project_id) not in participating.split(" "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have access to this project.")
    user_calling = request.headers["username"]
    added_docs = []
    for file in upload_files:
        try:
            contents = await file.read()
            doc = project_handler.associate_document(project_id=project_id,
                                               doc_name=file.filename,
                                               content_type=file.content_type,
                                               caller=user_calling,
                                               byfile=contents,
                                               db=db)
            added_docs.append(doc)
        except HTTPException as ex:
            raise ex
    return added_docs


@project_router.get("/project/{project_id}/documents", response_model=list[ProjectDocument])
async def get_all_documents(request: Request,
                            project_id: int,
                            db: Session = Depends(get_db),
                            project_handler: object = Depends(createHandler)):
    # check project exists
    try:
        project_handler.check_project_exists(project_id, db)
    except HTTPException as ex:
        raise ex
    # check privileges
    owned = request.headers["owned"]
    participating = request.headers["participating"]
    if str(project_id) not in owned.split(" ") and str(project_id) not in participating.split(" "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have access to this project.")
    try:
        return project_handler.get_docs(project_id=project_id, db=db)
    except HTTPException as ex:
        raise ex
    

@project_router.put("/project/{project_id}/logo", response_model=ProjectLogo)
async def upload_project_logo(request: Request,
                              project_id: int,
                              logo: UploadFile,
                              db: Session = Depends(get_db),
                              project_handler: object = Depends(createHandler)):
    # check project exists
    try:
        project_handler.check_project_exists(project_id, db)
    except HTTPException as ex:
        raise ex
    # check privilege
    owned = request.headers["owned"]
    participating = request.headers["participating"]
    if str(project_id) not in owned.split(" ") and str(project_id) not in participating.split(" "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have access to this project.")
    # check valid upload file (content_type is image/png or image/jpg or image/jpeg)
    if logo.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Logo must be a .png or .jpeg file")
    # call method and return created logo
    username = request.headers["username"] 
    content = await logo.read()
    try:
        return project_handler.upload_logo(project_id=project_id,
                                           logo_name=logo.filename,
                                           b_content=content,
                                           logo_poster=username,
                                           db=db)
    except HTTPException as ex:
        raise ex
    

@project_router.get("/project/{project_id}/logo", response_model=ProjectLogo)
async def download_logo(request: Request,
                        project_id: int,
                        db: Session = Depends(get_db),
                        project_handler: object = Depends(createHandler)):
    # check project exists
    try:
        project_handler.check_project_exists(project_id, db)
    except HTTPException as ex:
        raise ex
    # check privilege
    owned = request.headers["owned"]
    participating = request.headers["participating"]
    if str(project_id) not in owned.split(" ") and str(project_id) not in participating.split(" "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have access to this project.")
    # call method and return file response
    try:
        name, content = project_handler.download_logo(project_id=project_id,
                                                      db=db)
        return Response(
            content=content,
            headers={
                "Content-Disposition": f"attachment;filename={name}",
                "Content-Type": "application/octet-stream"
            }
        )
    except HTTPException as ex:
        raise ex
    

@project_router.delete("/project/{project_id}/logo")
async def delete_logo(request: Request,
                      project_id: int,
                      db: Session = Depends(get_db),
                      project_handler: object = Depends(createHandler)):
    # check project exists
    try:
        project_handler.check_project_exists(project_id, db)
    except HTTPException as ex:
        raise ex
    # check privilege
    owned = request.headers["owned"]
    participating = request.headers["participating"]
    if str(project_id) not in owned.split(" ") and str(project_id) not in participating.split(" "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have access to this project.")
    username = request.headers["username"]
    try:
        project_handler.delete_logo(project_id=project_id,
                                    user_calling=username,
                                    db=db)
        return status.HTTP_204_NO_CONTENT
    except HTTPException as ex:
        raise ex
