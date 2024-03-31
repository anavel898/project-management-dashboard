from enum import Enum
from src.services.project_operations import InMemProjectHandler

class ProjectHandlerType(Enum):
    IN_MEMORY = 1

def createHandler(type: ProjectHandlerType) -> object:
    match type:
        case ProjectHandlerType.IN_MEMORY:
            return InMemProjectHandler()
        case _:
            raise ValueError