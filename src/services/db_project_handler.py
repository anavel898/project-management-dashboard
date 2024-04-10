from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, select, delete, update
from sqlalchemy.orm import Session
from src.project_handler_interface import ProjectHandlerInterface
from json import dumps


# will move to env
username= "anavel"
password="123"
host="localhost"
port=5432 
db="project_manager_test"

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
               createdBy: str,  # not consistent with the interface 
               description: str,
               logo: str = None,
               documents: str = None,   # will remove this and contributors
               contributors: list[int] = None) -> None:
        session = Session(engine)
        # add new project to Projects table
        new_project = Projects(name=name,
                               created_by=createdBy,
                               description=description,
                               logo=logo)
        session.add(new_project)
        session.commit()

        # add new permission of type 'owner' to ProjectAccess
        session.add(ProjectAccess(project_id=new_project.id,
                                  username=createdBy,
                                  access_type="owner"))
        session.commit()
        session.close()


    def get(self, project_id: int):
        session = Session(engine)
        project = session.get(Projects, project_id)
        # create dict with basic project details
        project_as_dict = {"id": project.id,
                           "name": project.name,
                           "created_by": project.created_by,
                           "created_on": project.created_on.isoformat(),
                           "description": project.description,
                           "updated_by": project.updated_by,
                           "updated_on": project.updated_on.isoformat(),
                           "logo": project.logo
                           }
        # add list of project documents
        docs = session.execute(
            select(Documents.id, Documents.name).where(
                Documents.project_id==project_id
            )
        )
        docs_list = [{"id": row[0], "name": row[1]} for row in docs.all()]
        project_as_dict["documents"] = docs_list
        # add list of project contributors
        contributors = session.execute(
            select(ProjectAccess.username, ProjectAccess.access_type).where(
                ProjectAccess.project_id == project_id
            )
        )
        contributors_list = [(row[0], row[1]) for row in contributors.all()]
        project_as_dict["contributors"] = contributors_list
        session.close()
        return dumps(project_as_dict)

    
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
        q = update(Projects).where(Projects.id == project_id).values(
                attributes_to_update
        )
        session.execute(q)
        session.commit()
        session.close()
