from src.services.inmem_project_handler import InMemProjectHandler
from dotenv import load_dotenv
import os
from src.services.db_project_handler import DbProjectHandler

load_dotenv()
LOCAL_STORAGE = os.getenv('LOCAL_STORAGE') == 'True'

def createHandler() -> object:
    if LOCAL_STORAGE:
        return InMemProjectHandler()
    else:
        # will return DBHandler when implemented
        pass

