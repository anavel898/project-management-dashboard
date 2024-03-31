from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from src.project_handler_factory import createHandler, ProjectHandlerType

class NewProject(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(max_length=100)
    ownerId: int
    description: str = Field(max_length=500)
    logo: str | None = None
    documents: str | None = None
    contributors: list[int] | None = None

class ProjectData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(None, max_length=100)
    ownerId: int | None = None
    description: str = Field(None, max_length=500)
    logo: str | None = None
    documents: str | None = None
    contributors: list[int] | None = None

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
        projectHandler.create(newProject.name, newProject.ownerId, newProject.description, newProject.logo, newProject.documents, newProject.contributors)
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
async def update_project_details(project_id:int, newInfo: ProjectData):
    if newInfo.__fields_set__ == set():
        raise HTTPException(status_code=400, detail="Can't update. No project properties were specified in the request body")
    try:
        projectHandler.update_info(project_id, newInfo.dict())
        return Response(status_code=200)
    except HTTPException as ex:
        raise ex
    except:
        raise HTTPException(status_code=500)
    