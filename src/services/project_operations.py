from src.project_handler_interface import ProjectHandlerInterface
import json
from fastapi import HTTPException


class Project:    
    def __init__(self, id: int, name: str, ownerId: int, description: str, logo: str = None, documents:str = None, contributors: list[int] = None) -> None:
        self.id = id
        self.name = name
        self.ownerId = ownerId  
        self.description = description
        self.logo = logo
        self.documents = documents
        self.contributors = contributors
    
    def update_attribute(self, attributeName, newAttributeValue) -> None:
        self.__dict__[attributeName] = newAttributeValue

    def to_dict(self) -> dict:
        return {"id": self.id,
                "name": self.name,
                "ownerId": self.ownerId,
                "description": self.description,
                "logo": self.logo,
                "documents": self.documents,
                "contributors": self.contributors}


class InMemProjectHandler(ProjectHandlerInterface):
    def __init__(self) -> None:
        self.allProjects = dict()
        self.projectsNumber = 0


    def create(self, name: str, ownerId: int, description: str, logo: str = None, documents: str = None, contributors: list[int] = None) -> None:
        newProjectId = self.projectsNumber + 1
        newProject = Project(newProjectId, name, ownerId, description, logo, documents, contributors)
        self.allProjects[newProjectId] = newProject
        self.projectsNumber += 1


    def get_all(self) -> object:
        temp_projects = {}
        for key, value in self.allProjects.items():
            temp_projects[key] = value.to_dict()
        return json.dumps(temp_projects)
    

    def get(self, projectId: int) -> object:
        if self.allProjects.get(projectId) is None:
            raise HTTPException(status_code=400, detail=f"no project with id {projectId} found")
        return json.dumps(self.allProjects[projectId].to_dict())

    
    def update_info(self, projectId: int, attributesToUpdate: dict) -> None:
        if self.allProjects.get(projectId) is None:
            raise HTTPException(status_code=400, detail=f"no project with id {projectId} found")
        for item in attributesToUpdate.items():
            if item[1] is not None:
                self.allProjects[projectId].update_attribute(item[0], item[1])
    

