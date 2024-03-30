from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
import json
from src.services.project_operations import projects, all_projects_to_json, create_new_project, edit_existing_project

class NewProject(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(None, max_length=100)
    ownerId: int
    owner: str
    description: str = Field(None, max_length=500)
    logo: str | None = None
    documents: str | None = None
    contributors: list[int] | None = []

class ProjectData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(None, max_length=100)
    ownerId: int | None = None
    owner: str | None = None
    description: str = Field(None, max_length=500)
    logo: str | None = None
    documents: str | None = None
    contributors: list[int] | None = []

router = APIRouter()

@router.get("/projects")
async def get_all_projects():
    return all_projects_to_json(projects)

@router.post("/projects")
async def make_new_project(newProject: NewProject):
    new_id = create_new_project(newProject.name, newProject.ownerId, newProject.owner, newProject.description, newProject.logo, newProject.documents, newProject.contributors)
    return Response(status_code=201)


@router.get("/project/{project_id}/info")
async def get_project_details(project_id: int):
    if projects.get(project_id) is not None:
        return json.dumps(projects[project_id].to_dict())
    else:
        raise HTTPException(status_code=400, detail=f"no project with id {project_id} found")


@router.put("/project/{project_id}/info")
async def update_project_details(project_id:int, newInfo: ProjectData):
    if newInfo.__fields_set__ == set():
        raise HTTPException(status_code=400, detail="Can't update. No project properties were specified in the request body")
    elif projects.get(project_id) is None:
        raise HTTPException(status_code=400, detail=f"no project with id {project_id} found")
    else:
        edit_existing_project(project_id, newInfo.dict())
        return Response(status_code=200)