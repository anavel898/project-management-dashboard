from fastapi import APIRouter, HTTPException, Response

from src.project_handler_factory import ProjectHandlerType, createHandler
from src.routers.project.schemas import NewProject, ProjectData

router = APIRouter()
projectHandler = createHandler(ProjectHandlerType.IN_MEMORY)


@router.get("/projects")
async def get_all_projects():
    try:
        return projectHandler.get_all()
    except HTTPException as ex:
        raise ex
    except:
        raise HTTPException(status_code=500)


@router.post("/projects")
async def make_new_project(newProject: NewProject):
    try:
        projectHandler.create(
            newProject.name,
            newProject.createdBy,
            newProject.description,
            newProject.logo,
            newProject.documents,
            newProject.contributors,
        )
        return Response(status_code=201)
    except HTTPException as ex:
        raise ex
    except:
        raise HTTPException(status_code=500)


@router.get("/project/{project_id}/info")
async def get_project_details(project_id: int):
    try:
        return projectHandler.get(project_id)
    except HTTPException as ex:
        raise ex
    except:
        raise HTTPException(status_code=500)


@router.put("/project/{project_id}/info")
async def update_project_details(project_id: int, newInfo: ProjectData):
    if newInfo.__fields_set__ == set("updatedBy"):
        raise HTTPException(
            status_code=400,
            detail="No project properties were specified in the request body",
        )
    try:
        projectHandler.update_info(project_id, newInfo.dict())
        return projectHandler.get(project_id)
    except HTTPException as ex:
        raise ex
    except:
        raise HTTPException(status_code=500)
