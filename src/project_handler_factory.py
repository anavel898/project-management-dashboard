from enum import Enum

from src.services.inmem_project_handler import InMemProjectHandler
from src.services.db_project_handler import DbProjectHandler


class ProjectHandlerType(Enum):
    IN_MEMORY = 1
    DB = 2


def createHandler(type: ProjectHandlerType) -> object:
    match type:
        case ProjectHandlerType.IN_MEMORY:
            return InMemProjectHandler()
        case ProjectHandlerType.DB:
            return DbProjectHandler()
        case _:
            raise ValueError
