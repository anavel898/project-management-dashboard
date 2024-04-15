from src.services.inmem_project_handler import InMemProjectHandler
from dotenv import load_dotenv
import os
from src.services.db_project_handler import DbProjectHandler

load_dotenv()
LOCAL_STORAGE = 1 if os.getenv("LOCAL_STORAGE") == "True" else 0

def createHandler() -> object:
    if LOCAL_STORAGE:
        return InMemProjectHandler()
    else:
        return DbProjectHandler()
