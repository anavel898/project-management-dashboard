from fastapi import APIRouter, Depends, HTTPException
from src.dependecies import get_db
from src.routers.join.schemas import Invite
from src.routers.project.schemas import ProjectPermission
from sqlalchemy.orm import Session
from src.services.db_project_handler import DbProjectHandler
from starlette import status

from src.services.invite_utils import decode_join_token

join_router = APIRouter()

@join_router.get("/join", response_model=ProjectPermission)
async def join_project_via_invite(project_id: int,
                                  join_token: str,
                                  db: Session = Depends(get_db)):
    # check project from query exists
    DbProjectHandler.check_project_exists(project_id=project_id, db=db)
    # decode the join token
    new_user, extracted_project_id = decode_join_token(token=join_token,
                                                       db=db)
    # check if extracted project_id and query project_id don't match
    if extracted_project_id != project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Project ids in token and request body do not match")
    # grant access and return permission representation
    return DbProjectHandler.grant_access(project_id=extracted_project_id,
                                         username=new_user,
                                         db=db)