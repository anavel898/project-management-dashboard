from fastapi import APIRouter, HTTPException
from starlette import status

from src.project_handler_factory import createHandler
from src.routers.project.schemas import NewProject, ProjectData

router = APIRouter()
project_handler = createHandler()

@router.get("/projects")
async def get_all_projects():
    try:
        return project_handler.get_all()
    except HTTPException as ex:
        raise ex


@router.post("/projects")
async def make_new_project(new_project: NewProject):
    try:
        project_handler.create(
            new_project.name,
            new_project.created_by,
            new_project.description,
            new_project.logo,
            new_project.documents,
            new_project.contributors,
        )
        return status.HTTP_201_CREATED
    except HTTPException as ex:
        raise ex

@router.get("/project/{project_id}/info")
async def get_project_details(project_id: int):
    try:
        return project_handler.get(project_id)
    except HTTPException as ex:
        raise ex


@router.put("/project/{project_id}/info")
async def update_project_details(project_id: int, new_info: ProjectData):
    if new_info.model_fields_set == set("updated_by"):
        raise HTTPException(
            status_code=400,
            detail="No project properties were specified in the request body"
        )
    try:
        project_handler.update_info(project_id,
                                   new_info.model_dump(exclude_unset=True))
        return project_handler.get(project_id)
    except HTTPException as ex:
        raise ex


@router.delete("/project/{project_id}")
async def delete_project(project_id: int):
    try:
        project_handler.delete(project_id)
        return status.HTTP_204_NO_CONTENT
    except HTTPException as ex:
        raise ex   