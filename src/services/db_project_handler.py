from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.project_handler_interface import ProjectHandlerInterface
from src.routers.project.schemas import Project, ProjectDocument, ProjectLogo
from datetime import datetime
from fastapi import HTTPException
from src.services.documents_utils import delete_file_from_s3, download_file_from_s3, upload_file_to_s3
from src.services.project_manager_tables import Projects, ProjectAccess, Users, Documents
from uuid import uuid4

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

    
    def get_all(self, db: Session, accessible_projects: list[int]):
        all_projects = list()
        for project_id in accessible_projects:
            curr_project = self.get(int(project_id), db)
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


    def grant_access(self, project_id: int, username: str, db: Session):
        new_access = ProjectAccess(project_id=project_id,
                                   username=username,
                                   access_type="participant")
        db.add(new_access)
        db.commit()
        

    @staticmethod
    def get_project_privileges(db: Session, username: str):
        owned_projects = db.execute(select(ProjectAccess.project_id)
                                             .where((ProjectAccess.username == username) &
                                                    (ProjectAccess.access_type == 'owner')))
        participant_projects = db.execute(select(ProjectAccess.project_id)
                                    .where((ProjectAccess.username == username) & 
                                           (ProjectAccess.access_type == 'participant')))
        list_owned_projects = [str(row[0]) for row in owned_projects]
        list_participant_projects = [str(row[0]) for row in participant_projects]
        owned_projects_as_str = " ".join(list_owned_projects)
        participant_projects_as_str = " ".join(list_participant_projects)
        return owned_projects_as_str, participant_projects_as_str


    def associate_document(self,
                           project_id: int,
                           doc_name: str,
                           content_type: str,
                           caller: str,
                           byfile: bytes,
                           db: Session):
        written = False
        new_document = Documents(name=doc_name.strip().replace(" ","-"),
                                 project_id=project_id,
                                 added_by=caller,
                                 content_type=content_type)
        db.add(new_document)
        db.commit()
        while not written:
            # generate uuid and write to db
            try:
                uuid = uuid4()
                to_update = {"s3_key": str(uuid)}
                db.execute(update(Documents)
                           .where(Documents.id == new_document.id)
                           .values(to_update))
                written = True
            except Exception as ex:
                continue
        # upload to s3
        try:
            upload_file_to_s3(bucket_name="project-manager-documents",
                                    key=str(uuid),
                                    bin_file=byfile)
        except Exception as ex:
            raise ex
        
        # commit only if db update and upload to s3 were both success
        db.commit()

        final_document = db.get(Documents, new_document.id)
        return ProjectDocument(id=final_document.id,
                        name=final_document.name,
                        added_by=final_document.added_by,
                        content_type=final_document.content_type,
                        project_id=final_document.project_id)


    def get_docs(self,
                 project_id: int,
                 db: Session):
        all_documents = db.execute(select(Documents.id,
                                          Documents.name,
                                          Documents.added_by,
                                          Documents.content_type)
                                          .where(Documents.project_id == project_id))
        all_docs_formatted = []
        for row in all_documents.all():
            doc = ProjectDocument(id=row[0],
                           name=row[1],
                           added_by=row[2],
                           content_type=row[3],
                           project_id=project_id)
            all_docs_formatted.append(doc)
        return all_docs_formatted
    

    def upload_logo(self,
                    project_id: int,
                    logo_name: str,
                    b_content: bytes,
                    db: Session) -> ProjectLogo:
        logo_key = f"project-{project_id}-logo-{logo_name}"
        q = update(Projects).where(Projects.id == project_id).values(
                {"logo": logo_key}
            )
        try:
            db.execute(q)
            upload_file_to_s3("logos-raw", logo_key, b_content)
        except Exception as ex:
            raise ex
        else:
            # commit update of logo field only if upload finished successfully
            db.commit()
        updated_proj = db.get(Projects, project_id)
        name_for_user = updated_proj.logo[len(f"project-{project_id}-logo-"):]
        return ProjectLogo(project_id=updated_proj.id,
                           logo_name=name_for_user)
    

    def download_logo(self,
                      project_id: int,
                      db: Session):
        proj = db.get(Projects, project_id)
        name_for_user = proj.logo[len(f"project-{project_id}-logo-"):]
        try:
            contents = download_file_from_s3(bucket_name="logos-processed",
                                         key=proj.logo)
        except Exception as ex:
            raise ex
        return name_for_user, contents
    

    def delete_logo(self,
                    project_id: int,
                    db: Session):
        proj = db.get(Projects, project_id)
        try:
            # delete from bucket with resized
            delete_file_from_s3("logos-processed", proj.logo)
            # delete from bucket with original images
            delete_file_from_s3("logos-raw", proj.logo)
            q = update(Projects).where(Projects.id == project_id).values(
                {"logo": None}
            )
            db.execute(q)
        except Exception as ex:
            raise ex
        else:
            db.commit()

        



