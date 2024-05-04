from fastapi import APIRouter, HTTPException, Depends, Request, Response, UploadFile
from starlette import status

from sqlalchemy.orm import Session
from src.logs.logger import get_logger
from src.project_handler_factory import createHandler
from src.routers.project.schemas import NewProject, UpdateProject, Project, InviteProject, ProjectDocument, ProjectLogo, CoreProjectData, ProjectPermission, EmailInviteProject, SentEmailProjectInvite
from src.dependecies import get_db
from src.services.auth_utils import check_privilege
from src.services.aws_utils import SESService
from src.services.invite_utils import get_user_from_email

project_router = APIRouter()
logger = get_logger(__name__)

@project_router.get("/projects", response_model=list[CoreProjectData])
async def get_all_projects(request: Request,
                           db: Session = Depends(get_db),
                           project_handler: object = Depends(createHandler)):
    owned = request.state.owned
    participating = request.state.participating
    accessible = owned + participating
    resp = project_handler.get_all(db, accessible)
    logger.info(f"Successfully retrieved projects for user '{request.state.username}'")
    return resp


@project_router.post("/projects", response_model=Project)
async def make_new_project(request: Request,
                           new_project: NewProject,
                           db: Session = Depends(get_db),
                           project_handler: object = Depends(createHandler)):
    user_calling = request.state.username
    resp = project_handler.create(name=new_project.name,
                                  created_by=user_calling,
                                  description=new_project.description,
                                  db=db)
    logger.info(f"Created new project with id {resp.id} for user '{user_calling}'")
    return resp

@project_router.get("/project/{project_id}/info", response_model=Project)
async def get_project_details(request: Request,
                              project_id: int,
                              db: Session = Depends(get_db),
                              project_handler: object = Depends(createHandler)):
    # check if project exists
    project_handler.get_project_internal(project_id, db)
    # extract user permissions injected by middleware
    owned = request.state.owned
    participating = request.state.participating
    # check appropriate privileges for this operation
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    resp = project_handler.get(project_id=project_id, db=db)
    logger.info(f"Successfully retrieved project with id {project_id}")
    return resp
    

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
    project_handler.get_project_internal(project_id, db)
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
    resp = project_handler.update_info(project_id, for_update, db)
    logger.info(f"Updated project {project_id} details")
    return resp


@project_router.delete("/project/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(request: Request,
                         project_id: int,
                         db: Session = Depends(get_db),
                         project_handler: object = Depends(createHandler)):
    project_handler.get_project_internal(project_id, db)
    owned = request.state.owned
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    owner_status_required=True)        
    project_handler.delete(project_id, db)
    logger.info(f"Project with id {project_id} deleted")
    

@project_router.post("/project/{project_id}/invite", response_model=ProjectPermission)
async def add_collaborator(request: Request,
                           project_id: int,
                           new_participant: InviteProject,
                           db: Session = Depends(get_db),
                           project_handler: object = Depends(createHandler)):
    # check if project exists
    project_handler.get_project_internal(project_id, db)
    owned = request.state.owned
    # check owner privileges
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    owner_status_required=True)
    resp = project_handler.grant_access(project_id, new_participant.name, db)
    logger.info(f"Added user {new_participant.name} as a participant to project {project_id}")
    return resp
    

@project_router.post("/project/{project_id}/documents", response_model=list[ProjectDocument])
async def upload_document(request: Request,
                          project_id: int,
                          upload_files: list[UploadFile],
                          db: Session = Depends(get_db),
                          project_handler: object = Depends(createHandler)):
    # check project exists
    project_handler.get_project_internal(project_id, db)
    # check privileges
    owned = request.state.owned
    participating = request.state.participating
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    user_calling = request.state.username
    added_docs = []
    for file in upload_files:
        contents = await file.read()
        doc = project_handler.associate_document(project_id=project_id,
                                                 doc_name=file.filename,
                                                 content_type=file.content_type,
                                                 caller=user_calling,
                                                 byfile=contents,
                                                 db=db)
        added_docs.append(doc)
    logger.info(f"Added {len(added_docs)} documents to project {project_id}")
    return added_docs


@project_router.get("/project/{project_id}/documents", response_model=list[ProjectDocument])
async def get_all_documents(request: Request,
                            project_id: int,
                            db: Session = Depends(get_db),
                            project_handler: object = Depends(createHandler)):
    # check project exists
    project_handler.get_project_internal(project_id, db)
    # check privileges
    owned = request.state.owned
    participating = request.state.participating
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    resp = project_handler.get_docs(project_id=project_id, db=db)
    logger.info(f"Retrieved info on documents for project {project_id}")
    return resp
    

@project_router.put("/project/{project_id}/logo", response_model=ProjectLogo)
async def upload_project_logo(request: Request,
                              project_id: int,
                              logo: UploadFile,
                              db: Session = Depends(get_db),
                              project_handler: object = Depends(createHandler)):
    # check project exists
    project_handler.get_project_internal(project_id, db)
    # check privilege
    owned = request.state.owned
    participating = request.state.participating
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    # check valid upload file (content_type is image/png or image/jpeg)
    if logo.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Logo must be a .png or .jpeg file")
    # call method and return created logo
    username = request.state.username
    content = await logo.read()
    resp = project_handler.upload_logo(project_id=project_id,
                                       logo_name=logo.filename,
                                       b_content=content,
                                       logo_poster=username,
                                       content_type=logo.content_type,
                                       db=db)
    logger.info(f"Updated logo for project {project_id}")
    return resp
    

@project_router.get("/project/{project_id}/logo", response_model=ProjectLogo)
async def download_logo(request: Request,
                        project_id: int,
                        db: Session = Depends(get_db),
                        project_handler: object = Depends(createHandler)):
    # checks
    project_handler.get_project_internal(project_id, db)
    owned = request.state.owned
    participating = request.state.participating
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    # calling method
    name, content = project_handler.download_logo(project_id=project_id,
                                                      db=db)
    resp = Response(
            content=content,
            headers={
                "Content-Disposition": f"attachment;filename={name}",
                "Content-Type": "application/octet-stream"
            }
        )
    logger.info(f"Retrieved logo for project {project_id}")
    return resp
    

@project_router.delete("/project/{project_id}/logo", status_code=status.HTTP_204_NO_CONTENT)
async def delete_logo(request: Request,
                      project_id: int,
                      db: Session = Depends(get_db),
                      project_handler: object = Depends(createHandler)):
    # check project exists
    project_handler.get_project_internal(project_id, db)

    # check privilege
    owned = request.state.owned
    participating = request.state.participating
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    username = request.state.username
    project_handler.delete_logo(project_id=project_id,
                                user_calling=username,
                                db=db)
    logger.info(f"Deleted logo for project {project_id}")


@project_router.get("/project/{project_id}/share", response_model=SentEmailProjectInvite)
async def send_email_invite(request: Request,
                            project_id: int,
                            email: str,
                            db: Session = Depends(get_db),
                            project_handler: object = Depends(createHandler)):
    project_handler.get_project_internal(project_id, db)
    owned = request.state.owned
    # check owner privileges
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    owner_status_required=True)
    invite_username = get_user_from_email(email, db=db)
    username = request.state.username
    if username == invite_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot invite yourself to project")
    text, token = project_handler.email_invite(project_id=project_id,
                                        invite_sender_username=username,
                                        invite_receiver=invite_username,
                                        email=email,
                                        db=db)
    message_id = SESService.send_email_via_ses(text=text, to_address=email)
    resp = SentEmailProjectInvite(aws_message_id=message_id,
                                  join_token=token)
    logger.info(f"Sent email invite to {invite_username} for project {project_id}")
    return resp
