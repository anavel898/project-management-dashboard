from src.services.inmem_project_handler import InMemProjectHandler
from dotenv import load_dotenv
import os
from src.services.db_project_handler import DbProjectHandler
from src.project_handler_interface import ProjectHandlerInterface

load_dotenv()
LOCAL_STORAGE = os.getenv("LOCAL_STORAGE") in ["True", 1, "1", "true"]

def createHandler() -> ProjectHandlerInterface:
    if LOCAL_STORAGE:
        return InMemProjectHandler()
    else:
        return DbProjectHandler()
