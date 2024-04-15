from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, select, delete, update
from sqlalchemy.orm import Session
from src.project_handler_interface import ProjectHandlerInterface
from dotenv import load_dotenv
import os
from src.routers.project.schemas import Project
from datetime import datetime
from fastapi import HTTPException


load_dotenv()
username= os.getenv("DB_USERNAME")
password=os.getenv("DB_PASSWORD")
host=os.getenv("DB_HOST")
port=os.getenv("DB_PORT") 
db=os.getenv("DB_NAME")

engine = create_engine(
    f"postgresql://{username}:{password}@{host}:{port}/{db}")

Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# getting mapped classes
Projects = Base.classes.projects
Documents = Base.classes.documents
Users = Base.classes.users
ProjectAccess = Base.classes.project_access

class DbProjectHandler(ProjectHandlerInterface):
    def create(self,
               name: str,
               created_by: str,
               description: str):
        session = Session(engine)
        # add new project to Projects table
        new_project = Projects(name=name,
                               created_by=created_by,
                               description=description)
        session.add(new_project)
        session.commit()

        # add new permission of type 'owner' to ProjectAccess
        session.add(ProjectAccess(project_id=new_project.id,
                                  username=created_by,
                                  access_type="owner"))
        session.commit()
        session.close()


    def get(self, project_id: int):
        session = Session(engine)
        project = session.get(Projects, project_id)
        if project is None:
            raise HTTPException(status_code=404,
                                detail=f"No project with id {project_id} found")
        docs = session.execute(
            select(Documents.id, Documents.name).where(
                Documents.project_id==project_id
            )
        )
        docs_list = [{"id": row[0], "name": row[1]} for row in docs.all()]
        contributors = session.execute(
            select(ProjectAccess.username).where(
                ProjectAccess.project_id == project_id
            )
        )
        contributors_list = [row[0] for row in contributors.all()]
        session.close()
        project_repr = Project(id=project.id,
                               name=project.name,
                               created_by=project.created_by,
                               created_on=project.created_on,
                               description=project.description,
                               updated_by=project.updated_by,
                               updated_on=project.updated_on,
                               logo=project.logo,
                               documents=docs_list,
                               contributors=contributors_list)
        return project_repr

    
    def get_all(self):
        session = Session(engine)
        all_project_ids = session.execute(select(Projects.id))
        all_projects = dict()
        for row in all_project_ids:
            curr_project = self.get(row[0])
            all_projects[row[0]] = curr_project
        return all_projects

    
    def delete(self, project_id: int):
        session = Session(engine)
        session.execute(delete(Projects).where(Projects.id == project_id))
        session.commit()
        session.close()
    
    def update_info(self, project_id: int,
                    attributes_to_update: dict):
        session = Session(engine)
        if session.get(Projects, project_id) is None:
            raise HTTPException(status_code=404,
                                detail=f"No project with id {project_id} found")
        attributes_to_update.update({"updated_on": datetime.now()})
        
        q = update(Projects).where(Projects.id == project_id).values(
                attributes_to_update
        )
        session.execute(q)
        session.commit()
        session.close()
        return self.get(project_id)
