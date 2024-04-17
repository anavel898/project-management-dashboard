from fastapi import APIRouter, HTTPException, Depends
from starlette import status

from sqlalchemy.orm import Session
from src.project_handler_factory import createHandler
from src.routers.project.schemas import NewProject, UpdateProject, Project
from src.services.database import engine#, SessionLocal
from src.services.project_manager_tables import Base
from src.dependecies import get_db

router = APIRouter()
project_handler = createHandler()
Base.metadata.create_all(bind=engine)

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

@router.get("/projects", response_model=list[Project])
async def get_all_projects(db: Session = Depends(get_db)):
    try:
        return project_handler.get_all(db)
    except HTTPException as ex:
        raise ex


@router.post("/projects", response_model=Project)
async def make_new_project(new_project: NewProject, db: Session = Depends(get_db)):
    try:
        return project_handler.create(
            new_project.name,
            new_project.created_by,
            new_project.description,
            db
        )
    except HTTPException as ex:
        raise ex

@router.get("/project/{project_id}/info", response_model=Project)
async def get_project_details(project_id: int, db: Session = Depends(get_db)):
    try:
        return project_handler.get(project_id, db)
    except HTTPException as ex:
        raise ex


@router.put("/project/{project_id}/info", response_model=Project)
async def update_project_details(project_id: int,
                                 new_info: UpdateProject,
                                 db: Session = Depends(get_db)):
    if new_info.model_fields_set == set("updated_by"):
        raise HTTPException(
            status_code=400,
            detail="No project properties were specified in the request body"
        )
    try:
        return project_handler.update_info(project_id,
                                   new_info.model_dump(exclude_unset=True),
                                   db)
    except HTTPException as ex:
        raise ex


@router.delete("/project/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    try:
        project_handler.delete(project_id, db)
        return status.HTTP_204_NO_CONTENT
    except HTTPException as ex:
        raise ex   