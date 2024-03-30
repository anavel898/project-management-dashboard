import json

class Project:
    createdProjects = 0

    def __init__(self, name: str, ownerId: int, owner: str, description: str, logo: str = "", documents:str = "", contributors: list[int] = []) -> None:
        self.id = Project.createdProjects + 1
        self.name = name
        self.ownerId = ownerId  
        self.owner = owner  # when user creation is implemented this will be replaced with a query to find the name of user with id provided as ownerId
        self.description = description
        self.logo = logo
        self.documents = documents
        self.contributors = contributors
        Project.createdProjects += 1
    
    def update_attribute(self, attributeName, newAttributeValue) -> None:
        self.__dict__[attributeName] = newAttributeValue

    def to_dict(self) -> dict:
        return {"id": self.id,
                "name": self.name,
                "ownerId": self.ownerId,
                "owner": self.owner,
                "description": self.description,
                "logo": self.logo,
                "documents": self.documents,
                "contributors": self.contributors}



def all_projects_to_json(projects_dict: dict[int, Project]) -> object:
    temp_projects = {}
    for key, value in projects_dict.items():
        temp_projects[key] = value.to_dict()
    return json.dumps(temp_projects)


def create_new_project(name, ownerId, owner, description, logo, documents, contributors) -> None:
    newProject = Project(name, ownerId, owner, description, logo, documents, contributors)
    projects[Project.createdProjects] = newProject
    return Project.createdProjects


def edit_existing_project(projectId, infoForUpdate) -> None:
    for item in infoForUpdate.items():
        if item[1] is not None:
            projects[projectId].update_attribute(item[0], item[1])



projects = {1:Project("project 1", 1, "Ana Velimirovic", "toy project to test the API"),
            2:Project("project 2", 1, "Ana Velimirovic", "second toy project")}

