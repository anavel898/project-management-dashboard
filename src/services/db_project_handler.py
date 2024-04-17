from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session
from src.project_handler_interface import ProjectHandlerInterface
from src.routers.project.schemas import Project
from datetime import datetime
from fastapi import HTTPException
from src.services.project_manager_tables import Projects, ProjectAccess, Users, Documents


class DbProjectHandler(ProjectHandlerInterface):
    def create(self,
               name: str,
               created_by: str,
               description: str,
               db: Session):
        # add new project to Projects table
        new_project = Projects(name=name,
                               created_by=created_by,
                               description=description)
        db.add(new_project)
        db.commit()

        #add new permission of type 'owner' to ProjectAccess
        db.add(ProjectAccess(project_id=new_project.id,
                                  username=created_by,
                                  access_type="owner"))
        db.commit()
        db.close()


    def get(self, project_id: int, db: Session):
        project = db.get(Projects, project_id)
        # if project doesn't exist, raise exception
        if project is None:
            raise HTTPException(status_code=404,
                                detail=f"No project with id {project_id} found")
        # retrieve documents associated to the project
        docs = db.execute(
            select(Documents.id, Documents.name).where(
                Documents.project_id==project_id
            )
        )
        docs_list = [{"id": row[0], "name": row[1]} for row in docs.all()]
        
        # retrieve full list of project contributors
        contributors = db.execute(
            select(ProjectAccess.username).where(
                ProjectAccess.project_id == project_id
            )
        )
        contributors_list = [row[0] for row in contributors.all()]
        db.close()
        project_repr = Project(id=project.id,
                               name=project.name,
                               created_by=project.created_by,
                               created_on=project.created_on,
                               description=project.description,
                               updated_by=project.updated_by,
                               updated_on=project.updated_on,
                               logo=project.logo,
                               documents= None if docs_list == [] else docs_list,
                               contributors=contributors_list)
        return project_repr

    
    def get_all(self, db: Session):
        all_project_ids = db.execute(select(Projects.id))
        all_projects = dict()
        for row in all_project_ids:
            curr_project = self.get(row[0], db)
            all_projects[row[0]] = curr_project
        return all_projects

    
    def delete(self, project_id: int, db: Session):
        db.execute(delete(Projects).where(Projects.id == project_id))
        db.commit()
        db.close()
    
    def update_info(self, project_id: int,
                    attributes_to_update: dict,
                    db: Session):
        if db.get(Projects, project_id) is None:
            raise HTTPException(status_code=404,
                                detail=f"No project with id {project_id} found")
        attributes_to_update.update({"updated_on": datetime.now()})
        
        q = update(Projects).where(Projects.id == project_id).values(
                attributes_to_update
        )
        db.execute(q)
        db.commit()
        db.close()
        return self.get(project_id, db)
    
    def grant_access(self, project_id: int, new_user: str, db: Session):
        new_access = ProjectAccess(project_id=project_id,
                                   username=new_user,
                                   access_type='participant')
        db.add(new_access)
        db.commit()
        db.close()
