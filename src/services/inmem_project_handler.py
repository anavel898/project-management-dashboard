from fastapi import HTTPException
from src.project_handler_interface import ProjectHandlerInterface
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class Project(BaseModel):
    """
    Class represents the project managed by the app.
    """
    id: int
    name: str
    created_by: str
    created_on: datetime = Field(default_factory=datetime.now)
    description: str
    updated_on: Optional[datetime] = None
    updated_by: Optional[str] = None
    logo: Optional[str] = None
    documents: Optional[List[str]] = None
    contributors: Optional[List[str]] = None

    def update_attribute(self, attribute_name, new_attribute_value) -> None:
        setattr(self, attribute_name, new_attribute_value)


class InMemProjectHandler(ProjectHandlerInterface):
    """
    Class implements the methods of ProjectHandlerInterface.
    Implements only the methods necessary to implement endpoints specified
    by the in memory business logic implementation step.
    """

    def __init__(self) -> None:
        # {ID: Project} dictionary storing all projects managed by the handler
        self.all_projects = dict()
        # tracks number of projects managed by the handler and simulates 
        # auto-incremented ids in database
        self.projects_number = 0

    def create(
        self,
        name: str,
        created_by: str,
        description: str
    ) -> None:
        new_project_id = self.projects_number + 1
        
        newProject = Project(id=new_project_id,
                             name=name,
                             created_by=created_by,
                             description=description)
        self.all_projects[new_project_id] = newProject
        self.projects_number += 1

    def get_all(self) -> dict:
        return self.all_projects

    def get(self, project_id: int) -> Project:
        if self.all_projects.get(project_id) is None:
            raise HTTPException(
                status_code=404,
                detail=f"No project with id {project_id} found"
            )
        return self.all_projects[project_id]

    def update_info(self,
                    project_id: int,
                    attributes_to_update: dict) -> Project:
        if self.all_projects.get(project_id) is None:
            raise HTTPException(
                status_code=404,
                detail=f"No project with id {project_id} found"
            )
        for key, value in attributes_to_update.items():
            if value is not None:
                self.all_projects[project_id].update_attribute(key, value)
        update_time = datetime.now()
        self.all_projects[project_id].update_attribute("updated_on",
                                                       update_time)
        return self.all_projects[project_id]

    def delete(self, project_id: int):
        try:
            del self.all_projects[project_id]
        except KeyError:
            raise HTTPException(status_code=404,
                                detail=f"No project with id {project_id} found"
                                )
        