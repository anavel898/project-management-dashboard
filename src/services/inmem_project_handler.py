import json

from fastapi import HTTPException

from src.project_handler_interface import ProjectHandlerInterface

from datetime import datetime


class Project:
    """
    Class represents the project managed by the app.
    """

    def __init__(
        self,
        id: int,
        name: str,
        createdBy: int,
        createdOn: datetime,
        description: str,
        updatedOn: datetime = None,
        updatedBy: int = None,
        logo: str = None,
        documents: str = None,
        contributors: list[int] = None,
    ) -> None:
        self.id = id
        self.name = name
        self.createdBy = createdBy
        # upon db implementation this field will be auto-filled with timestamps
        # corresponding to time of row creation
        self.createdOn = createdOn
        self.description = description
        # self.updatedBy tracks who last made updates to project details
        self.updatedBy = updatedBy
        self.updatedOn = updatedOn
        self.logo = logo
        self.documents = documents
        # self.contributors tracks who is allowed to change project details
        self.contributors = contributors

    def update_attribute(self, attributeName, newAttributeValue) -> None:
        self.__dict__[attributeName] = newAttributeValue

    def to_dict(self) -> dict:
        # converting datetime objects to isoformat strings, so the resulting
        # dictionary is compatible with json.dumps()
        updateOnSerializable = None
        if self.updatedOn is not None:
            updateOnSerializable = self.updatedOn.isoformat()
        createdOnSerializable = self.createdOn.isoformat()
        return {
            "id": self.id,
            "name": self.name,
            "createdBy": self.createdBy,
            "createdOn": createdOnSerializable,
            "description": self.description,
            "updatedBy": self.updatedBy,
            "updatedOn": updateOnSerializable,
            "logo": self.logo,
            "documents": self.documents,
            "contributors": self.contributors,
        }


class InMemProjectHandler(ProjectHandlerInterface):
    """
    Class implements the methods of ProjectHandlerInterface.
    Implements only the methods necessary to implement endpoints specified
    by the in memory business logic implementation step.
    """

    def __init__(self) -> None:
        # {ID: Project} dictionary storing all projects managed by the handler
        self.allProjects = dict()
        # tracks number of projects managed by the handler and simulates 
        # auto-incremented ids in database
        self.projectsNumber = 0

    def create(
        self,
        name: str,
        createdBy: int,
        description: str,
        logo: str = None,
        documents: str = None,
        contributors: list[int] = None,
    ) -> None:
        newProjectId = self.projectsNumber + 1
        creationTime = datetime.now()
        newProject = Project(
            newProjectId, name, createdBy, creationTime,
            description, logo, documents, contributors
        )
        self.allProjects[newProjectId] = newProject
        self.projectsNumber += 1

    def get_all(self) -> object:
        projects = {}
        # converting dictionary of {ID: Project} to {ID: project_as_dict} in 
        # order to achieve proper json format
        for key, value in self.allProjects.items():
            projects[key] = value.to_dict()
        return json.dumps(projects)

    def get(self, projectId: int) -> object:
        if self.allProjects.get(projectId) is None:
            raise HTTPException(
                status_code=404, detail=f"No project with id {projectId} found"
            )
        return json.dumps(self.allProjects[projectId].to_dict())

    def update_info(self, projectId: int, attributesToUpdate: dict) -> None:
        if self.allProjects.get(projectId) is None:
            raise HTTPException(
                status_code=404, detail=f"No project with id {projectId} found"
            )
        for key, value in attributesToUpdate.items():
            if value is not None:
                self.allProjects[projectId].update_attribute(key, value)
        updateTime = datetime.now()
        self.allProjects[projectId].update_attribute("updatedOn", updateTime)

    def delete(self, projectId: int):
        try:
            del self.allProjects[projectId]
        except KeyError:
            raise HTTPException(status_code=404,
                                detail=f"No project with id {projectId} found"
                                )