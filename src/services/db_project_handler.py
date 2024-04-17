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
        return self.get(new_project.id, db)

    def get(self, project_id: int, db: Session):
        # check if project exists
        try:
            project = self.check_project_exists(project_id, db)
        except HTTPException as ex:
            raise ex
        else:
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
            # create appropriate output format
            project_repr = Project(id=project.id,
                                name=project.name,
                                created_by=project.created_by,
                                created_on=project.created_on,
                                description=project.description,
                                updated_by=project.updated_by,
                                updated_on=project.updated_on,
                                logo=project.logo,
                                documents= docs_list,
                                contributors=contributors_list)
            return project_repr

    
    def get_all(self, db: Session):
        all_project_ids = db.execute(select(Projects.id))
        all_projects = list()
        for row in all_project_ids:
            curr_project = self.get(row[0], db)
            all_projects.append(curr_project)
        return all_projects

    
    def delete(self, project_id: int, db: Session):
        try:
            project = self.check_project_exists(project_id, db)
        except HTTPException as ex:
            raise ex
        else:
            db.delete(project)
            db.commit()
    

    def update_info(self, project_id: int,
                    attributes_to_update: dict,
                    db: Session):
        try:
            self.check_project_exists(project_id, db)
        except HTTPException as ex:
            raise ex
        else:
            attributes_to_update.update({"updated_on": datetime.now()})
            q = update(Projects).where(Projects.id == project_id).values(
                attributes_to_update
            )
            db.execute(q)
            db.commit()
        return self.get(project_id, db)
    

    def check_project_exists(self, project_id: int, db: Session) -> None:
        project = db.get(Projects, project_id)
        if project is None:
            raise HTTPException(status_code=404,
                                detail=f"No project with id {project_id} found")
        else:
            return project
