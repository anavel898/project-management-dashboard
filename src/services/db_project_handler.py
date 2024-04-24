from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.project_handler_interface import ProjectHandlerInterface
from src.routers.project.schemas import CoreProjectData, Project, ProjectPermission
from datetime import datetime
from fastapi import HTTPException
from src.services.project_manager_tables import Projects, ProjectAccess, Documents

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
        project = db.get(Projects, project_id)
        # retrieve documents associated to the project
        docs = db.execute(select(Documents.id, Documents.name).where(
            Documents.project_id==project_id))
        docs_list = [{"id": row[0], "name": row[1]} for row in docs.all()]
        
        # retrieve full list of project contributors
        contributors = db.execute(select(ProjectAccess.username).where(
                    ProjectAccess.project_id == project_id))
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

    
    def get_all(self, db: Session, accessible_projects: list[int]):
        all_projects = list()
        all_project_raw = db.query(Projects.id,
                                   Projects.name,
                                   Projects.description,
                                   Projects.created_by,
                                   Projects.created_on).filter(
                                       Projects.id.in_(accessible_projects))
        for row in all_project_raw.all():
            proj = CoreProjectData(id = row[0],
                                   name = row[1],
                                   description=row[2],
                                   owner=row[3],
                                   created_on=row[4])
            all_projects.append(proj)
        return all_projects

    
    def delete(self, project_id: int, db: Session):
        project = db.get(Projects, project_id)
        db.delete(project)
        db.commit()
    

    def update_info(self, project_id: int,
                    attributes_to_update: dict,
                    db: Session):
        attributes_to_update.update({"updated_on": datetime.now()})
        q = update(Projects).where(Projects.id == project_id).values(
            attributes_to_update)
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


    def grant_access(self, project_id: int, username: str, db: Session):
        new_access = ProjectAccess(project_id=project_id,
                                   username=username,
                                   access_type="participant")
        db.add(new_access)
        db.commit()
        return ProjectPermission(project_id=project_id,
                                 username=username,
                                 role="participant")
        

    @staticmethod
    def get_project_privileges(db: Session, username: str):
        owned_projects = db.execute(select(ProjectAccess.project_id)
                                             .where((ProjectAccess.username == username) &
                                                    (ProjectAccess.access_type == 'owner')))
        participant_projects = db.execute(select(ProjectAccess.project_id)
                                    .where((ProjectAccess.username == username) & 
                                           (ProjectAccess.access_type == 'participant')))
        list_owned_projects = [row[0] for row in owned_projects]
        list_participant_projects = [row[0] for row in participant_projects]
        return list_owned_projects, list_participant_projects

        
